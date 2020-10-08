# solidity-nft-sets

A Non-fungible Token (NFT) Framework including Serial Numbers and Identity, written in Solidity and Eth-Brownie Framework.

## Installing on Linux (with virtualenv)

Clone repo:

```
git clone https://github.com/joigno/solidity-nft-sets
```

Installing dependencies and applying some patches:

```
PYTHON3_BIN=$(which python3)
virtualenv -p ${PYTHON3_BIN} solidity-nft-sets
cd solidity-nft-sets
source ./bin/activate
pip3 install -r requirements.txt
npm install
./scripts/ganache-cli-linux-patch.sh
./scripts/run.sh
```

And each time your want to run the Ethereum development network and deploy the contracts locally, execute:

```
./scripts/run.sh
```

## Install on Windows (with no virtualenv)

Clone repo:

```
git clone https://github.com/joigno/solidity-nft-sets
```

Installing dependencies:

```
cd solidity-nft-sets
pip3 install -r requirements.txt
npm install -g ganache-cli@6.7.0
./scripts/run.sh
```

See docs for installing ganache-cli on Windows with optimizations (https://github.com/trufflesuite/ganache-cli/wiki/Installing-ganache-cli-on-Windows
).

## Testing Account Addresses

If you need to convert the private keys from the format on `./ganache-accounts.json` to your favorite Ethereum client format, we have a script. Run `.\scripts\secret_keys_testing_to_hex.py`:

```
$ python .\scripts\secret_keys_testing_to_hex.py
Address 0: 0x66ab6d9362d4f35596279692f0251db635165871
Secret Key: 0xbbfbee496161d506ffbb11dfea64eba16355cbf1d9c29613126ba7fecaed5d
Public Key: 0xbd2e5ac56f9ce4ae57c01c1e579dce4afebf1910c8bc341d6df19bad69dc3180627511d797b95f22a97c05240fc5e30af14b4676c8f39bf248fa82ba96521

Address 1: 0x33a4622b82d4c04a53e170c638b944ce27cffce3
Secret Key: 0x804365e293b9fab9bd11bddd3982396d56d30779efbb3ffb0a689027902c4a
Public Key: 0xef8e55574aabb9b22789ca1a4bf75131f0735cce7216752e08728538b94b38936373aecfc64f4574e57ba8abaefea53482abc983ff256c2e584777139

Address 2: 0x0063046686e46dc6f15918b61ae2b121458534a5
Secret Key: 0x1f52464c2fb44e9b7e88f2c5fe56d87b73eb3bcae72c66f9f74d7c6c9a81f
Public Key: 0x3611b5b980af561edc955be4d1347f8dd1616643c4e0736ce9df47ff61d2e6f4fe68a95324515d4a5e9adfb776e2cef847d1025954493ec21436e5d1c3a1e
...
...
```

## Private keys for testing

You will see something like the following, where you can find the Contract addresses to be accessed:

```
>>> ir = accounts[0].deploy(DefaultIdentityResolverService)
Transaction sent: 0xe2447aa1965991d20f9935165dcea692ac55272dd60cb743012513e8e87f8016
  Gas price: 20.0 gwei   Gas limit: 1005961
  DefaultIdentityResolverService.constructor confirmed - Block: 1   Gas used: 1005961 (100.00%)
  DefaultIdentityResolverService deployed at: 0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87

>>> im = accounts[0].deploy(IdentityMasterService)
Transaction sent: 0x70498f5dbd28cf57857ab05dbac0b41beb4f223bda153c6d5650755f96f6a031
  Gas price: 20.0 gwei   Gas limit: 804509
  IdentityMasterService.constructor confirmed - Block: 2   Gas used: 804509 (100.00%)
  IdentityMasterService deployed at: 0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6

>>> im.registerPlatform(ir.address,{'from': accounts[0]})
Transaction sent: 0x25c6a88070b7decc06eee20ca66345a96391852375a3cb66e7ff8fa0d00607d7
  Gas price: 20.0 gwei   Gas limit: 68944
  IdentityMasterService.registerPlatform confirmed - Block: 3   Gas used: 68944 (100.00%)

<Transaction object '0x25c6a88070b7decc06eee20ca66345a96391852375a3cb66e7ff8fa0d00607d7'>
>>> es = accounts[0].deploy(EventMasterService, im.address)
Transaction sent: 0xd29a6e1f609d0c237d82196d7cbab61df6e6e8004a8656e0d21ecb5bd3d1dd58
  Gas price: 20.0 gwei   Gas limit: 1794215
  EventMasterService.constructor confirmed - Block: 4   Gas used: 1794215 (100.00%)
  EventMasterService deployed at: 0x6951b5Bd815043E3F842c1b026b0Fa888Cc2DD85
```

Then (for example):

* DefaultIdentityResolverService deployed at: **0x3194cBDC3dbcd3E11a07892e7bA5c3394048Cc87**
* IdentityMasterService deployed at: **0x602C71e4DAC47a042Ee7f46E0aee17F94A3bA0B6**
* EventMasterService deployed at: **0x6951b5Bd815043E3F842c1b026b0Fa888Cc2DD85**

Initially, you only need to use the master service to create token batches, sub-series and buy NFTs.

As we mentioned, the private keys will be dumped into file `./ganache-accounts.json`.

## Compiling Smart Contracts

Clone the repository:

```
$ git clone https://github.com/joigno/solidity-nft-sets.git
$ cd solidity-nft-sets
$ brownie compile
```

## Running Smart Contracts tests

```
pytest tests
```

In some rare cases, you may find that if you modify the name of contracts or their signatures you may find issues with Brownie of PyTest caches, in that case you may want to start again and clone the project in a different folder. This issue has already been reported.








