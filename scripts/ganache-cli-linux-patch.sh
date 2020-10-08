#!/bin/bash

BROWNIE_DEFAULTS=$(ls lib/python3.*/site-packages/brownie/data/config.yaml)
sed -i 's/cmd: ganache-cli/cmd: \.\/node_modules\/\.bin\/ganache-cli/g' ${BROWNIE_DEFAULTS}

BROWNIE_RPC=$(ls lib/python3.*/site-packages/brownie/network/rpc.py)
sed -i 's/"mnemonic": "--mnemonic",/"mnemonic": "--mnemonic", "acctKeys": "--acctKeys",/g' ${BROWNIE_RPC}

BROWNIE_CONFIG=$(ls brownie-config.json)
sed -i 's/"cmd": "ganache-cli"/"cmd": "\.\/node_modules\/\.bin\/ganache-cli"/g' ${BROWNIE_CONFIG}
