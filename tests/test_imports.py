"""Basic import tests to verify package structure."""


def test_cli_import():
    """Test that CLI module can be imported."""
    from auction_sim import cli

    assert cli is not None


def test_engine_import():
    """Test that simulation engine can be imported."""
    from auction_sim.simulation import engine

    assert hasattr(engine, "simulate_block")


def test_mechanisms_import():
    """Test that auction mechanisms can be imported."""
    from auction_sim.auction import mechanisms

    assert hasattr(mechanisms, "allocate")
