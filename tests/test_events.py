import pytest
import brownie
import web3
import eth_abi

from secret_keys_testing_to_hex import getGanacheAccountsHex
from eth_account.messages import encode_defunct

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
# mtx           : a metatransaction is being tested, one account signs a tx and another is sending it to the blockchain.
# maxsize       : a complex element is tested with a maximum number of items.
# baddate       : a operation that was execute not in an appropriate block timestamp.
# 

# testing parameters

MAX_GAS_USED_PER_TX = 270000
MISSING_GROUP_ID = 2**40
MISSING_IDENTITY_ID = 2**45
MISSING_PLATFORM_ID = 2**50
MISSING_EVENT_ID = 2**20
MISSING_SECTION_ID = 2**14
MISSING_SEAT_ID = 2**15

EXAMPLE_QUANTITY = 20
EXAMPLE_BIG_QUANTITY = 200
EXAMPLE_MAX_SEATS_SMALL = 2
EXAMPLE_MAX_SEATS_BIG = 100
EXAMPLE_PRICE = 100
EXAMPLE_TICKET_ID = 30064836609
EXAMPLE_TICKET_ID2 = 8590000129
EXAMPLE_TICKET_ID3 = 47244705793
EXAMPLE_TICKET_ID_COMPLEX = 21474967553
EXAMPLE_PERCENTUAL_FEES = 500 # basic points = 1/100th of 1%
EXAMPLE_FEELESS_FEES_PREMIUM = 200 # basic points = 1/100th of 1%
EXAMPLE_ALL_PERMISSIONS = 0x7
EXAMPLE_NO_BUYTICKET_PERMISSION = 0x6
EXAMPLE_NO_RESELLTICKET_PERMISSION = 0x5
EXAMPLE_NO_CREATEEVENT_PERMISSION = 0x3
EX_START_SELL_DATE = 0
EX_START_WITHDRAWAL_DATE = 0
EX_EXPIRY_DATE = 2000000000
EXAMPLE_FUTURE_DATE = EX_EXPIRY_DATE
EXAMPLE_PAST_DATE = EX_START_SELL_DATE

ganache_keys = getGanacheAccountsHex()

# fixtures

@pytest.fixture(scope="module", autouse=True)
def ecrecovery_library(ECRecovery, accounts):
    ecl = accounts[0].deploy(ECRecovery)
    yield ecl

@pytest.fixture(scope="module", autouse=True)
def identity_resolver(DefaultIdentityResolverService, accounts):
    ir = accounts[0].deploy(DefaultIdentityResolverService)
    yield ir

@pytest.fixture(scope="module", autouse=True)
def identity_resolver_complex(DefaultIdentityResolverService, accounts):
    ir = accounts[0].deploy(DefaultIdentityResolverService)
    txid1 = ir.newIdentity( accounts[0], EXAMPLE_ALL_PERMISSIONS, {'from': accounts[0]})
    _ = ir.registerAddress( txid1.return_value, accounts[-1], {'from': accounts[0]})
    _ = ir.newGroup( txid1.return_value, {'from': accounts[0]})
    txid2 = ir.newIdentity( accounts[1], EXAMPLE_ALL_PERMISSIONS, {'from': accounts[0]})
    _ = ir.registerAddress( txid2.return_value, accounts[-2], {'from': accounts[0]})
    txid3 = ir.newIdentity( accounts[2], EXAMPLE_ALL_PERMISSIONS, {'from': accounts[0]})
    _ = ir.registerAddress( txid3.return_value, accounts[-3], {'from': accounts[0]})
    txg2 = ir.newGroup( txid2.return_value, {'from': accounts[0]})
    _ = ir.registerAddress( txid3.return_value, accounts[-4], {'from': accounts[0]})
    _ = ir.addToGroup( txg2.return_value, txid3.return_value, {'from': accounts[0]})
    # Permission Testing Identities
    txidp1 = ir.newIdentity( accounts[3], EXAMPLE_NO_CREATEEVENT_PERMISSION, {'from': accounts[0]})
    txidp2 = ir.newIdentity( accounts[4], EXAMPLE_NO_RESELLTICKET_PERMISSION, {'from': accounts[0]})
    txidp3 = ir.newIdentity( accounts[5], EXAMPLE_NO_BUYTICKET_PERMISSION, {'from': accounts[0]})
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
def identity_master_complex(IdentityMasterService, accounts, identity_resolver_complex, simple_token):
    im = accounts[0].deploy(IdentityMasterService)
    _ = im.registerPlatform( identity_resolver_complex.address, simple_token.address, EXAMPLE_MAX_SEATS_BIG, {'from': accounts[0]})
    yield im

@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

@pytest.fixture(scope="module", autouse=True)
def zero_address():
    yield brownie.convert.to_address("0x"+"0"*40)

@pytest.fixture(scope="module", autouse=True)
def events_service(EventMasterService, identity_master_complex, accounts):
    es = accounts[0].deploy(EventMasterService, identity_master_complex.address, 0, 0)
    yield es

@pytest.fixture(scope="module", autouse=True)
def events_service_fees(EventMasterService, identity_master_complex, accounts):
    es = accounts[0].deploy(EventMasterService, identity_master_complex.address, EXAMPLE_PERCENTUAL_FEES, EXAMPLE_FEELESS_FEES_PREMIUM)
    yield es

@pytest.fixture(scope="module", autouse=True)
def events_service_complex(EventMasterService, identity_master_complex, accounts):
    es = accounts[0].deploy(EventMasterService, identity_master_complex.address, 0, 0)
    _ = es.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    _ = es.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    _ = es.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    yield es

## Tx Gas Used Fixtures

# No Feeless MetaTx.

@pytest.fixture(scope="module", autouse=True)
def gas_used_create_event(events_service, accounts):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    yield tx.gas_used

@pytest.fixture(scope="module", autouse=True)
def gas_used_add_section(events_service, accounts):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    tx = events_service.addSection(txev.return_value, EXAMPLE_QUANTITY, EXAMPLE_PRICE, {'from': accounts[0]})
    yield tx.gas_used


