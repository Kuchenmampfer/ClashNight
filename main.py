import argparse
import traceback

from bot import Bot
from settings import Settings

parser = argparse.ArgumentParser(description="uuuuu's bot")
parser.add_argument('--dev', dest='dev_mode', action='store_true', default=False,
                    help='set this, to run the bot in developer mode')
args = parser.parse_args()
dev_mode = vars(args)['dev_mode']

settings = Settings(dev_mode, False)

if __name__ == "__main__":
    try:
        bot = Bot(settings)
        bot.run(settings.discord_bot_token)
    except BaseException:
        traceback.print_exc()
