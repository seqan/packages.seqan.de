#!/usr/bin/env python2
"""Build the SeqAn Releases Website."""

import operator
import optparse
import os
import os.path
import re
import sys
import time
import xml.sax.saxutils
from distutils.version import StrictVersion
from collections import OrderedDict

import pyratemp

# Patterns matching seqan srcs, apps and library.
SRC_PATTERN = (r'seqan-src-([0-9])\.([0-9])(?:\.([0-9]))?\.'
                   '(tar\.gz|tar\.bz2|tar\.xz|zip)')
SEQAN3_LIBRARY_PATTERN = (r'seqan3-library-([0-9]+)(?:\.([0-9]+)\.([0-9]+))?\.'
                          '(tar\.gz|tar\.bz2|tar\.xz|zip)')
LIBRARY_PATTERN = (r'seqan-library-([0-9])\.([0-9])(?:\.([0-9]))?\.'
                   '(tar\.gz|tar\.bz2|tar\.xz|zip)')
APPS_PATTERN = (r'seqan-apps-([0-9])\.([0-9])(?:\.([0-9]))?-'
                '(Linux|Mac|FreeBSD|Windows)-(x86_64|x86_64_sse4|x86_64_avx2|i686)?'
                '\.(tar\.gz|tar\.bz2|tar\.xz|zip|exe|msi)')
# The regular expression to use for matching patterns.
PACKAGE_PATTERN = (r'(.*)-([0-9]+)\.([0-9]+)(?:\.([0-9]+))?-'
                   '(Linux|Mac|FreeBSD|Windows)-(x86_64|x86_64_sse4|x86_64_avx2|i686)?'
                   '\.(tar\.gz|tar\.bz2|tar\.xz|zip|exe|msi|deb|rpm|dmg)')
# The operating systems that we expect.
OPERATING_SYSTEMS = ['Linux', 'Mac', 'FreeBSD', 'Windows', 'src']
# The architectures that we expect.
ARCHITECTURES = ['x86_64', 'x86_64_sse4', 'x86_64_avx2', 'i686', 'src']
# The file formats.
FORMATS = ['tar.gz', 'tar.bz2', 'tar.xz', 'zip', 'exe', 'msi', 'deb', 'rpm', 'dmg']
# Path to template.
TPL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'release_page.html')
PACKAGE_TPL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'one_package.html')
# Base URL for links.
BASE_URL='http://packages.seqan.de'


class Arch(object):
    def __init__(self, name):
        self.name = name
        self.files = {}


class Packages(object):
    def __init__(self, os_):
        self.os = os_
        self.archs = {}
        for arch in ARCHITECTURES:
            self.archs[arch] = Arch(arch)


class Version(object):
    def __init__(self, version):
        self.version = version
        self.packages = {}
        self.date = ""
        self.is_nightly_stable = False
        for os_ in OPERATING_SYSTEMS:
            self.packages[os_] = Packages(os_)


class Software(object):
    def __init__(self, name):
        self.name = name
        self.versions = OrderedDict()

def sorted_nicely( l ):
    """ Sorts the given iterable in the way that is expected.

    Required arguments:
    l -- The iterable to be sorted.
    """

    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key = alphanum_key)

