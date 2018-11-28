# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2018 Nortxort

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

import logging
from .data.message import TextMessage, YoutubeMessage

log = logging.getLogger(__name__)


class ProcessEvent:
    """
    Process an event before it's method gets called.
    """
    def __init__(self, client, event, method, event_data):
        """
        Initialize the event processing.

        :param client: An instance of TinychatClient.
        :type client: client.TinychatClient
        :param event: The event to process.
        :type event: str
        :param method: The method name to call once the processing is done.
        :type method: str
        :param event_data: The event data
        :type event_data: dict
        """
        self._client = client
        self._event = event
        self._method = method
        self._event_data = event_data

    async def process(self):
        """
        Process an event.
        """
        log.info(f'processing: `{self._event}` event_data: '
                 f'{self._event_data} method: {self._method}')

        # strict user events
        if self._event == 'join':
            await self._process_join()
        elif self._event == 'nick':
            await self._process_nick()
        elif self._event == 'quit':
            await self._process_quit()

        # general user events
        elif self._event in ['msg', 'pvtmsg']:
            await self._process_msg()
        elif self._event == 'yut_play':
            await self._process_yut_play()
        elif self._event == 'yut_pause':
            await self._process_yut_pause()
        elif self._event == 'yut_stop':
            await self._process_yut_stop()

        # broadcasting events
        elif self._event in ['publish', 'unpublish',
                             'pending_moderation']:
            await self._process_broadcasting()

        # client events
        elif self._event == 'userlist':
            await self._process_userlist()
        elif self._event == 'banlist':
            await self._process_banlist()
        elif self._event == 'ban':
            await self._process_ban()
        elif self._event == 'unban':
            await self._process_unban()
        elif self._event == 'stream_moder_allow':
            await self._process_stream_moder_allow()
        elif self._event == 'stream_moder_close':
            await self._process_stream_moder_close()
        elif self._event == 'captcha':
            await self._process_captcha()
        elif self._event == 'password':
            await self._process_password()

        else:
            # no processing
            await self._client.run_method(self._method, self._event_data)

    async def _process_join(self):
        """
        Process a join event.
        """
        user = self._client.users.add(self._event_data)
        await self._client.run_method(self._method, user)

    async def _process_nick(self):
        """
        Process a nick event.
        """
        user = self._client.users.change_nick(self._event_data)
        await self._client.run_method(self._method, user)

    async def _process_quit(self):
        """
        Process a quit event.
        """
        user = self._client.users.delete(self._event_data.get('handle'))
        await self._client.run_method(self._method, user)

    async def _process_msg(self):
        """
        Process a msg event.

        NOTE: this could be either a private message
        or a public message.
        """
        user = self._client.users.search(self._event_data.get('handle'))
        text = self._event_data.get('text')
        msg = TextMessage(text, self._event)
        await self._client.run_method(self._method, *(user, msg))

    async def _process_yut_play(self):
        """
        Process an yut_play event.
        """
        user = None

        if 'handle' in self._event_data:
            user = self._client.users.search(self._event_data.get('handle'))

        youtube = YoutubeMessage(self._event_data)
        await self._client.run_method(self._method, *(user, youtube))

    async def _process_yut_pause(self):
        """
        Process an yut_pause event.
        """
        user = self._client.users.search(self._event_data.get('handle'))
        youtube = YoutubeMessage(self._event_data)
        await self._client.run_method(self._method, *(user, youtube))

    async def _process_yut_stop(self):
        """
        Process an yut_stop event.
        """
        youtube = YoutubeMessage(self._event_data)
        await self._client.run_method(self._method, youtube)

    async def _process_broadcasting(self):
        """
        Process a broadcasting event.
        """
        user = self._client.users.search(self._event_data.get('handle'))
        await self._client.run_method(self._method, user)

    async def _process_userlist(self):
        """
        Process the userlist event.
        """
        userlist = []
        for item in self._event_data.get('users'):
            user = self._client.users.add(item)
            # do not add the client data, its already there
            if user.handle != self._client.users.client.handle:
                userlist.append(user)

        await self._client.run_method(self._method, userlist)

    async def _process_banlist(self):
        """
        Process the banlist event.
        """
        banlist = []
        for item in self._event_data.get('items'):
            banned_user = self._client.users.add_banned_user(item)
            banlist.append(banned_user)

        await self._client.run_method(self._method, banlist)

    async def _process_ban(self):
        """
        Process a ban event.
        """
        if self._event_data.get('success'):
            user_ban = self._client.users.add_banned_user(self._event_data)

            await self._client.run_method(self._method, user_ban)
        else:
            # await self._client.on_error(self._method, **self._event_data)
            pass

    async def _process_unban(self):
        """
        Process an unban event.
        """
        if self._event_data.get('success'):
            unbanned = self._client.users.delete_banned_user(self._event_data)

            await self._client.run_method(self._method, unbanned)
        else:
            # await self._client.on_error(self._method, **self._event_data)
            pass

    async def _process_stream_moder_allow(self):
        """
        Process an stream_moder_allow event.
        """
        if self._event_data.get('success'):
            allowed = self._client.users.search(self._event_data.get('handle'))

            await self._client.run_method(self._method, allowed)
        else:
            # await self._client.on_error(self._method, **self._event_data)
            pass

    async def _process_stream_moder_close(self):
        """
        Process and stream_moder_close event.
        """
        if self._event_data.get('success'):
            closed = self._client.users.search(self._event_data.get('handle'))

            await self._client.run_method(self._method, closed)
        else:
            # await self._client.on_error(self._method, **self._event_data)
            pass

    async def _process_captcha(self):
        """
        Process captcha event.
        """
        site_key = self._event_data.get('key')
        await self._client.run_method(self._method, site_key)

    async def _process_password(self):
        """
        Process password event.
        """
        req_id = self._event_data.get('req')
        await self._client.run_method(self._method, req_id)
