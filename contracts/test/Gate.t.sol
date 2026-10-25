// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {CreditiumBase} from "./CreditiumBase.sol";
import {PurposeVault} from "../src/PurposeVault.sol";
import {VendorRegistry} from "../src/VendorRegistry.sol";

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

    // Plan B1 / 14:30 gate: Solidity checks against Ayaan's sim/fixtures/vector.json.

    function _vectorBill(string memory json) internal pure returns (PurposeVault.Bill memory) {
        return PurposeVault.Bill({
            vendor: vm.parseJsonAddress(json, ".bill.vendor"),
            buyerNGO: vm.parseJsonAddress(json, ".bill.buyerNGO"),
            billNo: vm.parseJsonUint(json, ".bill.billNo"),
            amountPaise: vm.parseJsonUint(json, ".bill.amountPaise"),
            issuedAt: vm.parseJsonUint(json, ".bill.issuedAt"),
            category: vm.parseJsonBytes32(json, ".bill.category"),
            itemsCommitment: vm.parseJsonBytes32(json, ".bill.itemsCommitment")
        });
    }

    function _vectorChainBAllocation(string memory json) internal pure returns (PurposeVault.Allocation memory) {
        return PurposeVault.Allocation({
            billNullifier: vm.parseJsonBytes32(json, ".chainB.allocation.billNullifier"),
            donorVault: vm.parseJsonAddress(json, ".chainB.allocation.donorVault"),
            chainId: vm.parseJsonUint(json, ".chainB.allocation.chainId"),
            fractionBps: vm.parseJsonUint(json, ".chainB.allocation.fractionBps"),
            reportId: vm.parseJsonBytes32(json, ".chainB.allocation.reportId")
        });
    }

    function test_vectorDomainSeparatorMatches() public view {
        string memory json = vm.readFile("../sim/fixtures/vector.json");
        assertEq(vault.DOMAIN_SEPARATOR(), vm.parseJsonBytes32(json, ".domainSeparator"));
    }

    function test_vectorChainBAllocationRecoversVectorNgo() public view {
        string memory json = vm.readFile("../sim/fixtures/vector.json");
        PurposeVault.Allocation memory a = _vectorChainBAllocation(json);
        bytes memory ngoSig = vm.parseJsonBytes(json, ".chainB.ngoSig");
        assertEq(vault.allocationSigner(a, ngoSig), vm.parseJsonAddress(json, ".ngo"));
    }

    function test_vectorChainBReleaseOnChainAReverts() public {
        string memory json = vm.readFile("../sim/fixtures/vector.json");
        PurposeVault.Bill memory b = _vectorBill(json);
        PurposeVault.Allocation memory a = _vectorChainBAllocation(json);
        bytes memory vendorSig = vm.parseJsonBytes(json, ".vendorSig");
        bytes memory ngoSig = vm.parseJsonBytes(json, ".chainB.ngoSig");

        // Vault whose NGO and vendor are the vector's, so the release reaches the chainId check.
        VendorRegistry vectorRegistry = new VendorRegistry(registrar);
        vm.prank(registrar);
        vectorRegistry.enroll(b.vendor, "Ramesh Hardware");
        vm.warp(block.timestamp + 7 days);
        PurposeVault vectorVault = new PurposeVault(address(token), b.buyerNGO, address(vectorRegistry), category, CAP_PAISE);

        vm.expectRevert(abi.encodeWithSelector(PurposeVault.WrongChain.selector, CHAIN_B));
        vectorVault.release(b, vendorSig, a, ngoSig);
    }
}