class PackageDatabase(object):
    def __init__(self, path):
        self.path = path
        self.seqan_apps = Software('SeqAn Apps')
        self.seqan_library = Software('SeqAn Library')
        self.seqan3_library = Software('SeqAn3 Library')
        self.seqan_src = Software('SeqAn Sources')
        self.softwares = {}

    def load(self):
        # Two craw directory structure by two levels.
        xs = []
        for x in os.listdir(self.path):
            if os.path.isdir(os.path.join(self.path, x)):
                for y in os.listdir(os.path.join(self.path, x)):
                    xs.append(y)

        for x in sorted_nicely(xs):
            if re.match(SRC_PATTERN, x):
                major, minor, patch, suffix = re.match(SRC_PATTERN, x).groups()
                if not patch:
                    patch = '0'
                major_minor_patch = '%s.%s.%s' % (major, minor, patch)
                software = self.seqan_src
                if not major_minor_patch in software.versions:
                    software.versions[major_minor_patch] = Version(major_minor_patch)
                version = software.versions[major_minor_patch]
                version.packages['src'].archs['src'].files[suffix] = x
            elif re.match(LIBRARY_PATTERN, x):
                major, minor, patch, suffix = re.match(LIBRARY_PATTERN, x).groups()
                if not patch:
                    patch = '0'
                major_minor_patch = '%s.%s.%s' % (major, minor, patch)
                software = self.seqan_library
                if not major_minor_patch in software.versions:
                    software.versions[major_minor_patch] = Version(major_minor_patch)
                version = software.versions[major_minor_patch]
                version.packages['src'].archs['src'].files[suffix] = x
            elif re.match(SEQAN3_LIBRARY_PATTERN, x):
                major, minor, patch, suffix = re.match(SEQAN3_LIBRARY_PATTERN, x).groups()
                is_nightly = False
                version_id = ''
                if not patch and not minor:
                    is_nightly = True
                    version_id = '%s' % (major)
                else:
                    version_id = '%s.%s.%s' % (major, minor, patch)
                software = self.seqan3_library
                if not version_id in software.versions:
                    software.versions[version_id] = Version(version_id)
                version = software.versions[version_id]
                version.is_nightly_stable = is_nightly
                version.packages['src'].archs['src'].files[suffix] = x
            elif re.match(APPS_PATTERN, x):
                major, minor, patch, os_, arch, suffix = re.match(APPS_PATTERN, x).groups()
                if not patch:
                    patch = '0'
                major_minor_patch = '%s.%s.%s' % (major, minor, patch)
                software = self.seqan_apps
                if not major_minor_patch in software.versions:
                    software.versions[major_minor_patch] = Version(major_minor_patch)
                version = software.versions[major_minor_patch]
                version.packages[os_].archs[arch].files[suffix] = x
            elif re.match(PACKAGE_PATTERN, x):  # individual apps
                filename = x
                name, major, minor, patch, os_, arch, suffix = re.match(PACKAGE_PATTERN, x).groups()
                if not patch:
                    patch = '0'
                major_minor_patch = '%s.%s.%s' % (major, minor, patch)

                if not name in self.softwares:
                    self.softwares[name] = Software(name)
                software = self.softwares[name]

                if not major_minor_patch in software.versions:
                    software.versions[major_minor_patch] = Version(major_minor_patch)
                version = software.versions[major_minor_patch]

                version.packages[os_].archs[arch].files[suffix] = filename
            else:
                pass

        # do not use .zip for linux/bsd
        '''
        for name in self.softwares :
            for major_minor_patch in self.softwares[name].versions :
                version = self.softwares[name].versions[major_minor_patch]
                for os_ in version.packages :
                    if (os_ != "Windows" and os_ != "Mac") :
                        for arch in version.packages[os_].archs :
                            if ("zip" in version.packages[os_].archs[arch].files) :
                                del version.packages[os_].archs[arch].files["zip"]
        '''

        # do not use tar.bz2 if it contains tar.xz
        for name in self.softwares :
            for major_minor_patch in self.softwares[name].versions :
                version = self.softwares[name].versions[major_minor_patch]
                for os_ in version.packages :
                    for arch in version.packages[os_].archs :
                        if (("tar.bz2" in version.packages[os_].archs[arch].files) and \
                            ("tar.xz" in version.packages[os_].archs[arch].files)):
                            del version.packages[os_].archs[arch].files["tar.bz2"]

        # get modified time
        os_list = ["Linux", "Mac", "Windows"]
        for name in self.softwares :
            for major_minor_patch in self.softwares[name].versions :
                version = self.softwares[name].versions[major_minor_patch]
                found = False;
                for os_ in os_list :
                    if (os_ in version.packages) == False :
                        continue
                    for arch in version.packages[os_].archs :
                        for suffix in version.packages[os_].archs[arch].files :
                            filename = os.path.join(self.path, name, version.packages[os_].archs[arch].files[suffix])
                            version.date = time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(filename)))
                            found = True
                            break
                        if found : break
                    if found : break

class RssItem(object):
    """One RSS item."""
    def __init__(self, title, description, link):
        self.title = title
        self.description = description
        self.link = link

    def generate(self):
        tpl = ('<item>\n'
               '  <title>%s</title>\n'
               '  <summary>%s</summary>\n'
               '  <link>%s</link>\n'
               '</item>\n')
        return tpl % (self.title, self.description, self.link)


