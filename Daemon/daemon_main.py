import argparse
import asyncio

import nest_asyncio
import traceback

import os
import sys
sys.path.append(os.getcwd())

from Daemon.daemon import Daemon
from settings import Settings

parser = argparse.ArgumentParser(description="daemon for builder base bot")
parser.add_argument('--dev', dest='dev_mode', action='store_true', default=False,
                    help='set this, to run the bot in developer mode')
args = parser.parse_args()
dev_mode = vars(args)['dev_mode']

settings = Settings(dev_mode, True)

if __name__ == "__main__":
    try:
        # Nest patches asyncio to allow for nested loops to allow logging into coc
        nest_asyncio.apply()

        daemon = Daemon(settings)
        asyncio.get_event_loop().run_until_complete(daemon.start())
    except BaseException:
        traceback.print_exc()
