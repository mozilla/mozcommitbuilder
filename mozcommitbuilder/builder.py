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
#
#  Sam Liu <sam@ambushnetworks.com>
#
# Portions created by the Initial Developer are Copyright (C) 2009
# the Initial Developer. All Rights Reserved.
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


'''
Known Issues:
    1) Multi-core compilation on Windows not supported
'''

from optparse import OptionParser, OptionGroup #note: deprecated in Python27, use argparse
from mozrunner import Runner, FirefoxRunner
from mozrunner import FirefoxProfile
from types import *
from utils import hgId, captureStdout
import os, sys, subprocess, string, re, tempfile, shlex, glob, shutil,datetime
import simplejson, urllib
import ximport

#Global Variables
showMakeData = 0
progVersion="0.4.1"

class Builder():
    def __init__(self, makeCommand=["make","-f","client.mk","build"] , shellCacheDir=os.path.join(os.path.expanduser("~"), "moz-commitbuilder-cache"), cores=1, repoURL="http://hg.mozilla.org/mozilla-central",clean=False, mozconf=None):
        #Set variables that we need
        self.makeCommand = makeCommand
        self.shellCacheDir = shellCacheDir
        self.cores = cores
        self.repoURL = repoURL
        self.confDir = os.path.join(shellCacheDir, "mozconf")
        self.repoPath = os.path.join(shellCacheDir,"mozbuild-trunk")
        self.hgPrefix = ['hg', '-R', self.repoPath]
        self.mozconf = mozconf
        self.objdir = os.path.join(self.repoPath,"obj-ff-dbg")

        self.mochitest = os.path.join(self.objdir,"_tests","testing","mochitest","tests")
        self.mochitest_tmp = os.path.join(self.objdir,"_tests","testing","mochitest","tests","commitbuilder")
        #self.ui = ui.ui()
        #self.hgrepo = hg.repository(self.ui, self.repoPath)
        #To use hg-python, you do: commands.MYCMDNAME(self.ui, self.repo, {args})

        if not os.path.exists(shellCacheDir):
            os.mkdir(shellCacheDir)
        if not os.path.exists(self.confDir):
            os.mkdir(self.confDir)
        if not os.path.exists(self.mochitest_tmp):
            os.mkdir(self.mochitest_tmp)
            print self.mochitest_tmp
            print "created!"

        #Sanity check: make sure hg is installed on the system, otherwise do not proceed!
        try:
            testhgInstall = subprocess.Popen(["hg","--version"],stdout=subprocess.PIPE)
            testresult = testhgInstall.communicate()
        except OSError as err:
            print "hg not installed on this system."
            quit()

        #Download a local trunk.
        self.getTrunk(makeClean=clean)

    def getTip(self):
        #Get trunk's tip changeset identifier hash
        try:
            tiprev = subprocess.Popen(self.hgPrefix+["tip"],stdout=subprocess.PIPE)
            capturedString = tiprev.communicate()
            try:
                changesetTip = capturedString[0].split("\n")[0].split(" ")[3].split(":")[1]
            except:
                pass
        except:
            print "Woops, something went wrong!"
            quit()
        if changesetTip:
            return changesetTip
        else:
            print "Couldn't get the tip changeset."

    def increment_day(self, date):
        #TODO: MOVE TO UTILS. Increments a date string.
        s = date.split("-")
        delta = datetime.timedelta(days=1)
        nextDate = datetime.date(int(s[0]),int(s[1]),int(s[2])) + delta
        return str(nextDate)

    def changesetFromDay(self, date, oldest=True):
        #Gets first changeset from a given date
        nextDate = self.increment_day(date)
        pushlog_url = "http://hg.mozilla.org/mozilla-central/json-pushes?startdate="+date+"&enddate="+nextDate
        pushlog_json = simplejson.load(urllib.urlopen(pushlog_url))
        sorted_keys = sorted(map(int,pushlog_json.keys()))

        changesetString = None
        if oldest:
           try:
               pushlog_first = str(sorted_keys.pop(0))
               changesetString = str(pushlog_json[pushlog_first]['changesets'][0])
           except:
              pass
        else:
           try:
              pushlog_last = str(sorted_keys.pop(-1))
              changesetString = str(pushlog_json[pushlog_last]['changesets'][0])
           except:
                   pass

        if changesetString != None:
            return changesetString

        return False

    def getTrunk(self, makeClean=False):
        #Get local trunk
        #Delete old trunk if set to "clean" mode
        if makeClean:
            print "Making clean trunk environment..."
            try:
                shutil.rmtree(self.repoPath)
            except:
                pass
        #Gets or updates our cached repo for building
        if os.path.exists(os.path.join(self.repoPath,".hg")):
            print "Found a recent trunk. Updating it to head before we begin..."
            updateTrunk = subprocess.call(self.hgPrefix + ["pull","-u"])
            print "Update successful."
        else:
            print "Trunk not found."
            makeClean = subprocess.call(["rm","-rf", self.repoPath])
            print "Removed old mozbuild-trunk directory. Downloading a fresh repo from mozilla-central..."
            #downloadTrunk = os.popen("hg clone http://hg.mozilla.org/mozilla-central mozbuild-trunk")
            downloadTrunk = subprocess.call(["hg", "clone", self.repoURL, "mozbuild-trunk"], cwd=self.shellCacheDir)

    def mozconfigure(self):
        #Set mozconfig settings
        #See if we are told to use an externally customized one
        print "\nConfiguring mozconfig:"
        if self.mozconf:
            os.environ['MOZCONFIG']=self.mozconf
            return

        #Make mozconfig
        os.chdir(self.confDir)
        if os.path.exists("config-default"):
            os.unlink("config-default")

        f=open('config-default', 'w')
        #Ensure we know where to find our built stuff by using a custom mozconfig
        f.write('mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-ff-dbg\n')

        #HACK :/
        if sys.platform == "win32" or sys.platform == "cygwin":
            print "Windows detected, compiling with 1 core."
            f.write("ac_add_options --with-windows-version=600\n")
            f.write("ac_add_options --enable-application=browser\n")
        else:
            print "Compiling with "+str(self.cores)+ " cores.\n"
            f.write('mk_add_options MOZ_MAKE_FLAGS="-s -j '+str(self.cores)+'"')

        f.close()

        #export MOZCONFIG=/path/to/mozilla/mozconfig-firefox
        os.environ['MOZCONFIG']=self.confDir+"/config-default"

    def bisect(self,good,bad, testfile=None, testpath=None, testcondition=None, args_for_condition=None):
        #Call hg bisect with initial params, set up building environment (mozconfig)
        #testfile is an external file, testpath is an actual mochitest
        good = hgId(good, self.hgPrefix)
        bad = hgId(bad, self.hgPrefix)
        if good and bad and self.validate(good, bad): #valid commit numbers, do the bisection!
            subprocess.call(self.hgPrefix+["bisect","--reset"])
            subprocess.call(self.hgPrefix+["up",bad])
            subprocess.call(self.hgPrefix+["bisect","--bad"])
            subprocess.call(self.hgPrefix+["bisect","--good",good])

            #Prebuild stuff here!!

            self.mozconfigure()
            self.bisectRecurse(testfile=testfile, testpath=testpath)
        else:
            print "Invalid values. Please check your changeset revision numbers."

    def bisectRecurse(self, testfile=None, testpath=None, testcondition=None, args_for_condition=[]):
        #Recursively build, run, and prompt
        verdict = ""

        if testfile==None and testpath==None and testcondition==None:
            #Not using a test, interactive bisect begin!
            self.buildAndRun()
        elif testcondition != None:
            #Using Jesse's idea: import any testing script and run it as the truth condition
            conditionscript = ximport.importRelativeOrAbsolute(testcondition)
            verdict = conditionscript.interesting([self.objdir] + args_for_condition)
        else:
            #TODO UNCOMMENT LINE BELOW
            self.build()
            if testfile == None:
                #Using External testfile
                #1. Clear self.mochitest_tmp
                try:
                    shutil.rmtree(self.mochitest_tmp)
                except:
                    pass
                #2. Move file from testpath to self.mochitest_tmp
                try:
                    os.mkdir(self.mochitest_tmp)
                    dst =  os.path.join(self.mochitest_tmp,"test_bug999999.html")
                    subprocess.call(['touch',dst])
                    print "copy " + str(testpath) + " to " +dst
                    shutil.copy(str(testpath),dst)
                except:
                    print "Unable to generate test path, quitting. Is your inputted test a valid mochitest?"
                    quit()
                #3. Make mochitest use the commitbuilder directory.
                testfile="commitbuilder"

            #DEBUG
            #testfile = "content/base/test/test_CrossSiteXHR.html"

            print "Trying testfile "+str(testfile)
            #TODO:
            # 1. Copy relevant test to a directory of my choice


            #sts = os.system("TEST_PATH="+testpath+" EXTRA_TEST_ARGS='--close-when-done' make -C " +self.objdir+ " mochitest-plain")
            sts = subprocess.call(['make','-C',self.objdir,'mochitest-plain'],stdout=open('/dev/null','w'),env={'TEST_PATH': testfile, 'EXTRA_TEST_ARGS':"--close-when-done"})
            shutil.rmtree(self.mochitest_tmp) #cleanup
            if sts != 0:
                verdict = "bad"
                print "============================"
                print "Verdict: FAILED test, bad changeset detected!"
                print "============================"
            else:
                verdict = "good"
                print "============================"
                print "Verdict: PASSED test, good changeset detected!"
                print "============================"

        if verdict != 'good' and verdict !='bad':
            while verdict != 'good' and verdict != 'bad' and verdict != 'b' and verdict != 'g':
                verdict = raw_input("Was this commit good or bad? (type 'good' or 'bad' and press Enter): ")

        #do hg bisect --good or --bad depending on whether it's good or bad
        retval = 0;
        if verdict == 'good':
            retval = captureStdout(self.hgPrefix+["bisect","--good"])
        else:
            retval = captureStdout(self.hgPrefix+["bisect","--bad"])

        print str(retval)

        # HACK
        if retval[1] == 'h': #if retval starts with "the" then we can quit
            quit()
        elif retval[1] == 'e': #if retval starts with "testing" then it needs to keep going
            print "\n"
        else:
            print "Something went wrong! :("
            quit()

        self.bisectRecurse(testfile=testfile, testpath=testpath, testcondition=testcondition, args_for_condition=args_for_condition)

    def buildAndRun(self, changeset=0):
        #API convenience function
        self.build(changeset=changeset)
        #print "Starting up Firefox..."
        self.run()
        #print "Complete! Firefox should be running."

    def build(self, changeset=0):
        #Build a binary and return the file path
        #Binary file named by changeset number
        if changeset != 0:
            changeset = str(changeset)
            print "Switching to revision "+changeset[:8]+"..."
            subprocess.call(self.hgPrefix+["update",changeset]) #switch to a given directory

        #Call make on our cached trunk
        print "Building..."
        makeData = captureStdout(self.makeCommand, ignoreStderr=True,
                                                        currWorkingDir=self.repoPath)
        if showMakeData == 1:
            print makeData

        print "Build complete!"

    def run(self):
        #Run the built binary if it exists. ONLY WORKS IF BUILD WAS CALLED!
        if sys.platform == "darwin":
            runner = FirefoxRunner(binary=os.path.join(self.shellCacheDir,"mozbuild-trunk","obj-ff-dbg","dist","Nightly.app","Contents","MacOS")+"/firefox-bin")
            runner.start()
            runner.wait()
        elif sys.platform == "linux2":
            runner = FirefoxRunner(binary=os.path.join(self.shellCacheDir,"mozbuild-trunk","obj-ff-dbg","dist","bin") + "/firefox")
            runner.start()
            runner.wait()
        elif sys.platform == "win32" or sys.platform == "cygwin":
            runner = FirefoxRunner(binary=os.path.join(self.shellCacheDir,"mozbuild-trunk","obj-ff-dbg","dist","bin") + "/firefox.exe")
            runner.start()
            runner.wait()
        else:
            print "Your platform is not currently supported."
            quit()

    def getBinary(self, revision):
        #Create binary, put into cache directory.
        #Returns path of binary for a given changeset
        self.build(changeset=revision)

        #Run "make package"
        print "Making binary..."
        makeData = captureStdout(["make","package"], ignoreStderr=True,
                                 currWorkingDir=os.path.join(self.repoPath,"obj-ff-dbg"))

        binary = None
        renamedBinary = None
        distFolder = os.path.join(self.repoPath,"obj-ff-dbg","dist")
        #return path to package
        if sys.platform == "darwin":
            try:
                binary = glob.glob(distFolder+"/firefox-*.dmg")[0]
            except:
                binary = None
            renamedBinary = str(revision[:8]) + ".dmg" #Don't want the filename to be too long :)
        elif sys.platform == "linux2":
            try:
                binary = glob.glob(distFolder+"/firefox-*.tar.gz")[0]
            except:
                binary = None
            renamedBinary = str(revision[:8]) + ".tar.gz"
        elif sys.platform == "win32" or sys.platform == "cygwin":
            try:
                binary = glob.glob(distFolder+"/firefox-*.zip")[0]
            except:
                binary = None
            renamedBinary = str(revision[:8]) + ".zip"
        else:
            print "ERROR: This platform is unsupported."
            quit()

        if binary != None:
            print "Binary build successful!"
            print renamedBinary + " is the binary:"

            #Move the binary into the correct place.
            try:
                os.remove(os.path.join(self.shellCacheDir,renamedBinary))
            except:
                pass
            shutil.move(binary, os.path.join(self.shellCacheDir,"builds",renamedBinary))

            #Return binary path
            return (os.path.join(self.shellCacheDir,"builds",renamedBinary), renamedBinary)

        print "ERROR: Binary not found."
        quit()

    def validate(self, good, bad):
        #Check that given changeset numbers aren't wonky
        if (good == bad):
            return False
        return True

