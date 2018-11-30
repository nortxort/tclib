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

import logging
import asyncio
from contextlib import suppress

from .protocol import TinychatWebSocket
from .users import Users
from .console import Console
from ._process_event import ProcessEvent
from .api import Account, user_info, close_session
from .data.room import RoomState
from . import utils, captcha


log = logging.getLogger(__name__)


class TinychatClient(object):
    """
    Tinychat websocket client.

    The client takes the following optional keyword arguments.

    :keyword nick: Nickname to enter the room with.
    :type nick: str
    :keyword loop: Asyncio event loop.
    :keyword account: Tinychat account.
    :type account: str | None
    :keyword password: Tinychat password.
    :type password: str | None
    :keyword debug: Enable asyncio debug logging.
    :type debug: bool
    :keyword acak: anti-captcha API key.
    :type acak: str
    """
    def __init__(self, room_name, *, nick=None, loop=None, **options):
        """
        Initiate the client.

        :param room_name: The room name of the room to enter.
        :type room_name: str
        """
        self.room = room_name
        self.nick = nick
        self.loop = asyncio.get_event_loop() if loop is None else loop
        self.account = options.get('account', None)
        self.password = options.get('password', None)

        self.ws = None
        self.users = Users()
        self.state = RoomState()
        self.console = Console(loop=self.loop)
        self.debug = options.get('debug', False)

        self._anti_captcha_key = options.get('acak', '')
        self._acc = None

        if nick is None:
            # if no nick is provided, create one
            self.nick = utils.create_random_string(5, 15)

        # asyncio debug mode
        self.loop.set_debug(self.debug)

    # Internals.
    def _clean_up(self):
        """
        Cancel pending tasks.

        Modified and moved from self.run()
        were it was in discord.client
        """
        # close the web session.
        self.loop.create_task(close_session())

        pending = asyncio.Task.all_tasks(loop=self.loop)
        for task in pending:
            task.cancel()
            # https://stackoverflow.com/questions/37278647/fire-and-forget-python-async-await/37345564#37345564
            with suppress(asyncio.CancelledError):
                self.loop.run_until_complete(task)

        # close the event loop
        self.loop.close()

    async def _process_event(self, event, method, event_data):
        """
        Process an event.

        This will process an event based on the event itself,
        before the event method will be called.

        :param event: The event to process.
        :type event: str
        :param method: The method to call once the event has been processed.
        :type method: str
        :param event_data: The event data as dictionary.
        :type event_data: dict
        """
        pe = ProcessEvent(self, event, method, event_data)
        await pe.process()

    async def run_method(self, method, *args, **kwargs):
        """
        Call an event method.

        NOTE: This is for internal use only.

        :param method: The name of the method to run.
        :type method: str
        :param args: A tuple of arguments to the method.
        :type args: tuple
        :param kwargs: keyword arguments.
        :type kwargs: dict
        """
        # Async From Async
        func = getattr(self, method, None)
        if func is not None:
            await func(*args, **kwargs)

    def dispatch(self, event, event_data):
        """

        :param event: The event to be dispatched.
        :type event: str
        :param event_data: The event data.
        :type event_data: dict
        """
        # Sync From Async
        log.debug(f'dispatching: {event}')
        method = f'on_{event}'
        if hasattr(self, method):
            # https://www.aeracode.org/2018/02/19/python-async-simplified/
            asyncio.create_task(self._process_event(event, method, event_data))
            # asyncio.run_coroutine_threadsafe(
            #     self._run_method(method, *args, **kwargs), self.loop)

    # Properties.
    @property
    def connected(self):
        """
        Returns a bool depending on the state of the connection.

        :return: True if the connection is in a open state.
        :rtype: bool
        """
        if self.ws is not None:
            if not self.ws.closed and self.ws.open:
                return True

        return False

    @property
    def is_logged_in(self):
        """
        Indicates if the client is logged in.

        :return: True if logged in, else False.
        :rtype: bool
        """
        if isinstance(Account, self._acc):
            return self._acc.is_logged_in()

        return False

    @property
    def page_url(self):
        """
        The link for the room.

        :return: The url to the room on tinychat.
        :rtype: str
        """
        return f'https://tinychat.com/room/{self.room}'

    def run(self):
        """

        """
        self.loop.run_until_complete(self.start())
        # try:
        #     self.loop.run_until_complete(self.start(account, password))
        # except KeyboardInterrupt:
        #     log.debug('keyboard interrupt.')
        # finally:
        #     # close the websocket connection.
        #     self.loop.run_until_complete(self.close())  # use task?
        #     # close the event loop.
        #     log.warning('CLOSING LOOP')
        #     self.loop.close()

    async def start(self):
        """

        """
        if self.account is not None and self.password is not None:
            await self.login(self.account, self.password)
        await self.connect()

    async def login(self, account, password):
        """
        Login to a tinychat account.

        :param account: The account name.
        :type account: str
        :param password: The account password.
        :type password: str
        """
        self._acc = Account(account, password)
        if await self._acc.login():
            self.console.write(f'Logged in as: {account}')
        else:
            self.console.write(f'Failed to login as: {account}')

    # Connection.
    async def connect(self):
        """
        Connect to the websocket and start event polling.
        """
        self.ws = await TinychatWebSocket.connect(self)
        if self.ws is not None:

            if self.ws.open:
                # TODO: set is connected event?
                while not self.ws.closed:
                    # loop will end by calling self.close()
                    try:
                        await self.ws.poll_event()
                    except Exception as e:
                        log.warning(e)
                        break
                # TODO: reset is connected event?

    async def disconnect(self, clean_up=True):
        """
        Close the websocket connection.

        :param clean_up: Should be False if reconnecting.
        :type clean_up: bool
        """
        if self.ws is not None and self.ws.open:
            log.debug('closing websocket connection.')
            # close the websocket with code 1001 (GoingAway)
            # https://tools.ietf.org/html/rfc6455#section-7.4.1
            await self.ws.close(1001, 'GoingAway')

        # self.users.clear()
        # self.users.clear_banlist()

        if clean_up:
            self._clean_up()

    # Error handler.
    async def on_error(self, *args, **kwargs):
        pass

    # Events.
    async def on_closed(self, data):
        """
        This gets sent when ever the connection gets closed
        by the server for what ever reason.

        NOTE: Close the websocket connection
        on any code.

        :param data: The close data.
        :type data: dict
        """
        code = data.get('error')
        if code == 3:
            self.console.write(f'Closed with code {code}')
        elif code == 4:
            self.console.write(f'You have been banned from the room. {code}')
        elif code == 5:
            self.console.write(f'Reconnect code? {code}')
        elif code == 6:
            self.console.write(f'Double account sign in. {code}')
        elif code == 8:
            # timeout error. usually when not entering
            # password or captcha within ~60 seconds.
            self.console.write(f'Timeout error {code}')
        elif code == 11:
            # not sure what this is or why it occurs
            self.console.write(f'Something went wrong, code {code}')
        elif code == 12:
            self.console.write(f'You have been kicked from the room. {code}')

        else:
            self.console.write(f'Connection was closed, code: {code}')

    async def on_joined(self, data):
        """
        Received when the client have joined the room successfully.

        :param data: This contains info about the client,
        such as user role and so on.
        :type data: dict
        """
        log.info(f'client info: {data}')
        client = self.users.add(data.get('self'), is_client=True)
        self.console.write(f'Client joined the room: {client.nick}:{client.handle}')

        if client.is_mod:
            await self.send_banlist()

        await self.on_room_info(data.get('room'))

    async def on_room_info(self, room_info):
        """
        Received when the client have joined the room successfully.

        This information will only show in the console
        if debug is enabled.

        :param room_info: This contains information about the room
        such as about, profile image and so on.
        :type room_info: dict
        """
        self.state.update(**room_info)
        if self.debug:
            self.console.write('<Room Information>')
            self.console.write(self.state.formatted(), ts=False)

    async def on_room_settings(self, room_settings):
        """
        Received when a change has been made to
        the room settings(privacy page).

        This information will only show in the console
        if debug is enabled.

        :param room_settings: The room settings.
        :type room_settings: dict
        """
        self.state.update(**room_settings)
        self.console.write('<Room State Changed>')
        if self.debug:
            self.console.write(self.state.formatted(), ts=False)

    async def on_userlist(self, user_list):  # P
        """
        Received upon joining a room.

        :param user_list: All users in the room.
        :type user_list: list
        """
        for user in user_list:
            if user.is_owner:
                self.console.write(f'Joins room owner: '
                                   f'{user.nick}:{user.handle}:{user.account}')
            elif user.is_mod:
                self.console.write(f'Joins room moderator: '
                                   f'{user.nick}:{user.handle}:{user.account}')

            elif user.account:
                self.console.write(f'Joins: {user.nick}:{user.handle}:{user.account}')

            else:
                self.console.write(f'Joins: {user.nick}:{user.handle}')

    async def on_join(self, user):  # P
        """
        Received when a user joins the room.

        :param user: The user joining as User object.
        :type user: Users.User
        """
        if user.account:
            tc_info = await user_info(user.account)
            if tc_info is not None:
                self.users.add_tc_info(user.handle, tc_info)

            if user.is_owner:
                self.console.write(f'Owner joined: '
                                   f'{user.nick}:{user.handle}:{user.account}')
            elif user.is_mod:
                self.console.write(f'Moderator joined: '
                                   f'{user.nick}:{user.handle}:{user.account}')
            else:
                self.console.write(f'User joined: '
                                   f'{user.nick}:{user.handle}:{user.account}')
        else:
            self.console.write(f'Guest joined: {user.nick}:{user.handle}')

    async def on_nick(self, user):   # P
        """
        Received when a user changes nick name.

        :param user: The user changing nick as User object.
        :type user: Users.User
        """
        old_nick = user.old_nicks[-2]
        self.console.write(f'{old_nick} changed nick to {user.nick}:{user.handle}')

    async def on_quit(self, user):  # P
        """
        Received when a user leaves the room.

        :param user: The user leaving as User object.
        :type user: Users.User
        """
        if user is not None:
            # user can be None if user is broadcasting, and then leaves?
            self.console.write(f'{user.nick}:{user.handle} left the room.')

    async def on_ban(self, banned):  # P
        """
        Received when the client bans a user.

        TODO: Test this

        :param banned: The user who was banned.
        :type banned: Users.BannedUser
        """
        self.console.write(f'{banned.nick} was banned.')

    async def on_unban(self, unbanned):  # P
        """
        Received when the client un-bans a user.

        TODO: Test this

        :param unbanned: The banned user who was unbanned.
        :type unbanned: Users.BannedUser
        """
        self.console.write(f'{unbanned.nick} was unbanned.')

    async def on_banlist(self, banlist):  # P
        """
        Received when a request for the ban list has been made.

        :param banlist: A list of BannedUser objects.
        :type banlist: list
        """
        for banned in banlist:
            self.console.write(f'Nick: {banned.nick} '
                               f'Account: {banned.account} '
                               f'Banned By: {banned.banned_by}')

    async def on_msg(self, user, msg):  # P
        """
        Received when a message is sent to the room.

        :param user: The user sending a message as User object.
        :type user: Users.User
        :param msg: The text message as TextMessage object.
        :type msg: TextMessage
        """
        self.console.write(f'{user.nick}: {msg.text}')
        # add the message to the user message list.
        user.messages.append(msg)

    async def on_pvtmsg(self, user, msg):  # P
        """
        Received when a user sends the client a private message.

        :param user: The user sending a private message as User object.
        :type user: Users.User
        :param msg: The text message as TextMessage object.
        :type msg: TextMessage
        """
        self.console.write(f'[PM] {user.nick}: {msg.text}')
        # add the message to the user message list.
        user.messages.append(msg)

    async def on_publish(self, user):  # P
        """
        Received when a user starts broadcasting.

        :param user: The user broadcasting as User object.
        :type user: Users.User
        """
        user.is_broadcasting = True
        user.is_waiting = False
        self.console.write(f'{user.nick}:{user.handle} is broadcasting.')

    async def on_unpublish(self, user):  # P
        """
        Received when a user stops broadcasting.

        :param user: The user who stops broadcasting as User object.
        :type user: Users.User
        """
        if user is not None:
            user.is_broadcasting = False
            self.console.write(f'{user.nick}:{user.handle} stopped broadcasting.')

    async def on_sysmsg(self, msg):
        """
        System messages sent from the server to all clients (users).

        These messages are special events notifications.

        :param msg: The special notifications message data.
        :type msg: dict
        """
        text = msg.get('text')

        if 'banned' in text and self.users.client.is_mod:
            self.users.clear_banlist()
            await self.send_banlist()
        elif 'green room enabled' in text:
            self.state.set_greenroom(True)
        elif 'green room disabled' in text:
            self.state.set_greenroom(False)

        self.console.write(f'[SYSTEM]:{text}')

    async def on_password(self, req_id):  # P
        """
        Received when a room is password protected.

        An on_closed event with code 8 will be called
        if a password has not been provided within
        ~60 seconds

        3 password attempts can be tried
        before a reconnect is required.
        """
        try:
            rp = await asyncio.wait_for(self.console.input(
                f'Password protected room ({req_id}), '
                f'enter password:\n'), 59)
        except asyncio.TimeoutError:
            self.console.write('Password timeout. '
                               'Click enter to quit.', ts=False)
            await self.disconnect()
        else:
            await self.send_room_password(rp)

    async def on_pending_moderation(self, user):  # P
        """
        Received when a user is waiting in the green room.

        :param user: The user waiting in the green room as User object.
        :type user: Users.User
        """
        self.state.set_greenroom(True)
        user.is_waiting = True
        self.console.write(f'{user.nick}:{user.handle} is waiting '
                           f'for broadcast approval.')

    async def on_stream_moder_allow(self, allowed):  # P
        """
        Received when a user has been allowed by the client,
        to broadcast in a green room.

        TODO: Test this

        :param allowed: The user that was allowed to broadcast.
        :type allowed: Users.User
        """
        self.console.write(f'{allowed.nick}:{allowed.handle}'
                           f' was allowed to broadcast.')

    async def on_stream_moder_close(self, closed):  # P
        """
        Received when a user has their broadcast
        closed by the client.

        TODO: Test this

        :param closed: The user that was closed.
        :type closed: Users.User
        """
        self.console.write(f'{closed.nick}:{closed.handle} '
                           f'was closed.')

    async def on_captcha(self, site_key):  # P
        """
        Received when a room has captcha enabled.

        :param site_key: The captcha site key.
        :type site_key: str
        """
        if len(self._anti_captcha_key) == 32:
            self.console.write('Starting captcha solving service, please wait...')
            try:
                ac = captcha.AntiCaptcha(self.page_url, self._anti_captcha_key)
                token = await ac.solver(site_key)
            except (captcha.NoFundsError, captcha.MaxTriesError) as e:
                self.console.write(e)
                await self.loop.create_task(self.disconnect())
            except captcha.AntiCaptchaApiError as ace:
                self.console.write(ace.description)
                await self.loop.create_task(self.disconnect())
            else:
                # what is the length of a token?
                if len(token) > 20:
                    await self.send_captcha(token)
        else:
            self.console.write(f'Captcha enabled: {site_key}\n '
                               f'1) Open {self.page_url} in a browser.\n '
                               f'2) Solve the captcha and close the browser.\n '
                               f'3) Connect the client/bot.', ts=False)

            await self.loop.create_task(self.disconnect())

    # Media Events.
    async def on_yut_playlist(self, playlist_data):
        """
        Received when a request for the playlist has been made.

        The playlist is as, one would see if being a moderator
        and using a web browser.

        :param playlist_data: The data of the items in the playlist.
        :type playlist_data: dict
        """
        pass

    async def on_yut_play(self, user, youtube):  # P
        """
        Received when a youtube gets started or searched.
        
        :param user: The User object of the user
        starting or searching the youtube.
        :type user: Users.User
        :param youtube: The YoutubeMessage object.
        :type youtube: YoutubeMessage
        """
        if user is None:
            self.console.write(f'[YOUTUBE] {youtube.title} is playing.')
        else:
            if not youtube.is_response:
                if youtube.offset == 0:
                    self.console.write(f'{user.nick} is playing {youtube.title}')

                elif youtube.offset > 0:
                    self.console.write(f'{user.nick} searched {youtube.title} to '
                                       f'{youtube.offset}')

            # add the message to user message list,
            # even if the user is the client itself
            user.messages.append(youtube)

    async def on_yut_pause(self, user, youtube):  # P
        """
        Received when a youtube gets paused or searched while paused.

        :param user: The User object of the user pausing the video.
        :type user: Users.User
        :param youtube: The YoutubeMessage object.
        :type youtube: YoutubeMessage
        """
        if not youtube.is_response:
            self.console.write(f'{user.nick} paused {youtube.title}'
                               f' at {youtube.offset}')

    async def on_yut_stop(self, youtube):  # P
        """
        Received when a youtube is stopped.

        :param youtube: The YoutubeMessage object.
        :type youtube: YoutubeMessage
        """
        self.console.write(f'{youtube.title} was stopped at {youtube.offset} '
                           f'({youtube.duration})')

    # Messages.
    async def set_nick(self, nickname):
        """

        :param nickname:
        :type nickname:
        """
        await self.ws.nick(nickname)

    async def send_public_msg(self, msg):
        """
        Send a chat message to the room.

        :param msg: The message to send.
        :type msg: str
        """
        await self.ws.msg(msg)

    async def send_private_msg(self, msg, handle):
        """
        Send a private message to a user.

        :param msg: The private message to send.
        :type msg: str
        :param handle: The handle(id) of the user to send the message to.
        :type handle: int
        """
        await self.ws.pvtmsg(msg, handle)

    async def send_kick(self, handle):
        """
        Send a kick message to kick a user out of the room.

        :param handle: The handle(id) of the user to kick.
        :type handle: int
        """
        await self.ws.kick(handle)

    async def send_ban(self, handle):
        """
        Send a ban message to ban a user from the room.

        :param handle: The handle(id) of the user to ban.
        :type handle: int
        """
        await self.ws.ban(handle)

    async def send_unban(self, ban_id):
        """
        Send a un-ban message to un-ban a banned user.

        :param ban_id: The ban ID of the user to un-ban.
        :type ban_id: int
        """
        await self.ws.unban(ban_id)

    async def send_banlist(self):
        """
        Send a banlist request message.
        """
        await self.ws.banlist()

    async def send_room_password(self, password):
        """
        Send a room password message.

        :param password: The room password.
        :type password: str
        """
        await self.ws.password(password)

    async def send_approve_broadcast(self, handle):
        """
        Allow a user to broadcast in green room enabled room.

        :param handle: The handle(id) of the user.
        :type handle: int
        """
        await self.ws.stream_moder_allow(handle)

    async def send_close_broadcast(self, handle):
        """
        Close a users broadcast.

        :param handle: The handle(id) of the user.
        :type handle: int
        """
        await self.ws.stream_moder_close(handle)

    async def send_captcha(self, token):
        """
        Send a captcha token to a captcha enabled room.

        :param token: A valid captcha token.
        :type token: str
        """
        await self.ws.captcha(token)

    # Media Messages.
    async def send_yut_playlist(self):
        """
        Send a youtube playlist request.
        """
        await self.ws.yut_playlist()

    async def send_yut_playlist_add(self, video_id, duration, title, image):
        """
        Add a youtube video to the web browser playlist.

        TODO: Explore this

        :param video_id: The youtube video ID.
        :type video_id: str
        :param duration: The duration of the video (in seconds).
        :type duration: int
        :param title: The title of the video.
        :type title: str
        :param image: The thumbnail image url of the video.
        :type image: str
        """
        await self.ws.yut_playlist_add(video_id, duration, title, image)

    async def send_yut_playlist_remove(self, video_id, duration, title, image):
        """
        Remove a youtube video from the web browser playlist.

        TODO: Explore this

        :param video_id: The youtube video ID to remove.
        :type video_id: str
        :param duration: The duration of the video to remove.
        :type duration: int | float
        :param title: The title of the video to remove.
        :type title: str
        :param image: The thumbnail image url of the video.
        :type image: str
        """
        await self.ws.yut_playlist_remove(video_id, duration, title, image)

    async def send_yut_playlist_mode(self, randomize=False, repeat=False):
        """
        Set the mode of the web browser playlist.

        TODO: Explore this

        :param randomize: Setting this to True,
        will make videos play at random?
        :type randomize: bool
        :param repeat: Setting this to True,
        will make the playlist repeat itself?
        :type repeat: bool
        """
        await self.ws.yut_playlist_mode(randomize, repeat)

    async def send_yut_play(self, video_id, duration, title, offset=0):
        """
        Start or search a youtube video.

        :param video_id: The youtube video ID to start or search.
        :type video_id: str
        :param duration: The duration of the video in seconds.
        :type duration: int | float
        :param title: The title of the video.
        :type title: str
        :param offset: The offset seconds to start the video at,
        in the case of doing a search.
        :type offset: int | float
        """
        await self.ws.yut_play(video_id, duration, title, offset)

    async def send_yut_pause(self, video_id, duration, offset=0):
        """
        Pause, or search while a youtube video is paused .

        :param video_id: The youtube video ID to pause or search.
        :type video_id: str
        :param duration: The duration of the video in seconds.
        :type duration: int |float
        :param offset: The offset seconds to pause the
        video at in case of doing search while in pause.
        :type offset: int |float
        """
        await self.ws.yut_pause(video_id, duration, offset)

    async def send_yut_stop(self, video_id, duration, offset=0):
        """
        Stop a youtube video currently playing.

        :param video_id: The youtube video ID to stop.
        :type video_id: str
        :param duration: The duration of the video in seconds.
        :type duration: int | float
        :param offset: The offset seconds where the video gets stopped at.
        :type offset: int |float
        """
        await self.ws.yut_stop(video_id, duration, offset)

    # Broadcasting.
    async def ice(self):
        pass
