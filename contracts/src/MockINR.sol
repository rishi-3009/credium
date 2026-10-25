// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

// SIMULATED. Mock rupee token: units are paise, so decimals is 0. Mint is open because it is a mock.
contract MockINR is ERC20 {
    constructor() ERC20("Mock INR (simulated)", "mINR") {}

    function decimals() public pure override returns (uint8) {
        return 0;
    }

    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}
