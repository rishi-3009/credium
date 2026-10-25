// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Test} from "forge-std/Test.sol";
import {MockINR} from "../src/MockINR.sol";
import {PurposeVault} from "../src/PurposeVault.sol";
import {VendorRegistry} from "../src/VendorRegistry.sol";

// 14:30 gate. Signatures here come from vm.sign. The cross-check against Ayaan's
// sim/fixtures/vector.json (plan §8b, B1) is still to add once his file arrives at 13:50.
contract GateTest is Test {
    uint256 constant NGO_PK = 0xA11CE;
    uint256 constant VENDOR_PK = 0xB0B;
    uint256 constant CHAIN_A = 31337;
    uint256 constant CHAIN_B = 31338;

    address registrar = makeAddr("registrar");
    address ngo;
    address vendor;
    bytes32 category = keccak256("WATER");

    MockINR token;
    VendorRegistry registry;
    PurposeVault vault;

    function setUp() public {
        ngo = vm.addr(NGO_PK);
        vendor = vm.addr(VENDOR_PK);
        vm.chainId(CHAIN_A);

        token = new MockINR();
        registry = new VendorRegistry(registrar);
        vault = new PurposeVault(address(token), ngo, address(registry), category, 2_000_000_000);

        vm.prank(registrar);
        registry.enroll(vendor, "Ramesh Hardware");
        vm.warp(block.timestamp + 7 days);
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

    function _nullifier(PurposeVault.Bill memory b) internal pure returns (bytes32) {
        bytes32 billDigest = keccak256(
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
        return keccak256(abi.encode(b.vendor, b.billNo, billDigest));
    }

    function _alloc(PurposeVault.Bill memory b, uint256 chainId, uint256 fractionBps)
        internal
        pure
        returns (PurposeVault.Allocation memory)
    {
        return PurposeVault.Allocation({
            billNullifier: _nullifier(b),
            donorVault: address(0),
            chainId: chainId,
            fractionBps: fractionBps,
            reportId: keccak256("report-417")
        });
    }

    function _typed(bytes32 structHash) internal view returns (bytes32) {
        return keccak256(abi.encodePacked(bytes2(0x1901), vault.DOMAIN_SEPARATOR(), structHash));
    }

    function _signBill(uint256 pk, PurposeVault.Bill memory b) internal view returns (bytes memory) {
        bytes32 structHash = keccak256(
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
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(pk, _typed(structHash));
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

    function test_domainSeparatorMatchesSpec() public view {
        assertEq(
            vault.DOMAIN_SEPARATOR(),
            keccak256(abi.encode(keccak256("EIP712Domain(string name,string version)"), keccak256("Credium"), keccak256("1")))
        );
    }

    function test_vendorSignatureRecoversVendor() public view {
        PurposeVault.Bill memory b = _bill();
        assertEq(vault.billSigner(b, _signBill(VENDOR_PK, b)), vendor);
    }

    function test_ngoAllocationRecoversNgo() public view {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_B, 10_000);
        assertEq(vault.allocationSigner(a, _signAlloc(NGO_PK, a)), ngo);
    }

    function test_chainBAllocationReleasedOnChainAReverts() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_B, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.WrongChain.selector, CHAIN_B));
        vault.release(b, vendorSig, a);
    }

    function test_chainAAllocationPassesChecksSoFar() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        vault.release(b, _signBill(VENDOR_PK, b), a);
    }

    function test_vendorSignedByNgoReverts() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory ngoSignedBill = _signBill(NGO_PK, b);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.BadVendorSig.selector, ngo));
        vault.release(b, ngoSignedBill, a);
    }
}
