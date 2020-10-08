import pytest
import brownie

####################
# TESTS GUIDELINES #
####################
#
# The following criteria are combined in the following tests. For example a good_complex test is testing
# a complete positive scenario of the function with a complex state.
#
# good          : a test that finishes the function execution properly and/or gives a positive result (true).
# bad           : a test that does not finished it proper execution (raises a revert) or gives a negative result (false).
# badinputN     : parameter number N is malformed or invalid for this type of function.
# badowner      : the method is being from an address that is not the owner that created this contract.
# gaslimit      : the function consumes more than MAX_GAS_USED_PER_TX gas per execution.
# complex       : the contract is on a complex state, usually 2 or 3 elements of different types have been added to the contarct.
# fees          : a payments is executed including positive fees (>0).
# exact         : an exact amount payments is being tested.
# excess        : a payment is being tested, where the amount payed is excessive.
# notenough     : a payment is being tested, where the amount payed is not enough to complete the payment.
# badpermission : the method is being called by an address that has no permission to execute this operation.
# 

# testing parameters

MAX_GAS_USED_PER_TX = 120000
MISSING_GROUP_ID = 2**40
MISSING_IDENTITY_ID = 2**45
MISSING_PLATFORM_ID = 2**50
EXAMPLE_MAX_SEATS = 50

# fixtures

@pytest.fixture(scope="module", autouse=True)
def identity_resolver(DefaultIdentityResolverService, accounts):
    ir = accounts[0].deploy(DefaultIdentityResolverService)
    yield ir

@pytest.fixture(scope="module", autouse=True)
def identity_resolver_complex(DefaultIdentityResolverService, accounts):
    ir = accounts[0].deploy(DefaultIdentityResolverService)
    txid1 = ir.newIdentity( accounts[-1], 0x3, {'from': accounts[0]})
    _ = ir.registerAddress( txid1.return_value, accounts[-2], {'from': accounts[0]})
    _ = ir.newGroup( txid1.return_value, {'from': accounts[0]})
    txid2 = ir.newIdentity( accounts[-2], 0x3, {'from': accounts[0]})
    _ = ir.registerAddress( txid2.return_value, accounts[-3], {'from': accounts[0]})
    txid3 = ir.newIdentity( accounts[-4], 0x3, {'from': accounts[0]})
    _ = ir.registerAddress( txid3.return_value, accounts[-4], {'from': accounts[0]})
    txg2 = ir.newGroup( txid2.return_value, {'from': accounts[0]})
    _ = ir.registerAddress( txid3.return_value, accounts[-5], {'from': accounts[0]})
    _ = ir.addToGroup( txg2.return_value, txid3.return_value, {'from': accounts[0]})
    yield ir

@pytest.fixture(scope="module", autouse=True)
def simple_token(SimpleToken, accounts):
    im = accounts[0].deploy(SimpleToken)
    yield im

@pytest.fixture(scope="module", autouse=True)
def identity_master(IdentityMasterService, accounts):
    im = accounts[0].deploy(IdentityMasterService)
    yield im

@pytest.fixture(scope="module", autouse=True)
def identity_master_complex(IdentityMasterService, accounts, identity_resolver, simple_token):
    im = accounts[0].deploy(IdentityMasterService)
    _ = im.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    yield im

@pytest.fixture(scope="module", autouse=True)
def zero_address():
    yield brownie.convert.to_address("0x"+"0"*40)

# isolate each function
# This fixture takes a snapshot of the local 
# environment before running each test, and 
# revert to it after the test completes.
@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

def test_chain_reverted(identity_resolver, accounts):
    assert accounts[1].balance() == 100000000000000000000

# DefaultIdentityResolverService

# resolveIdentity
def test_resolve_identity_good(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0, {'from': accounts[0]})
    assert identity_resolver.resolveIdentity( accounts[0], {'from': accounts[0]}) == tx.return_value

def test_resolve_identity_good_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0, {'from': accounts[0]})
    assert identity_resolver_complex.resolveIdentity( accounts[0], {'from': accounts[0]}) == tx.return_value

def test_resolve_identity_bad(identity_resolver, accounts, zero_address):
    with pytest.reverts("Account has not been registered before."):
        tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
        assert identity_resolver.resolveIdentity( accounts[1], {'from': accounts[0]}) == tx.return_value