@pytest.fixture(scope="module", autouse=True)
def gas_used_buy_ticket_with_tokens(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 200, {'from': accounts[0]})
    tx = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    yield tx.gas_used


@pytest.fixture(scope="module", autouse=True)
def gas_used_buy_tickets_batch_with_tokens(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    tx = events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    yield tx.gas_used


@pytest.fixture(scope="module", autouse=True)
def gas_used_withdraw_funds(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 400, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    tx = events_service.withdrawFunds(tx.return_value, {'from': accounts[1]})
    yield tx.gas_used


@pytest.fixture(scope="module", autouse=True)
def gas_used_withdraw_fees(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.transfer(accounts[1].address, 210, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 210, {'from': accounts[1]})
    events_service_fees.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[1]})
    # Identity platform #1
    tx = events_service_fees.withdrawFees(1, {'from': accounts[0]})
    yield tx.gas_used

## Tests Gas Used Non-metatx.

def test_gas_used_create_event(gas_used_create_event):
    assert gas_used_create_event == 114133

def test_gas_used_add_section(gas_used_add_section):
    assert gas_used_add_section == 104137

def test_gas_used_buy_ticket_with_tokens(gas_used_buy_ticket_with_tokens):
    assert gas_used_buy_ticket_with_tokens == 169279

def test_gas_used_buy_tickets_batch_with_tokens(gas_used_buy_tickets_batch_with_tokens):
    assert gas_used_buy_tickets_batch_with_tokens == 211069

def test_gas_used_withdraw_funds(gas_used_withdraw_funds):
    assert gas_used_withdraw_funds == 43091

def test_gas_used_withdraw_fees(gas_used_withdraw_fees):
    assert gas_used_withdraw_fees == 33782


# Feeless MetaTx.

# encodeABI
def encodeABI(fname, lstTypes, lstValues):
    hashsign = web3.Web3.keccak(text='%s(%s)' % (fname,','.join(lstTypes) ))[:4] 
    vals = eth_abi.encode_abi(lstTypes,lstValues)
    return hashsign + vals

def encodeTx(accounts, accountNum, contract, funcName, lstTypes, lstValues, expiryDateSecs):
    # encode Tx.
    contractAddress = contract.address
    accountNonce = accounts[accountNum].nonce
    abiData = encodeABI(funcName,lstTypes,lstValues)
    nonceToHex = "{0:0{1}x}".format(accountNonce,64)
    expiryToHex = "{0:0{1}x}".format(expiryDateSecs,64)
    textToHash = contractAddress + abiData.hex() + nonceToHex + expiryToHex
    txHash = web3.Web3.keccak( hexstr = textToHash )
    txHash = txHash.hex()[2:]
    msghash = encode_defunct(hexstr=txHash)
    bytes_private_key = bytes.fromhex(ganache_keys[accountNum]['secretKey'][2:])
    txSig = web3.eth.Account.sign_message(msghash, private_key=bytes_private_key)
    assert len(txSig.signature) == 65
    return contractAddress, abiData, accountNonce, txSig.signature

@pytest.fixture(scope="module", autouse=True)
def gas_used_mtx_create_event(events_service, accounts):
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'createEvent'
    lstTypes = ['uint256','uint256','uint256']
    lstValues = [1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    #contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues)
    # execute encoded and signed Tx.
    tx = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    #tx = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, signature, { 'from' : accounts[1] })
    yield tx.gas_used

@pytest.fixture(scope="module", autouse=True)
def gas_used_mtx_add_section(events_service, accounts):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'addSection'
    lstTypes = ['uint32','uint16','uint256']
    lstValues = [txev.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    tx = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    yield tx.gas_used


@pytest.fixture(scope="module", autouse=True)
def gas_used_mtx_buy_ticket_with_tokens(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service.address, 200, {'from': accounts[0]})
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'buyTicketWithTokens'
    lstTypes = ['uint32','uint16','uint16']
    lstValues = [tx.return_value, txsec.return_value, 1]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    txtix = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    yield tx.gas_used


@pytest.fixture(scope="module", autouse=True)
def gas_used_mtx_buy_tickets_batch_with_tokens(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'buyTicketsBatchWithTokens'
    lstTypes = ['uint32','uint16[]','uint16[]']
    lstValues = [tx.return_value, [txsec.return_value,txsec.return_value], [1,3]]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    tx = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    yield tx.gas_used


@pytest.fixture(scope="module", autouse=True)
def gas_used_mtx_withdraw_funds(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 400, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    # encode Tx.
    accountNumber = 1
    contract = events_service
    funcName = 'withdrawFunds'
    lstTypes = ['uint32']
    lstValues = [tx.return_value]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    tx = events_service.performFeelessTransaction( accounts[1].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[0] })
    yield tx.gas_used


## Tests for GasUsed on Meta-Transactions.

def test_gas_used_mtx_create_event(gas_used_mtx_create_event):
    assert gas_used_mtx_create_event == 141118

def test_gas_used_mtx_add_section(gas_used_mtx_add_section):
    assert gas_used_mtx_add_section == 146157

def test_gas_used_mtx_buy_ticket_with_tokens(gas_used_mtx_buy_ticket_with_tokens):
    assert gas_used_mtx_buy_ticket_with_tokens == 114133

def test_gas_used_mtx_buy_tickets_batch_with_tokens(gas_used_mtx_buy_tickets_batch_with_tokens):
    assert gas_used_mtx_buy_tickets_batch_with_tokens == 239791

def test_gas_used_mtx_withdraw_funds(gas_used_mtx_withdraw_funds):
    assert gas_used_mtx_withdraw_funds == 99715


## EventMasterService


# getTicketID(uint256 eventID, uint256 sectionID, uint256 seatID)
def test_get_ticket_id_good(events_service, accounts):
    assert events_service.getTicketID(1,1,1) == 4295032833

def test_get_ticket_id_injectivity1(events_service, accounts):
    assert events_service.getTicketID(1,1,1) != events_service.getTicketID(2,1,1)

def test_get_ticket_id_injectivity2(events_service, accounts):
    assert events_service.getTicketID(1,1,1) != events_service.getTicketID(1,2,1)

def test_get_ticket_id_injectivity3(events_service, accounts):
    assert events_service.getTicketID(1,1,1) != events_service.getTicketID(1,1,2)

def test_get_ticket_id_projection1(events_service, accounts):
    assert events_service.getEventIDFromTicketID(events_service.getTicketID(1,2,3)) == 1

def test_get_ticket_id_projection2(events_service, accounts):
    assert events_service.getSectionIDFromTicketID(events_service.getTicketID(1,2,3)) == 2
    
def test_get_ticket_id_projection3(events_service, accounts):
    assert events_service.getSeatIDFromTicketID(events_service.getTicketID(1,2,3)) == 3


# createEvent
def test_create_event_good(events_service, accounts):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    assert events_service.existsEvent(tx.return_value) 
    assert tx.gas_used == 114133

def test_create_event_good_complex(events_service_complex, accounts):
    tx = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    assert events_service_complex.existsEvent(tx.return_value, {'from': accounts[0]}) 
    
def test_create_event_bad(events_service, accounts):
    with pytest.reverts("Identity platform has not been registered before."):
        tx = events_service.createEvent(0, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})

def test_create_event_badpermission(events_service_complex, accounts):
    with pytest.reverts("Ident. of sender has no permission to create event on this ticket platform."):
        tx = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[3]})

def test_create_event_gaslimit(events_service, accounts):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX
    

# # addSection(uint256 eventID, uint256 quantity, uint256 price )
def test_add_section_good(events_service, accounts):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    _ = events_service.addSection(txev.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    assert events_service.numberOfSections(txev.return_value, {'from': accounts[0]}) == 1
    # number of sections < N

def test_add_section_good_complex(events_service_complex, accounts):
    _ = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev2 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev3 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_complex.addSection(txev3.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec2 = events_service_complex.addSection(txev3.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec3 = events_service_complex.addSection(txev3.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    assert events_service_complex.numberOfSections(txev3.return_value, {'from': accounts[0]}) == 3

def test_add_section_bad(events_service, accounts):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    with pytest.reverts("EventID does not exists."):
        _ = events_service.addSection(MISSING_EVENT_ID,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})

def test_add_section_maxsize(events_service, accounts):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    with pytest.reverts("Too many seats for this ticket platform on this event."):
        _ = events_service.addSection(txev.return_value,EXAMPLE_BIG_QUANTITY,EXAMPLE_PRICE,{'from': accounts[0]})

def test_add_section_badowner(events_service, accounts):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    with pytest.reverts("Only event owner can add sections."):
        _ = events_service.addSection(txev.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})

def test_add_section_gaslimit(events_service, accounts):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    tx = events_service.addSection(txev.return_value, EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX


# buyTicketWithTokens(uint32 eventID, uint16 sectionID, uint16 seatID, uint256 value, address token)def test_buy_ticket_good(events_service, accounts):
def test_buy_ticket_with_tokens_good(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service.address, 200, {'from': accounts[0]})
    txtix = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    assert txtix.return_value == EXAMPLE_TICKET_ID3 and avail == True and not_avail == False

def test_buy_ticket_with_tokens_good_complex(events_service_complex, accounts, simple_token):
    txev = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev2 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev3 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec2 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec3 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_complex.ticketIsAvailable(txev2.return_value, txsec2.return_value, 1)
    simple_token.approve(events_service_complex.address, 200, {'from': accounts[0]})
    txtix = events_service_complex.buyTicketWithTokens(txev2.return_value, txsec2.return_value, 1, {'from': accounts[0]})
    not_avail = events_service_complex.ticketIsAvailable(txev2.return_value, txsec2.return_value, 1)
    assert txtix.return_value == EXAMPLE_TICKET_ID_COMPLEX and avail == True and not_avail == False

def test_buy_ticket_with_tokens_exact(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    simple_token.approve(events_service.address, 100, {'from': accounts[0]})
    beforeBalance = accounts[0].balance()
    txtix = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 139279 # buyTicketWithTokens()
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance == afterBalance + 20000000000*gasUsed
    assert txtix.return_value == EXAMPLE_TICKET_ID3 and avail == True and not_avail == False
    assert beforeTokenBalance == (afterTokenBalance + 100)

def test_buy_ticket_with_tokens_exact_fees(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 105, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    txtix = events_service_fees.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 154279 # vecchio 156450  # buyTicketWithTokens() using Fees
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance == afterBalance + 20000000000*gasUsed
    assert txtix.return_value == EXAMPLE_TICKET_ID2 and avail == True and not_avail == False
    assert beforeTokenBalance == (afterTokenBalance + 105)

def test_buy_ticket_with_tokens_excess(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service.address, 150, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    txtix = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 154279 # buyTicketWithTokens() no Fees.
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance == afterBalance + 20000000000*gasUsed
    assert txtix.return_value == EXAMPLE_TICKET_ID3 and avail == True and not_avail == False
    assert beforeTokenBalance == (afterTokenBalance + 100)

def test_buy_ticket_with_tokens_excess_fees(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 150, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    txtix = events_service_fees.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 169279 # buyTicketWithTokens() using Fees
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance == afterBalance + 20000000000*gasUsed
    assert txtix.return_value == EXAMPLE_TICKET_ID2 and avail == True and not_avail == False
    assert beforeTokenBalance == (afterTokenBalance + 105)

def test_buy_ticket_with_tokens_notenough(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service.address, 50, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    with pytest.reverts("Not enough tokens provided in tx to buy the ticket plus fees."):
        _ = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 68515 # buyTicketWithTokens() no Fees.
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance == afterBalance + 20000000000*gasUsed
    assert beforeTokenBalance == afterTokenBalance
    assert avail == True and not_avail == True
    
def test_buy_ticket_with_tokens_notenough_fees(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 104, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    with pytest.reverts("Not enough tokens provided in tx to buy the ticket plus fees."):
        _ = events_service_fees.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 68515 # buyTicketWithTokens() no Fees.
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance == afterBalance + 20000000000*gasUsed
    assert beforeTokenBalance == afterTokenBalance
    assert avail == True and not_avail == True
    
def test_buy_ticket_with_tokens_badinput1(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    with pytest.reverts("EventID does not exists."):
        tx = events_service.buyTicketWithTokens(MISSING_EVENT_ID, txsec.return_value, 1, {'from': accounts[0]})
    
def test_buy_ticket_with_tokens_badinput2(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    with pytest.reverts("SectionID does not exists for this event."):
        tx = events_service.buyTicketWithTokens(tx.return_value, MISSING_SECTION_ID, 1, {'from': accounts[0]})

def test_buy_ticket_with_tokens_badinput3(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    with pytest.reverts("SeatID does not exists for this event and section."):
        tx = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, MISSING_SEAT_ID, {'from': accounts[0]})

def test_buy_ticket_with_tokens_badpermission(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    with pytest.reverts("Identity of sender has no permission to buy tickets on this ticket platform."):
        tx = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[5]})

def test_buy_ticket_with_tokens_baddate(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EXAMPLE_FUTURE_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    with pytest.reverts("Event has not reached the start of ticket selling date."):
        tx = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[1]})

def test_buy_ticket_with_tokens_gaslimit(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 200, {'from': accounts[0]})
    tx = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX


# buyTicketsBatchWithTokens(uint256 eventID, uint256[] calldata sectionIDs, uint256[] calldata seatIDs)
def test_buy_tickets_batch_with_tokens_good(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    
def test_buy_tickets_batch_with_tokens_good_complex(events_service_complex, accounts, simple_token):
    txev = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev2 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev3 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec2 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec3 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_complex.ticketIsAvailable(txev2.return_value, txsec2.return_value, 5)
    avail2 = events_service_complex.ticketIsAvailable(txev2.return_value, txsec3.return_value, 5)
    avail3 = events_service_complex.ticketIsAvailable(txev2.return_value, txsec3.return_value, 7)
    simple_token.approve(events_service_complex.address, 400, {'from': accounts[0]})
    events_service_complex.buyTicketsBatchWithTokens(txev2.return_value, [txsec2.return_value,txsec3.return_value,txsec3.return_value], [5,5,7], {'from': accounts[0]})
    not_avail = events_service_complex.ticketIsAvailable(txev2.return_value, txsec2.return_value, 5)
    not_avail2 = events_service_complex.ticketIsAvailable(txev2.return_value, txsec3.return_value, 5)
    not_avail3 = events_service_complex.ticketIsAvailable(txev2.return_value, txsec3.return_value, 7)
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False and avail3 == True and not_avail3 == False 

def test_buy_ticket_batch_with_tokens_exact(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service.address, 200, {'from': accounts[0]})
    beforeBalance = accounts[0].balance()
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 196069 # buyTicketsBatchWithTokens()
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    assert beforeTokenBalance == (afterTokenBalance + 200)

def test_buy_ticket_batch_with_tokens_exact_fees(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service_fees.address, 210, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    events_service_fees.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 211069 # buyTicketsBatchWithTokens()
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    assert beforeTokenBalance == (afterTokenBalance + 210)

def test_buy_ticket_batch_with_tokens_excess(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service.address, 250, {'from': accounts[0]})
    beforeBalance = accounts[0].balance()
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = 211069
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    assert beforeTokenBalance == (afterTokenBalance + 200)

def test_buy_ticket_batch_with_tokens_excess_fees(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service_fees.address, 250, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    events_service_fees.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    afterBalance = accounts[0].balance()
    gasUsed = 226069 # buyTicketsBatchWithTokens() and fees
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    assert beforeTokenBalance == (afterTokenBalance + 210)
    
def test_buy_ticket_batch_with_tokens_notenough(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service.address, 150, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    with pytest.reverts("Not enough tokens provided in tx to buy the batch of tickets plus fees."):
        events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    afterBalance = accounts[0].balance()
    gasExpendedBeforeReverting = 169774
    # gasPrice*gasExpendedBeforeReverting
    assert beforeBalance - ( afterBalance +  20000000000*gasExpendedBeforeReverting) == 0
    assert avail == True and not_avail == True and avail2 == True and not_avail2 == True 
    assert beforeTokenBalance == (afterTokenBalance + 0)

def test_buy_ticket_batch_with_tokens_notenough_fees(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service_fees.address, 209, {'from': accounts[0]})
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[0].balance()
    with pytest.reverts("Not enough tokens provided in tx to buy the batch of tickets plus fees."):
        events_service_fees.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasExpendedBeforeReverting = 169774
    # gasPrice*gasExpendedBeforeReverting
    assert beforeBalance - ( afterBalance +  20000000000*gasExpendedBeforeReverting) == 0
    assert avail == True and not_avail == True and avail2 == True and not_avail2 == True 

def test_buy_tickets_batch_with_tokens_badinput1(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    with pytest.reverts("EventID does not exists."):
        events_service.buyTicketsBatchWithTokens(MISSING_EVENT_ID, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    
def test_buy_tickets_batch_with_tokens_badinput2(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    with pytest.reverts("SectionID does not exists for this event."):
        events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,MISSING_SECTION_ID], [1,3], {'from': accounts[0]})
    
def test_buy_tickets_batch_with_tokens_badinput3(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    with pytest.reverts("SeatID does not exists for this SectionID on this event."):
        events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,MISSING_SEAT_ID], {'from': accounts[0]})
    
def test_buy_tickets_batch_with_tokens_badpermission(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[5]})
    with pytest.reverts("Identity of sender has no permission to buy tickets on this ticket platform."):
        events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[5]})
    
def test_buy_tickets_batch_with_tokens_baddate(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EXAMPLE_FUTURE_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[5]})
    with pytest.reverts("Event has not reached the start of ticket selling date."):
        events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[5]})
    
def test_buy_tickets_batch_with_tokens_gaslimit(events_service, accounts, simple_token):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(txev.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(txev.return_value, txsec.return_value, 1)
    avail2 = events_service.ticketIsAvailable(txev.return_value, txsec.return_value, 3)
    simple_token.approve(events_service.address, 200, {'from': accounts[0]})
    tx = events_service.buyTicketsBatchWithTokens(txev.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(txev.return_value, txsec.return_value, 1)
    not_avail2 = events_service.ticketIsAvailable(txev.return_value, txsec.return_value, 3)
    assert tx.gas_used < MAX_GAS_USED_PER_TX


# withdrawFunds(uint256 eventID)
def test_withdraw_funds_good(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service.address, 400, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    beforeBalance = accounts[1].balance()
    beforeTokenBalance = simple_token.balanceOf(accounts[1])
    events_service.withdrawFunds(tx.return_value, {'from': accounts[1]})
    afterTokenBalance = simple_token.balanceOf(accounts[1])
    afterBalance = accounts[1].balance()
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    gasUsed = 43091
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert beforeTokenBalance - (afterTokenBalance - 200) == 0
    
def test_withdraw_funds_good_complex(events_service_complex, accounts, simple_token):
    txev = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txev2 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txev3 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    txsec2 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    txsec3 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    avail = events_service_complex.ticketIsAvailable(txev2.return_value, txsec2.return_value, 5)
    avail2 = events_service_complex.ticketIsAvailable(txev2.return_value, txsec3.return_value, 5)
    avail3 = events_service_complex.ticketIsAvailable(txev2.return_value, txsec3.return_value, 7)    
    simple_token.approve(events_service_complex.address, 300, {'from': accounts[0]})
    events_service_complex.buyTicketsBatchWithTokens(txev2.return_value, [txsec2.return_value,txsec3.return_value,txsec3.return_value], [5,5,7], {'from': accounts[0]})
    not_avail = events_service_complex.ticketIsAvailable(txev2.return_value, txsec2.return_value, 5)
    not_avail2 = events_service_complex.ticketIsAvailable(txev2.return_value, txsec3.return_value, 5)
    not_avail3 = events_service_complex.ticketIsAvailable(txev2.return_value, txsec3.return_value, 7)
    beforeBalance = accounts[1].balance()
    beforeTokenBalance = simple_token.balanceOf(accounts[1])
    events_service_complex.withdrawFunds(txev2.return_value, {'from': accounts[1]})
    afterTokenBalance = simple_token.balanceOf(accounts[1])
    afterBalance = accounts[1].balance()
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False and avail3 == True and not_avail3 == False 
    gasUsed = 36546
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert beforeTokenBalance - (afterTokenBalance - 300) == 0
    
def test_withdraw_funds_badinput(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    with pytest.reverts("EventID does not exists."):
            events_service.withdrawFunds(MISSING_EVENT_ID, {'from': accounts[1]})

def test_withdraw_funds_badowner(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    with pytest.reverts("Only owner of the event can withdraw funds."):
            events_service.withdrawFunds(tx.return_value, {'from': accounts[2]})

def test_withdraw_funds_gaslimit(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    events_service.withdrawFunds(tx.return_value, {'from': accounts[1]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX


# withdrawFees() external onlyOwner
def test_withdraw_fees_good(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.transfer(accounts[1].address, 210, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 210, {'from': accounts[1]})
    events_service_fees.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[1]})
    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    beforeBalance = accounts[0].balance()
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    # Identity platform #1
    events_service_fees.withdrawFees(1, {'from': accounts[0]})
    afterBalance = accounts[0].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    # 20 gwei = gas price = 20,000,000,000 wei
    gasUsed = 33782
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert beforeTokenBalance - (afterTokenBalance - 10) == 0
    
def test_withdraw_fees_good_complex_exact(events_service_fees, accounts, simple_token):
    txev = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txev2 = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txev3 = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service_fees.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    txsec2 = events_service_fees.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    txsec3 = events_service_fees.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    avail = events_service_fees.ticketIsAvailable(txev2.return_value, txsec2.return_value, 5)
    avail2 = events_service_fees.ticketIsAvailable(txev2.return_value, txsec3.return_value, 5)
    avail3 = events_service_fees.ticketIsAvailable(txev2.return_value, txsec3.return_value, 7)
    simple_token.transfer(accounts[2].address, 315, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 315, {'from': accounts[2]})
    events_service_fees.buyTicketsBatchWithTokens(txev2.return_value, [txsec2.return_value,txsec3.return_value,txsec3.return_value], [5,5,7], {'from': accounts[2]})
    not_avail = events_service_fees.ticketIsAvailable(txev2.return_value, txsec2.return_value, 5)
    not_avail2 = events_service_fees.ticketIsAvailable(txev2.return_value, txsec3.return_value, 5)
    not_avail3 = events_service_fees.ticketIsAvailable(txev2.return_value, txsec3.return_value, 7)
    beforeBalance = accounts[0].balance()
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    # Identity platform #1
    events_service_fees.withdrawFees(1, {'from': accounts[0]})
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    afterBalance = accounts[0].balance()
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False and avail3 == True and not_avail3 == False 
    gasUsed = 33782
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert beforeTokenBalance - (afterTokenBalance - 15) == 0
    
def test_withdraw_fees_good_complex_excess(events_service_fees, accounts, simple_token):
    txev = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txev2 = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txev3 = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service_fees.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    txsec2 = events_service_fees.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    txsec3 = events_service_fees.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    avail = events_service_fees.ticketIsAvailable(txev2.return_value, txsec2.return_value, 5)
    avail2 = events_service_fees.ticketIsAvailable(txev2.return_value, txsec3.return_value, 5)
    avail3 = events_service_fees.ticketIsAvailable(txev2.return_value, txsec3.return_value, 7)
    simple_token.transfer(accounts[2].address, 400, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 400, {'from': accounts[2]})
    events_service_fees.buyTicketsBatchWithTokens(txev2.return_value, [txsec2.return_value,txsec3.return_value,txsec3.return_value], [5,5,7], {'from': accounts[2]})
    not_avail = events_service_fees.ticketIsAvailable(txev2.return_value, txsec2.return_value, 5)
    not_avail2 = events_service_fees.ticketIsAvailable(txev2.return_value, txsec3.return_value, 5)
    not_avail3 = events_service_fees.ticketIsAvailable(txev2.return_value, txsec3.return_value, 7)
    beforeBalance = accounts[0].balance()
    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    events_service_fees.withdrawFees(1, {'from': accounts[0]})
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    afterBalance = accounts[0].balance()
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False and avail3 == True and not_avail3 == False 
    gasUsed = 33782
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert beforeTokenBalance - (afterTokenBalance - 15) == 0

def test_withdraw_fees_badowner(events_service, accounts,simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    with pytest.reverts("Only contract owner can do this operation."):
            events_service.withdrawFees(1, {'from': accounts[1]})

def test_withdraw_fees_gaslimit(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.transfer(accounts[1].address, 210, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 210, {'from': accounts[1]})
    events_service_fees.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[1]})
    events_service_fees.withdrawFees(1, {'from': accounts[0]})
    assert tx.gas_used < MAX_GAS_USED_PER_TX


# safeTransferFrom
def test_safe_transfer_from_good(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    beforeOwns0 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[0])
    beforeOwns1 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[1])
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    events_service.safeTransferFrom(accounts[0], accounts[1], ticketID, 1, "abc")
    afterOwns0 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[0])
    afterOwns1 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[1])
    assert beforeOwns0==True and beforeOwns1==False and afterOwns0==False and afterOwns1==True

def test_safe_transfer_from_badinput1(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    with pytest.reverts("Need operator approval for 3rd party transfers."):
        # msg.sender not token owner, and no approval.
        events_service.safeTransferFrom(accounts[2], accounts[1], ticketID, 1, "abc")
    
def test_safe_transfer_from_badinput2(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    with pytest.reverts("_to must be non-zero."):
        events_service.safeTransferFrom(accounts[0], zero_address, ticketID, 1, "abc")

def test_safe_transfer_from_insufficientfunds(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    with pytest.reverts():
        events_service.safeTransferFrom(accounts[0], accounts[1], ticketID, 2, "abc")

def test_safe_transfer_from_badpermission(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.transfer(accounts[4].address, 400, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[4]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[4]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    with pytest.reverts("Sender has no permission to transfer tickets on this ticket platform."):
        events_service.safeTransferFrom(accounts[4], accounts[1], ticketID, 2, "abc", {'from': accounts[4]})

def test_safe_transfer_from_nooperatorapproval(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    with pytest.reverts("Need operator approval for 3rd party transfers."):
        events_service.safeTransferFrom(accounts[0], accounts[1], ticketID, 2, "abc", {'from': accounts[2]})

def test_safe_transfer_from_gaslimit(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    tx = events_service.safeTransferFrom(accounts[0], accounts[1], ticketID, 1, "abc")
    assert tx.gas_used < MAX_GAS_USED_PER_TX


# safeBatchTransferFrom
def test_safe_batch_transfer_from_good(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    beforeOwns0Tix1 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[0])
    beforeOwns1Tix1 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[1])
    beforeOwns0Tix2 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 3, accounts[0])
    beforeOwns1Tix2 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 3, accounts[1])
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    ticketID2 = events_service.getTicketID(tx.return_value, txsec.return_value, 3)
    events_service.safeBatchTransferFrom(accounts[0], accounts[1], [ticketID,ticketID2], [1,1], "abc")
    afterOwns0Tix1 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[0])
    afterOwns1Tix1 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[1])
    afterOwns0Tix2 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 3, accounts[0])
    afterOwns1Tix2 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 3, accounts[1])
    assert beforeOwns0Tix1==True and beforeOwns1Tix1==False and afterOwns0Tix1==False and afterOwns1Tix1==True
    assert beforeOwns0Tix2==True and beforeOwns1Tix2==False and afterOwns0Tix2==False and afterOwns1Tix2==True

def test_safe_batch_transfer_from_badinput1(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    ticketID2 = events_service.getTicketID(tx.return_value, txsec.return_value, 3)
    with pytest.reverts("Need operator approval for 3rd party transfers."):
        # msg.sender not token owner, and no approval.
        events_service.safeBatchTransferFrom(accounts[2], accounts[1], [ticketID,ticketID2], [1,1], "abc")
    
def test_safe_batch_transfer_from_badinput2(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    ticketID2 = events_service.getTicketID(tx.return_value, txsec.return_value, 3)
    with pytest.reverts("destination address must be non-zero."):
        events_service.safeBatchTransferFrom(accounts[0], zero_address, [ticketID,ticketID2], [1,1], "abc")
    
def test_safe_batch_transfer_from_badinput3(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    ticketID2 = events_service.getTicketID(tx.return_value, txsec.return_value, 3)
    with pytest.reverts("_ids and _values array lenght must match."):
        events_service.safeBatchTransferFrom(accounts[0], accounts[1], [ticketID,ticketID2], [1,1,1], "abc")

def test_safe_batch_transfer_from_insufficientfunds(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    ticketID2 = events_service.getTicketID(tx.return_value, txsec.return_value, 3)
    with pytest.reverts():
        events_service.safeBatchTransferFrom(accounts[0], zero_address, [ticketID,ticketID2], [1,1234], "abc")

def test_safe_batch_transfer_from_badpermission(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.transfer(accounts[4].address, 300, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[4]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[4]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    ticketID2 = events_service.getTicketID(tx.return_value, txsec.return_value, 3)
    with pytest.reverts("Sender has no permission to transfer tickets on this ticket platform."):
        events_service.safeBatchTransferFrom(accounts[4], accounts[1], [ticketID,ticketID2], [1,1], "abc", {'from': accounts[4]})

def test_safe_batch_transfer_from_nooperatorapproval(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.transfer(accounts[2].address, 300, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[2]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[2]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    ticketID2 = events_service.getTicketID(tx.return_value, txsec.return_value, 3)
    with pytest.reverts("Need operator approval for 3rd party transfers."):
        events_service.safeBatchTransferFrom(accounts[0], accounts[1], [ticketID,ticketID2], [1,1], "abc", {'from': accounts[2]})

def test_safe_batch_transfer_from_gaslimit(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    ticketID2 = events_service.getTicketID(tx.return_value, txsec.return_value, 3)
    tx = events_service.safeBatchTransferFrom(accounts[0], accounts[1], [ticketID,ticketID2], [1,1], "abc")
    assert tx.gas_used < MAX_GAS_USED_PER_TX


# ERC1155 approvals
def test_approvals_good(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    beforeOwns0 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[0])
    beforeOwns1 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[1])
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    assert events_service.isApprovedForAll(accounts[0], accounts[2]) == False
    events_service.setApprovalForAll(accounts[2], True, {'from': accounts[0]})
    assert events_service.isApprovedForAll(accounts[0], accounts[2]) == True
    events_service.safeTransferFrom(accounts[0], accounts[1], ticketID, 1, "abc", {'from': accounts[2]})
    afterOwns0 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[0])
    afterOwns1 = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[1])
    assert beforeOwns0==True and beforeOwns1==False and afterOwns0==False and afterOwns1==True


# existsEvent
def test_exists_event_good(events_service, accounts):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    assert events_service.existsEvent(tx.return_value, {'from': accounts[0]}) == True
    
def test_exists_event_good_complex(events_service_complex, accounts):
    tx = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    assert events_service_complex.existsEvent(tx.return_value, {'from': accounts[0]}) == True
    

# numberOfSections(uint256 eventID)
def test_number_of_sections_good(events_service, accounts):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    assert events_service.numberOfSections(tx.return_value) == 0
    
def test_number_of_sections_good_complex(events_service_complex, accounts):
    txev = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev2 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev3 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec2 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec3 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    assert events_service_complex.numberOfSections(txev2.return_value, {'from': accounts[0]}) == 3

def test_number_of_sections_bad(events_service, accounts):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    with pytest.reverts("EventID does not exists."):
        assert events_service.numberOfSections(MISSING_EVENT_ID) == 0


# doesTicketBelongTo(uint256 eventID, uint256 sectionID, uint256 seatID, address belongs)
def test_does_ticket_belong_to_good(events_service, accounts, zero_address, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.transfer(accounts[1].address, 300, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[1]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[1]})
    assert events_service.doesTicketBelongTo(tx.return_value,txsec.return_value,3, accounts[1]) == True
    
def test_does_ticket_belong_to_good_complex(events_service_complex, accounts, zero_address, simple_token):
    txev = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev2 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev3 = events_service_complex.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec2 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec3 = events_service_complex.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.transfer(accounts[1].address, 400, {'from': accounts[0]})
    simple_token.approve(events_service_complex.address, 400, {'from': accounts[1]})
    events_service_complex.buyTicketsBatchWithTokens(txev2.return_value, [txsec2.return_value,txsec3.return_value,txsec3.return_value], [5,5,7], {'from': accounts[1]})
    tixid = events_service_complex.getTicketID(txev2.return_value,txsec3.return_value,5)
    assert events_service_complex.doesTicketBelongTo(txev2.return_value,txsec3.return_value,5,accounts[1]) == True
    assert events_service_complex.doesTicketIdBelongTo(tixid,accounts[1]) == True
    
def test_does_ticket_belong_to_complex2(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    simple_token.transfer(accounts[1].address, 300, {'from': accounts[0]})
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    ticketID = events_service.getTicketID(tx.return_value, txsec.return_value, 1)
    beforeOwns0A = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[0])
    beforeOwns1A = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[1])
    beforeOwns0B = events_service.doesTicketIdBelongTo(ticketID, accounts[0])
    beforeOwns1B = events_service.doesTicketIdBelongTo(ticketID, accounts[1])
    events_service.safeTransferFrom(accounts[0], accounts[1], ticketID, 1, "abc")
    afterOwns0A = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[0])
    afterOwns1A = events_service.doesTicketBelongTo(tx.return_value, txsec.return_value, 1, accounts[1])
    afterOwns0B = events_service.doesTicketIdBelongTo(ticketID, accounts[0])
    afterOwns1B = events_service.doesTicketIdBelongTo(ticketID, accounts[1])
    assert beforeOwns0A==beforeOwns0B and beforeOwns1A==beforeOwns1B and afterOwns0A==afterOwns0B and afterOwns1A==afterOwns1B

def test_does_ticket_belong_to_bad(events_service, accounts, zero_address, simple_token):
    _ = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txev2 = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    _ = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    _ = events_service.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec2 = events_service.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    txsec3 = events_service.addSection(txev2.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    simple_token.transfer(accounts[1].address, 400, {'from': accounts[0]})
    simple_token.approve(events_service.address, 400, {'from': accounts[1]})
    events_service.buyTicketsBatchWithTokens(txev2.return_value, [txsec2.return_value,txsec3.return_value,txsec3.return_value], [5,5,7], {'from': accounts[1]})
    with pytest.reverts("Zero-account address(0) address not allowed."):
        assert events_service.doesTicketBelongTo(txev2.return_value,txsec3.return_value,5,zero_address) == True

# #############################
# # Feeless Metatransactions. #
# #############################

# # JS example:
# # const target = myToken.options.address;
# # const nonce = await myToken.methods.nonces(wallet1).call();
# # const data = await myToken.methods.transfer(wallet2, 5 * 10**18).encodeABI();
# # const hash = web3.utils.sha3(target + data.substr(2) + web3.utils.toBN(nonce).toString(16,64));
# # const sig = await web3.eth.accounts.sign(hash, wallet1PrivateKey);

# createEvent()
def test_create_event_good_mtx(events_service, accounts):
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'createEvent'
    lstTypes = ['uint256','uint256','uint256']
    lstValues = [1,EX_START_SELL_DATE,EX_START_WITHDRAWAL_DATE]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    tx = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    assert tx.gas_used == 141138
    assert tx.gas_used < MAX_GAS_USED_PER_TX
    # check effects.
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    assert events_service.existsEvent(tx.return_value-1)

def test_create_event_baddate_mtx(events_service, accounts):
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'createEvent'
    lstTypes = ['uint256','uint256','uint256']
    lstValues = [1,EX_START_SELL_DATE,EX_START_WITHDRAWAL_DATE]
    expiryDateSecs = EXAMPLE_PAST_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    with pytest.reverts("Feeless metatx has expired and cannot be executed (check expiryDateSecs)."):
        _ = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })


def test_add_section_good_mtx(events_service, accounts):
    txev = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'addSection'
    lstTypes = ['uint32','uint16','uint256']
    lstValues = [txev.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    tx = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    assert tx.gas_used == 131157
    assert tx.gas_used < MAX_GAS_USED_PER_TX
    # check effects.
    assert events_service.numberOfSections(txev.return_value, {'from': accounts[0]}) == 1


def test_buy_ticket_with_tokens_good_mtx(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service.address, 200, {'from': accounts[0]})
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'buyTicketWithTokens'
    lstTypes = ['uint32','uint16','uint16']
    lstValues = [tx.return_value, txsec.return_value, 1]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    txtix = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    assert txtix.gas_used == 181682
    assert txtix.gas_used < MAX_GAS_USED_PER_TX
    #txtix = events_service.buyTicketWithTokens(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    assert avail == True and not_avail == False


def test_buy_ticket_with_tokens_exact_fees_mtx(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    simple_token.approve(events_service_fees.address, 107, {'from': accounts[0]})

    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[1].balance()

    # encode Tx.
    accountNumber = 0
    contract = events_service_fees
    funcName = 'buyTicketWithTokens'
    lstTypes = ['uint32','uint16','uint16']
    lstValues = [tx.return_value, txsec.return_value, 1]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    txtix = events_service_fees.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    assert txtix.gas_used == 196746
    assert txtix.gas_used < MAX_GAS_USED_PER_TX

    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    afterBalance = accounts[1].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])

    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1, {'from': accounts[0]})
    assert avail == True and not_avail == False
    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance == afterBalance + 20000000000*txtix.gas_used
    assert beforeTokenBalance == (afterTokenBalance + 107)


def test_buy_tickets_batch_with_tokens_mtx(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service.address, 300, {'from': accounts[0]})
    # encode Tx.
    accountNumber = 0
    contract = events_service
    funcName = 'buyTicketsBatchWithTokens'
    lstTypes = ['uint32','uint16[]','uint16[]']
    lstValues = [tx.return_value, [txsec.return_value,txsec.return_value], [1,3]]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    txtix = events_service.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    assert txtix.gas_used == 239811
    assert txtix.gas_used < MAX_GAS_USED_PER_TX
    #events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 


def test_buy_tickets_batch_with_tokens_exact_fees_mtx(events_service_fees, accounts, simple_token):
    tx = events_service_fees.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[0]})
    txsec = events_service_fees.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[0]})
    avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service_fees.address, 214, {'from': accounts[0]})

    beforeTokenBalance = simple_token.balanceOf(accounts[0])
    beforeBalance = accounts[1].balance()

    # encode Tx.
    accountNumber = 0
    contract = events_service_fees
    funcName = 'buyTicketsBatchWithTokens'
    lstTypes = ['uint32','uint16[]','uint16[]']
    lstValues = [tx.return_value, [txsec.return_value,txsec.return_value], [1,3]]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    txtix = events_service_fees.performFeelessTransaction( accounts[0].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[1] })
    assert txtix.gas_used == 254855
    assert txtix.gas_used < MAX_GAS_USED_PER_TX

    afterBalance = accounts[1].balance()
    afterTokenBalance = simple_token.balanceOf(accounts[0])
    gasUsed = txtix.gas_used # buyTicketsBatchWithTokens()

    not_avail = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service_fees.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 

    # 100 wei ticketPrice + gasPrice*gasExpended
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    assert beforeTokenBalance == (afterTokenBalance + 214)


def test_withdraw_funds_good_mtx(events_service, accounts, simple_token):
    tx = events_service.createEvent(1, EX_START_SELL_DATE, EX_START_WITHDRAWAL_DATE, {'from': accounts[1]})
    txsec = events_service.addSection(tx.return_value,EXAMPLE_QUANTITY,EXAMPLE_PRICE, {'from': accounts[1]})
    avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    simple_token.approve(events_service.address, 400, {'from': accounts[0]})
    events_service.buyTicketsBatchWithTokens(tx.return_value, [txsec.return_value,txsec.return_value], [1,3], {'from': accounts[0]})
    not_avail = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 1)
    not_avail2 = events_service.ticketIsAvailable(tx.return_value, txsec.return_value, 3)
    beforeBalance = accounts[0].balance()
    beforeTokenBalance = simple_token.balanceOf(accounts[1])
    
    # encode Tx.
    accountNumber = 1
    contract = events_service
    funcName = 'withdrawFunds'
    lstTypes = ['uint32']
    lstValues = [tx.return_value]
    expiryDateSecs = EX_EXPIRY_DATE
    contractAddress, abiData, accountNonce, signature = encodeTx(accounts,accountNumber,contract,funcName,lstTypes,lstValues,expiryDateSecs)
    # execute encoded and signed Tx.
    txwd = events_service.performFeelessTransaction( accounts[1].address, contractAddress, abiData, accountNonce, expiryDateSecs, signature, { 'from' : accounts[0] })
    assert txwd.gas_used == 69715
    assert txwd.gas_used < MAX_GAS_USED_PER_TX
    
    #events_service.withdrawFunds(tx.return_value, {'from': accounts[1]})
    afterTokenBalance = simple_token.balanceOf(accounts[1])
    afterBalance = accounts[0].balance()
    assert avail == True and not_avail == False and avail2 == True and not_avail2 == False 
    gasUsed = 69715
    assert beforeBalance - (afterBalance + 20000000000*gasUsed) == 0
    assert beforeTokenBalance - (afterTokenBalance - 200) == 0
