// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {StdStorage, stdStorage} from "forge-std/StdStorage.sol";
import {CreditiumBase} from "./CreditiumBase.sol";
import {PurposeVault} from "../src/PurposeVault.sol";

// Plan Block 6: one happy path and eight negatives for release().
contract ReleaseTest is CreditiumBase {
    using stdStorage for StdStorage;

    uint256 constant STRANGER_PK = 0xDEAD;
    uint256 constant AMBER_PK = 0xA0B;
    address stranger;
    address amberVendor;
    address other = makeAddr("other");

    function setUp() public override {
        super.setUp();
        stranger = vm.addr(STRANGER_PK);
        amberVendor = vm.addr(AMBER_PK);
    }

    function test_happyPathPaysGreenVendorAndEmitsReleased() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectEmit(true, true, false, true, address(vault));
        emit PurposeVault.Released(
            a.billNullifier, vendor, 417, 18_000_000, address(vault), CHAIN_A, 10_000, a.reportId, ngoSig, 0
        );
        vault.release(b, vendorSig, a, ngoSig);

        assertEq(token.balanceOf(vendor), 18_000_000);
        assertEq(vault.released(), 18_000_000);
        assertEq(vault.usedBps(a.billNullifier), 10_000);
        assertEq(token.balanceOf(address(vault)), FUNDED_PAISE - 18_000_000);
    }

    function test_wrongCategoryReverts() public {
        PurposeVault.Bill memory b = _bill();
        b.category = keccak256("PPE");
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(PurposeVault.WrongCategory.selector);
        vault.release(b, vendorSig, a, ngoSig);
    }

    function test_wrongNgoReverts() public {
        PurposeVault.Bill memory b = _bill();
        b.buyerNGO = other;
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(PurposeVault.WrongNGO.selector);
        vault.release(b, vendorSig, a, ngoSig);
    }

    function test_unknownVendorReverts() public {
        PurposeVault.Bill memory b = _bill();
        b.vendor = stranger;
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(STRANGER_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.UnknownVendor.selector, stranger));
        vault.release(b, vendorSig, a, ngoSig);
    }

    function test_amberVendorReverts() public {
        vm.prank(ngo);
        registry.enroll(amberVendor, "Shree Supplies");

        PurposeVault.Bill memory b = _bill();
        b.vendor = amberVendor;
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(AMBER_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.TierNotGreen.selector, uint8(1)));
        vault.release(b, vendorSig, a, ngoSig);
    }

    function test_badVendorSigReverts() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory forgedSig = _signBill(NGO_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.BadVendorSig.selector, ngo));
        vault.release(b, forgedSig, a, ngoSig);
    }

    function test_wrongVaultReverts() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        a.donorVault = other;
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(PurposeVault.WrongVault.selector);
        vault.release(b, vendorSig, a, ngoSig);
    }

    function test_overAllocatedReverts() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory first = _alloc(b, CHAIN_A, 6_000);
        PurposeVault.Allocation memory second = _alloc(b, CHAIN_A, 6_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory firstNgoSig = _signAlloc(NGO_PK, first);
        bytes memory secondNgoSig = _signAlloc(NGO_PK, second);
        vault.release(b, vendorSig, first, firstNgoSig);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.OverAllocated.selector, uint256(12_000)));
        vault.release(b, vendorSig, second, secondNgoSig);
    }

    function test_frozenVaultReverts() public {
        // Freeze is set directly here. Block 10 adds the real path, submitEquivocation, and its test
        // then checks the full VaultFrozen("equivocation") text.
        stdstore.target(address(vault)).sig("frozen()").checked_write(true);

        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.VaultFrozen.selector, ""));
        vault.release(b, vendorSig, a, ngoSig);
    }
}
