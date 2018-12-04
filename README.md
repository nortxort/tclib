## tclib

Websocket package for tinychat chat rooms.

This is more or less a rewrite of pinylib, but for python 3. This implements some benefits(hopefully) that python 3 has to offer, one of them being asynchronous implementation using asyncio.

Since this is my first attempt at asynchronous programming, some things might not work as exspected, and some things might be changed later.

I'd like to mention, that a lot of inspiration has been taken from the [discord package](https://github.com/Rapptz/discord.py) by [Rapptz](https://github.com/Rapptz).

## Setup

tclib has been confirmed to work on Python 3.7+ under Windows 7/10 (x64) and GNU/Linux (x64)

### Requirements

See [requirements.txt](https://github.com/nortxort/tclib/blob/master/requirements.txt) for information.

**colorama is an optional requirement. I am not sure, if it should be included or not, at this stage.*

## Usage.

A simple client that will enter a room with a random nick.

    from tclib import TinychatClient
    
    
    client = TinychatClient('aroomname')
    client.run()

If you wanted a specific name in the room, you could do so by providing the `nick` keyword.
    
    client = TinychatClient('aroomname', nick='mycoolnick')
    client.run()

Similar to the `nick` keyword, you can use the `account` and `password` keywords to have the client use a tinychat account.
 
    client = TinychatClient('aroomname', account='tinychataccount', password='accountpassword')
    client.run()


## Submitting an issue.

Please read through the [TODO](https://github.com/nortxort/tclib/blob/master/TODO.md)s and/or [issues](https://github.com/nortxort/tclib/issues) before submitting a new issue. If you want to submit a new issue, then use the [ISSUE TEMPLATE](https://github.com/nortxort/tclib/blob/master/ISSUE_TEMPLATE.md).


## Author

* [nortxort](https://github.com/nortxort)

## License

The MIT License (MIT)

See [LICENSE](https://github.com/nortxort/tclib/blob/master/LICENSE) for more details.

## Acknowledgments

*Thanks to the following people, who in some way or another, has contributed to this project.*

* [Rapptz](https://github.com/Rapptz)
* [Aida](https://github.com/Autotonic)


