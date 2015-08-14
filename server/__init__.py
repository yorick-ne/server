"""
Forged Alliance Forever server project

Copyright (c) 2014 Gael Honorez
Copyright (c) 2015 Michael Søndergaard <sheeo@sheeo.dk>

Distributed under GPLv3, see license.txt
"""

__version__ = '0.1'
__author__ = 'Chris Kitching, Dragonfire, Gael Honorez, Jeroen De Dauw, Crotalus, Michael Søndergaard'
__contact__ = 'admin@faforever.com'
__license__ = 'GPLv3'
__copyright__ = 'Copyright (c) 2011-2015 ' + __author__

import asyncio
import json
import config

player_service = None
game_service = None

from .playerservice import PlayerService

# Initialise the game and player services.
@asyncio.coroutine
def initialise_player_service():
    global player_service
    player_service = playerservice.PlayerService()
    yield from player_service.really_update_static_ish_data()

@asyncio.coroutine
def initialise_game_service(players, db):
    global game_service
    game_service = gameservice.GameService(players, db)
    yield from game_service.load_game_id_counter()

asyncio.get_event_loop().run_until_complete(asyncio.async(initialise_player_service()))
asyncio.get_event_loop().run_until_complete(asyncio.async(initialise_game_service()))

from .gameservice import GameService
from .gameconnection import GameConnection
from .natpacketserver import NatPacketServer

from server.games import GamesContainer, Ladder1V1GamesContainer, CoopGamesContainer
from server.lobbyconnection import LobbyConnection
from server.protocol import QDataStreamProtocol
from server.servercontext import ServerContext
from server.control import init as run_control_server

def run_lobby_server(address: (str, int),
                     db,
                     loop):
    """
    Run the lobby server

    :param address: Address to listen on
    :param player_service: Service to talk to about players
    :param game_service: Service to talk to about games
    :param db: QSqlDatabase
    :param loop: Event loop to use
    :return ServerContext: A server object
    """
    def report_dirty_games():
        dirties = game_service.dirty_games
        game_service.clear_dirty()

        def encode(game):
            return QDataStreamProtocol.pack_block(
                QDataStreamProtocol.pack_qstring(json.dumps(game.to_dict()))
            )
        for game in dirties:
            if game.state == server.games.game.GameState.ENDED:
                game_service.remove_game(game)
        message = b''.join(map(encode, dirties))
        if len(message) > 0:
            ctx.broadcast_raw(message, validate_fn=lambda lobby_conn: lobby_conn.authenticated)
        loop.call_later(5, report_dirty_games)

    def ping_broadcast():
        ctx.broadcast_raw(QDataStreamProtocol.pack_block(QDataStreamProtocol.pack_qstring('PING')))
        loop.call_later(45, ping_broadcast)

    def initialize_connection():
        return LobbyConnection(context=ctx,
                               db=db,
                               loop=loop)
    ctx = ServerContext(initialize_connection, name="LobbyServer", loop=loop)
    loop.call_later(5, report_dirty_games)
    loop.call_soon(ping_broadcast)
    return ctx.listen(*address)


def run_game_server(address: (str, int),
                    loop):
    """
    Run the game server

    :return (NatPacketServer, ServerContext): A pair of server objects
    """
    nat_packet_server = NatPacketServer(loop, config.LOBBY_UDP_PORT)

    def initialize_connection():
        gc = GameConnection(loop)
        nat_packet_server.subscribe(gc, ['ProcessServerNatPacket'])
        return gc
    ctx = ServerContext(initialize_connection, name='GameServer', loop=loop)
    server = ctx.listen(*address)
    return nat_packet_server, server
