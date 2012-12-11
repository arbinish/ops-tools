#!/usr/bin/env python

import os, sys, tarfile, subprocess
from shutil import copytree, rmtree, copy
from string import Template
from optparse import OptionParser

VERSION = '1.0'

def do_cleanup():
    try:
        if dest_dir: rmtree(dest_dir)
        if specfile: os.unlink(specfile)
    except Exception, e:
        pass

sys.exitfunc = do_cleanup

def create_rpm(tgz):
    import re
    if not os.path.isfile(tgz):
        print '%s: no such file' % (tgz,)
        sys.exit(1)

    p = subprocess.Popen(['rpmbuild', '-tb', tgz], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    p.wait()
    if p.returncode != 0:
        print ''.join(p.stderr.readlines())
        sys.exit(1)
    r = re.compile('Wrote:\s+(\S+)', re.DOTALL)
    outfiles = r.findall(''.join(p.stdout.readlines()))
    print 'Done'
    if len(outfiles) > 1:
        print "More than 1 output!"
        print outfiles
    else:
        print "RPM generated succesfully at %s" % (outfiles[0])

    
def create_tar_file(dirname):
    name = dirname + '.tar.gz'
    fd = tarfile.open(name, mode='w:gz')
    try:
        fd.add(dirname)
    except Exception, e:
        print 'Unable to add %s to tar' % (dirname, e)
        sys.exit(1)
    finally:
        fd.close()
    
def create_spec_file(name, contents):
    try:
        with open(name, 'w') as fd:
            fd.write(contents)
    except Exception, e:
        print 'unable to create spec file: %s' % e
        sys.exit(1)

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--author', '-a', dest='author')
    parser.add_option('--version', '-v', dest='version', type='string')
    parser.add_option('--release', '-r', dest='release', type='string', default='1')
    parser.add_option('--name', '-n', dest='name')
    parser.add_option('-V', dest='V', action='store_true')
    parser.add_option('--summary', '-s', dest='summary')
    parser.add_option('--group', '-g', dest='group', default='Application/System')
    parser.add_option('--prefix', '-p', dest='prefix', help='RPM install location')
    parser.add_option('--directory', '-d', dest='dir', help='Directory holding the RPM files')

    options, rest = parser.parse_args()

    if options.V:
        print 'Version: %s' % VERSION
        sys.exit(0)

    needed_args = ['author', 'version', 'name', 'prefix', 'dir', 'summary']

    for args in needed_args:
        if not getattr(options, args):
            print 'Missing', args
            parser.print_help()
            sys.exit(1)

    if not os.path.isdir(options.dir):
        print '%s must be a directory' % options.dir
        sys.exit(2)

### name is just the package name!
#    if not os.path.basename(options.dir).startswith(options.name):
#        print 'Warning: package name %s and directory name %s should match' % (options.name, options.dir)
#        sys.exit(1)

### lets create a destination dir to copy over files and directories from source
#    dest_dir = '%s-%s' % (os.path.basename(options.dir), options.version)
    dest_dir = '%s-%s' % (options.name, options.version)
    specfile = '%s-%s.spec' % (options.name, options.version)

    spec = Template('''%define name      $name
%define summary   $summary
%define version   $version
%define release   $release
%define license   GPL
%define group     $group
%define source    %{name}-%{version}.tar.gz
%define packager  $author
%define buildroot %{_tmppath}/%{name}-root
%define _prefix   $prefix
Name:      %{name}
Summary:   %{summary}
Version:   %{version}
Release:   %{release}
Group:     %{group}
License:   %{license}
Source0:   %{source}
BuildArch: noarch
Provides:  %{name}
Buildroot: %{buildroot}
%description
$summary

%prep
%setup -q
%build
%install
install -d %{buildroot}%{_prefix}/
tar cf - . | (cd %{buildroot}%{_prefix}/; tar xfp -)
rm %{buildroot}%{_prefix}/$specfile

%clean
rm -rf %{buildroot}
%files
%defattr(-,root,root)
%{_prefix}/*
''')

    options.specfile = specfile

    print 'Creating spec file ... ',
    sys.stdout.flush()
    create_spec_file(specfile, spec.safe_substitute(options.__dict__))
    print 'Done'

    try:
        copytree(options.dir, dest_dir, symlinks=True)
        copy(specfile, dest_dir)
    except Exception, e:
        print "copy failed %s: %s" % (options.dir, e)
        sys.exit(3)

    print 'Creating tar file ... ',
    sys.stdout.flush()
    create_tar_file(dest_dir) 
    print 'Done'

    print 'Buliding RPM ... ',
    sys.stdout.flush()
    create_rpm(dest_dir + '.tar.gz')
    

#### dirname should be name-version and spec file should be name-version.spec
