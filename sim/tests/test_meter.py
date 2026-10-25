from sim.meter import compute_meter


def test_positive_example():
    """Positive example: unexplainedPaise 160000000 and invariantOk True."""
    result = compute_meter(2300000000, 2140000000, 18000000, 18000000, 0)
    assert result["unexplainedPaise"] == 160000000
    assert result["invariantOk"] is True


def test_rogue_example():
    """Rogue example: invariantOk False."""
    result = compute_meter(2300000000, 2140000000, 23000000, 18000000, 0)
    assert result["invariantOk"] is False


def test_amber_counted():
    """Amber is counted in invariant check."""
    result = compute_meter(100, 100, 30, 20, 10)
    assert result["invariantOk"] is True


def test_all_keys_present():
    """All 7 keys are present in the result."""
    result = compute_meter(100, 100, 30, 20, 10)
    assert set(result.keys()) == {
        "pledgedPaise",
        "depositedPaise",
        "releasedPaise",
        "verifiedPaise",
        "amberPaise",
        "unexplainedPaise",
        "invariantOk",
    }