def test_resolve_identity_bad_complex(identity_resolver_complex, accounts, zero_address):
    with pytest.reverts("Account has not been registered before."):
        tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
        assert identity_resolver_complex.resolveIdentity( accounts[1], {'from': accounts[0]}) == tx.return_value

# resolvePermissions
def test_resolve_permissions_good(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x1, {'from': accounts[0]})
    assert identity_resolver.resolvePermissions( tx.return_value, {'from': accounts[0]}) == 0x1

def test_resolve_permissions_good_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x1, {'from': accounts[0]})
    assert identity_resolver_complex.resolvePermissions( tx.return_value, {'from': accounts[0]}) == 0x1

def test_resolve_permissions_bad(identity_resolver, accounts):
    with pytest.reverts():
            ret = identity_resolver.resolvePermissions( 1, {'from': accounts[0]})

def test_resolve_permissions_bad_complex(identity_resolver_complex, accounts):
    with pytest.reverts():
            ret = identity_resolver_complex.resolvePermissions( MISSING_IDENTITY_ID, {'from': accounts[0]})

# resolveGroupExists
def test_resolve_group_exists_good(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    tx2 = identity_resolver.newGroup( txid.return_value, {'from': accounts[0]})
    assert identity_resolver.resolveGroupExists( tx2.return_value, {'from': accounts[0]}) == True

def test_resolve_group_exists_good_complex(identity_resolver_complex, accounts):
    txid = identity_resolver_complex.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    tx2 = identity_resolver_complex.newGroup( txid.return_value, {'from': accounts[0]})
    assert identity_resolver_complex.resolveGroupExists( tx2.return_value, {'from': accounts[0]}) == True

def test_resolve_group_exists_bad(identity_resolver, accounts):
    assert identity_resolver.resolveGroupExists( 0, {'from': accounts[0]}) == False

def test_resolve_group_exists_bad_complex(identity_resolver_complex, accounts):
    assert identity_resolver_complex.resolveGroupExists( 0, {'from': accounts[0]}) == False

# # resolveIsInGroup
def test_resolve_is_in_group_exists_true(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( txid.return_value, {'from': accounts[0]})
    assert identity_resolver.resolveIsInGroup( txgroup.return_value, txid.return_value, {'from': accounts[0]}) == True

def test_resolve_is_in_group_exists_true_complex(identity_resolver_complex, accounts):
    txid = identity_resolver_complex.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txgroup = identity_resolver_complex.newGroup( txid.return_value, {'from': accounts[0]})
    assert identity_resolver_complex.resolveIsInGroup( txgroup.return_value, txid.return_value, {'from': accounts[0]}) == True

def test_resolve_is_in_group_exists_false(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txid2 = identity_resolver.newIdentity( accounts[1], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( txid2.return_value, {'from': accounts[0]})
    assert identity_resolver.resolveIsInGroup( txgroup.return_value, txid.return_value, {'from': accounts[0]}) == False

def test_resolve_is_in_group_exists_false_complex(identity_resolver_complex, accounts):
    txid = identity_resolver_complex.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txid2 = identity_resolver_complex.newIdentity( accounts[1], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver_complex.newGroup( txid2.return_value, {'from': accounts[0]})
    assert identity_resolver_complex.resolveIsInGroup( txgroup.return_value, txid.return_value, {'from': accounts[0]}) == False

def test_resolve_is_in_group_exists_badinput1(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    with pytest.reverts("Group of identities has not been registered before."):
        assert identity_resolver.resolveIsInGroup( MISSING_GROUP_ID, txid.return_value, {'from': accounts[0]}) == False

def test_resolve_is_in_group_exists_badinput2(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( txid.return_value, {'from': accounts[0]})
    with pytest.reverts("Account has not been registered before."):
        assert identity_resolver.resolveIsInGroup( txgroup.return_value, MISSING_IDENTITY_ID, {'from': accounts[0]}) == False

# canBuyTicket
def test_can_buy_ticket_true(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x1, {'from': accounts[0]})
    assert identity_resolver.canBuyTicket( tx.return_value, {'from': accounts[0]}) == True

def test_can_buy_ticket_true_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x1, {'from': accounts[0]})
    assert identity_resolver_complex.canBuyTicket( tx.return_value, {'from': accounts[0]}) == True

def test_can_buy_ticket_false(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x2, {'from': accounts[0]})
    assert identity_resolver.canBuyTicket( tx.return_value, {'from': accounts[0]}) == False

def test_can_buy_ticket_false_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x2, {'from': accounts[0]})
    assert identity_resolver_complex.canBuyTicket( tx.return_value, {'from': accounts[0]}) == False

def test_can_buy_ticket_badinput(identity_resolver, accounts):
    with pytest.reverts():
            _ = identity_resolver.canBuyTicket( 0, {'from': accounts[0]})

# canResellTicket
def test_can_resell_ticket_true(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x2, {'from': accounts[0]})
    assert identity_resolver.canResellTicket( tx.return_value, {'from': accounts[0]}) == True

def test_can_resell_ticket_true_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x2, {'from': accounts[0]})
    assert identity_resolver_complex.canResellTicket( tx.return_value, {'from': accounts[0]}) == True

def test_can_resell_ticket_false(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x4, {'from': accounts[0]})
    assert identity_resolver.canResellTicket( tx.return_value, {'from': accounts[0]}) == False

def test_can_resell_ticket_false_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x4, {'from': accounts[0]})
    assert identity_resolver_complex.canResellTicket( tx.return_value, {'from': accounts[0]}) == False

def test_can_resell_ticket_badinput(identity_resolver, accounts):
    with pytest.reverts():
        _ = identity_resolver.canResellTicket( 0, {'from': accounts[0]})

# canCreateEvent
def test_can_create_event_true(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x4, {'from': accounts[0]})
    assert identity_resolver.canCreateEvent( tx.return_value, {'from': accounts[0]}) == True

def test_can_create_event_true_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x4, {'from': accounts[0]})
    assert identity_resolver_complex.canCreateEvent( tx.return_value, {'from': accounts[0]}) == True

def test_can_create_event_false(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    assert identity_resolver.canCreateEvent( tx.return_value, {'from': accounts[0]}) == False

def test_can_create_event_false_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    assert identity_resolver_complex.canCreateEvent( tx.return_value, {'from': accounts[0]}) == False

def test_can_create_event_badinput(identity_resolver, accounts):
    with pytest.reverts():
        _ = identity_resolver.canCreateEvent( 0, {'from': accounts[0]})

# new Identity
def test_new_identity_good(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0, {'from': accounts[0]})
    assert tx.return_value > 0

def test_new_identity_good_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0, {'from': accounts[0]})
    assert tx.return_value > 0

def test_new_identity_badinput(identity_resolver, accounts, zero_address):
    #with pytest.reverts():     
    with pytest.reverts("Zero-account address(0) address not allowed."):
        identity_resolver.newIdentity( zero_address, 0, {'from': accounts[0]})
    
def test_new_identity_notowner(identity_resolver, accounts):
    with pytest.reverts("Only contract owner can do this operation."):
        identity_resolver.newIdentity( accounts[1], 0, {'from': accounts[1]})

def test_new_identity_gasusedlimit(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0, {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX


# existsIdentity
def test_exists_identity_true(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0, {'from': accounts[0]})
    newId = tx.return_value
    assert identity_resolver.existsIdentity( newId, {'from': accounts[0]}) == True

def test_exists_identity_true_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0, {'from': accounts[0]})
    newId = tx.return_value
    assert identity_resolver_complex.existsIdentity( newId, {'from': accounts[0]}) == True

def test_exists_identity_false(identity_resolver, accounts):
   assert identity_resolver.existsIdentity( MISSING_GROUP_ID, {'from': accounts[0]}) == False

def test_exists_identity_false_complex(identity_resolver_complex, accounts):
   assert identity_resolver_complex.existsIdentity( MISSING_GROUP_ID, {'from': accounts[0]}) == False

# registerAddress
def test_register_address_good(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0, {'from': accounts[0]})
    tx = identity_resolver.registerAddress( tx.return_value, accounts[1], {'from': accounts[0]})

def test_register_address_good_complex(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0, {'from': accounts[0]})
    tx = identity_resolver_complex.registerAddress( tx.return_value, accounts[1], {'from': accounts[0]})

def test_register_address_badinput1(identity_resolver, accounts):
    with pytest.reverts("Account has not been registered before."):
        identity_resolver.registerAddress( 0, accounts[0], {'from': accounts[0]})

def test_register_address_badinput2(identity_resolver, accounts, zero_address):
    tx = identity_resolver.newIdentity( accounts[0], 0, {'from': accounts[0]})
    with pytest.reverts("Zero-account address(0) address not allowed."):
        identity_resolver.registerAddress( tx.return_value, zero_address, {'from': accounts[0]})
    
def test_register_address_notowner(identity_resolver, accounts):
    with pytest.reverts("Only contract owner can do this operation."):
        identity_resolver.registerAddress( 0, accounts[1], {'from': accounts[1]})
    
def test_register_address_gasusedlimit(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    tx = identity_resolver.registerAddress( tx.return_value, accounts[0], {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX

# newGroup
def test_new_group_good(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    _ = identity_resolver.newGroup( tx.return_value, {'from': accounts[0]})

def test_new_group_good(identity_resolver_complex, accounts):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    _ = identity_resolver_complex.newGroup( tx.return_value, {'from': accounts[0]})

def test_new_group_badinput(identity_resolver, accounts, zero_address):
    with pytest.reverts("Account has not been registered before."):
        _ = identity_resolver.newGroup( 0, {'from': accounts[0]})
    
def test_new_group_notowner(identity_resolver, accounts):
    with pytest.reverts("Only contract owner can do this operation."):
        tx = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
        _ = identity_resolver.newGroup( tx.return_value, {'from': accounts[1]})

def test_new_group_gasusedlimit(identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    tx2 = identity_resolver.newGroup( tx.return_value, {'from': accounts[0]})
    assert tx2.gas_used < MAX_GAS_USED_PER_TX

# addToGroup
def test_add_to_group_good(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txid2 = identity_resolver.newIdentity( accounts[1], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( txid.return_value, {'from': accounts[0]})
    _ = identity_resolver.addToGroup( txgroup.return_value, txid2.return_value, {'from': accounts[0]})

def test_add_to_group_good_complex(identity_resolver_complex, accounts):
    txid = identity_resolver_complex.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txid2 = identity_resolver_complex.newIdentity( accounts[1], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver_complex.newGroup( txid.return_value, {'from': accounts[0]})
    _ = identity_resolver_complex.addToGroup( txgroup.return_value, txid2.return_value, {'from': accounts[0]})

def test_add_to_group_badinput1(identity_resolver, accounts, zero_address):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txid2 = identity_resolver.newIdentity( accounts[1], 0x3, {'from': accounts[0]})
    with pytest.reverts("Group of identities has not been registered before."):
        _ = identity_resolver.addToGroup( 0, txid2.return_value, {'from': accounts[0]})
        
def test_add_to_group_badinput2(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( txid.return_value, {'from': accounts[0]})
    with pytest.reverts("Account has not been registered before."):
        _ = identity_resolver.addToGroup( txgroup.return_value, MISSING_IDENTITY_ID, {'from': accounts[0]})

def test_add_to_group_notowner(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txid2 = identity_resolver.newIdentity( accounts[1], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( txid.return_value, {'from': accounts[0]})
    with pytest.reverts("Only contract owner can do this operation."):
            _ = identity_resolver.addToGroup( txgroup.return_value, txid2.return_value, {'from': accounts[1]})
    
def test_add_to_group_gasusedlimit(identity_resolver, accounts):
    txid = identity_resolver.newIdentity( accounts[0], 0x7, {'from': accounts[0]})
    txid2 = identity_resolver.newIdentity( accounts[1], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( txid.return_value, {'from': accounts[0]})
    tx = identity_resolver.addToGroup( txgroup.return_value, txid2.return_value, {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX

# IdentityMasterService

# registerPlatform
def test_register_platform_true(identity_master, identity_resolver, accounts, simple_token):
    _ = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})

def test_register_platform_true_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    _ = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})

def test_register_platform_false(identity_master, accounts, zero_address, simple_token):
    with pytest.reverts():
        _ = identity_master.registerPlatform( zero_address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})

def test_register_platform_false_complex(identity_master_complex, accounts, zero_address, simple_token):
    with pytest.reverts():
        _ = identity_master_complex.registerPlatform( zero_address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})

def test_register_platform_notowner(identity_master, identity_resolver, accounts, simple_token):
    with pytest.reverts("Only contract owner can do this operation."):
        _ = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[1]})

def test_register_platform_gasusedlimit(identity_master, accounts, simple_token):
    tx = identity_master.registerPlatform( accounts[0], simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX

# deregisterPlatform
def test_deregister_platform_true(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    _ = identity_master.deregisterPlatform( tx.return_value, {'from': accounts[0]})
    assert identity_master.existsPlatform( tx.return_value ) == False

def test_deregister_platform_true_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    tx = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    _ = identity_master_complex.deregisterPlatform( tx.return_value, {'from': accounts[0]})
    assert identity_master_complex.existsPlatform( tx.return_value ) == False

def test_deregister_platform_false(identity_master, identity_resolver, identity_resolver_complex, accounts, simple_token):
    tx = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    tx2 = identity_master.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    _ = identity_master.deregisterPlatform( tx.return_value, {'from': accounts[0]})
    assert identity_master.existsPlatform( tx2.return_value ) == True

def test_deregister_platform_false_complex(identity_master_complex, accounts):
    with pytest.reverts("Platform has not been registered before."):
        _ = identity_master_complex.deregisterPlatform( MISSING_PLATFORM_ID, {'from': accounts[0]})

def test_deregister_platform_badinput(identity_master, accounts):
    with pytest.reverts("Platform has not been registered before."):
        _ = identity_master.deregisterPlatform( MISSING_PLATFORM_ID, {'from': accounts[0]})

def test_deregister_platform_notowner(identity_master, identity_resolver, accounts, simple_token):
    with pytest.reverts("Only contract owner can do this operation."):
        tx = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
        _ = identity_master.deregisterPlatform( tx.return_value, {'from': accounts[1]})

def test_deregister_platform_gasusedlimit(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    _ = identity_master.deregisterPlatform( tx.return_value, {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX

# resolveIdentityOnPlatform
def test_resolve_identity_on_platform_good(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master.resolveIdentityOnPlatform( txreg.return_value, accounts[0], {'from': accounts[0]}) == 1

def test_resolve_identity_on_platform_good_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master_complex.resolveIdentityOnPlatform( txreg.return_value, accounts[0], {'from': accounts[0]}) == tx.return_value

def test_resolve_identity_on_platform_badinput1(identity_master, accounts):
    with pytest.reverts("Platform has not been registered before."):
        ret = identity_master.resolveIdentityOnPlatform( 0, accounts[0], {'from': accounts[0]})

def test_resolve_identity_on_platform_badinput2(identity_master, identity_resolver, accounts, zero_address, simple_token):
    tx = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    with pytest.reverts("Zero-account address(0) address not allowed."):
        assert identity_master.resolveIdentityOnPlatform( tx.return_value, zero_address, {'from': accounts[0]}) == 0

def test_resolve_identity_on_platform_badinput3(identity_master, identity_resolver, accounts, zero_address, simple_token):
    tx = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    with pytest.reverts():
        assert identity_master.resolveIdentityOnPlatform( tx.return_value, accounts[1], {'from': accounts[0]}) == 0


# resolvePermissionsOnPlatform
def test_resolve_permissions_on_platform_good(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master.resolvePermissionsOnPlatform( txreg.return_value, tx.return_value, {'from': accounts[0]}) == 0x3

def test_resolve_permissions_on_platform_good_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master_complex.resolvePermissionsOnPlatform( txreg.return_value, tx.return_value, {'from': accounts[0]}) == 0x3

def test_resolve_permissions_on_platform_badinput1(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    with pytest.reverts("Platform has not been registered before."):
        assert identity_master.resolvePermissionsOnPlatform( MISSING_PLATFORM_ID, tx.return_value, {'from': accounts[0]}) == 0x3

def test_resolve_permissions_on_platform_badinput2(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    with pytest.reverts():
        assert identity_master.resolvePermissionsOnPlatform( tx.return_value, MISSING_IDENTITY_ID, {'from': accounts[0]}) == 0

# resolveMaxSeatsForPlatform
def test_resolve_max_seats_on_platform_good(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master.resolveMaxSeatsForPlatform( txreg.return_value, {'from': accounts[0]}) == EXAMPLE_MAX_SEATS

def test_resolve_max_seats_on_platform_good_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master_complex.resolveMaxSeatsForPlatform( txreg.return_value, {'from': accounts[0]}) == EXAMPLE_MAX_SEATS

def test_resolve_max_seats_on_platform_badinput1(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    with pytest.reverts("Platform has not been registered before."):
        assert identity_master.resolveMaxSeatsForPlatform( MISSING_PLATFORM_ID, {'from': accounts[0]}) == EXAMPLE_MAX_SEATS

# resolveCurrencyForPlatform
def test_resolve_currency_on_platform_good(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master.resolveCurrencyForPlatform( txreg.return_value, {'from': accounts[0]}) == simple_token

def test_resolve_currency_on_platform_good_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master_complex.resolveCurrencyForPlatform( txreg.return_value, {'from': accounts[0]}) == simple_token

def test_resolve_currency_on_platform_badinput1(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    with pytest.reverts("Platform has not been registered before."):
        assert identity_master.resolveCurrencyForPlatform( MISSING_PLATFORM_ID, {'from': accounts[0]}) == simple_token

# resolveGroupExistsOnPlatform
def test_resolve_group_exists_on_platform_true(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( tx.return_value, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master.resolveGroupExistsOnPlatform( txreg.return_value, txgroup.return_value, {'from': accounts[0]}) == True

def test_resolve_group_exists_on_platform_true_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver_complex.newGroup( tx.return_value, {'from': accounts[0]})
    txreg = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master_complex.resolveGroupExistsOnPlatform( txreg.return_value, txgroup.return_value, {'from': accounts[0]}) == True

def test_resolve_group_exists_on_platform_false(identity_master, identity_resolver, accounts, simple_token):
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master.resolveGroupExistsOnPlatform( txreg.return_value, MISSING_GROUP_ID, {'from': accounts[0]}) == False

def test_resolve_group_exists_on_platform_false_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    txreg = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master_complex.resolveGroupExistsOnPlatform( txreg.return_value, MISSING_GROUP_ID, {'from': accounts[0]}) == False

def test_resolve_group_exists_on_platform_badinput1(identity_master, identity_resolver, accounts):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( tx.return_value, {'from': accounts[0]})
    with pytest.reverts("Platform has not been registered before."):
        assert identity_master.resolveGroupExistsOnPlatform( MISSING_PLATFORM_ID, txgroup.return_value, {'from': accounts[0]}) == False

# resolveIsInGroupOnPlatform
def test_resolve_is_in_group_on_platform_true(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( tx.return_value, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master.resolveIsInGroupOnPlatform( txreg.return_value, txgroup.return_value, tx.return_value, {'from': accounts[0]}) == True

def test_resolve_is_in_group_on_platform_true_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver_complex.newGroup( tx.return_value, {'from': accounts[0]})
    txreg = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master_complex.resolveIsInGroupOnPlatform( txreg.return_value, txgroup.return_value, tx.return_value, {'from': accounts[0]}) == True

def test_resolve_is_in_group_on_platform_false(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    tx2 = identity_resolver.newIdentity( accounts[1], 0x7, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( tx.return_value, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master.resolveIsInGroupOnPlatform( txreg.return_value, txgroup.return_value, tx2.return_value, {'from': accounts[0]}) == False

def test_resolve_is_in_group_on_platform_false_complex(identity_master_complex, identity_resolver_complex, accounts, simple_token):
    tx = identity_resolver_complex.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    tx2 = identity_resolver_complex.newIdentity( accounts[1], 0x7, {'from': accounts[0]})
    txgroup = identity_resolver_complex.newGroup( tx.return_value, {'from': accounts[0]})
    txreg = identity_master_complex.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    assert identity_master_complex.resolveIsInGroupOnPlatform( txreg.return_value, txgroup.return_value, tx2.return_value, {'from': accounts[0]}) == False

def test_resolve_is_in_group_on_platform_badinput1(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    tx2 = identity_resolver.newIdentity( accounts[1], 0x7, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( tx.return_value, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    with pytest.reverts("Platform has not been registered before."):
        assert identity_master.resolveIsInGroupOnPlatform( MISSING_PLATFORM_ID, txgroup.return_value, tx.return_value, {'from': accounts[0]}) == True
    
def test_resolve_is_in_group_on_platform_badinput2(identity_master, identity_resolver, accounts, simple_token):
    tx = identity_resolver.newIdentity( accounts[0], 0x3, {'from': accounts[0]})
    txgroup = identity_resolver.newGroup( tx.return_value, {'from': accounts[0]})
    txreg = identity_master.registerPlatform( identity_resolver.address, simple_token.address, EXAMPLE_MAX_SEATS, {'from': accounts[0]})
    with pytest.reverts():
        assert identity_master.resolveIsInGroupOnPlatform( txreg.return_value, MISSING_GROUP_ID, tx.return_value, {'from': accounts[0]}) == True