def cli():
    #Command line interface
    usage = """usage: %prog --good=[changeset] --bad=[changeset] [options] \n       %prog --single=[changeset] -e
            """

    parser = OptionParser(usage=usage,version="%prog "+progVersion)
    parser.disable_interspersed_args()

    group1 = OptionGroup(parser, "Global Options",
                                        "")
    group1.add_option("-j", "--cores", dest="cores",
                                        help="Number of cores to compile with",
                                        metavar="[numcores]")
    group1.add_option("-f", "--freshtrunk", action = "store_true", dest="makeClean", default=False,
                                        help="Delete old trunk and use a fresh one")

    group2 = OptionGroup(parser, "Bisector Options",
                                        "These are options for bisecting on changesets")
    group2.add_option("-g", "--good", dest="good",
                                        help="Last known good revision",
                                        metavar="[changeset]")
    group2.add_option("-b", "--bad", dest="bad",
                                        help="Broken commit revision",
                                        metavar="[changeset]")

    group3 = OptionGroup(parser, "Single Changeset Options",
                                        "These are options for building a single changeset")

    group3.add_option("-s", "--single", dest="single",
                                        help="Build a single changeset",
                                        metavar="[changeset]")

    group3.add_option("-e", "--run", action="store_true", dest="run", default=False,
                                        help="run the current build -- only works if already built")

    group4 = OptionGroup(parser, "Binary building options",
                                        "These are options for building binaries from a single changeset")

    group4.add_option("-x", "--binary", action="store_true", dest="binary", default=False,
                                        help="build binary and return path to it")

    group4.add_option("-q", "--revision", dest="revision", default=None, metavar="[changeset]",
                                        help="revision number for single changeset to build binary from")

    group5 = OptionGroup(parser, "Automatic Testing Options (EXPERIMENTAL)",
                                        "Options for using an automated test instead of interactive prompting for bisection")

    group5.add_option("-t", "--testfile", dest="testfile", default=None, metavar="content/base/test",
                                        help="relative path of test directory in mochitest")

    group5.add_option("-w", "--exttest", dest="testpath", default=None, metavar="~/Desktop/mytest.html",
                                        help="absolute path to your own test file")

    group5.add_option("-c", "--condition", dest="condition", default=None, metavar="[cond.py -opt1 -opt2]",
                                        help="external condition for bisecting: MAKE THIS LAST OPTION")

    group6 = OptionGroup(parser, "Unstable Options",
                                        "Caution: use these options at your own risk.  "
                                        "They aren't recommended.")

    group6.add_option("-r", "--repo", dest="repoURL",
                                        help="alternative mercurial repo to bisect",
                                        metavar="valid repository url")

    #group.add_option("-m", "--altmake", dest="alternateMake",
    #                                    help="alternative make command for building",
    #                                    metavar="make command, in quotes")
    group6.add_option("-m", "--mozconfig", dest="mozconf",
                                        help="external mozconfig if so desired",
                                        metavar="path_to_mozconfig", default=False)

    parser.add_option_group(group1)
    parser.add_option_group(group2)
    parser.add_option_group(group3)
    parser.add_option_group(group4)
    parser.add_option_group(group5)
    parser.add_option_group(group6)
    (options, args_for_condition) = parser.parse_args()

    # If a user only wants to make clean or has supplied no options:
    if (not options.good or not options.bad) and not options.single:
        if options.makeClean:
            #Make a clean trunk
            commitBuilder = Builder(clean=options.makeClean)
        else:
            print """Use -h flag for available options."""
            print """To bisect, you must specify both a good and a bad date. (-g and -b flags are not optional)."""
            print """You can also use the --single=[chset] flag to build and --run to run a single changeset."""
        quit()

    # Set up a trunk for either bisection or build.
    mozConfiguration = options.mozconf
    commitBuilder = Builder(clean=options.makeClean, mozconf=mozConfiguration)
    if options.cores:
        commitBuilder.cores = options.cores
        commitBuilder.mozconfigure()

    # TODO: Allow a user to build a binary from cli
    if options.binary:
        pass
        #if options.revision:
        #    pass
        #else:
        #    print "You need to specify a revision to build the binary from."

    # For building single commits:
    if options.single:
        if options.run:
            commitBuilder.buildAndRun(changeset=options.single)
            print "Firefox successfully built and ran!"
        else:
            commitBuilder.build(changeset=options.single)
            print "Local trunk built. Not running."

    # For bisections:
    elif options.good and options.bad:
        print "Begin interactive commit bisect!\n"

        if options.repoURL:
            commitBuilder.repoURL = options.repoURL
            print "Using alternative repository "+options.repoURL
        #if options.alternateMake:
        #    commitBuilder.makeCommand = shlex.split(options.alternateMake)

        commitBuilder.bisect(options.good,options.bad, testfile=options.testfile, testpath=options.testpath, testcondition=options.condition, args_for_condition=args_for_condition)

    # Should not get here.
    else:
        print "Invalid input. Please try again."

if __name__ == "__main__":
    cli()
