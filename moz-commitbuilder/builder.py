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
  @title builder.py
  @desc  Gets mozilla-central repo: interactively bisects commits, builds and runs them

  Step 1. Get the trunk
  Step 2. Decide which revision to build via hg bisect
  Step 3. Build it
  Step 4. Launch it
  Step 5. Upon close, prompt to see if it was good or bad
  Step 6. Recurse through step 2-5 until it returns "The first bad revision is..." -- print that revision and quit.

  Assumption: ~/.mozconfig is set correctly. TODO: See if these args can be passed in some other way?
  Improvement: Make the repo URL a variable that can be set through flags
  Improvement: Build can handle OSX, Windows, or Linux
  Improvement: Stop using os.popen and start using subprocess
  Improvement: Use argparse instead of optionparser
  Improvement: Back up .mozconfig, pipe a new one into place, then clean up when done?

'''

from optparse import OptionParser #note: deprecated in Python27, use argparse
import os, sys, subprocess, string, re, tempfile
from types import *

showCapturedCommands = False
progVersion="Mozilla Commitbuilder 0.1"

#Setup a cache to store our repo
shellCacheDir = os.path.join(os.path.expanduser("~"), "moz-commitbuilder-cache")
if not os.path.exists(shellCacheDir):
    os.mkdir(shellCacheDir)

#Prefix for hg commands
hgPrefix = ['hg', '-R', os.path.join(shellCacheDir,"mozbuild-trunk")]

#Gets or updates our cached repo for building
def getTrunk():
  if os.path.exists(os.path.join(shellCacheDir,"mozbuild-trunk",".hg")):
    print "Found a recent trunk. Updating it to head before we begin..."
    updateTrunk = subprocess.call(hgPrefix + ["pull","-u"])
    print "Update successful."
  else:
    print "Trunk not found."
    makeClean = subprocess.call(["rm","-rf", os.path.join(shellCacheDir,"mozbuild-trunk")])
    print "Removed old mozbuild-trunk directory. Downloading a fresh repo from mozilla-central..."
    #downloadTrunk = os.popen("hg clone http://hg.mozilla.org/mozilla-central mozbuild-trunk")
    downloadTrunk = subprocess.call(["hg","clone","http://hg.mozilla.org/mozilla-central", os.path.join(shellCacheDir,"mozbuild-trunk")])

#This function was copied directly from Jesse Ruderman's autoBisect
#Resolves names like "tip" and "52707" to the long stable hg hash ids
def hgId(rev):
    return captureStdout(hgPrefix + ["id", "-i", "-r", rev])

#Build the current repo
def build(revision):
  os.system("cd mozbuild-trunk && hg up "+revision)
  print "Changed to revision "+revision+"."
  print "Building..."
  #TODO: Use a specific mozconfig
  #Possibly add a flag that lets us toggle what config we're using?
  #export MOZCONFIG=/path/to/mozilla/mozconfig-firefox

  #os.system("cd mozbuild-trunk && make -f client.mk build")
  subprocess.call(["rm","-rf", os.path.join(shellCacheDir,"mozbuild-trunk")])

def bisect(good,bad):
  if good and bad and validate(good, bad): #valid commit numbers, do the bisection!
      getTrunk()
      findCommit(good,bad)
  else:
    print "Invalid values. Please check your changeset revision numbers."

#NOTE TO SELF: This needs to recurse. Also, parsing. Stupid.
def findCommit(good, bad):
  #os.system("cd mozbuild-trunk && hg bisect --reset")
  subprocess.call(hgPrefix+["bisect","--reset"])

  #Switch to bad commit here, then mark it as bad
  #hg bisect --bad"

  #Bisect with the commit number of the good below:
  #hg bisect --good commitNumberOfGood

  #Working set updated to something in between. Test it!!!
  build(good) #STUB just build the good one to test that building actually works -- the real build function doesn't need a param because bisect automatically updates to the middle commit
  print "Build complete!"

  #Run the build and open a prompt ("Is this revision good? (Y/N)")
  args = "cd mozbuild-trunk/obj-ff-dbg/dist/bin && ./firefox"
  proc = subprocess.Popen(args, shell=True)
  proc.wait()
  verdict = ""
  while verdict != 'good' and verdict != 'bad' and verdict != 'b' and verdict != 'g':
    verdict = raw_input("Was this commit good or bad? (type 'good' or 'bad' and press Enter): ")
  #do hg bisect --good or --bad depending on whether it's good or bad

  #when we find a bad revision after a good revision, hg will tell us and stop

#Method by Jesse Ruderman -- captures command line output into python string
def captureStdout(cmd, ignoreStderr=False, combineStderr=False, ignoreExitCode=False, currWorkingDir=os.getcwdu()):
    '''
    This function captures standard output into a python string.
    '''
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
  '''
    TODO Validations:
      1) If the commit numbers aren't real commits, abort
      2) If good is newer than bad, quit
      3) If good is right after bad, return the bad
  '''


#Main method
if __name__ == "__main__":
  usage = "usage: %prog [options] repo"
  parser = OptionParser(usage=usage,version=progVersion)
  parser.add_option("-g", "--good", dest="good",
                    help="Last known good revision",
                    metavar="changeset#")
  parser.add_option("-b", "--bad", dest="bad",
                    help="Broken commit revision",
                    metavar="changeset#")
  (options, args) = parser.parse_args()

  # Run it
  if not options.good or not options.bad:
    print "Use -h flag for available options"
  else:
    good = hgId(options.good)
    bad = hgId(options.bad)
    print "good is "+good+" and bad is "+bad
    print "Begin interactive commit bisect!"
    bisect(good,bad)
