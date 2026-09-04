from app import compute_increment, compute_reset, demo


def test_compute_increment():
    assert compute_increment(0) == (1, "1")
    assert compute_increment(4) == (5, "5")


def test_compute_reset():
    assert compute_reset(10) == (0, "0")


def test_demo_builds():
    assert demo is not None
