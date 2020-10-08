pragma solidity ^0.5.11;
pragma experimental ABIEncoderV2;

contract EventMasterServiceInterface {

    // pure (read-only, calculation not accessing storage)
    function getTicketID(uint32 eventID, uint16 sectionID, uint16 seatID) public pure returns(uint256);
    function getEventIDFromTicketID(uint256 ticketID) public pure returns(uint32);
    function getSectionIDFromTicketID(uint256 ticketID) public pure returns(uint16);
    function getSeatIDFromTicketID(uint256 ticketID) public pure returns(uint16);

    // write
    function createEvent(uint256 platID, uint256 startSellingDate, uint256 startWithdrawalDate) external returns(uint256);
    function addSection(uint32 eventID, uint16 size, uint256 price ) external returns(uint16);
    function buyTicketWithTokens(uint32 eventID, uint16 sectionID, uint16 seatID) external returns(uint256);
    function buyTicketsBatchWithTokens(uint32 eventID, uint16[] calldata sectionIDs, uint16[] calldata seatIDs) external;
    function withdrawFunds(uint32 eventID) external;
    function withdrawFees(uint256 platID) external;
    function setBasicPointsFees(uint256 basicPoints) external;
    function setBasicPointsFeelessPremium(uint256 basicPointsPremium) external;

    // view (read-only)
    function existsEvent(uint32 eventID) public view returns(bool);
    function numberOfSections(uint32 eventID) public view returns(uint16);
    function sectionSize(uint32 eventID, uint16 sectionID) public view returns(uint16);
    function sectionPrice(uint32 eventID, uint16 sectionID) public view returns(uint256);
    function sectionFee(uint32 eventID, uint16 sectionID) public view returns(uint256);
    function ticketIsAvailable(uint32 eventID, uint16 sectionID, uint16 seatID) external view returns(bool);
    function doesTicketBelongTo(uint32 eventID, uint16 sectionID, uint16 seatID, address belongs) external view returns(bool);
    function doesTicketIdBelongTo(uint256 ticketID, address belongs) external view returns(bool);

}
