#!/usr/bin/python

import zmq
import time
import subprocess
import resource
import logging
import os
import sys

PORT = "5892"
HOST = '10.14.116.32'


def irc_notify():
	if (hasattr(os, "devnull")):
	   REDIRECT_TO = os.devnull
	else:
	   REDIRECT_TO = "/dev/null"

	os.open(REDIRECT_TO, os.O_RDWR)
	os.dup2(0, 1)
	os.dup2(0, 2)

	logging.basicConfig(filename='/tmp/ircNotify.log', level=logging.DEBUG, filemode='a', datefmt='%Y-%m-%d %H:%M:%S',
		format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	_log = logging.getLogger('notifier')
	_log.info('%s Starting application %s' % (20*'-', 20*'-'))
	ctx = zmq.Context()
	sock = ctx.socket(zmq.SUB)
	sock.connect("tcp://%s:%s" % (HOST, PORT))
	sock.setsockopt(zmq.SUBSCRIBE, 'notify')

	while True:
		_ret = sock.recv()
		topic, messagedata = _ret.split(None, 1)
		notifier_args = [
		  '/usr/bin/terminal-notifier',
		  '-title',
		  topic,
		  '-message',
		  '%r' % messagedata,
		  '-activate',
		  'com.apple.Terminal',
		]
		_log.info('%r' % messagedata)
		subprocess.check_call(notifier_args)
	sock.close()


def daemonize():
	try:
		pid = os.fork()
		if pid > 0:
			sys.exit(0)
	except OSError, e:
		print >>sys.stderr, "fork #1 failed: (%s)" % e.strerror
		sys.exit(1)

	maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
	for _fd in range(maxfd):
		try:
			os.close(_fd)
		except OSError:
			pass
	os.setsid()
	os.chdir("/")
	os.umask(0)

	try:
		pid = os.fork()
		if pid > 0:
			print >>sys.stderr, "Daemon PID %d" % pid
			sys.exit(0)
	except OSError, e:
		print >>sys.stderr, "fork #2 failed: (%s)" % e.strerror
		sys.exit(1)

if __name__ == '__main__':
	daemonize()
	irc_notify()
