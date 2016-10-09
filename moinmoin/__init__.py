"""MoinMoin module for sopel

Print information on changes of a MoinMoin wiki by polling and parsing the
RecentChanges action page.
"""

import json
import os
import re
import requests

from sopel import module
from sopel.module import interval
from sopel.config.types import FilenameAttribute, StaticSection, ValidatedAttribute

try:
    import xml.etree.cElementTree as et
except ImportError:
    print("cElementTree not found. Using slower Python implementation 'ElementTree' instead.")
    import xml.etree.ElementTree as et


# Time in seconds, that the bot reloads network metrics
INTERVAL_UPDATE = 60

# Colored prefix
#   \x03AA,BB
#   AA = foreground color
#   BB = background color
#   ,BB can be omitted
#
#   For more information
#   https://github.com/myano/jenni/wiki/IRC-String-Formatting
#   http://www.mirc.co.uk/colors.html
COLOR_NETWORK = '\x0306' # magenta
COLOR_BOLD    = '\x02'
COLOR_RESET   = '\x0F'
COLOR_PREFIX  = '[%sweb%s]' % (COLOR_NETWORK, COLOR_RESET)


class MoinMoinSection(StaticSection):
    cache_file = FilenameAttribute('cache_file', default='moinmoin_cache.xml')
    rss_url = ValidatedAttribute('rss_url', default='https://freifunk-kassel.de/action/rss_rc/RecentChanges?action=rss_rc&unique=1&ddiffs=1')
    announce_channel = ValidatedAttribute('announce_channel', default='#ffks')


def setup(bot):
    bot.config.define_section('moinmoin', MoinMoinSection)


def cache_read(bot):
    announce_channel = bot.config.moinmoin.announce_channel
    cache_file = bot.config.moinmoin.cache_file
    if not os.path.isfile(cache_file):
        bot.say("{} Cache file does not exist.".format(COLOR_PREFIX), announce_channel)
        return

    with open(cache_file) as xml_file:
        cache = xml_file.read()

    return cache


def cache_write(bot, cache):
    announce_channel = bot.config.moinmoin.announce_channel
    cache_file = bot.config.moinmoin.cache_file
    if not os.path.isfile(cache_file):
        bot.say("{} Cache file does not exist.".format(COLOR_PREFIX), announce_channel)
        return

    with open(cache_file, 'w') as xml_file:
        try:
            xml_file.write(cache.decode('utf-8'))
        except AttributeError:
            xml_file.write(cache)


@interval(INTERVAL_UPDATE)
def check_recent_changes(bot, force=False):
    """Download recent changes xml file and print on diff with local cache"""
    announce_channel = bot.config.moinmoin.announce_channel

    r = requests.get(bot.config.moinmoin.rss_url)
    if r.status_code != 200:
        bot.say("{} Could not download recent changes".format(COLOR_PREFIX), announce_channel)
        return

    changes_new = r.text.encode('utf-8')
    changes_old = cache_read(bot)
    if changes_old == "":
        bot.say("{} No cached recent changes yet".format(COLOR_PREFIX), announce_channel)

    # No change detected, no need for comparisons
    if changes_new == changes_old:
        return

    items_new = parse_xml(changes_new)
    items_old = parse_xml(changes_old)

    for item in items_new:
        if item in items_old:
            continue
        bot.say("{} {}{}{} updated by {}:".format(COLOR_PREFIX,
                 COLOR_BOLD,
                 item['title'],
                 COLOR_RESET,
                 item['author']), announce_channel)
        bot.say("      {}".format(item['url']), announce_channel)

    cache_write(bot, changes_new)

# Parses MoinMoin's RSS XML structure and gives back a list of dicts with the
# following elements:
#   author
#   date
#   title
#   url
def parse_xml(xml_string):
    tree = et.fromstring(xml_string)
    items = []

    for item in tree.findall("{http://purl.org/rss/1.0/}item"):
        author = item.find("{http://purl.org/dc/elements/1.1/}contributor").find("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description").find("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}value").text
        date = item.find("{http://purl.org/dc/elements/1.1/}date").text
        title = item.find("{http://purl.org/rss/1.0/}title").text
        url = item.find("{http://purl.org/rss/1.0/}link").text

        author = re.sub(r"Self:(.+)", r"\1", author)

        items.append({"author":author,
                      "date":date,
                      "title":title,
                      "url":url})

    return items
