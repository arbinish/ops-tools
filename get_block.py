import re
import sys
import os
from optparse import OptionParser
from glob import glob
from time import time


def parse_entry(fname, buf):
    #find the source index
    resp = {}
    for typ in ('source-address', 'destination-address', 'service'):
        idx = buf.find(typ)
        if idx < 0:
            log_fd.write('%s: error parsing [%s]: missing %s\n' %
                         (fname, buf, typ))
            return None
        start = buf[idx:].find('{')
        if start < 0:
            log_fd.write('%s: error parsing [%s]: missing {\n' % (fname, buf))
            return None
        end = buf[idx:].find('}')
        if end < 0:
            log_fd.write('%s: error parsing [%s]: missing }\n' % (fname, buf))
            return None
        ## ridiculous comments within a block starts with /*, weed them out
        entries = filter(lambda x: not x.startswith('/'),
                         [i.strip() for i in
                          buf[idx + start + 1:idx + end].strip().split('\n')])
        if typ == 'service':
            resp[typ] = []
            for e in entries:
                e = e.replace('TCP-', '')
                e = e.replace('UDP-', '')
                if '-' in e:
                    pstart, pend = [int(i) for i in e.split('-')]
                    pend += 1
                    if pend < pstart:
                        log_fd.write('%s: unknown range %s' % (fname, e))
                        return None
                    resp[typ].extend(range(pstart, pend))
                else:
                    resp[typ].append(e)
        else:
            resp[typ] = entries
    return resp


def parse_file(fname):
    """
    file structure has blocks, which are something like this
    {
        source-address {
            ENTRY
            ENTRY
            ...
        }
        destination-address {
            ENTRY
            ENTRY
            ...
            optional comments of the form /* ... */
        }
        service {
            ENTRY
            ...
            optional comments of the form /* ... */
        }
    }
    """

    try:
        fd = open(fname)
    except Exception, e:
        log_fd.write('%s: %s\n' % (fname, e))
        return

    config = []
    while True:
        line = fd.readline()
        if not line:
            break
        if not re.match(r'[\w\s]+[{]', line, re.DOTALL):
            continue
        buf = line
        count = 1
        while count != 0:
            line = fd.readline()
            count += line.count('{')
            count -= line.count('}')
            buf += line
        _block = parse_entry(fname, buf)
        if _block:
            config.append(_block)
    return config


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option("-f",  "--file", dest="fileglob", action="append",
                      help="input .acl files to read")
    parser.add_option("-o",  "--out", dest="outfile", action="store",
                      help="write output file", default="/tmp/acl-map")
    parser.add_option("-l",  "--log", dest="logfile", action="store",
                      help="path to log file", default="/tmp/acl-map.log")
    opts, args = parser.parse_args()

    try:
        o_fd = open(opts.outfile, 'w')
    except IOError, e:
        print >> sys.stderr, "Unable to open %s in append mode: [%s]" % \
            (opts.outfile, e)
        sys.exit(1)

    try:
        log_fd = open(opts.logfile, 'w')
    except IOError, e:
        print >> sys.stderr, 'Cannot create log file: %s [%s]' % \
            (opts.logfile, e)
        sys.exit(1)

    _files = []
    for i in opts.fileglob:
        _files.extend(glob(i))

    _pstart = int(time())
    for acl_f in _files:
        print 'processing %s ... ' % acl_f,
        sys.stdout.flush()
        for cfg in parse_file(acl_f):
            if not len(cfg):
                print 'failed'
                continue
            for src in cfg['source-address']:
                for dst in cfg['destination-address']:
                    for svc in cfg['service']:
                        o_fd.write('%s %s %s\n' % (src, dst, svc))
        print 'done'
    o_fd.close()
    log_fd.close()

    print '\n\n[-] Generated acl-map in %s' % opts.outfile
    if os.stat(opts.logfile).st_size > 0:
        print '[-] Please take a look at %s for errors during acl parse\n' % \
            opts.logfile
