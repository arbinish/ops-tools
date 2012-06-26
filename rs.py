import pycurl, sys, urllib, getpass, traceback, pylibmc, re, time, pickle, os, getopt
from StringIO import StringIO
from hashlib import sha1
from collections import defaultdict

#_user = raw_input("Enter RS username/email: ")
#_passw = getpass.getpass('Enter password: ')
_user = ''
_passw = ''
_acct = 12345
options = {}

def parse_options(cmdline, flags):
	opts, rem = getopt.getopt(cmdline, flags)
	options = {}
	for k, v in opts:
		options[k] = v
	return options

def init_session(_user, _passw, _acct):
	if os.path.exists(COOKIEFILE) and not options.has_key('-r'):
		if (int)(time.time()) - (int)(os.path.getctime(COOKIEFILE)) < 3600: return	
	
	if options.has_key('-v'): print "initializing session ..."
	postdata = urllib.urlencode({'email': _user, 'password': _passw, 'account_href': '/api/accounts/%d' % _acct})
	curl = pycurl.Curl()
	curl.setopt(pycurl.URL, 'https://my.rightscale.com/api/session')
	curl.setopt(pycurl.HTTPHEADER, ['X_API_VERSION: 1.5'])
	curl.setopt(pycurl.FOLLOWLOCATION, 1)
	curl.setopt(pycurl.POST, 1)
	curl.setopt(pycurl.POSTFIELDS, postdata)
	curl.setopt(pycurl.COOKIEJAR, COOKIEFILE)
	try:
	   curl.perform()
	except:
	   traceback.print_exc(file=sys.stderr)
	if curl.getinfo(pycurl.HTTP_CODE) != 204:
		print "Invalid credentials for %s" % _user
		sys.exit(1)
	curl.close()

def get_deployments():
	buf = StringIO()
	curl = pycurl.Curl()
	curl.setopt(pycurl.URL, 'https://my.rightscale.com/api/deployments')
	curl.setopt(pycurl.HTTPHEADER, ['X_API_VERSION: 1.5'])
	curl.setopt(pycurl.FOLLOWLOCATION, 1)
	curl.setopt(pycurl.POST, 0)
	curl.setopt(pycurl.COOKIEFILE, COOKIEFILE)
	curl.setopt(pycurl.WRITEFUNCTION, buf.write)
	try:
		curl.perform()
	except:
		traceback.print_exc(file=sys.stderr)
	if curl.getinfo(pycurl.HTTP_CODE) != 200:
		print "Unable to retreive deployment info"
		sys.exit(1)

	null = None
	entries = eval(buf.getvalue())
	_servers = {}
	for e in entries:
		print e['name']
		_servers[e['name']] = dict(map(lambda x: (x['rel'], x['href']), e['links']))
	curl.close()
	mc = pylibmc.Client(['localhost'], binary=True)
	mc.set('rs_deployments_%d' % _acct, _servers, 7200)
	mc = None
	return _servers

