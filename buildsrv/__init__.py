"""Build server module for sopel

Allows building new firmware and print information on builds' progress.
"""

from sopel import module

# Colored prefix
#   \x03AA,BB
#   AA = foreground color
#   BB = background color
#   ,BB can be omitted
#
#   For more information
#   https://github.com/myano/jenni/wiki/IRC-String-Formatting
#   http://www.mirc.co.uk/colors.html
COLOR_NETWORK = '\x0303' # green
COLOR_BOLD    = '\x02'
COLOR_RESET   = '\x0F'
COLOR_PREFIX  = '[%sbld%s]' % (COLOR_NETWORK, COLOR_RESET)


class BuildServerSection(StaticSection):
    bot_log = FilenameAttribute('cache_file', default='/tmp/sopel-build-gluon.log')
    build_log = FilenameAttribute('cache_file', default='/tmp/build-gluon.log')
    announce_channel = ValidatedAttribute('announce_channel', default='#ffks-test')


def setup(bot):
    bot.config.define_section('buildsrv', BuildServerSection)


@module.example('!build beta')
@module.example('!build stable')
@module.commands('build')
def status(bot, trigger):
    """Starts building all targets for given branch."""
    announce_channel = bot.config.moinmoin.announce_channel

    if len(trigger.groups()) < 2:
        bot.say("{} Please enter a branch to be built".format(COLOR_PREFIX), announce_channel)
    branch = trigger.group(2)

    bot.say("{} Starting build for branch '{}'".format(COLOR_PREFIX,
             branch), announce_channel)
