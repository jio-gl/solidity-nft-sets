pragma solidity ^0.5.11;

import "./IdentityInterface.sol";
import "../utils/Ownable.sol";


contract IdentityMasterService is IdentityMasterServiceInterface,Ownable {

    uint256 nextNewPlatformId = 1;
    // Mapping from platform id to resolver.
    // numerical platform identities to resolver addresses.
    mapping (uint256 => address) platformsMap;
    // Mapping from platform id to resolver.
    // numerical platform identities to resolver addresses.
    mapping (uint256 => uint256) maxSeatsMap;
    // Mapping from platform id to currency.
    // numerical platform identities to currency token addresses.
    mapping (uint256 => address) currencyMap;
    // resolver addresses to num platform identities
    mapping (address => uint256) reversePlatformsMap;
    // user addresses to num platform identities
    mapping (address => uint256) userAddrToPlatIDMap;

    function registerPlatform ( address resolver, address currencyToken, uint256 maxSeatsPerEvent ) external onlyOwner returns ( uint256 ) {
        require(resolver != address(0), "Zero-account address(0) address not allowed.");
        uint256 newId = nextNewPlatformId;
        nextNewPlatformId++;
        platformsMap[newId] = resolver;
        maxSeatsMap[newId] = maxSeatsPerEvent;
        currencyMap[newId] = currencyToken;
        reversePlatformsMap[resolver] = newId;
        return newId;
    }

    function deregisterPlatform ( uint256 platID ) external onlyOwner {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        platformsMap[platID] = address(0);
    }

    function resolveCurrencyForPlatform (uint256 platID) external view returns (address) {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        return currencyMap[platID];
    }

    function resolveMaxSeatsForPlatform (uint256 platID) external view returns (uint256) {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        return maxSeatsMap[platID];
    }

    function existsPlatform ( uint256 platID ) external view returns(bool) {
        return platformsMap[platID] != address(0);
    }

    function resolveIdentityOnPlatform ( uint256 platID, address accountAddr ) external view returns ( uint256 ) {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        require(accountAddr != address(0), "Zero-account address(0) address not allowed.");
        address resolverAddr = platformsMap[platID];
        IdentityResolverServiceInterface resolverObj = IdentityResolverServiceInterface(resolverAddr);
        //assert(resolverObj.existsAddress(accountAddr));
        return resolverObj.resolveIdentity(accountAddr);
    }

    function resolvePermissionsOnPlatform ( uint256 platID , uint256 identity ) external view returns ( uint256 ) {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        address resolverAddr = platformsMap[platID];
        IdentityResolverServiceInterface resolverObj = IdentityResolverServiceInterface(resolverAddr);
        assert(resolverObj.existsIdentity(identity));
        return resolverObj.resolvePermissions(identity);
    }

    function resolveGroupExistsOnPlatform ( uint256 platID , uint256 groupID ) external view returns ( bool ){
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        address resolverAddr = platformsMap[platID];
        IdentityResolverServiceInterface resolverObj = IdentityResolverServiceInterface(resolverAddr);
        return resolverObj.resolveGroupExists(groupID);
    }

    function resolveIsInGroupOnPlatform ( uint256 platID, uint256 groupID , uint256 identity ) external view returns (  bool ) {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        address resolverAddr = platformsMap[platID];
        IdentityResolverServiceInterface resolverObj = IdentityResolverServiceInterface(resolverAddr);
        assert(resolverObj.existsIdentity(identity));
        assert(resolverObj.resolveGroupExists(groupID));
        return resolverObj.resolveIsInGroup(groupID,identity);
    }

    function canBuyTicketOnPlatform( uint256 platID, uint256 identity ) external view returns (bool) {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        address resolverAddr = platformsMap[platID];
        IdentityResolverServiceInterface resolverObj = IdentityResolverServiceInterface(resolverAddr);
        return resolverObj.canBuyTicket(identity);
    }

    function canResellTicketOnPlatform( uint256 platID, uint256 identity ) external view returns (bool) {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        address resolverAddr = platformsMap[platID];
        IdentityResolverServiceInterface resolverObj = IdentityResolverServiceInterface(resolverAddr);
        return resolverObj.canResellTicket(identity);
    }

    function canCreateEventOnPlatform( uint256 platID, uint256 identity ) external view returns (bool) {
        require(platformsMap[platID] != address(0), "Platform has not been registered before.");
        address resolverAddr = platformsMap[platID];
        IdentityResolverServiceInterface resolverObj = IdentityResolverServiceInterface(resolverAddr);
        return resolverObj.canCreateEvent(identity);
    }
}


