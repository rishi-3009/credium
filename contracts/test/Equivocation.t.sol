// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {CreditiumBase} from "./CreditiumBase.sol";
import {PurposeVault} from "../src/PurposeVault.sol";
import {VendorRegistry} from "../src/VendorRegistry.sol";

// Plan Block 10: two NGO-signed allocations for one bill freeze every vault they are submitted to.
// Each vault is a separate contract here. Chain B's allocation is checked on this chain by design (plan §8b).
contract EquivocationTest is CreditiumBase {
    PurposeVault vaultB;

    function setUp() public override {
        super.setUp();
        vaultB = new PurposeVault(address(token), ngo, address(registry), category, CAP_PAISE);
    }

    function _bill417() internal view returns (PurposeVault.Bill memory) {
        return _bill();
    }

    function test_bill417At100PlusB100FreezesBothVaults() public {
        PurposeVault.Bill memory b = _bill417();
        PurposeVault.Allocation memory onA = _alloc(b, CHAIN_A, 10_000);
        PurposeVault.Allocation memory onB = _alloc(b, CHAIN_B, 10_000);
        bytes memory sigA = _signAlloc(NGO_PK, onA);
        bytes memory sigB = _signAlloc(NGO_PK, onB);

        vault.submitEquivocation(onA, sigA, onB, sigB);
        vaultB.submitEquivocation(onA, sigA, onB, sigB);

        assertTrue(vault.frozen());
        assertTrue(vaultB.frozen());
        assertEq(vault.frozenReason(), "equivocation");
        assertEq(vaultB.frozenReason(), "equivocation");
    }

    function test_releaseAfterFreezeReverts() public {
        PurposeVault.Bill memory b = _bill417();
        PurposeVault.Allocation memory onA = _alloc(b, CHAIN_A, 10_000);
        PurposeVault.Allocation memory onB = _alloc(b, CHAIN_B, 10_000);
        bytes memory sigA = _signAlloc(NGO_PK, onA);
        bytes memory sigB = _signAlloc(NGO_PK, onB);
        vault.submitEquivocation(onA, sigA, onB, sigB);

        // A fresh bill, so the revert reason is the freeze and not an earlier check.
        PurposeVault.Bill memory fresh = _bill();
        fresh.billNo = 405;
        PurposeVault.Allocation memory freshAlloc = _alloc(fresh, CHAIN_A, 10_000);
        bytes memory vendorSig = _signBill(VENDOR_PK, fresh);
        bytes memory ngoSig = _signAlloc(NGO_PK, freshAlloc);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.VaultFrozen.selector, "equivocation"));
        vault.release(fresh, vendorSig, freshAlloc, ngoSig);
    }

    function test_bill418At60PlusB60FreezesBothVaults() public {
        PurposeVault.Bill memory b = _bill();
        b.billNo = 418;
        PurposeVault.Allocation memory onA = _alloc(b, CHAIN_A, 6_000);
        PurposeVault.Allocation memory onB = _alloc(b, CHAIN_B, 6_000);
        bytes memory sigA = _signAlloc(NGO_PK, onA);
        bytes memory sigB = _signAlloc(NGO_PK, onB);

        vault.submitEquivocation(onA, sigA, onB, sigB);
        vaultB.submitEquivocation(onA, sigA, onB, sigB);

        assertTrue(vault.frozen());
        assertTrue(vaultB.frozen());
    }

    function test_alreadyFrozenIsNoOp() public {
        PurposeVault.Bill memory b = _bill417();
        PurposeVault.Allocation memory onA = _alloc(b, CHAIN_A, 10_000);
        PurposeVault.Allocation memory onB = _alloc(b, CHAIN_B, 10_000);
        bytes memory sigA = _signAlloc(NGO_PK, onA);
        bytes memory sigB = _signAlloc(NGO_PK, onB);
        vault.submitEquivocation(onA, sigA, onB, sigB);

        // Invalid evidence (6000 + 4000 is within 100%) would revert, but a frozen vault returns first.
        PurposeVault.Allocation memory small = _alloc(b, CHAIN_B, 4_000);
        PurposeVault.Allocation memory smaller = _alloc(b, CHAIN_A, 6_000);
        vault.submitEquivocation(smaller, _signAlloc(NGO_PK, smaller), small, _signAlloc(NGO_PK, small));

        assertTrue(vault.frozen());
        assertEq(vault.frozenReason(), "equivocation");
    }

    function test_withinOneHundredPercentReverts() public {
        PurposeVault.Bill memory b = _bill417();
        PurposeVault.Allocation memory onA = _alloc(b, CHAIN_A, 6_000);
        PurposeVault.Allocation memory onB = _alloc(b, CHAIN_B, 4_000);
        bytes memory sigA = _signAlloc(NGO_PK, onA);
        bytes memory sigB = _signAlloc(NGO_PK, onB);

        vm.expectRevert(PurposeVault.NotEquivocation.selector);
        vault.submitEquivocation(onA, sigA, onB, sigB);
    }

    function test_identicalAllocationsRevert() public {
        PurposeVault.Bill memory b = _bill417();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory sig = _signAlloc(NGO_PK, a);

        vm.expectRevert(PurposeVault.NotEquivocation.selector);
        vault.submitEquivocation(a, sig, a, sig);
    }

    function test_nonNgoSignatureReverts() public {
        PurposeVault.Bill memory b = _bill417();
        PurposeVault.Allocation memory onA = _alloc(b, CHAIN_A, 10_000);
        PurposeVault.Allocation memory onB = _alloc(b, CHAIN_B, 10_000);
        bytes memory sigA = _signAlloc(NGO_PK, onA);
        bytes memory forged = _signAlloc(VENDOR_PK, onB);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.BadNgoSig.selector, vendor));
        vault.submitEquivocation(onA, sigA, onB, forged);
    }

    function test_differentNullifiersRevert() public {
        PurposeVault.Bill memory b = _bill417();
        PurposeVault.Bill memory other = _bill417();
        other.billNo = 418;
        PurposeVault.Allocation memory onA = _alloc(b, CHAIN_A, 10_000);
        PurposeVault.Allocation memory onB = _alloc(other, CHAIN_B, 10_000);
        bytes memory sigA = _signAlloc(NGO_PK, onA);
        bytes memory sigB = _signAlloc(NGO_PK, onB);

        vm.expectRevert(PurposeVault.NullifierMismatch.selector);
        vault.submitEquivocation(onA, sigA, onB, sigB);
    }

    function test_fractionOverMaxReverts() public {
        PurposeVault.Bill memory b = _bill417();
        PurposeVault.Allocation memory onA = _alloc(b, CHAIN_A, 10_001);
        PurposeVault.Allocation memory onB = _alloc(b, CHAIN_B, 10_000);
        bytes memory sigA = _signAlloc(NGO_PK, onA);
        bytes memory sigB = _signAlloc(NGO_PK, onB);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.BadFraction.selector, uint256(10_001)));
        vault.submitEquivocation(onA, sigA, onB, sigB);
    }
}
