#!/usr/bin/python


import sys,os,getopt

_charset = 'abcdefghijklmnopqrstuvwxyz'
_numbers = '0123456789'
_uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
_special = '!@#$%^&*()'

_user1 = '$1$6rUfqgjP$iMaJ0035Pf8g1QALdyjPY1'

def generate_strings(entry, charclass, maxlen, currlen):
	if (len(entry) < maxlen):
		for i in charclass:
			generate_strings(entry+i, charclass, maxlen, currlen+1)
	else:
		print("%s\r" % entry),

## __main__

opts, remains = getopt.getopt(sys.argv[1:], 'hl:')

options = {}
for k,v in opts:
	options[k] = v

length = 5

if options.has_key('-h'):
	print '''Usage: %s [-l length] [-h]
	-l: length of password, defaults to 5
	-h: shows usage''' % (sys.argv[0],)
	sys.exit(0)

if options.has_key('-l'):
	length = int(options['-l'])

print("length set to %s" % length)

sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
generate_strings("", _charset +  _special, length, 0)
