#!/usr/bin/python
''' Quick dirty way to implement messaging system for IRC servers.
If you run your IRC client on a remote host, possibly within a screen session, 
you won't get any notification on your workstation. This script runs an agent 
in the form of a user who watches public messages and publish on a channel.
We can write a simple client which subscribes to this channel and displays 
popup/notification appropriately. A sample subscriber script is committed in the same repo,
checkout the notifier.py script

	Dependencies: pyzmq
	To install: apt-get install python-zmq or pip install pyzmq or easy_install pyzmq
'''


import zmq
import socket
import sys
import time
import logging

''' Give the IRCSERVER name and channel you would like to subscribe to
Pick an unused NICK and dummyUser name '''

IRCSERVER = 'irc.freenode.net'
NICK = 'timMoriarty786'
NAME = 'Tim Richards'
CHANNEL = '#bash'
PORT = 6667

''' We are using zmq for publish/subscribe mechanism. Specify an ephemeral port # here'''

ZMQ_PORT = 5892

''' Lets add some logging here '''
logging.basicConfig(filename='/tmp/irssi-notifier.log', level=logging.DEBUG, filemode='a', datefmt='%Y-%m-%d %H:%M:%S',
	format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
_log = logging.getLogger('notifier')
_log.info('%s\nStarting application\n' % '-' * 80)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
	sock.connect((IRCSERVER, PORT))
except Exception, e:
	print '%s: Cannot connect to %s:%d' % (e, IRCSERVER, PORT)
	_log.error('%s: Cannot connect to %s:%d' % (e, IRCSERVER, PORT))
	sys.exit(1)

_log.info('Connected to %s' % IRCSERVER)

sock.sendall('NICK %s\r\n' % NICK)
sock.sendall('USER %s +i * :%s\r\n' % (NAME.split()[0], NAME))
sock.sendall('JOIN %s\r\n' % CHANNEL)

metadata = {
	'IDENT': 0,
	'CMD': 1,
	'CHANNEL': 2,
	'MSG': 3,
}

ctx = zmq.Context()
zsock = ctx.socket(zmq.PUB)
zsock.bind("tcp://*:%s" % ZMQ_PORT)


while True:
	resp = sock.recv(1024)
	lines = resp.strip().splitlines()
	for line in lines:
		if line.startswith('PING'):
			_, ident = line.split(None, 1)
			_log.info('Ping received. responding with PONG %s' % ident)
			sock.sendall('PONG %s\r\n' % ident)
			continue
		if line.startswith(':') is False:
			_log.debug('Skipping %s...' % line[:40])
			continue
		parsed_resp = line.split(None, 3)
		ident = parsed_resp[metadata['IDENT']]

		if len(parsed_resp) <= metadata['MSG']:
			continue

		cmd = parsed_resp[metadata['CMD']]
		channel = parsed_resp[metadata['CHANNEL']]
		msg = parsed_resp[metadata['MSG']][1:]       ### skip the leading :

		_usr = ident.split('!')[0][1:]               ### skip the leading :
		if 'JOIN' in cmd:
			_log.info('JOIN Event: %s' % line)
		if 'QUIT' in cmd:
			_log.info('%s Quitting' % _usr)
		if 'PRIVMSG' in cmd:
			_log.info('[%s]: %s' % (_usr, msg))
			zsock.send('%s %s' % ('notify', '[%s] %s' % (_usr, msg)))


sock.sendall('PART %s :Bye\r\n' % CHANNEL)
sock.sendall('QUIT\r\n')
sock.shutdown(socket.SHUT_RDWR)
sock.close()
zsock.close()
sys.exit(0)	
