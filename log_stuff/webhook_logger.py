#  This file is copied from https://github.com/bijij/Ditto/tree/master/ditto/utils
#  It was published under the following license:
"""
The MIT License (MIT)

Copyright (c) 2018-2021 Bijij

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

import asyncio
import aiohttp

import discord
from discord.ext import tasks

__all__ = ("EmbedWebhookLogger",)


class EmbedWebhookLogger:
    _to_log: list[discord.Embed]

    def __init__(self, webhook_url: str, *, loop: asyncio.BaseEventLoop = None) -> None:
        self.loop = loop or asyncio.get_event_loop()
        self._webhook_url = webhook_url
        self._to_log = []

        self._session = aiohttp.ClientSession()
        self._webhook = discord.Webhook.from_url(self._webhook_url, session=self._session)

        # setup loop
        self._loop.start()

    def log(self, embed: discord.Embed) -> None:
        self._to_log.append(embed)

    @tasks.loop(seconds=5)
    async def _loop(self) -> None:
        while self._to_log:
            embeds = [self._to_log.pop(0) for _ in range(min(10, len(self._to_log)))]
            await self._webhook.send(embeds=embeds)
