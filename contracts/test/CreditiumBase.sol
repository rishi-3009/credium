// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Test} from "forge-std/Test.sol";
import {MockINR} from "../src/MockINR.sol";
import {PurposeVault} from "../src/PurposeVault.sol";
import {VendorRegistry} from "../src/VendorRegistry.sol";

// Shared fixtures for the gate, release and equivocation tests. SIMULATED data only.
// Signatures use vm.sign with throwaway keys. Ayaan's vector.json cross-check is still to add (B1).
abstract contract CreditiumBase is Test {
    uint256 constant NGO_PK = 0xA11CE;
    uint256 constant VENDOR_PK = 0xB0B;
    uint256 constant CHAIN_A = 31337;
    uint256 constant CHAIN_B = 31338;
    uint256 constant CAP_PAISE = 2_000_000_000; // ₹2 cr
    uint256 constant FUNDED_PAISE = 2_000_000_000;

    address registrar = makeAddr("registrar");
    address ngo;
    address vendor;
    bytes32 category = keccak256("WATER");

    MockINR token;
    VendorRegistry registry;
    PurposeVault vault;

    function setUp() public virtual {
        ngo = vm.addr(NGO_PK);
        vendor = vm.addr(VENDOR_PK);
        vm.chainId(CHAIN_A);

        token = new MockINR();
        registry = new VendorRegistry(registrar);
        vault = new PurposeVault(address(token), ngo, address(registry), category, CAP_PAISE);

        vm.prank(registrar);
        registry.enroll(vendor, "Ramesh Hardware");
        vm.warp(block.timestamp + 7 days);

        token.mint(address(this), FUNDED_PAISE);
        token.approve(address(vault), FUNDED_PAISE);
        vault.deposit(FUNDED_PAISE);
    }

    function _bill() internal view returns (PurposeVault.Bill memory) {
        return PurposeVault.Bill({
            vendor: vendor,
            buyerNGO: ngo,
            billNo: 417,
            amountPaise: 18_000_000,
            issuedAt: 1_792_806_000,
            category: category,
            itemsCommitment: keccak256("items-417")
        });
    }

    function _billStructHash(PurposeVault.Bill memory b) internal pure returns (bytes32) {
        return keccak256(
            abi.encode(
                keccak256(
                    "Bill(address vendor,address buyerNGO,uint256 billNo,uint256 amountPaise,uint256 issuedAt,bytes32 category,bytes32 itemsCommitment)"
                ),
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

    function _nullifier(PurposeVault.Bill memory b) internal pure returns (bytes32) {
        return keccak256(abi.encode(b.vendor, b.billNo, _billStructHash(b)));
    }

    function _alloc(PurposeVault.Bill memory b, uint256 chainId, uint256 fractionBps)
        internal
        view
        returns (PurposeVault.Allocation memory)
    {
        return PurposeVault.Allocation({
            billNullifier: _nullifier(b),
            donorVault: address(vault),
            chainId: chainId,
            fractionBps: fractionBps,
            reportId: keccak256("report-417")
        });
    }

    function _typed(bytes32 structHash) internal view returns (bytes32) {
        return keccak256(abi.encodePacked(bytes2(0x1901), vault.DOMAIN_SEPARATOR(), structHash));
    }

    function _signBill(uint256 pk, PurposeVault.Bill memory b) internal view returns (bytes memory) {
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, _typed(_billStructHash(b)));
        return abi.encodePacked(r, s, v);
    }

    function _signAlloc(uint256 pk, PurposeVault.Allocation memory a) internal view returns (bytes memory) {
        bytes32 structHash = keccak256(
            abi.encode(
                keccak256(
                    "Allocation(bytes32 billNullifier,address donorVault,uint256 chainId,uint256 fractionBps,bytes32 reportId)"
                ),
                a.billNullifier,
                a.donorVault,
                a.chainId,
                a.fractionBps,
                a.reportId
            )
        );
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, _typed(structHash));
        return abi.encodePacked(r, s, v);
    }
}
