// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {CreditiumBase} from "./CreditiumBase.sol";
import {PurposeVault} from "../src/PurposeVault.sol";

// 14:30 gate. Full cross-check against sim/fixtures/vector.json still to add (plan B1).
contract GateTest is CreditiumBase {
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
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.WrongChain.selector, CHAIN_B));
        vault.release(b, vendorSig, a, ngoSig);
    }

    function test_chainAReleaseWithValidSigsPays() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        vault.release(b, _signBill(VENDOR_PK, b), a, _signAlloc(NGO_PK, a));
        assertEq(token.balanceOf(vendor), 18_000_000);
    }

    function test_vendorSignedByNgoReverts() public {
        PurposeVault.Bill memory b = _bill();
        PurposeVault.Allocation memory a = _alloc(b, CHAIN_A, 10_000);
        bytes memory ngoSignedBill = _signBill(NGO_PK, b);
        bytes memory ngoSig = _signAlloc(NGO_PK, a);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.BadVendorSig.selector, ngo));
        vault.release(b, ngoSignedBill, a, ngoSig);
    }
}
