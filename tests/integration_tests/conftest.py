from unittest import mock
import pytest
from server import PlayerService, GameService


def pytest_addoption(parser):
    parser.addoption('--mysql_host', action='store', default='127.0.0.1', help='mysql host to use for test database')
    parser.addoption('--mysql_username', action='store', default='root', help='mysql username to use for test database')
    parser.addoption('--mysql_password', action='store', default='', help='mysql password to use for test database')
    parser.addoption('--mysql_database', action='store', default='faf_test', help='mysql database to use for tests')

@pytest.fixture
def mock_players(mock_db_pool):
    m = mock.create_autospec(PlayerService(mock_db_pool))
    m.client_version_info = (0, None)
    return m

@pytest.fixture
def mock_games(mock_players, db):
    return mock.create_autospec(GameService(mock_players, db))
