#!/usr/bin/env python
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
# Samuel C Liu
#
# Contributor(s): Sam Liu <sam@ambushnetworks.com>
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

'''
  Known Issues
  -------------
  1. Firefox doesn't close correctly -- potentially decide to run it via a system call?
  2. Running the build makes an assumption that ~/.mozconfig is set correctly.

        TODO: See if these args can be passed in some other way?
'''

from optparse import OptionParser, OptionGroup #note: deprecated in Python27, use argparse
import os, sys, subprocess, string, re, tempfile, shlex
from types import *

#Setting Variables
showCapturedCommands = False
showMakeData = 0
progVersion="Mozilla Commitbuilder 0.1"
repoURL="http://hg.mozilla.org/mozilla-central"
makeCommand=["make","-f","client.mk","build"]
alternateMake = False
shellCacheDir = os.path.join(os.path.expanduser("~"), "moz-commitbuilder-cache")
confDir = os.path.join(shellCacheDir, "mozconf")
repoPath = os.path.join(shellCacheDir,"mozbuild-trunk")

#Create cache folder if nonexistent
if not os.path.exists(shellCacheDir):
  os.mkdir(shellCacheDir)

if not os.path.exists(confDir):
  os.mkdir(confDir)

  #f = open(os.path.join(shellCacheDir,"mozconf")+"mozconfig-temp", "w")

  #subprocess.call(["echo",'"mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-ff-dbg"'], cwd=os.path.join(shellCacheDir,"mozconf"), stdout=f)

#Prefix for hg commands
hgPrefix = ['hg', '-R', repoPath]

#Gets or updates our cached repo for building
def getTrunk():
  if os.path.exists(os.path.join(repoPath,".hg")):
    print "Found a recent trunk. Updating it to head before we begin..."
    updateTrunk = subprocess.call(hgPrefix + ["pull","-u"])
    print "Update successful."
  else:
    print "Trunk not found."
    makeClean = subprocess.call(["rm","-rf", repoPath])
    print "Removed old mozbuild-trunk directory. Downloading a fresh repo from mozilla-central..."
    #downloadTrunk = os.popen("hg clone http://hg.mozilla.org/mozilla-central mozbuild-trunk")
    downloadTrunk = subprocess.call(["hg", "clone", repoURL, "mozbuild-trunk"], cwd=shellCacheDir)

#This function was copied directly from Jesse Ruderman's autoBisect
#Resolves names like "tip" and "52707" to the long stable hg hash ids
def hgId(rev):
    return captureStdout(hgPrefix + ["id", "-i", "-r", rev])

#Build the current repo
def build():
  print "Building..."
  makeData = captureStdout(makeCommand, ignoreStderr=True,
                          currWorkingDir=repoPath)
  if showMakeData == 1:
    print makeData

  print "Build complete!"

def bisect(good,bad):
  if good and bad and validate(good, bad): #valid commit numbers, do the bisection!
      subprocess.call(hgPrefix+["bisect","--reset"])
      subprocess.call(hgPrefix+["up",bad])
      subprocess.call(hgPrefix+["bisect","--bad"])
      subprocess.call(hgPrefix+["bisect","--good",good])

      #Prebuild stuff here!!

      #Make mozconfig
      os.chdir(confDir)
      if os.path.exists("config-default"):
        os.unlink("config-default")

      f=open('config-default', 'w')
      #Ensure we know where to find our built stuff by using a custom mozconfig
      f.write('mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-ff-dbg\n')

      #Cores are nice. Make this an optional flag later.
      f.write('mk_add_options MOZ_MAKE_FLAGS="-s -j8"')
      f.close()

      #export MOZCONFIG=/path/to/mozilla/mozconfig-firefox
      os.environ['MOZCONFIG']=confDir+"/config-default"

      bisectRecurse()
  else:
    print "Invalid values. Please check your changeset revision numbers."

def bisectRecurse():
  build() #build current revision

  if sys.platform == "darwin":
    proc = subprocess.Popen("./firefox-bin", cwd=os.path.join(shellCacheDir,"mozbuild-trunk","obj-ff-dbg","dist","Nightly.app","Contents","MacOS"))
  else:
    print "Your platform is not currently supported."
    quit()

  verdict = ""
  while verdict != 'good' and verdict != 'bad' and verdict != 'b' and verdict != 'g':
    verdict = raw_input("Was this commit good or bad? (type 'good' or 'bad' and press Enter): ")

  #do hg bisect --good or --bad depending on whether it's good or bad
  retval = 0;
  if verdict == 'good':
    retval = captureStdout(hgPrefix+["bisect","--good"])
  else:
    retval = captureStdout(hgPrefix+["bisect","--bad"])

  print str(retval)

  #This is totally a hack to avoid parsing
  #if retval starts with "Testing" then it needs to keep going
  #if retval starts with "The" then we can quit
  if retval[1] == 'h':
    quit()
  elif retval[1] == 'e':
    print "\n"
  else:
    print "Something went wrong! :("
    quit()

  bisectRecurse()

#Method by Jesse Ruderman -- captures command line output into python string
def captureStdout(cmd, ignoreStderr=False, combineStderr=False, ignoreExitCode=False, currWorkingDir=os.getcwdu()):
    #This function captures standard output into a python string.
    if showCapturedCommands:
        print ' '.join(cmd)
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
            raise Exception('Nonzero exit code')
    if not combineStderr and not ignoreStderr and len(stderr) > 0:
        print 'Unexpected output on stderr from ' + repr(cmd)
        print stdout, stderr
        raise Exception('Unexpected output on stderr')
    if showCapturedCommands:
        print stdout
        if stderr is not None:
            print stderr
    return stdout.rstrip()

#Check that given changeset numbers aren't wonky
def validate(good, bad):
  if (good == bad):
    return False
  return True
  '''                                              "
    TODO Validations:
      1) If the commit numbers aren't real commits, abort
      2) If good is newer than bad, quit
      3) If good is right after bad, return the bad
  '''


#Main method
#TODO make this module work as an imported package...currently kind of useless

def cli():
  usage = "usage: %prog [options] [optional: repository URL]"
  parser = OptionParser(usage=usage,version=progVersion)
  parser.add_option("-g", "--good", dest="good",
                    help="Last known good revision",
                    metavar="changeset#")
  parser.add_option("-b", "--bad", dest="bad",
                    help="Broken commit revision",
                    metavar="changeset#")

  group = OptionGroup(parser, "Unstable Options",
                    "Caution: use these options at your own risk.  "
                    "They aren't recommended.")

  group.add_option("-r", "--repo", dest="repoURL",
                    help="alternative mercurial repo to bisect",
                    metavar="valid repository url")
  group.add_option("-m", "--altmake", dest="alternateMake",
                    help="alternative make command for building",
                    metavar="make command, in quotes")
  parser.add_option_group(group)
  (options, args) = parser.parse_args()

  # Run it
  if not options.good or not options.bad:
    print "Use -h flag for available options"
  else:
    getTrunk()
    good = hgId(options.good)
    bad = hgId(options.bad)
    newrepoURL = options.repoURL

    if newrepoURL:
      print "Flag: using "+newrepoURL+" instead of Mozilla Central as our repository."
      repoURL = newrepoURL

    if alternateMake:
      print "Flag: using custom make command to build the repo."
      makeCommand = shlex.split(alternateMake)

    print "good is "+good+" and bad is "+bad
    print "Begin interactive commit bisect!"
    bisect(good,bad)

if __name__ == "__main__":
  cli()
