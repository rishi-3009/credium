// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {Test} from "forge-std/Test.sol";
import {MockINR} from "../src/MockINR.sol";
import {VendorRegistry} from "../src/VendorRegistry.sol";

contract RegistryTest is Test {
    VendorRegistry registry;
    address registrar = makeAddr("registrar");
    address ngo = makeAddr("ngo");
    address vendor = makeAddr("vendor");

    function setUp() public {
        registry = new VendorRegistry(registrar);
    }

    function test_unregisteredIsTier2() public view {
        assertFalse(registry.isRegistered(vendor));
        assertEq(registry.tierOf(vendor), 2);
    }

    function test_registrarEnrolledYoungIsAmber() public {
        vm.prank(registrar);
        registry.enroll(vendor, "Ramesh Hardware");
        assertEq(registry.tierOf(vendor), 1);
    }

    function test_registrarEnrolledAt6DaysIsStillAmber() public {
        vm.prank(registrar);
        registry.enroll(vendor, "Ramesh Hardware");
        vm.warp(block.timestamp + 7 days - 1);
        assertEq(registry.tierOf(vendor), 1);
    }

    function test_registrarEnrolledAt7DaysIsGreen() public {
        vm.prank(registrar);
        registry.enroll(vendor, "Ramesh Hardware");
        vm.warp(block.timestamp + 7 days);
        assertEq(registry.tierOf(vendor), 0);
    }

    function test_ngoEnrolledIsAmberEvenAfter7Days() public {
        vm.prank(ngo);
        registry.enroll(vendor, "Shree Supplies");
        vm.warp(block.timestamp + 30 days);
        assertEq(registry.tierOf(vendor), 1);
    }
}

contract MockINRTest is Test {
    MockINR token;
    address alice = makeAddr("alice");

    function setUp() public {
        token = new MockINR();
    }

    function test_decimalsIsZero() public view {
        assertEq(token.decimals(), 0);
    }

    function test_openMint() public {
        vm.prank(alice);
        token.mint(alice, 1_000);
        assertEq(token.balanceOf(alice), 1_000);
    }
}
