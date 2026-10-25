// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {ECDSA} from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {VendorRegistry} from "./VendorRegistry.sol";

// SIMULATED. Plan §8a/§8b. No owner, no pause. The signing domain has no chainId on purpose.
contract PurposeVault {
    using SafeERC20 for IERC20;

    struct Bill {
        address vendor;
        address buyerNGO;
        uint256 billNo;
        uint256 amountPaise;
        uint256 issuedAt;
        bytes32 category;
        bytes32 itemsCommitment;
    }

    struct Allocation {
        bytes32 billNullifier;
        address donorVault;
        uint256 chainId;
        uint256 fractionBps;
        bytes32 reportId;
    }

    event Deposited(address indexed donor, uint256 amountPaise);
    event Released(
        bytes32 indexed billNullifier,
        address indexed vendor,
        uint256 billNo,
        uint256 amountPaise,
        address donorVault,
        uint256 chainId,
        uint256 fractionBps,
        bytes32 reportId,
        bytes ngoSig,
        uint8 tier
    );
    event Frozen(string reason, bytes32 indexed billNullifier, address submitter);

    error VaultFrozen(string reason);
    error WrongCategory();
    error WrongNGO();
    error UnknownVendor(address vendor);
    error TierNotGreen(uint8 tier);
    error BadVendorSig(address recovered);
    error WrongChain(uint256 allocationChainId);
    error WrongVault();
    error NullifierMismatch();
    error BadNgoSig(address recovered);
    error BadFraction(uint256 fractionBps);
    error OverAllocated(uint256 usedBps);
    error CapExceeded();
    error InsufficientBalance();

    bytes32 public constant BILL_TYPEHASH = keccak256(
        "Bill(address vendor,address buyerNGO,uint256 billNo,uint256 amountPaise,uint256 issuedAt,bytes32 category,bytes32 itemsCommitment)"
    );
    bytes32 public constant ALLOCATION_TYPEHASH =
        keccak256("Allocation(bytes32 billNullifier,address donorVault,uint256 chainId,uint256 fractionBps,bytes32 reportId)");
    // Hard-coded EIP-712 domain, not OZ EIP712 inheritance (plan M4). No chainId on purpose.
    bytes32 public constant DOMAIN_SEPARATOR =
        keccak256(abi.encode(keccak256("EIP712Domain(string name,string version)"), keccak256("Credium"), keccak256("1")));

    IERC20 public immutable token;
    address public immutable ngo;
    VendorRegistry public immutable registry;
    bytes32 public immutable category;
    uint256 public immutable cap;

    uint256 public released;
    bool public frozen;
    string public frozenReason;
    mapping(bytes32 => uint256) public usedBps;

    constructor(address _token, address _ngo, address _registry, bytes32 _category, uint256 _capPaise) {
        token = IERC20(_token);
        ngo = _ngo;
        registry = VendorRegistry(_registry);
        category = _category;
        cap = _capPaise;
    }

    function deposit(uint256 amountPaise) external {
        token.safeTransferFrom(msg.sender, address(this), amountPaise);
        emit Deposited(msg.sender, amountPaise);
    }

    function billSigner(Bill calldata b, bytes calldata sig) public pure returns (address) {
        (address signer, ECDSA.RecoverError err, ) = ECDSA.tryRecover(_digest(_billStructHash(b)), sig);
        return err == ECDSA.RecoverError.NoError ? signer : address(0);
    }

    function allocationSigner(Allocation calldata a, bytes calldata sig) public pure returns (address) {
        (address signer, ECDSA.RecoverError err, ) = ECDSA.tryRecover(_digest(_allocationStructHash(a)), sig);
        return err == ECDSA.RecoverError.NoError ? signer : address(0);
    }

    // Release checks run in the §8a order. Block 6 adds the rest: donorVault, nullifier,
    // NGO signature, fraction, usedBps, cap, balance, transfer and the Released event.
    // ngoSig joins the signature when Block 6 lands.
    function release(Bill calldata b, bytes calldata vendorSig, Allocation calldata a) external {
        if (frozen) revert VaultFrozen(frozenReason);
        if (b.category != category) revert WrongCategory();
        if (b.buyerNGO != ngo) revert WrongNGO();

        uint8 tier = registry.tierOf(b.vendor);
        if (tier == 2) revert UnknownVendor(b.vendor);
        if (tier == 1) revert TierNotGreen(1);

        address vendorSigner = billSigner(b, vendorSig);
        if (vendorSigner != b.vendor) revert BadVendorSig(vendorSigner);

        if (a.chainId != block.chainid) revert WrongChain(a.chainId);
    }

    function _billStructHash(Bill calldata b) internal pure returns (bytes32) {
        return keccak256(
            abi.encode(
                BILL_TYPEHASH,
                b.vendor,
                b.buyerNGO,
                b.billNo,
                b.amountPaise,
                b.issuedAt,
                b.category,
                b.itemsCommitment
            )
        );
    }

    function _allocationStructHash(Allocation calldata a) internal pure returns (bytes32) {
        return keccak256(
            abi.encode(ALLOCATION_TYPEHASH, a.billNullifier, a.donorVault, a.chainId, a.fractionBps, a.reportId)
        );
    }

    function _digest(bytes32 structHash) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(bytes2(0x1901), DOMAIN_SEPARATOR, structHash));
    }
}
