"""Network module for sopel

Provides several commands that print information on the current state of the
Freifunk Kassel network.
"""

import json
import os

from sopel import module
from sopel.module import interval
from sopel.config.types import FilenameAttribute, StaticSection


# Time in seconds, that the bot reloads network metrics
INTERVAL_UPDATE = 60


class NetworkSection(StaticSection):
    cache_file = FilenameAttribute('cache_file', default='network_cache.json')
    meshviewer_file = FilenameAttribute('meshviewer_file', default='/home/ffks-map/meshviewer/build/data/nodes.json')


def setup(bot):
    bot.config.define_section('network', NetworkSection)


def cache_read(bot):
    cache_file = bot.config.network.cache_file
    if not os.path.isfile(cache_file):
        bot.say('Cache file does not exist.')
        return

    with open(cache_file) as json_file:
        cache = json.load(json_file)

    return cache


@interval(INTERVAL_UPDATE)
def update_metrics(bot, force=False):
    """Load metrics from meshviewer_file and update values in cache_file"""
    # Partly grabbed from here:
    # https://github.com/freifunkks/salt-conf/blob/master/state/graphite/ffks-nodestats.py

    meshviewer_file = bot.config.network.meshviewer_file
    if not os.path.isfile(meshviewer_file):
        bot.say('Meshviewer file does not exist.')
        return

    with open(meshviewer_file) as json_file:
        data = json.load(json_file)
    nodes = data['nodes']
    nodes_online = 0
    client_count = 0

    for node_mac, node in nodes.items():
        try:
            if node['flags']['online']:
                nodes_online += 1
        except KeyError:
            pass
        try:
            clients = node['statistics']['clients']
            client_count += int(clients)
        except KeyError:
            pass

    cache = cache_read(bot)

    print("Nodes online: %s"   % nodes_online)
    print("Clients online: %s" % client_count)


@module.commands('status')
def status(bot, trigger):
    """Print current and maximum nodes and clients."""
    current(bot, trigger)
    maximum(bot, trigger)


@module.commands('current')
def current(bot, trigger):
    """Print current nodes and clients."""
    cache = cache_read(bot)
    nodes_current = cache['nodes']['current']
    clients_current = cache['clients']['current']
    bot.say('Current: %s nodes, %s clients' % (nodes_current, clients_current))


@module.commands('maximum')
def maximum(bot, trigger):
    """Print maximum nodes and clients."""
    cache = cache_read(bot)
    nodes_max = cache['nodes']['max']
    clients_max = cache['clients']['max']
    bot.say('Maximum: %s nodes, %s clients' % (nodes_max, clients_max))
