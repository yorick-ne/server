import asyncio
import pytest

from unittest import mock

from server.playerservice import PlayerService
from server.players import Player


@pytest.fixture
def player_service(mock_db_pool):
    return mock.create_autospec(PlayerService(mock_db_pool))