contract DefaultIdentityResolverService is IdentityResolverServiceInterface,Ownable {

    uint256 nextNewId = 1;
    uint256 nextNewGroupId = 1;
    // numerical identities to addresses.
    mapping (uint256 => address[]) ownedAddresses;
    // addresses to num identities
    mapping (address => uint256) reverseOwnedAddresses;
    // id to permissions
    mapping (uint256 => uint256) permissionsPerID;
    // numerical groups to num ids.
    mapping (uint256 => uint256[]) groupMembers;
    // num ids to numerical groups.
    mapping (uint256 => uint256[]) identityGroups;

    function existsAddress( address addr) external view returns ( bool ){
        return reverseOwnedAddresses[addr] > 0;
    }

    function resolveIdentity( address addr ) external view returns ( uint256 ) {
        require(addr != address(0), "Zero-account address(0) address not allowed.");
        require(reverseOwnedAddresses[addr] > 0, "Account has not been registered before.");
        return reverseOwnedAddresses[addr] ;
    }

    function resolvePermissions ( uint256 identity ) external view returns ( uint256 ) {
        require(ownedAddresses[identity].length > 0, "Account has not been registered before.");
        return permissionsPerID[identity];
    }

    function resolveGroupExists( uint256 groupID ) external view returns ( bool ) {
        return groupMembers[groupID].length > 0;
    }

    function resolveIsInGroup( uint256 groupID , uint256 identity ) external view returns ( bool ) {
        require(groupMembers[groupID].length > 0, "Group of identities has not been registered before.");
        require(ownedAddresses[identity].length > 0, "Account has not been registered before.");
        uint arrayLength = identityGroups[identity].length;
        for (uint i = 0; i < arrayLength; i++) {
            if (identityGroups[identity][i] == groupID) {
                return true;
            }
        }
        return false;
    }

    function canBuyTicket( uint256 identity ) external view returns ( bool ) {
        require(ownedAddresses[identity].length > 0, "Account has not been registered before.");
        // last bit
        return permissionsPerID[identity] & 0x1 > 0;
    }
    
    function canResellTicket( uint256 identity ) external view returns ( bool ) {
        require(ownedAddresses[identity].length > 0, "Account has not been registered before.");
        // one before last bit
        return permissionsPerID[identity] & 0x2 > 0;
    }
    
    function canCreateEvent( uint256 identity ) external view returns ( bool ) {
        require(ownedAddresses[identity].length > 0, "Account has not been registered before.");
        // two before last bit
        return permissionsPerID[identity] & 0x4 > 0;
    }

    function newIdentity( address addr, uint256 permissions ) external onlyOwner  returns ( uint256 ) {
        require(addr != address(0), "Zero-account address(0) address not allowed.");
        uint256 newId = nextNewId;
        nextNewId++;
        ownedAddresses[newId] = [addr];
        reverseOwnedAddresses[addr] = newId;
        permissionsPerID[newId] = permissions;
        return newId;
    }
    
    function existsIdentity( uint256 accID) external view returns ( bool ) {
        return ownedAddresses[accID].length > 0;
    }
    
    function registerAddress( uint256 accID, address addr ) external onlyOwner {
        require(ownedAddresses[accID].length > 0, "Account has not been registered before.");
        require(addr != address(0), "Zero-account address(0) address not allowed.");
        ownedAddresses[accID].push(addr);
        reverseOwnedAddresses[addr] = accID;
    }
    
    function newGroup( uint256 firstMemberId ) external onlyOwner returns ( uint256 ) {
        require(ownedAddresses[firstMemberId].length > 0, "Account has not been registered before.");
        uint256 newGroupId = nextNewGroupId;
        nextNewGroupId++;
        groupMembers[newGroupId] = [firstMemberId];
        if (identityGroups[firstMemberId].length == 0) {
            identityGroups[firstMemberId] = [newGroupId];
        }
        else {
            identityGroups[firstMemberId].push(newGroupId);
        }
        return newGroupId;
    }

    function addToGroup( uint256 groupId, uint256 memberId ) external onlyOwner {
        require(ownedAddresses[memberId].length > 0, "Account has not been registered before.");
        require(groupMembers[groupId].length > 0, "Group of identities has not been registered before.");
        groupMembers[groupId].push(memberId);
        identityGroups[memberId].push(groupId);
    }

}

// Idempotent or Null Id Resolver for Testing.
// Just gives True or 1 to everything.
contract NullIdentityResolverService is IdentityResolverServiceInterface,Ownable {

    uint256 nextNewId = 1;
    uint256 nextNewGroupId = 1;
    // numerical identities to addresses.
    mapping (uint256 => address[]) ownedAddresses;
    // addresses to num identities
    mapping (address => uint256) reverseOwnedAddresses;
    // id to permissions
    mapping (uint256 => uint256) permissionsPerID;
    // numerical groups to num ids.
    mapping (uint256 => uint256[]) groupMembers;
    // num ids to numerical groups.
    mapping (uint256 => uint256[]) identityGroups;

    function existsAddress( address addr) external view returns ( bool ){
        return true;
    }

    function resolveIdentity( address addr ) external view returns ( uint256 ) {
        require(addr != address(0), "Zero-account address(0) address not allowed.");
        return 1;
    }

    function resolvePermissions ( uint256 identity ) external view returns ( uint256 ) {
        return 1;
    }

    function resolveGroupExists( uint256 groupID ) external view returns ( bool ) {
        return true;
    }

    function resolveIsInGroup( uint256 groupID , uint256 identity ) external view returns ( bool ) {
        return true;
    }

    function canBuyTicket( uint256 identity ) external view returns ( bool ) {
        return true;
    }
    
    function canResellTicket( uint256 identity ) external view returns ( bool ) {
        return true;
    }
    
    function canCreateEvent( uint256 identity ) external view returns ( bool ) {
        return true;
    }

    function newIdentity( address addr, uint256 permissions ) external onlyOwner  returns ( uint256 ) {
        require(addr != address(0), "Zero-account address(0) address not allowed.");
        return 1;
    }
    
    function existsIdentity( uint256 accID) external view returns ( bool ) {
        return true;
    }
    
    function registerAddress( uint256 accID, address addr ) external onlyOwner {
    }
    
    function newGroup( uint256 firstMemberId ) external onlyOwner returns ( uint256 ) {
        return 1;
    }

    function addToGroup( uint256 groupId, uint256 memberId ) external onlyOwner {
    }

}

