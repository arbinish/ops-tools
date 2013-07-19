#!/usr/bin/python

''' Client/Subscriber part of IRC remote session notifier
	Dependencies: pyzmq
	To install: apt-get install python-zmq or pip install pyzmq or easy_install pyzmq
'''

import zmq
import time
import subprocess

''' specifiy the ZMQ/Publisher port '''
PORT = "5892"
''' Specify the remote host where your irc session is running
	technically it can be any remote node which can connect to irc and 
	which has necessary acl to communicate with subscriber '''
HOST = '10.14.116.32'

ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.connect("tcp://%s:%s" % (HOST, PORT))
''' we know that the publisher publishes messages to "notify" channel '''
sock.setsockopt(zmq.SUBSCRIBE, 'notify')

while True:
	_ret = sock.recv()
	topic, messagedata = _ret.split(None, 1)
	''' I am using mac os x. Linux users may replace terminal-notifier with notify-send with appropriate args '''
	notifier_args = [
	  '/usr/bin/terminal-notifier',
	  '-title',
	  topic,
	  '-message',
	  '%r' % messagedata,
	  '-activate',
	  'com.apple.Terminal',
	]
#	print 'Topic: %s messagedata: %s' % (topic, messagedata)
	subprocess.check_call(notifier_args)
	

sock.close()
