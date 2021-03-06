"""
Forged Alliance Forever server project

Copyright (c) 2014 Gael Honorez
Copyright (c) 2015 Michael Søndergaard <sheeo@sheeo.dk>

Distributed under GPLv3, see license.txt
"""
import json
import logging

import aiomeasures

import server.db
import config

from .games.game import GameState, VisibilityState
from .stats.game_stats_service import GameStatsService
from .gameconnection import GameConnection
from .natpacketserver import NatPacketServer
from .lobbyconnection import LobbyConnection
from .protocol import Protocol, QDataStreamProtocol
from .servercontext import ServerContext
from .player_service import PlayerService
from .game_service import GameService
from .ladder_service import LadderService
from .control import init as run_control_server

__version__ = '0.1'
__author__ = 'Chris Kitching, Dragonfire, Gael Honorez, Jeroen De Dauw, Crotalus, Michael Søndergaard'
__contact__ = 'admin@faforever.com'
__license__ = 'GPLv3'
__copyright__ = 'Copyright (c) 2011-2015 ' + __author__


__all__ = [
    'run_lobby_server',
    'games',
    'control',
    'abc',
    'protocol'
]

stats = aiomeasures.StatsD(config.STATSD_SERVER)

def run_lobby_server(address: (str, int),
                     player_service: PlayerService,
                     games: GameService,
                     loop):
    """
    Run the lobby server

    :param address: Address to listen on
    :param player_service: Service to talk to about players
    :param games: Service to talk to about games
    :param loop: Event loop to use
    :return ServerContext: A server object
    """
    def encode_game(game):
        # Crazy evil encoding scheme
        return QDataStreamProtocol.pack_block(
            QDataStreamProtocol.pack_qstring(json.dumps(game.to_dict()))
        )

    def encode_players(players):
        return QDataStreamProtocol.pack_block(
            QDataStreamProtocol.pack_qstring(json.dumps(
                    {
                        'command': 'player_info',
                        'players': [player.to_dict() for player in players]
                    }
            ))
        )

    def report_dirties():
        try:
            dirty_games = games.dirty_games
            dirty_players = player_service.dirty_players
            games.clear_dirty()
            player_service.clear_dirty()

            if len(dirty_players) > 0:
                ctx.broadcast_raw(encode_players(dirty_players), lambda lobby_conn: lobby_conn.authenticated)

            # TODO: This spams squillions of messages: we should implement per-connection message
            # aggregation at the next abstraction layer down :P
            for game in dirty_games:
                if game.state == GameState.ENDED:
                    games.remove_game(game)

                # So we're going to be broadcasting this to _somebody_...
                message = encode_game(game)

                # These games shouldn't be broadcast, but instead privately sent to those who are
                # allowed to see them.
                if game.visibility == VisibilityState.FRIENDS:
                    # To see this game, you must have an authenticated connection and be a friend of the host.
                    validation_func = lambda lobby_conn: lobby_conn.player.id in game.host.friends
                else:
                    validation_func = lambda lobby_conn: lobby_conn.player.id not in game.host.foes

                ctx.broadcast_raw(message, lambda lobby_conn: lobby_conn.authenticated and validation_func(lobby_conn))
        except Exception as e:
            logging.getLogger().exception(e)
        finally:
            loop.call_later(1, report_dirties)

    ping_msg = QDataStreamProtocol.pack_block(QDataStreamProtocol.pack_qstring('PING'))

    def ping_broadcast():
        ctx.broadcast_raw(ping_msg)
        loop.call_later(45, ping_broadcast)

    def initialize_connection():
        return LobbyConnection(context=ctx,
                               games=games,
                               players=player_service,
                               loop=loop)
    ctx = ServerContext(initialize_connection, name="LobbyServer", loop=loop)
    loop.call_later(5, report_dirties)
    loop.call_soon(ping_broadcast)
    loop.run_until_complete(ctx.listen(*address))
    return ctx
