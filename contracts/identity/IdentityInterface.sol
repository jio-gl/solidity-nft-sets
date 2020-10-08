pragma solidity ^0.5.11;

/**
 * @title IdentityMasterServiceInterface
 * @dev IdentityMasterServiceInterface is an interface for implementing flexible
 * identity services, allowing different ticketing platforms. This interface describe
 * such functionality for the identity master service hosting several identity
 * platforms.
 * Its main services are mapping many addresses into one identity and describing
 * the permissions the identity has on each particular platform.
 * Initially there is going to be only one identity master, so the interface serves
 * for code organization now only.
 */
interface IdentityMasterServiceInterface {

    /**
    * @dev Register a contract with a IdentityResolverServiceInterface interface
    * as an identity platform.
    *
    * Returns the new platform unique number in the identity master.
    *
    */
    function registerPlatform(address resolver, address currencyToken, uint256 maxSeatPerEvent) external returns (uint256);

    /**
    * @dev Given `platID` platform number deregister a contract with a
    * IdentityResolverServiceInterface interface from the identity master.
    */
    function deregisterPlatform(uint256 platID) external;

    /**
    * @dev Given `platID` platform number returns the token contract address
    * of the curreny used for payments on this identity platform.
    */
    function resolveCurrencyForPlatform (uint256 platID) external view returns (address);

    /**
    * @dev Given `platID` platform number returns the configure maxSeats param
    * of this particular platform (for example 100 for Cinemas, 50,000 for stadiums, etc)
    */
    function resolveMaxSeatsForPlatform (uint256 platID) external view returns (uint256);

    /**
    * @dev Given `platID` platform number checks existence of platform.
    *
    * Returns a boolean value indicating the platform exists.
    *
    */
    function existsPlatform(uint256 platID) external view returns(bool);

    /**
    * @dev Given `platID` platform number and `addr` address gives identity number.
    *
    * Returns a numerical identity if the address belong to some identity.
    *
    */
    function resolveIdentityOnPlatform(uint256 platID, address addr) external view returns (uint256);

    /**
    * @dev Given `platID` platform number and `identity` number returns all permissions.
    *
    * Returns a number describing all permissions.
    *
    */
    function resolvePermissionsOnPlatform( uint256 platID, uint256 identity) external view returns (uint256);

    /**
    * @dev Given `platID` platform number and `groupID` identity group number return all permissions.
    * Identities can be group and belong to many groups.
    *
    * Returns a boolean value indicating the group exists on the particular platform.
    *
    */
    function resolveGroupExistsOnPlatform(uint256 platID, uint256 groupID) external view returns (bool);

    /**
    * @dev Given `platID` platform number, `groupID` group number and `identity` identity
    * answer the question if the identity belong to the group on a particular platform.
    *
    * Returns a boolean value indicating the identity belong to the group.
    *
    */
    function resolveIsInGroupOnPlatform(uint256 platID, uint256 groupID, uint256 identity) external view returns (bool);

    function canBuyTicketOnPlatform( uint256 platID, uint256 identity ) external view returns (bool);
    function canResellTicketOnPlatform( uint256 platID, uint256 identity ) external view returns (bool);
    function canCreateEventOnPlatform( uint256 platID, uint256 identity ) external view returns (bool);

}

/**
 * @title IdentityResolverServiceInterface
 * @dev IdentityResolverServiceInterface is an interface for implementing flexible
 * identity services, allowing different ticketing platforms. This interface describe
 * such functionality for the identity master service hosting several identity
 * platforms.
 * This resolver interface describes the behavior of what is going to be each
 * ticketing platform. For example, one resolver for cinema ticketing, one resolver
 * for concert ticketing, etc.
 */
interface IdentityResolverServiceInterface {

    /**
    * @dev Given `addr` a wallet address answer if address was registered on this platform.
    * Addresses can be registered on many platforms.
    *
    * Returns a boolean value indicating existence in the platform.
    *
    */
    function existsAddress(address addr) external view returns (bool);

    /**
    * @dev Given `accID` an identity number answers if identity was added to this platform.
    *
    * Returns a boolean value indicating existence in the platform.
    *
    */
    function existsIdentity(uint256 accID) external view returns (bool);

    /**
    * @dev Given `addr` address gives identity number.
    *
    * Returns a numerical identity if the address belong to some identity
    * on this resolver platform.
    *
    */
    function resolveIdentity(address addr) external view returns (uint256);

     /**
    * @dev Given `identity` number returns all permissions condensed in one number.
    *
    * Returns a number describing all permissions.
    *
    */
    function resolvePermissions(uint256 identity) external view returns (uint256);

    /**
    * @dev Given `groupID` identity group number returns all permissions.
    * Identities can be group and belong to many groups.
    *
    * Returns a boolean value indicating the group exists on this particular platform.
    *
    */
    function resolveGroupExists(uint256 groupID) external view returns (bool);
    
    /**
    * @dev Given `groupID` group number and `identity` identity
    * answer the question if the identity belong to the group on this particular platform.
    *
    * Returns a boolean value indicating the identity belong to the group.
    *
    */
    function resolveIsInGroup( uint256 groupID, uint256 identity ) external view returns (bool);

    /**
    * @dev This is one of some particular flag permissions.
    * Given `identity` identity answers the question if the
    * identity can buy tickets on platform using this identity
    * resolver.
    *
    * Returns a boolean value indicating the flag permission.
    *
    */
    function canBuyTicket(uint256 identity) external view returns ( bool );

    /**
    * @dev This is one of some particular flag permissions.
    * Given `identity` identity answers the question if the
    * identity can resell tickets on platform using this identity
    * resolver.
    *
    * Returns a boolean value indicating the flag permission.
    *
    */
    function canResellTicket(uint256 identity) external view returns ( bool );

    /**
    * @dev This is one of some particular flag permissions.
    * Given `identity` identity answers the question if the
    * identity can create events on platform using this identity
    * resolver.
    *
    * Returns a boolean value indicating the flag permission.
    *
    */
    function canCreateEvent(uint256 identity) external view returns ( bool );


}
