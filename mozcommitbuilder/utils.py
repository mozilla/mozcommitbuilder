# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Corporation Code.
#
# The Initial Developer of the Original Code is
# Heather Arthur
# Portions created by the Initial Developer are Copyright (C) 2009
# the Initial Developer. All Rights Reserved.
#
# Contributor(s): Heather Arthur <fayearthur@gmail.com>
#                 Sam Liu <sam@ambushnetworks.com>
#                 Jesse Ruderman
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****
import re
import httplib2
import datetime
import platform
import os
import subprocess
import multiprocessing
from BeautifulSoup import BeautifulSoup
import zipfile

def cpuCount():
    try:
        return multiprocessing.cpu_count()
    except NotImplementedError:
        return 1

def increment_day(date):
    #TODO: MOVE TO UTILS. Increments a date string.
    s = date.split("-")
    delta = datetime.timedelta(days=1)
    nextDate = datetime.date(int(s[0]),int(s[1]),int(s[2])) + delta
    return str(nextDate)

#Resolves names like "tip" and "52707" to the long stable hg hash ids
def hgId(rev, hgPrefix):
    return captureStdout(hgPrefix + ["id", "-i", "-r", rev],ignoreExitCode=True, ignoreStderr=True)

#Captures command line output into python string
def captureStdout(cmd, ignoreStderr=False, combineStderr=False, ignoreExitCode=False, currWorkingDir=os.getcwdu()):
    #This function captures standard output into a python string.
#    if showCapturedCommands:
#        print ' '.join(cmd)
    p = subprocess.Popen(cmd,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.STDOUT if combineStderr else subprocess.PIPE,
        cwd=currWorkingDir)
    (stdout, stderr) = p.communicate()
    if not ignoreExitCode and p.returncode != 0:
        # Potential problem area: Note that having a non-zero exit code does not mean that the operation
        # did not succeed, for example when compiling a shell. A non-zero exit code can appear even
        # though a shell compiled successfully. This issue has been bypassed in the makeShell
        # function in autoBisect.
        # Pymake in builds earlier than revision 232553f741a0 did not support the '-s' option.
        if 'no such option: -s' not in stdout:
            print 'Nonzero exit code from ' + repr(cmd)
            print stdout
        if stderr is not None:
            print stderr
        # Pymake in builds earlier than revision 232553f741a0 did not support the '-s' option.
        if 'no such option: -s' not in stdout:
            raise Exception('Nonzero exit code from %s' % repr(cmd))
    if not combineStderr and not ignoreStderr and len(stderr) > 0:
        print 'Unexpected output on stderr from ' + repr(cmd)
        print stdout, stderr
        raise Exception('Unexpected output on stderr')
#    if showCapturedCommands:
#        print stdout
#        if stderr is not None:
#            print stderr
    return stdout.rstrip()

def get_platform():
    uname = platform.uname()
    name = uname[0]
    version = uname[2]

    if name == "Linux":
        (distro, version, codename) = platform.linux_distribution()
        version = distro + " " + version
    elif name == "Darwin":
        name = "Mac"
        (release, versioninfo, machine) = platform.mac_ver()
        version = "OS X " + release
    elif name == "Microsoft":
        name = "Windows"

    bits = platform.architecture()[0]
    cpu = uname[4]
    if cpu == "i386" or cpu == "i686":
        if bits == "32bit":
            cpu = "x86"
        elif bits == "64bit":
            cpu = "x86_64"
    elif cpu == 'Power Macintosh':
        cpu = 'ppc'

    bits = re.compile('(\d+)bit').search(bits).group(1)

    return {'name': name, 'version': version, 'bits': bits, 'cpu': cpu}


def strsplit(string, sep):
    strlist = string.split(sep)
    if len(strlist) == 1 and strlist[0] == '': # python's split function is ridiculous
      return []
    return strlist

def download_url(url, dest=None):
    print "Downloading "+ url+"..."
    h = httplib2.Http()
    resp, content = h.request(url, "GET")
    if dest == None:
        dest = os.path.basename(url)

    local = open(dest, 'wb')
    local.write(content)
    local.close()
    print "Downloaded!"
    return dest

def get_date(dateString):
    p = re.compile('(\d{4})\-(\d{1,2})\-(\d{1,2})')
    m = p.match(dateString)
    if not m:
        print "Incorrect date format"
        return
    return datetime.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))


def urlLinks(url):
    res = [] # do not return a generator but an array, so we can store it for later use

    h = httplib2.Http();
    resp, content = h.request(url, "GET")
    if resp.status != 200:
        return res

    soup = BeautifulSoup(content)
    for link in soup.findAll('a'):
        res.append(link)
    return res

def getTestUrl():
    platform=get_platform()
    buildregex = None
    binary = None
    if platform['name'] == "Windows":
        if platform['bits'] == '64':
            print "64 bit Windows not supported."
            sys.exit()
        buildRegex = ".*win32.tests.zip"
    elif platform['name'] == "Linux":
        if platform['bits'] == '64':
            buildRegex = ".*linux-x86_64.tests.zip"
        else:
            buildRegex = ".*linux-i686.tests.zip"
    elif platform['name'] == "Mac":
        buildRegex = ".*mac.tests.zip"


    url = "http://ftp.mozilla.org/pub/mozilla.org/firefox/nightly/latest-trunk/"
    for link in urlLinks(url):
        href = link.get("href")
        if re.match(buildRegex, href):
            return url + href

    return False

def unzip(dest, src):
    zipped = zipfile.ZipFile(src)
    print "Unzipping file..."
    try:
        zipped.extractall(dest)
    except:
        args = ["unzip", "-o", "-q", "-d", dest, src]
        proc = subprocess.Popen(args)
        proc.wait()
    print "Successfully unzipped file!"

def url_base(url):
    items = url.split("/")
    return items[-1]
