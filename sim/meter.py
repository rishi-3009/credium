"""SIMULATED meter. Money in paise."""


def compute_meter(pledged: int, deposited: int, released_onchain: int, verified: int, amber: int) -> dict:
    """Compute meter values with invariant check.

    Args:
        pledged: Pledged amount in paise.
        deposited: Deposited amount in paise.
        released_onchain: Amount released on chain (sum from both vaults).
        verified: Amount verified by verifier (GREEN).
        amber: AMBER amount from verifier.

    Returns:
        Dictionary with meter values and invariant check.
    """
    return {
        "pledgedPaise": pledged,
        "depositedPaise": deposited,
        "releasedPaise": released_onchain,
        "verifiedPaise": verified,
        "amberPaise": amber,
        "unexplainedPaise": pledged - deposited,
        "invariantOk": released_onchain == verified + amber,
    }
