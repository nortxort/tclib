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

from datetime import datetime
import aioconsole

try:
    # try importing optional module.
    from colorama import init, Style, Fore

    init(autoreset=True)


    class Color:
        """
        Predefined colorama colors.
        """
        RED = Fore.RED
        GREEN = Fore.GREEN
        YELLOW = Fore.YELLOW
        CYAN = Fore.CYAN
        MAGENTA = Fore.MAGENTA
        BLUE = Fore.BLUE
        WHITE = Fore.WHITE

        B_RED = Style.BRIGHT + RED
        B_GREEN = Style.BRIGHT + GREEN
        B_YELLOW = Style.BRIGHT + YELLOW
        B_CYAN = Style.BRIGHT + CYAN
        B_MAGENTA = Style.BRIGHT + MAGENTA
        B_BLUE = Style.BRIGHT + BLUE

        RESET = Style.RESET_ALL

except ImportError:

    # importing failed, use dummies
    init = None
    Style = None
    Fore = None


    class Color:
        """
        Dummy class in case importing colorama failed.
        """
        RED = ''
        GREEN = ''
        YELLOW = ''
        CYAN = ''
        MAGENTA = ''
        BLUE = ''
        WHITE = ''

        B_RED = ''
        B_GREEN = ''
        B_YELLOW = ''
        B_CYAN = ''
        B_MAGENTA = ''
        B_BLUE = ''

        RESET = ''


class Console:
    """
    A class for reading and writing to console.
    """
    def __init__(self, loop, clock_color='',
                 use24hour=True, log=False, log_path=''):

        self._loop = loop
        self._clock_color = clock_color
        self._use24hour = use24hour
        self._chat_logging = log        # not sure
        self._log_path = log_path       # not sure

    async def input(self, prompt):
        """
        Asynchronous input.

        :param prompt: Input prompt.
        :type prompt: str
        """
        return await aioconsole.ainput(prompt, loop=self._loop)

    def write(self, text, color='', *, ts=True):
        """
        Writes text to console.

        :param text: The text to write.
        :type text: str
        :param color: Optional Color
        :type color: str
        :param ts: Show a timestamp before the text.
        :type ts: bool
        """
        time_stamp = ''
        if ts:
            time_stamp = f'[{_ts(as24hour=self._use24hour)}] '

        txt = f'{self._clock_color}{time_stamp}{Color.RESET}{color}{text}'

        print(txt)


def _ts(as24hour=False):
    """
    Timestamp in the format HH:MM:SS

    NOTE: milliseconds is included for the 24 hour format.

    :param as24hour: Use 24 hour time format.
    :type as24hour: bool
    :return: A string representing the time.
    :rtype: str
    """
    now = datetime.utcnow()

    fmt = '%I:%M:%S:%p'
    if as24hour:
        fmt = '%H:%M:%S:%f'

    ts = now.strftime(fmt)
    if as24hour:
        return ts[:-3]

    return ts
