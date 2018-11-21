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

import random
import json


def chunk_string(input_str, length):
    """
    Splits a string in to smaller chunks.

    NOTE: http://stackoverflow.com/questions/18854620/

    :param input_str: str the input string to chunk.
    :param length: int the length of each chunk.
    :return: list of input str chunks.
    """
    return list((input_str[0 + i:length + i]
                 for i in range(0, len(input_str), length)))


def create_random_string(min_length, max_length, upper=False, other=False):
    """
    Creates a random string of letters and numbers.

    For a fixed length, set min_length to the same as max_length.

    :param min_length: int the minimum length of the string
    :param max_length: int the maximum length of the string
    :param upper: bool do we need upper letters
    :param other: bool include other characters.
    :return: random str of letters and numbers
    """
    if min_length > max_length:
        raise Exception(f'min_length({min_length}) '
                        f'cannot be > max_length({max_length}).')

    if min_length == max_length:
        length = min_length
    else:
        length = random.randint(min_length, max_length)

    junk = 'abcdefghijklmnopqrstuvwxyz0123456789'
    if upper:
        junk += 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    if other:
        junk += '!"#&/()=?`;:,_-~|%&@£$€{[]}'

    return ''.join((random.choice(junk) for _ in range(length)))


def convert_to_seconds(duration):
    """
    Converts a ISO 8601 unicode duration str to seconds.

    :param duration: The ISO 8601 unicode duration str
    :return:  int seconds
    """
    duration_string = duration.replace('PT', '').upper()
    seconds = 0
    number_string = ''

    for char in duration_string:
        if char.isnumeric():
            number_string += char
        try:
            if char == 'H':
                seconds += (int(number_string) * 60) * 60
                number_string = ''
            if char == 'M':
                seconds += int(number_string) * 60
                number_string = ''
            if char == 'S':
                seconds += int(number_string)
        except ValueError:
            return 0
    return seconds
