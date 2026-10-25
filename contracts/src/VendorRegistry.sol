// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

// SIMULATED trust anchor. Only the registrar's enrolment can reach GREEN (plan M1).
contract VendorRegistry {
    struct Vendor {
        string name;
        address enrolledBy;
        uint256 enrolledAt;
    }

    uint256 public constant GREEN_AGE = 7 days;

    address public immutable registrar;
    mapping(address => Vendor) public vendors;

    constructor(address _registrar) {
        registrar = _registrar;
    }

    // Open on purpose: anyone can enrol, but the tier depends on who enrolled.
    function enroll(address vendor, string calldata name) external {
        vendors[vendor] = Vendor({name: name, enrolledBy: msg.sender, enrolledAt: block.timestamp});
    }

    function isRegistered(address vendor) public view returns (bool) {
        return vendors[vendor].enrolledAt != 0;
    }

    // 0 GREEN: enrolled by registrar and at least 7 days old
    // 1 AMBER: enrolled by anyone else, or by registrar but younger than 7 days
    // 2 UNREGISTERED
    function tierOf(address vendor) public view returns (uint8) {
        if (!isRegistered(vendor)) return 2;
        Vendor storage v = vendors[vendor];
        if (v.enrolledBy == registrar && block.timestamp >= v.enrolledAt + GREEN_AGE) return 0;
        return 1;
    }
}
