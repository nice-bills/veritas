"""Pytest configuration for Veritas tests."""

import pytest
import asyncio
from unittest.mock import MagicMock
from datetime import datetime
import uuid


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_agent_account():
    """Create mock agent account for testing."""
    account = MagicMock()
    account.address = "0x742d35Cc6634C0532925a3b844Bc9e7595f8fE45"
    account.key = b"\x01" * 32
    return account


@pytest.fixture
def mock_w3():
    """Create mock Web3 instance for testing."""
    w3 = MagicMock()
    w3.eth.get_code.return_value = b"\x00"
    w3.keccak.return_value = b"\x00" * 32
    w3.to_checksum_address.return_value = "0x742d35Cc6634C0532925a3b844Bc9e7595f8fE45"
    return w3


@pytest.fixture
def sample_agent_config():
    """Sample agent configuration for testing."""
    return {
        "name": "TestAgent",
        "brain_provider": "minimax",
        "network": "base-sepolia",
        "capabilities": ["wallet", "token", "basename"],
        "objective": "Check my balance and register a basename",
    }


@pytest.fixture
def sample_mission():
    """Sample mission for testing."""
    return {
        "objective": "Check my wallet balance and get ETH price",
        "max_steps": 5,
    }


@pytest.fixture
def sample_action_log():
    """Sample action log for testing."""
    return {
        "id": str(uuid.uuid4()),
        "basis_id": None,
        "event_type": "ACTION",
        "tool_name": "get_balance",
        "input_params": {"args": [], "kwargs": {}},
        "output_result": {"balance": "1.0 ETH"},
        "timestamp": datetime.utcnow().timestamp(),
    }


@pytest.fixture
def sample_observation_log():
    """Sample observation log for testing."""
    return {
        "id": str(uuid.uuid4()),
        "basis_id": str(uuid.uuid4()),
        "event_type": "OBSERVATION",
        "tool_name": "get_price",
        "input_params": {"args": [], "kwargs": {"pair": "ETH/USD"}},
        "output_result": {"price": 2937.54},
        "timestamp": datetime.utcnow().timestamp(),
    }
