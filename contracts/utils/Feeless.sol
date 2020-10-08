pragma solidity ^0.5.11;

import { ECRecovery } from "../utils/ECRecovery.sol";


contract Feeless {

    address internal msgSender;
    mapping(address => uint256) public nonces;

    modifier feeless {
        if (msgSender == address(0)) {
            msgSender = msg.sender;
            _;
            msgSender = address(0);
        } else {
            _;
        }
    }

    function isFeelessTransaction() internal view returns(bool) {
        return msgSender != msg.sender;
    }

    function performFeelessTransaction(address sender, address target, bytes memory data, uint256 nonce, uint256 expiryDateSecs, bytes memory sig) public payable {
    //function performFeelessTransaction(address sender, address target, bytes memory data, uint256 nonce, bytes memory sig) public payable {
        require(address(this) == target, "Contract target can only be the same contract.");

        bytes memory prefix = "\x19Ethereum Signed Message:\n32";
        bytes32 hash = keccak256(abi.encodePacked(prefix, keccak256(abi.encodePacked(target, data, nonce, expiryDateSecs))));
        //bytes32 hash = keccak256(abi.encodePacked(prefix, keccak256(abi.encodePacked(target, data, nonce))));
        msgSender = ECRecovery.recover(hash, sig);

        require(msgSender == sender, "Tx sender can only be the same sender encoded.");

        // Check the expiry date of the MetaTransaction.
        require(block.timestamp < expiryDateSecs,
                "Feeless metatx has expired and cannot be executed (check expiryDateSecs).");

        nonces[msgSender] = nonce;

        bool retBool;
        bytes memory retBytes;
        (retBool, retBytes) = target.call.value(msg.value)(data);
        require(retBool, "Tx called returned false.");
        msgSender = address(0);
    }


}