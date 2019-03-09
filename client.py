import config
from tclib import TinychatClient
CONFIG = config

if CONFIG.ROOM:
    room_name = CONFIG.ROOM
else:
    room_name = input('Enter room name: ').strip()
            
if CONFIG.ACCOUNT and CONFIG.PASSWORD:
    client = TinychatClient(room_name, account=CONFIG.ACCOUNT, password=CONFIG.PASSWORD)
else:
    client = TinychatClient(room_name, nick=CONFIG.NICK)
            
if CONFIG.ACCOUNT:
    client.account = CONFIG.ACCOUNT
else:
    client.account = input('Account: ').strip()
            
if CONFIG.PASSWORD:
    client.password = CONFIG.PASSWORD
else:
    client.password = input('Password: ')

if CONFIG.NICK:
    client.nick = CONFIG.NICK
else:
    client.nick = input('Enter nick name: (optional) ').strip()

client.run()
