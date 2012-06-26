from binascii import crc32
import getopt, sys

def show_usage():
	print '''\nUsage: %s -n NUMBER -v key1 key2 ... keyn
	    -n: Number of nodes in the MC pool
	    -v: Verbose, display key name along with the shard number
	    key1, key2, ...: MC key name\n''' % sys.argv[0]

try:
	opt, remain = getopt.getopt(sys.argv[1:], 'vn:')
except getopt.GetoptError, e:
	print e.msg
	show_usage()
	sys.exit(1)

options = dict(opt)

try:
	_count = int(options.get('-n'))
except ValueError, e:
	print e.message
	show_usage()
	sys.exit(1)

for key in remain:
	hash = (crc32(key) >> 16) & 0x7fff
	if options.has_key('-v'): print '%s ' % key,
	print hash % _count





