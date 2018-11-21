# -*- coding: utf-8 -*-

"""
The MIT License (MIT)

Copyright (c) 2015-2016 Rapptz
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

import asyncio
import logging
import json

import websockets
from websockets.http import Headers
from .api import connect_details, rtc_version

log = logging.getLogger(__name__)

# websocket:       https://tools.ietf.org/html/rfc6455
# websocket SDP:   https://tools.ietf.org/html/rfc8124


def tc_headers():
    """
    Default headers to use for the websocket handshake.

    If the user agent is changed here, it should
    be changed accordingly in the TinychatWebSocket.join
    method to, to mimic a browser connect in the best way.

    :return: A default headers dictionary.
    :rtype: dict
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:62.0) Gecko/20100101 Firefox/62.0',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
    }

    return headers


class TinychatWebSocket(websockets.client.WebSocketClientProtocol):
    """

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._dispatch = lambda *positional: None
        # self._dispatch_listeners = []
        self._req = 1

    @property
    def req(self):
        """
        Returns the next req ID.

        :return: The next req id.
        :rtype: int
        """
        return self._req

    @classmethod
    async def connect(cls, client):
        """

        :param client: An instance of tclib.TinychatClient.
        :type client: tclib.TinychatClient
        :return:
        :rtype:
        """
        ws = None

        log.info('requesting gateway')
        gateway = await connect_details(client.room)
        log.debug(f'gateway: {gateway}')

        if len(gateway) == 2:
            try:
                ws = await asyncio.wait_for(
                    websockets.connect(
                        uri=gateway['endpoint'],
                        origin='https://tinychat.com',
                        subprotocols=['tc'],
                        extra_headers=Headers(tc_headers()),
                        loop=client.loop,
                        klass=cls
                    ),
                    timeout=60, loop=client.loop)
            # check for connect timeout error.
            except asyncio.TimeoutError:
                log.warning('timed out waiting for client connect.')
                # return await cls.from_client(resume=resume)

            # send the join message.
            await ws.join(client, gateway['token'])

            # assign the dispatcher.
            # Sync From Async
            ws._dispatch = client.dispatch

            try:
                # make sure the websocket is in a open state.
                await ws.ensure_open()
            except websockets.exceptions.ConnectionClosed as e:
                log.warning(f'connection was closed: {e.code} {e.reason}')
            else:
                log.info(f'websocket connected to: {gateway["endpoint"]}')
        else:
            log.warning(f'failed to get gateway: {gateway}')

        return ws

    async def dispatch_message(self, message):
        """

        :param message:
        :type message:
        """
        # convert the message data to a json object.
        event_data = json.loads(message)
        # get the event.
        event = event_data.get('tc')

        # if the event is a ping, handle it here.
        if event == 'ping':
            await self._pong()
        else:
            # Sync From Async
            self._dispatch(event, event_data)

    async def poll_event(self):
        """

        :return:
        :rtype:
        """
        try:
            # receive the next message from the websocket.
            msg = await self.recv()
            # dispatch the message.
            await self.dispatch_message(msg)
        except websockets.exceptions.ConnectionClosed as e:
            log.info(f'websocket closed with: {e.code} reason: {e.reason}')

    async def ws_send(self, data):
        """

        :param data:
        :type data:
        """
        await super().send(data)
        log.debug(data)

    async def send_as_json(self, data):
        """

        :param data:
        :type data:
        """
        json_data = json.dumps(data)
        await self.ws_send(json_data)
        self._req += 1

    async def _pong(self):
        """
        Send a response to a tinychat ping event.
        """
        payload = {
            'tc': 'pong',
            'req': self.req
        }

        await self.send_as_json(payload)

    async def join(self, client, token):
        """

        :param client:
        :type client:
        :param token:
        :type token:
        """
        # this will be > 1 if reconnecting
        if self.req > 1:
            # reset back to 1
            self._req = 1

        tc_version = await rtc_version(client.room)

        payload = {
            'tc': 'join',
            'req': self.req,
            'useragent': f'tinychat-client-webrtc-undefined_win64-{tc_version}',
            'token': token,
            'room': client.room,
            'nick': client.nick
        }

        await self.send_as_json(payload)

    async def nick(self, nickname):

        payload = {
            'tc': 'nick',
            'req': self.req,
            'nick': nickname
        }

        await self.send_as_json(payload)

    async def msg(self, msg):

        payload = {
            'tc': 'msg',
            'req': self.req,
            'text': msg
        }

        await self.send_as_json(payload)

    async def pvtmsg(self, msg, handle):

        payload = {
            'tc': 'pvtmsg',
            'req': self.req,
            'text': msg,
            'handle': handle
        }

        await self.send_as_json(payload)

    async def kick(self, handle):

        payload = {
            'tc': 'kick',
            'req': self.req,
            'handle': handle
        }

        await self.send_as_json(payload)

    async def ban(self, handle):

        payload = {
            'tc': 'ban',
            'req': self.req,
            'handle': handle
        }

        await self.send_as_json(payload)

    async def unban(self, ban_id):

        payload = {
            'tc': 'unban',
            'req': self.req,
            'id': ban_id
        }

        await self.send_as_json(payload)

    async def banlist(self):

        payload = {
            'tc': 'banlist',
            'req': self.req
        }

        await self.send_as_json(payload)

    async def password(self, password):

        payload = {
            'tc': 'password',
            'req': self.req,
            'password': password
        }

        await self.send_as_json(payload)

    async def stream_moder_allow(self, handle):

        payload = {
            'tc': 'stream_moder_allow',
            'req': self.req,
            'handle': handle
        }

        await self.send_as_json(payload)

    async def stream_moder_close(self, handle):

        payload = {
            'tc': 'stream_moder_close',
            'req': self.req,
            'handle': handle
        }

        await self.send_as_json(payload)

    async def captcha(self, token):

        payload = {
            'tc': 'captcha',
            'req': self.req,
            'token': token
        }

        await self.send_as_json(payload)

    # Media.
    async def yut_playlist(self):

        payload = {
            'tc': 'yut_playlist',
            'req': self.req
        }

        await self.send_as_json(payload)

    async def yut_playlist_add(self, video_id, duration, title, image):

        payload = {
            'tc': 'yut_playlist_add',
            'req': self.req,
            'item': {
                'id': video_id,
                'duration': duration,
                'title': title,
                'image': image
            }
        }

        await self.send_as_json(payload)

    async def yut_playlist_remove(self, video_id, duration, title, image):

        payload = {
            'tc': 'yut_playlist_remove',
            'req': self.req,
            'item': {
                'id': video_id,
                'duration': duration,
                'title': title,
                'image': image
            }
        }
        await self.send_as_json(payload)

    async def yut_playlist_mode(self, randomize, repeat):

        payload = {
            'tc': 'yut_playlist_mode',
            'req': self.req,
            'mode': {
                'random': randomize,
                'repeat': repeat
            }
        }

        await self.send_as_json(payload)

    async def yut_play(self, video_id, duration, title, offset=0):

        payload = {
            'tc': 'yut_play',
            'req': self.req,
            'item': {
                'id': video_id,
                'duration': duration,
                'offset': offset,
                'title': title
            }
        }

        # when doing seek.
        if offset != 0:
            del payload['item']['title']
            payload['item']['playlist'] = False
            payload['item']['seek'] = True

        await self.send_as_json(payload)

    async def yut_pause(self, video_id, duration, offset=0):

        payload = {
            'tc': 'yut_pause',
            'req': self.req,
            'item': {
                'id': video_id,
                'duration': duration,
                'offset': offset
            }
        }

        await self.send_as_json(payload)

    async def yut_stop(self, video_id, duration, offset=0):

        payload = {
            'tc': 'yut_stop',
            'req': self.req,
            'item': {
                'id': video_id,
                'duration': duration,
                'offset': offset
            }
        }

        await self.send_as_json(payload)
