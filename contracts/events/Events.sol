pragma solidity ^0.5.11;
pragma experimental ABIEncoderV2;

import "../utils/Ownable.sol";
import "../utils/Feeless.sol";
import "../identity/IdentityInterface.sol";
import "../events/EventsInterface.sol";
//import "../identity/Identity.sol";
import "../tokens/ERC1155.sol";
import "../tokens/IERC20.sol";

/**
 * @title EventMasterService
 * @dev This contract allows to create events and adding section data to the events.
 *      Then it can be used to buy seat tickets on specific events paying with ERC20 token.
 */
contract EventMasterService is EventMasterServiceInterface,Ownable,ERC1155,Feeless {

    IdentityMasterServiceInterface identityMaster;

    uint32 nextNewEventId = 1;
    uint256 basicPointFees = 0;
    uint256 basicPointGaslessPremium = 0;

    struct SectionData {
        uint16 size;
        uint256 price;
        mapping(uint16 => bool) wasSold;
    }
    struct EventData {
        address owner;
        uint256 funds;
        uint256 platform;
        uint16 numberOfSections;
        uint16 totalSeats;
        uint256 startSellingDate;
        uint256 startWithdrawalDate;
        mapping(uint16 => SectionData) sectionDataMap;
    }
    mapping (uint32 => EventData) eventDataMap;

    mapping (uint256 => uint256) platformFeesCollected;

    // Events
    event ReceivedTokens(address _from, uint256 _value, address _token);

    ///////////////////////////////////////////////////////////
    /// Constructor                                         ///
    ///////////////////////////////////////////////////////////

    /**
     * @dev Constructor, creates EventMasterService.
     * @param initialIdentityMaster Service used to map address to identities
     * and checking permissions.
     * @param setBasicPointFees Global percentage points charged as fess (100 = 1%)
     */
    constructor(address initialIdentityMaster, uint256 setBasicPointFees, uint256 setBasicPointGaslessPremium) public {
        identityMaster = IdentityMasterServiceInterface(initialIdentityMaster);
        basicPointFees = setBasicPointFees;
        basicPointGaslessPremium = setBasicPointGaslessPremium;
        // percentualFees
    }

    ///////////////////////////////////////////////////////////
    /// Pure (read-only, calculation not accessing storage) ///
    ///////////////////////////////////////////////////////////

    /**
     * @dev Pure read-only helper function, not reading contract state.
     * @param eventID Specific event we want to calculate ticketID for
     * @param sectionID Specific section we want to calculate ticketID for
     * @param seatID Specific seatID we want to calculate ticketID for
     */
    function getTicketID(uint32 eventID, uint16 sectionID, uint16 seatID) public pure returns(uint256) {
        uint256 ret = 0;
        ret = uint256(eventID) << 32;
        ret = (ret | (uint256(sectionID) * (2**16)) ) | uint256(seatID);
        return ret;
    }

    /**
     * @dev Pure read-only helper function, inverse projection of getTicketID().
     * @param ticketID Specific ticketID we want get eventID.
     */
    function getEventIDFromTicketID(uint256 ticketID) public pure returns(uint32) {
        return uint32(ticketID >> 32);
    }

    /**
     * @dev Pure read-only helper function, inverse projection of getTicketID().
     * @param ticketID Specific ticketID we want get sectionID.
     */
    function getSectionIDFromTicketID(uint256 ticketID) public pure returns(uint16) {
        return uint16((ticketID & 0xffff0000) >> 16);
    }

    /**
     * @dev Pure read-only helper function, inverse projection of getTicketID().
     * @param ticketID Specific ticketID we want get seatID.
     */
    function getSeatIDFromTicketID(uint256 ticketID) public pure returns(uint16) {
        return uint16((ticketID & 0xffff));
    }

    ///////////////////////////////////////////////////////////
    /// Write operations                                    ///
    ///////////////////////////////////////////////////////////

    /**
     * @dev Mutator method, changes state.
     * @param platID Specific identity and permissions platform that will cater this event
     */
    function createEvent(uint256 platID, uint256 startSellingDate, uint256 startWithdrawalDate) external feeless returns(uint256) {
        require(identityMaster.existsPlatform(platID), "Identity platform has not been registered before.");

        uint256 identity = identityMaster.resolveIdentityOnPlatform(platID, msgSender);

        require(identityMaster.canCreateEventOnPlatform(platID, identity),
            "Ident. of sender has no permission to create event on this ticket platform.");

        uint32 newId = nextNewEventId;
        nextNewEventId++;

        eventDataMap[newId] = EventData(msgSender, 0, platID, 0, 0, startSellingDate, startWithdrawalDate);
        return newId;
    }

    /**
     * @dev Mutator method, adds new sections to an event.
     * @param eventID Specific event the section will belong to
     * @param size Number of seats in this section
     * @param price Cost (in tokens) of a seat in this section, all seats in section has the same
     */
    function addSection(uint32 eventID, uint16 size, uint256 price ) external feeless returns(uint16) {
        require(existsEvent(eventID), "EventID does not exists.");
        require(msgSender == eventDataMap[eventID].owner, "Only event owner can add sections.");

        // Check max seats for this ticketing platform.
        // Check if sender has permission to buy tickets.
        uint256 platID = eventDataMap[eventID].platform;
        uint256 maxSeats = identityMaster.resolveMaxSeatsForPlatform(platID);
        require( eventDataMap[eventID].totalSeats + size <= maxSeats,
            "Too many seats for this ticket platform on this event.");

        eventDataMap[eventID].numberOfSections++;
        uint16 eventSection = eventDataMap[eventID].numberOfSections;

        SectionData memory sectionData;
        sectionData.size = size;
        sectionData.price = price;
        eventDataMap[eventID].sectionDataMap[eventSection] = sectionData;
        eventDataMap[eventID].totalSeats += size;

        return eventSection;
    }

    /**
     * @dev Mutator method, must call previously approve() token method to give the allowance to collect the token here.
     * @param eventID Specific event we want to buy
     * @param sectionID Specific section of the buy
     * @param seatID Specific seatID of the event we want to buy
     */
    function buyTicketWithTokens(uint32 eventID, uint16 sectionID, uint16 seatID) external feeless returns(uint256) {
        require(existsEvent(eventID), "EventID does not exists.");
        require(sectionID > 0 && sectionID <= numberOfSections(eventID), "SectionID does not exists for this event.");
        require(seatID > 0 && seatID <= sectionSize(eventID,sectionID), "SeatID does not exists for this event and section.");

        // Check start of selling date.
        require(block.timestamp >= eventDataMap[eventID].startSellingDate,
                "Event has not reached the start of ticket selling date.");
    
        // Check if sender has permission to buy tickets.
        uint256 platID = eventDataMap[eventID].platform;
        uint256 identity = identityMaster.resolveIdentityOnPlatform(platID, msgSender);

        require(identityMaster.canBuyTicketOnPlatform(platID, identity),
            "Identity of sender has no permission to buy tickets on this ticket platform.");

        uint256 ticketID = getTicketID(eventID, sectionID, seatID);

        require(eventDataMap[eventID].sectionDataMap[sectionID].wasSold[seatID] == false, "Ticket has already been sold.");

        // Resolve type of token per user.
        address token = identityMaster.resolveCurrencyForPlatform(platID);
        IERC20 tokenContract = IERC20(token);
        uint256 allowance = tokenContract.allowance(msgSender,address(this));
        uint256 sectPriceWithFees = sectionPrice(eventID, sectionID) + sectionFee(eventID, sectionID);

        require(allowance >= sectPriceWithFees, "Not enough tokens provided in tx to buy the ticket plus fees.");

        // Combining eventId+sectionId+seatId we get a ticketId
        eventDataMap[eventID].sectionDataMap[sectionID].wasSold[seatID] = true;
        eventDataMap[eventID].funds += sectionPrice(eventID, sectionID);
        platformFeesCollected[platID] += sectionFee(eventID, sectionID);

        balances[ticketID][msgSender] = 1;

        // Recieve tokens.
        require(tokenContract.transferFrom(msgSender, address(this), sectPriceWithFees),
            "Not enough balance to transfer this amount of tokens.");

        emit ReceivedTokens(msgSender, sectPriceWithFees, token);

        return ticketID;
    }

    /**
     * @dev Mutator method, must call previously approve() token method to give the allowance to collect the token here.
     * @param eventID Specific event we want to buy
     * @param sectionIDs Specific sections of the batch buy
     * @param seatIDs Specific seatIDs of the events we want to buy in this batch, same length as sectionIDs
     */
    function buyTicketsBatchWithTokens(uint32 eventID, uint16[] calldata sectionIDs, uint16[] calldata seatIDs) external feeless {
        require(sectionIDs.length == seatIDs.length, "Section and Seat arrays must have the same length.");
        require(existsEvent(eventID), "EventID does not exists.");

        // Check start of selling date.
        require(block.timestamp >= eventDataMap[eventID].startSellingDate, "Event has not reached the start of ticket selling date.");

        // Check if sender has permission to buy tickets.
        uint256 platID = eventDataMap[eventID].platform;
        uint256 identity = identityMaster.resolveIdentityOnPlatform(platID, msgSender);
        require(identityMaster.canBuyTicketOnPlatform(platID, identity),
            "Identity of sender has no permission to buy tickets on this ticket platform.");

        uint256 totalCost = 0;
        uint256 totalFees = 0;

        for (uint i = 0; i < sectionIDs.length; i++) {
            require(sectionIDs[i] > 0 && sectionIDs[i] <= numberOfSections(eventID), "SectionID does not exists for this event.");
            require(seatIDs[i] > 0 && seatIDs[i] <= sectionSize(eventID,sectionIDs[i]),
                "SeatID does not exists for this SectionID on this event.");
            
            uint256 ticketID = getTicketID(eventID, sectionIDs[i], seatIDs[i]);
            require(eventDataMap[eventID].sectionDataMap[sectionIDs[i]].wasSold[seatIDs[i]] == false, "Ticket has already been sold.");
            
            totalCost += sectionPrice(eventID,sectionIDs[i]) + sectionFee(eventID,sectionIDs[i]);
            totalFees += sectionFee(eventID,sectionIDs[i]);
            
            // combining eventId+sectionId+seatId we get a ticketId
            eventDataMap[eventID].sectionDataMap[sectionIDs[i]].wasSold[seatIDs[i]] = true;
            balances[ticketID][msgSender] = 1;
        }

        // Resolve type of token per user.
        address token = identityMaster.resolveCurrencyForPlatform(platID);
        IERC20 tokenContract = IERC20(token);
        
        uint256 allowance = tokenContract.allowance(msgSender,address(this));
        require(allowance >= totalCost, "Not enough tokens provided in tx to buy the batch of tickets plus fees.");
        
        eventDataMap[eventID].funds += (totalCost - totalFees);
        platformFeesCollected[platID] += totalFees;

        // Receive tokens.
        require(tokenContract.transferFrom(msgSender, address(this), totalCost),
            "Not enough balance to transfer this amount of tokens.");

        emit ReceivedTokens(msgSender, totalCost, token);
    }

    /**
     * @dev Mutator method, only change token fees collected stores for one ticketing platform.
     * @param platID Specific platform id we want to deal with.
     */
    function withdrawFees(uint256 platID) external onlyOwner {
        require(identityMaster.existsPlatform(platID), "Identity platform has not been registered before.");

        // Get currency token.
        address token = identityMaster.resolveCurrencyForPlatform(platID);
        IERC20 tokenContract = IERC20(token);

        // How much was collected.
        uint256 collected = platformFeesCollected[platID];
        platformFeesCollected[platID] = 0;
        tokenContract.transfer(msg.sender, collected);
    }

    /**
     * @dev Mutator method, only change token funds stores for one event.
     * @param eventID Specific event we want to buy
     */
    function withdrawFunds(uint32 eventID) external feeless {
        require(existsEvent(eventID), "EventID does not exists.");
        require(eventDataMap[eventID].owner == msgSender, "Only owner of the event can withdraw funds.");

        // Check start of selling date.
        require(block.timestamp >= eventDataMap[eventID].startWithdrawalDate,
                "Event has not reached the start of event funds withdrawal date.");

        // Get platform and token currency.
        uint256 platID = eventDataMap[eventID].platform;
        address token = identityMaster.resolveCurrencyForPlatform(platID);
        IERC20 tokenContract = IERC20(token);

        // How much was collected.
        uint256 collected = eventDataMap[eventID].funds;
        eventDataMap[eventID].funds = 0;
        tokenContract.transfer(msgSender, collected);
    }

    /**
     * @dev Mutator method, setter of ticket fees charged by Ticket system.
     * @param basicPoints 1/100th of 1% applied to ticket price
     */
    function setBasicPointsFees(uint256 basicPoints) external onlyOwner {
        basicPointFees = basicPoints;
    }

    /**
     * @dev Mutator method, setter of ticket fees charged by Ticket system in case of metatx.
     * @param basicPointsPremium 1/100th of 1% applied to ticket price if using Feeless Metratransaction
     */
    function setBasicPointsFeelessPremium(uint256 basicPointsPremium) external onlyOwner {
        basicPointGaslessPremium = basicPointsPremium;
    }

    ///////////////////////////////////////////////////////////
    /// Write operations (Overriding parent contracts)      ///
    ///////////////////////////////////////////////////////////

    /**
     * @dev Mutator method, Override transfer functions to check ticket reseller permissions.
     *      Overrides method from IERC155.sol
     * @param _from    Source address
     * @param _to      Target address
     * @param _id      ID of the token type
     * @param _value   Transfer amount
     * @param _data    Additional data with no specified format, MUST be sent unaltered in call to `onERC1155Received` on `_to`
     */
    function safeTransferFrom(address _from, address _to, uint256 _id, uint256 _value, bytes calldata _data) external {

        require(_to != address(0x0), "_to must be non-zero.");
        require(_from == msg.sender || operatorApproval[_from][msg.sender] == true, "Need operator approval for 3rd party transfers.");

        // Begin Permission Check: Check RESELL permission first for owner of ticket.
        uint32 eventID = getEventIDFromTicketID(_id);
        uint256 platID = eventDataMap[eventID].platform;
        uint256 identity = identityMaster.resolveIdentityOnPlatform(platID, _from);
        require(identityMaster.canResellTicketOnPlatform(platID, identity),
            "Sender has no permission to transfer tickets on this ticket platform.");
        // End Permission Check: Check RESELL permission first for owner of ticket.

        // Begin Permission Check: Check BUYTICKET permission for receiver.
        identity = identityMaster.resolveIdentityOnPlatform(platID, _to);
        require(identityMaster.canResellTicketOnPlatform(platID, identity),
            "Receiver has no permit to receive or buy tickets on this ticket platform.");
        // End Permission Check: Check BUYTICKET permission for receiver.

        // SafeMath will throw with insuficient funds _from
        // or if _id is not valid (balance will be 0)
        balances[_id][_from] = balances[_id][_from].sub(_value);
        balances[_id][_to] = _value.add(balances[_id][_to]);

        // MUST emit event
        emit TransferSingle(msg.sender, _from, _to, _id, _value);

        // Now that the balance is updated and the event was emitted,
        // call onERC1155Received if the destination is a contract.
        if (_to.isContract()) {
            _doSafeTransferAcceptanceCheck(msg.sender, _from, _to, _id, _value, _data);
        }
    }

    /**
     * @dev Mutator method, Override transfer functions to check ticket reseller permissions.
     *      Overrides method from IERC155.sol
     * @param _from    Source address
     * @param _to      Target address
     * @param _ids     IDs of each token type (order and length must match _values array)
     * @param _values  Transfer amounts per token type (order and length must match _ids array)
     * @param _data    Additional data with no specified format, MUST be sent unaltered in call to the `ERC1155TokenReceiver` hook(s) on `_to`
    */
    function safeBatchTransferFrom(address _from, address _to, uint256[] calldata _ids, uint256[] calldata _values,
                                    bytes calldata _data) external {

        // MUST Throw on errors
        require(_to != address(0x0), "destination address must be non-zero.");
        require(_ids.length == _values.length && _values.length > 0, "_ids and _values array lenght must match.");
        require(_from == msg.sender || operatorApproval[_from][msg.sender] == true, "Need operator approval for 3rd party transfers.");

        // Begin Permission Check: Check RESELL permission first for owner of ticket.
        uint32 eventID = getEventIDFromTicketID(_ids[0]);
        uint256 platID = eventDataMap[eventID].platform;
        uint256 identity = identityMaster.resolveIdentityOnPlatform(platID, _from);
        require(identityMaster.canResellTicketOnPlatform(platID, identity),
            "Sender has no permission to transfer tickets on this ticket platform.");
        // End Permission Check: Check RESELL permission first for owner of ticket.

        // Begin Permission Check: Check BUYTICKET permission for receiver.
        identity = identityMaster.resolveIdentityOnPlatform(platID, _to);
        require(identityMaster.canResellTicketOnPlatform(platID, identity),
            "Receiver has no permit to receive or buy tickets on this ticket platform.");
        // End Permission Check: Check BUYTICKET permission for receiver.

        for (uint256 i = 0; i < _ids.length; ++i) {
            // SafeMath will throw with insuficient funds _from
            // or if _id is not valid (balance will be 0)
            balances[_ids[i]][_from] = balances[_ids[i]][_from].sub(_values[i]);
            balances[_ids[i]][_to] = _values[i].add(balances[_ids[i]][_to]);
        }

        // Note: instead of the below batch versions of event and acceptance check you MAY have emitted a TransferSingle
        // event and a subsequent call to _doSafeTransferAcceptanceCheck in above loop for each balance change instead.
        // Or emitted a TransferSingle event for each in the loop and then the single _doSafeBatchTransferAcceptanceCheck below.
        // However it is implemented the balance changes and events MUST match when a check (i.e. calling an external contract) is done.

        // MUST emit event
        emit TransferBatch(msg.sender, _from, _to, _ids, _values);

        // Now that the balances are updated and the events are emitted,
        // call onERC1155BatchReceived if the destination is a contract.
        if (_to.isContract()) {
            _doSafeBatchTransferAcceptanceCheck(msg.sender, _from, _to, _ids, _values, _data);
        }
    }

    ///////////////////////////////////////////////////////////
    /// View functions, read-only accessing state.          ///
    ///////////////////////////////////////////////////////////

    /**
     * @dev Observer method, gives boolean for existance of the event.
     * @param eventID Specific event we want to check
     */
    function existsEvent(uint32 eventID) public view returns(bool) {
        return eventDataMap[eventID].owner != address(0);
    }

    /**
     * @dev Observer method, gives how many sections an event has.
     * @param eventID Specific event we want to check
     */
    function numberOfSections(uint32 eventID) public view returns(uint16) {
        require(existsEvent(eventID), "EventID does not exists.");

        return eventDataMap[eventID].numberOfSections;
    }

    /**
     * @dev Observer method, gives how many sections an event has.
     * @param eventID Specific event we want to check
     * TODO: add tests for this.
     */
    function sectionSize(uint32 eventID, uint16 sectionID) public view returns(uint16) {
        require(existsEvent(eventID), "EventID does not exists.");
        require(sectionID > 0 && sectionID <= numberOfSections(eventID), "SectionID does not exists for this event.");

        return eventDataMap[eventID].sectionDataMap[sectionID].size;
    }

    /**
     * @dev Observer method, gives price each seat an event has.
     * @param eventID Specific event we want to check
     * TODO: add tests for this.
     */
    function sectionPrice(uint32 eventID, uint16 sectionID) public view returns(uint256) {
        require(existsEvent(eventID), "EventID does not exists.");
        require(sectionID > 0 && sectionID <= numberOfSections(eventID), "SectionID does not exists for this event.");

        return eventDataMap[eventID].sectionDataMap[sectionID].price;
    }

    /**
     * @dev Observer method, gives fee (in tokens) each seat sell has for this event.
     * @param eventID Specific event we want to check
     * TODO: add tests for this.
     */
    function sectionFee(uint32 eventID, uint16 sectionID) public view returns(uint256) {
        require(existsEvent(eventID), "EventID does not exists.");
        require(sectionID > 0 && sectionID <= numberOfSections(eventID), "SectionID does not exists for this event.");

        uint256 totalBasicPointFees = basicPointFees;
        if (isFeelessTransaction()) {
            totalBasicPointFees += basicPointGaslessPremium;
        }
        return eventDataMap[eventID].sectionDataMap[sectionID].price * totalBasicPointFees/10000;
    }

    /**
     * @dev Observer function, gives disponibility of the ticket, true if never sold.
     * @param eventID Specific event we want to check
     * @param sectionID Specific section of the event
     * @param seatID Specific seatID of the event we want to check
     */
    function ticketIsAvailable(uint32 eventID, uint16 sectionID, uint16 seatID) external view returns(bool) {
        return eventDataMap[eventID].sectionDataMap[sectionID].wasSold[seatID] == false;
    }

    /**
     * @dev Observer function, confirms ownership of the ticket, true if belongs to specific address.
     * @param eventID Specific event we want to check
     * @param sectionID Specific section of the event
     * @param seatID Specific seatID of the event we want to check
     * @param belongs Address we want to confirm is owner of ticket, or not.
     */
    function doesTicketBelongTo(uint32 eventID, uint16 sectionID, uint16 seatID, address belongs) external view returns(bool) {
        require(belongs != address(0), "Zero-account address(0) address not allowed.");
        uint256 ticketID = getTicketID(eventID, sectionID, seatID);
        return balances[ticketID][belongs] == 1;
    }


    /**
     * @dev Observer function, same as prev but now we directly send the ticketId and the address to check.
     * @param ticketID Specific ticketID we want to confirm ownwership
     * @param belongs Address we want to confirm is owner of ticket, or not
     */
    function doesTicketIdBelongTo(uint256 ticketID, address belongs) external view returns(bool) {
        require(belongs != address(0), "Zero-account address(0) address not allowed.");
        return balances[ticketID][belongs] == 1;
    }


}
