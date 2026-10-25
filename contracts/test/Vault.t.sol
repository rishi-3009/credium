// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {CreditiumBase} from "./CreditiumBase.sol";
import {PurposeVault} from "../src/PurposeVault.sol";

// Plan Block 8: deposit (approve, then deposit, then Deposited event) and cap behaviour.
contract VaultTest is CreditiumBase {
    address alice = makeAddr("alice");

    function test_depositPullsTokensAndEmits() public {
        PurposeVault v = new PurposeVault(address(token), ngo, address(registry), category, CAP_PAISE);
        token.mint(alice, 1_000);

        vm.startPrank(alice);
        token.approve(address(v), 1_000);
        vm.expectEmit(true, false, false, true, address(v));
        emit PurposeVault.Deposited(alice, 1_000);
        v.deposit(1_000);
        vm.stopPrank();

        assertEq(token.balanceOf(address(v)), 1_000);
        assertEq(token.balanceOf(alice), 0);
    }

    function test_depositWithoutApprovalReverts() public {
        PurposeVault v = new PurposeVault(address(token), ngo, address(registry), category, CAP_PAISE);
        token.mint(alice, 1_000);

        vm.prank(alice);
        vm.expectRevert();
        v.deposit(1_000);
    }

    function test_releaseAtExactlyCapPasses() public {
        PurposeVault.Bill memory b = _bill();
        b.amountPaise = CAP_PAISE;
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vault.release(b, vendorSig, a, ngoSig);

        assertEq(vault.released(), CAP_PAISE);
    }

    function test_releaseOverCapReverts() public {
        PurposeVault.Bill memory b = _bill();
        b.amountPaise = CAP_PAISE + 1;
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(PurposeVault.CapExceeded.selector);
        vault.release(b, vendorSig, a, ngoSig);
    }

    function test_releaseAddingPastCapReverts() public {
        PurposeVault.Bill memory first = _bill();
        first.amountPaise = CAP_PAISE;
        PurposeVault.Allocation memory firstAlloc = _alloc(first, CHAIN_A, 10_000);
        vault.release(first, _signBill(VENDOR_PK, first), firstAlloc, _signAlloc(NGO_PK, firstAlloc));

        PurposeVault.Bill memory second = _bill();
        second.billNo = 418;
        second.amountPaise = 1;
        PurposeVault.Allocation memory secondAlloc = _alloc(second, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, second);
        bytes memory ngoSig = _signAlloc(NGO_PK, secondAlloc);

        vm.expectRevert(PurposeVault.CapExceeded.selector);
        vault.release(second, vendorSig, secondAlloc, ngoSig);
    }

    function test_releaseWithoutBalanceReverts() public {
        PurposeVault empty = new PurposeVault(address(token), ngo, address(registry), category, CAP_PAISE);
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        a.donorVault = address(empty);
        bytes memory vendorSig = _signBill(VENDOR_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(PurposeVault.InsufficientBalance.selector);
        empty.release(b, vendorSig, a, ngoSig);
    }
}