def get_servers(deployment, array = 0):
	''' returns list of servers or arrays from named deployment 
	'''

	buf = StringIO()

	mc = pylibmc.Client(['localhost'], binary=True)
	if (options.has_key('-v')): print "MC get rs_deployments_%d" % _acct
	_servers = mc.get('rs_deployments_%d' % _acct)

	if not _servers:
		if options.has_key('-v'): print "fetching deployment info"
		_servers = get_deployments()

	if not _servers.has_key(deployment):
		print "Unknown deployment %s" % deployment
		sys.exit(0)

	s = _servers[deployment]
	if not s['servers']:
		print "cannot find servers for deployment %s" % deployment
		sys.exit(0)


	server_url = s['servers']
	if array:
		server_url = s['server_arrays']

	regex_ret = re.match(r'\D+(\d+)', s['self'])
	if not regex_ret:
		print "oopsies: cannot find deployment id for %s" % deployment
		print "--\n%s\n--" % s
		sys.exit(1)

	deploy_id = regex_ret.group(1)


	slist = mc.get('rs_deployment_%s_%d' % (deploy_id, array))
	if slist:
		if array == 0:
			for i in slist: 
				print "%s %s" % (i.strip().ljust(45), slist[i]['private_ip_addresses'][0])
		else:
			for wname in slist.keys():
				print "%s (%d)" % (wname, len(slist[wname]))
				for i in slist[wname]:
					print i['private_ip_addresses'][0]
		return

	if options.has_key('-v'): print "fetching server info ..."
	curl = pycurl.Curl()
	curl.setopt(pycurl.URL, 'https://my.rightscale.com%s/?view=instance_detail' % server_url)
	param = urllib.urlencode({'deployment_href': int(deploy_id)})
	curl.setopt(pycurl.HTTPHEADER, ['X_API_VERSION: 1.5'])
	curl.setopt(pycurl.FOLLOWLOCATION, 1)
	curl.setopt(pycurl.HTTPGET, 1)
	curl.setopt(pycurl.COOKIEFILE, COOKIEFILE)
	curl.setopt(pycurl.WRITEFUNCTION, buf.write)
	curl.perform()
	if curl.getinfo(pycurl.HTTP_CODE) != 200:
		print buf.getvalue()
		print "get_servers failed for deployment %s" % deployment
		sys.exit(1)
	null = None
	curl.close()
	entries = eval(buf.getvalue())
	if (options.has_key('-v')):
		dfile = sha1(deployment).hexdigest()[0:16]
		pickle.dump(entries, open('/tmp/%s' % dfile, 'wb'))
		print "Dumping entries onto %s" % dfile
	d = defaultdict(list)
	for e in entries:
		if array == 0:
			if e['state'] == 'operational': 
				print e['name'].strip().ljust(45),
				d[e['name']] = e['current_instance']
				print e['current_instance']['private_ip_addresses'][0]
		else:
			if e['instances_count'] > 0:
				buf.close()
				buf = StringIO()
				server_url = [  x for x in e['links'] if x['rel'] == 'current_instances' ][0]['href']
				curl = pycurl.Curl()
				curl.setopt(pycurl.URL, 'https://my.rightscale.com%s/?view=extended' % server_url)
				curl.setopt(pycurl.HTTPHEADER, ['X_API_VERSION: 1.5'])
				curl.setopt(pycurl.FOLLOWLOCATION, 1)
				curl.setopt(pycurl.HTTPGET, 1)
				curl.setopt(pycurl.COOKIEFILE, COOKIEFILE)
				curl.setopt(pycurl.WRITEFUNCTION, buf.write)
				curl.perform()
				if curl.getinfo(pycurl.HTTP_CODE) != 200:
					print buf.getvalue()
					print "get_servers failed for deployment %s" % deployment
					sys.exit(1)
				null = None
				curl.close()
				array_entries = eval(buf.getvalue())
				d[e['name']] = array_entries
				print '\t%s (%d)' % (e['name'], len(array_entries))
				for _a in array_entries:
					print _a['private_ip_addresses'][0]

	if (options.has_key('-v')):
		dfile = '%s_%d' % (sha1(deployment).hexdigest()[0:16], array)
		pickle.dump(dict(d), open('/tmp/%s' % dfile, 'wb'))
		print "Dumped entries onto %s" % dfile

	mc.set('rs_deployment_%s_%d' % (deploy_id, array), dict(d), 7200)

def usage():
	print "[-x account_id] [-d deployment_name] [-a] [-r] [-v]"
	print "\t account_id is the RS account id, default 30287 [zc2]"
	print "\t -d RS deployment name"
	print "\t -a display server arrays only"
	print "\t -r force initialize session"
	print "\t -v debug information"
	print "\t -h this information"

## __main__

COOKIEFILE = os.getenv('HOME') + '/rs.cookie.%s.%d' % (_user.split('@')[0], _acct)
options = parse_options(sys.argv[1:], 'x:d:ahvr')

if options.has_key('-h') or not options.has_key('-d'):
	usage()
	sys.exit(0)

m1 = time.time()

if options.has_key('-x'): _acct = int(options['-x'])

init_session(_user, _passw, _acct)
m2 = time.time()

if options.has_key('-v'):
	if (m2-m1) > 1:
		print "\t->init_session: took %f seconds\n" % (m2-m1,)
	else:
		print "\t->init_session: took %f milli seconds\n" % ((m2-m1) * 1000,)

#get_deployments()
#get_servers('Deployment Name')
m1 = time.time()
get_servers(options['-d'], int(options.has_key('-a')))
m2 = time.time()

if options.has_key('-v'):
	if (m2-m1) > 1:
		print "\t->get_servers: took %f seconds\n" % (m2-m1,)
	else:
		print "\t->get_servers: took %f milli seconds\n" % ((m2-m1) * 1000,)

sys.exit(0)