class RssFeed(object):
    """Feed with one channel."""

    def __init__(self, title, description, link):
        self.title = title
        self.description = description
        self.link = link
        self.items = []

    def generate(self):
        tpl = ('<?xml version="1.0" encoding="UTF-8" ?>\n'
               '<rss version="2.0">\n'
               '  <title>%s</title>\n'
               '  <description>%s</description>\n'
               '\n'
               '%s'
               '</rss>\n')
        items_s = '\n'.join([i.generate() for i in self.items])
        return tpl % (self.title, self.description, items_s)


class RssWriter(object):
    """Writing of RSS files for a PackageDB."""

    def __init__(self, out_dir, package_db, base_url):
        self.out_dir = out_dir
        self.package_db = package_db
        self.base_url = base_url

    def generate(self):
        """Create output RSS files."""
        for sname, software in self.package_db.softwares.items():
            feed = RssFeed(sname, '', '')
            vnames = [key for key in software.versions.keys()]
            vnames.sort(key=StrictVersion, reverse=True)
            for vname in vnames:
                description = 'Version %s of %s.' % (vname, sname)
                link = '%s/%s#%s' % (self.base_url, sname, vname)
                item = RssItem('%s %s' % (sname, vname), description, link)
                feed.items.append(item)
            path = os.path.join(self.out_dir, sname, 'package.rss')
            print >>sys.stderr, 'Writing %s' % path
            with open(path, 'wb') as f:
                f.write(feed.generate())

def work(options):
    print >>sys.stderr, 'Generating Release Site.'
    print >>sys.stderr, 'Package Dir: %s' % (options.package_db,)
    print >>sys.stderr, 'Out Dir: %s' % (options.out_dir,)

    try :
        os.makedirs(options.out_dir)
    except :
        pass

    db = PackageDatabase(options.package_db)
    db.load()
    # Load and render overview template.
    tpl = pyratemp.Template(filename=TPL_PATH)
    with open(options.out_dir + "/index.html", 'wb') as f:
        f.write(tpl(FORMATS=FORMATS,
                    seqan_apps=db.seqan_apps,
                    seqan_library=db.seqan_library,
                    seqan3_library=db.seqan3_library,
                    seqan_src=db.seqan_src,
                    softwares=db.softwares,
                    utc_time=time.strftime('%a, %d %b %Y %H:%M:%S UTC', time.gmtime()),
                    sorted=sorted))
    # Load and render package template.
    tpl = pyratemp.Template(filename=PACKAGE_TPL_PATH)
    for sname, software in db.softwares.items():
        out_path = os.path.join(options.out_dir, sname)
        try :
            os.makedirs(out_path)
        except :
            pass

        out_path += "/index.html"
        print >>sys.stderr, 'Writing %s.' % out_path
        with open(out_path, 'wb') as f:
            f.write(tpl(FORMATS=FORMATS,
                        utc_time=time.strftime('%a, %d %b %Y %H:%M:%S UTC', time.gmtime()),
                        software=software,
                        sorted=sorted))
    # Write out RSS feeds for the packages.
    rss_writer = RssWriter(options.out_dir, db, options.base_url)
    rss_writer.generate()

    # copy design files
    os.system("cp -r %s/design %s/design" % (os.path.dirname(os.path.abspath(__file__)), options.out_dir))

def main():
    parser = optparse.OptionParser()
    parser.add_option('-d', '--package-db', dest='package_db',
                      help='Path to directory with package files.')
    parser.add_option('-o', '--out-dir', dest='out_dir',
                      help='Path to the HTML file to generate.')
    parser.add_option('-b', '--base-url', dest='base_url',
                      help='Base URL.', default=BASE_URL)

    options, args = parser.parse_args()
    if args:
        parser.error('No arguments expected!')
        return 1
    if not options.package_db:
        parser.error('Option --package-db/-d is required!')
        return 1
    if not options.out_dir:
        parser.error('Option --out-dir/-o is required!')
        return 1

    return work(options)

if __name__ == '__main__':
    sys.exit(main())
