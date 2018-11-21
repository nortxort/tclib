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
import aiohttp

log = logging.getLogger(__name__)

# Default user agent string for all requests.
USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:62.0) Gecko/20100101 Firefox/62.0'


def default_headers():
    """
    A default header template.

    :return: A default header dictionary.
    :rtype: dict
    """
    header = {
        'User-Agent': USER_AGENT
    }
    return header


class WebSession(object):
    """
    A session `slave` class maintaining cookies across requests.
    """
    session = None

    @classmethod
    def create(cls, loop=None):
        """
        Create a new aiohttp.ClientSession object.

        :param loop: This might be good to have.
        :type loop:
        :return: A aiohttp.ClientSession object.
        :rtype: aiohttp.ClientSession
        """
        cls.session = aiohttp.ClientSession(loop=loop)
        log.debug(f'creating session: {cls.session} loop: {loop}')

        return cls.session

    @classmethod
    def close(cls):
        """
        Close the session object.

        This should be called before closing the app,
        to not have errors shown.

        :return: It seems to return NoneType. Not really sure about this,
        but apparently it needs to return.
        :rtype: None
        """
        if cls.session is not None:
            log.debug(f'closing session.')

            return cls.session.close()

    @classmethod
    def delete(cls):
        """
        Delete the session object.
        """
        cls.session = None
        log.debug('deleting WebSession.session.')

    @classmethod
    def cookies(cls):
        """
        Session cookies object.

        :return: A aiohttp.cookiejar.CookieJar class, or None.
        :rtype: CookieJar | None
        """
        if cls.session is not None:
            return cls.session.cookie_jar

        return None


async def session_close():
    """
    A template for closing the session.

    It could be made inside any file importing web, instead of here.
    """
    await WebSession.close()


def has_cookie(domain, cookie_name=None):
    """
    Checks if a cookie exists within the session cookies.

    If no cookie name is given(None), all cookies for the
    given domain will be returned(if any exists).

    :param domain: The domain for which the cookie(s) belongs.
    :type domain: str
    :param cookie_name: The name of the cookie.
    :type cookie_name: str | None
    :return: bool(False) if no cookie(s) was found, else a Morsel object.
    :rtype: bool | Morsel
    """
    if WebSession.session is not None and domain is not None:

        cookie_jar = WebSession.cookies()
        domain_cookies = cookie_jar.filter_cookies(domain)

        if cookie_name is None:
            if len(domain_cookies) == 0:
                return False

            return domain_cookies

        cookie = domain_cookies.get(cookie_name)

        if cookie is not None:
            return cookie

    return False


async def request(method, url, **kwargs):
    """
    A wrapper for any type of request.

    :param method: The request method. Supported are: DELETE, GET, HEAD?, OPTIONS?, PATCH, POST and PUT.
    :type method: str
    :param url: The url for the request.
    :type url: str
    :param kwargs: Keywords, see
    https://github.com/aio-libs/aiohttp/blob/581e97654410aa4b372b93e69434f6de79feeef4/aiohttp/client.py#L953
    :type kwargs: dict
    :return: A aiohttp.ClientResponse object or None on error.
    :rtype: aiohttp.ClientResponse | None
    """
    error = None
    response = None

    if kwargs.get('headers', None) is None:
        kwargs['headers'] = default_headers()

    loop = kwargs.get('loop', None)
    # connector = kwargs.get('connector', None)

    # if session is None, create a new session.
    if WebSession.session is None:
        session = WebSession.create(loop=loop)
    else:
        # use existing session.
        session = WebSession.session

    log.debug(f'{method} {url} {kwargs}')

    try:
        response = await session.request(method=method, url=url, **kwargs)
    except aiohttp.client_exceptions as e:
        error = e
    finally:
        if error is not None:
            # log the error.
            log.error(f'web error: {error}')

        return response


async def get(url, **kwargs):
    """
    Make a GET request.

    :param url: The url of the resource.
    :type url: str
    :return: A aiohttp.ClientResponse or None on error.
    :rtype: aiohttp.ClientResponse | None
    """
    return await request('GET', url=url, **kwargs)


async def post(url, **kwargs):
    """
    Make a POST request.

    :param url: The url of the resource.
    :type url: str
    :return: A aiohttp.ClientResponse or None on error.
    :rtype: aiohttp.ClientResponse | None
    """
    return await request('POST', url=url, **kwargs)
