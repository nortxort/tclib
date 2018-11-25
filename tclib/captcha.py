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
import asyncio
from . import web


log = logging.getLogger(__name__)


class InvalidApiKey(Exception):
    """
    Raised on invalid API key.
    """
    pass


class NoFundsError(Exception):
    """
    Raised when no funds available.
    """
    pass


class AntiCaptchaError(Exception):
    """
    Anti captcha APi error.
    """
    def __init__(self, error):
        self._error_id = error['errorId']
        self._error_code = error['errorCode']
        self._description = error['errorDescription']

    @property
    def id(self):
        """
        The API error id.

        :return: The anti-captcha API error id.
        :rtype: int
        """
        return self._error_id

    @property
    def code(self):
        """
        The API error code.

        :return: The anti-captcha API error code.
        :rtype: str
        """
        return self._error_code

    @property
    def description(self):
        """
        The API error description.

        :return: The anti-captcha API error description.
        :rtype: str
        """
        return self._description


class AntiCaptcha:
    """
    Anti captcha class for https://api.anti-captcha.com
    """
    def __init__(self, page_url, api_key, timeout=10):
        """
        Initialize the anti captcha class.

        :param page_url: The url of the room page.
        :type page_url: str
        :param api_key: A anti-captcha API key.
        :type api_key: str
        :param timeout: Timeout between fetching task result.
        :type timeout: int
        """
        self._page_url = page_url
        self._api_key = api_key
        self._timeout = timeout
        self._site_key = ''
        self._task_id = 0

        if len(self._api_key) != 32:
            raise InvalidApiKey(f'the api key is invalid, {len(self._api_key)}')

    async def balance(self):
        """
        Get the balance for an API key.

        :return: The balance of an API key
        :rtype: int | float
        """
        post_data = {
            'clientKey': self._api_key
        }
        url = 'https://api.anti-captcha.com/getBalance'
        pr = await web.post(url=url, json=post_data)

        if pr is not None:
            data = await pr.json()

            if data['errorId'] > 0:
                raise AntiCaptchaError(data)
            else:
                return data['balance']

    async def solver(self, site_key):
        """
        Initiate the captcha solving service.

        :param site_key: The site key.
        :type site_key: str
        :return: A gRecaptchaResponse token
        :rtype: str
        """
        self._site_key = site_key
        balance = await self.balance()
        log.debug(f'anti-captcha balance: {balance}')
        # balance is int if no funds
        if isinstance(balance, int):
            raise NoFundsError(f'api key({self._api_key}) '
                               f'does not have any funds({balance})')
        else:
            return await self._create_task()

    async def _create_task(self):
        """
        Create a captcha solving task.
        """
        log.info('creating anti-captcha task.')
        post_data = {
            'clientKey': self._api_key,
            'task':
                {
                    'type': 'NoCaptchaTaskProxyless',
                    'websiteURL': self._page_url,
                    'websiteKey': self._site_key
                }
        }
        url = 'https://api.anti-captcha.com/createTask'
        pr = await web.post(url=url, json=post_data)

        if pr is not None:
            data = await pr.json()

            if data['errorId'] > 0:
                raise AntiCaptchaError(data)
            else:
                self._task_id = data['taskId']
                await asyncio.sleep(self._timeout)
                return await self._task_waiter()

    async def _task_result(self):
        """
        Get the task result.
        """
        post_data = {
            'clientKey': self._api_key,
            'taskId': self._task_id
        }
        url = 'https://api.anti-captcha.com/getTaskResult'
        pr = await web.post(url=url, json=post_data)

        if pr is not None:
            data = await pr.json()

            if data['errorId'] > 0:
                raise AntiCaptchaError(data)
            else:
                log.debug(f'task result data: {data}')
                return data

    async def _task_waiter(self):
        """
        Wait for the task result to be done.

        :return: A gRecaptchaResponse token.
        :rtype: str
        """
        log.info('starting anti-captcha task waiter.')

        while True:
            solution = await self._task_result()
            if solution['status'] == 'ready':
                return solution['solution']['gRecaptchaResponse']

            log.debug(f'waiting {self._timeout}')
            await asyncio.sleep(self._timeout)
