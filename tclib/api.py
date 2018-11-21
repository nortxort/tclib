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

from . import web

__all__ = [
    'Account',
    'close_session',
    'rtc_version',
    'connect_details',
    'user_info'
]


async def close_session():
    await web.session_close()


async def rtc_version(room):
    """
    Parse the current tinychat RTC version.

    :param room: This could be a static room name,
    since the html of any room will do.
    :type room: str
    :return: The current tinychat rtc version, or None on failure.
    :rtype: str
    """
    # (28/10/2018)
    version = '2.0.20-420'

    url = f'https://tinychat.com/room/{room}'
    response = await web.get(url)

    if response is not None:
        html = await response.text()
        pattern = '<link rel="manifest" href="/webrtc/'
        if pattern in html:
            version = html.split(pattern)[1].split('/manifest.json">')[0]

    return version


async def connect_details(room):
    """
    Get the connect token and the wss server endpoint.

    :param room: The room to get the details for.
    :type room: str
    :return: The token and the wss endpoint.
    :rtype: dict | None
    """
    url = f'https://tinychat.com/api/v1.0/room/token/{room}'
    response = await web.get(url)

    if response is not None:
        json_data = await response.json()

        return {
            'token': json_data['result'],
            'endpoint': json_data['endpoint']
        }

    return None


async def user_info(account):
    """
    User account information.

    :param account: The tinychat account name.
    :type account: str
    :return: A dictionary containing info about the user account.
    :rtype: dict | None
    """
    url = f'https://tinychat.com/api/v1.0/user/profile?username={account}&'
    response = await web.get(url)

    if response is not None:
        json_data = await response.json()
        if json_data['result'] == 'success':
            return {
                'biography': json_data['biography'],
                'gender': json_data['gender'],
                'location': json_data['location'],
                'role': json_data['role'],
                'age': json_data['age']
            }

    return None


class LoginError(Exception):
    """
    Raised on login errors.
    """
    pass


class Account(object):
    """
    Account related methods.
    """
    def __init__(self, account, password):
        """
        Create a instance of the account class.

        :param account: Tinychat account.
        :type account: str | None
        :param password: Tinychat password.
        :type password: str | None
        """
        self.account = account
        self.password = password
        self._token = None

    async def _set_token(self, html=None):
        """
        Set the token needed for the login POST.

        :param html: The html to parse the token from.
        :type html: str | None
        """
        pattern = 'name="csrf-token" id="csrf-token" content="'

        url = 'https://tinychat.com/start?#signin'
        if html is None:
            response = await web.get(url)
            if response is not None:
                html = await response.text()

        if html is not None:
            if pattern in html:
                self._token = html.split(pattern)[1].split('" />')[0]

    async def _login(self):
        """
        Private login method.

        :raises LoginError: On response failure or missing token.
        """
        if self._token is not None:

            url = 'https://tinychat.com/login'

            data = {
                'login_username': self.account,
                'login_password': self.password,
                'remember': '1',
                'next': 'https://tinychat.com/',
                '_token': self._token
            }

            response = await web.post(url, data=data)
            if response is not None:
                await self._set_token(await response.text())
            else:
                raise LoginError(f'login failed, response: {response}')
        else:
            raise LoginError(f'missing login token: {self._token}')

    async def login(self):
        """
        Public login method.

        :return: True if logged in, else False.
        :rtype: bool
        :raises LoginError: On missing account or password.
        """
        if self.account is None:
            raise LoginError(f'login error, account: {self.account}')
        elif self.password is None:
            raise LoginError(f'login error, password: {self.password}')
        elif self.account is None and self.password is None:
            raise LoginError(f'login error: {self.account} {self.password}')
        else:

            if self._token is None:
                await self._set_token()

            await self._login()

            return self.is_logged_in()

    async def logout(self):  # TODO: Test logout
        """
        Logout of tinychat.

        NOTE: Some cookies are still left after logging out
        these being `remember_*`, `tcsession` and `XSRF-TOKEN`

        :return: True if logged out, else False.
        :rtype: bool
        """
        url = 'https://tinychat.com/logout'
        await web.get(url=url, allow_redirects=False)

        if not self.is_logged_in():
            return True

        return False

    def is_logged_in(self):
        """
        Check if WebSession has `user` cookie
        matching that of account.

        :return: True if logged in, else False.
        :rtype: bool
        """
        if self.account is not None:
            cookie = web.has_cookie('https://tinychat.com', 'user')
            if cookie and cookie.value == self.account:
                return True

        return False
