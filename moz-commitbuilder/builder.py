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

"""
  @title builder.py
  @desc  Gets mozilla-central repo and builds a given commit.

  Step 1. Get the trunk
  Step 2. Decide which revision to build (command line args)
  Step 3. Build it
  ??? Step 4. Launch it?


  Assumption: ~/.mozconfig is set correctly.
  Improvement: Make the repo URL a variable that can be set through flags
  Improvement: Build can handle OSX, Windows, or Linux
  Improvement: Stop using os.popen and start using subprocess
  Improvement: Use argparse instead of optionparser
  Improvement: Back up .mozconfig, pipe a new one into place, then clean up when done?

"""

from optparse import OptionParser #note: deprecated in Python27, use argparse
import os
import sys
import subprocess
import string
import platform
import re

def getTrunk():
  if os.path.exists("mozbuild-trunk/.hg"):
    print "Found a recent trunk. Updating it to head before we begin..."
    updateTrunk = os.popen("cd mozbuild-trunk && hg pull -u")
    print "Update successful."
    #output = updateTrunk.read()
  else:
    print "Trunk not found."
    os.system("rm -rf mozbuild-trunk")
    print "Removed old mozbuild-trunk directory. Downloading from mozilla-central..."
    downloadTrunk = os.popen("hg clone http://hg.mozilla.org/mozilla-central mozbuild-trunk")
    #output = downloadTrunk.read()

def findCommit(good, bad):
  #This func is gonna be recursive

  #os.system("cd mozbuild-trunk && hg bisect --reset")

  #Switch to bad commit here, then mark it as bad
  #os.system("cd mozbuild-trunk && hg bisect --bad")

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

def validate(good, bad):
  #todo: validate args
  """
    Validations:
      1) If the commit numbers aren't real commits, abort
      2) If commits are the same, quit
      3) If good is newer than bad, quit
      4) If good is right after bad, return the bad
      5) Correct behavior: call hg bisect, build the commit, and start the process!
  """
  
  return True  #stubbed


def bisect(good,bad):
  if good and bad and validate(good, bad): #valid commit numbers, do the bisection!
      getTrunk()
      findCommit(good,bad)
  else:
    print "Invalid values. Please check your changeset revision numbers."


def build(revision):
  os.system("cd mozbuild-trunk && hg up "+revision)
  print "Changed to revision "+revision+"."
  print "Building..."
  os.system("cd mozbuild-trunk && make -f client.mk build")

if __name__ == "__main__":
  parser = OptionParser()
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
    good = options.good
    bad = options.bad
    print "Begin interactive bisect:"
    bisect(good,bad)
