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
"""

import os
import sys
import subprocess
from optparse import OptionParser #note: deprecated in Python27, use argparse

def getTrunk():
  if os.path.exists("mozbuild-trunk/.hg"):
    print "the path exists!"
    updateTrunk = os.popen("cd mozbuild-trunk && hg pull -u")
    output = updateTrunk.read()
  else:
    print "Trunk not found."
    os.system("rm -rf mozbuild-trunk")
    print "Removed old mozbuild-trunk directory. Downloading from mozilla-central..."
    downloadTrunk = os.popen("hg clone http://hg.mozilla.org/mozilla-central mozbuild-trunk")
    output = downloadTrunk.read()
    #hg clone mozilla-trunk into the directory


def findCommit(good, bad):
  #os.system("cd mozbuild-trunk && hg bisect --reset")
  #Switch to bad commit
  #os.system("cd mozbuild-trunk && hg bisect --bad")
  #hg bisect --good commitNumberOfGood
  #Working set updated to something in between. Test it!!!
  #do hg bisect --good or --bad depending on whether it's good or bad
  #when we find a bad revision after a good revision, hg will tell us and stop

#Step 1: Get the trunk repo
getTrunk()

#Step 2:
print "done!"
