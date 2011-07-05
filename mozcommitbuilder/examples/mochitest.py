# mochitest.py
# Test for mozcommitbuilder
#
# Usage: mozcommitbuilder -g {good changeset} -b {bad changeset} -c /path/to/mochitest.py /path/to/mymochitest.html
#
# This is an example!
# TO WRITE YOUR OWN TEST FOR COMMITBUILDER
# Requirements:
#   Must define an "interesting" function that is called by the commitbuilder
#   Function takes (2) Params
#       1. args (will return a list of args, first parameter will be the object directory)
#       2. tmpdir gives us a directory to put things in and stuff
#
#   Your function needs to take both args but doesn't actually have to use either of them.
#
#   Return "bad" or "good"
#   You can also use True/False, BUT remember that True means "bad" (there is a regression!)
#                                                  False means "good" (there isn't a regression!)

import shutil
import subprocess
import os
import sys

def interesting(args, tmpdir):
    # This function is called by mozcommitbuilder. Returns "bad" or "good"
    # args -> first argument is an object directory
    #      -> the rest of the args are args inputted by the user

    testpath = os.path.expanduser(str(args[1]))

    objdir = args[0]

    # I'm going to create a new directory inside the tests directory
    # This will allow me to copy my mochitest into it and run it
    # A bug prevents auto-shutdown of firefox when you run single tests outside of a directory.
    mochitest_tmp = os.path.join(objdir,"_tests","testing","mochitest","tests","commitbuilder")

    # 1. Remove old temporary directory tree
    try:
        shutil.rmtree(mochitest_tmp)
    except:
        pass

    # 2. Move file from testpath to mochitest_tmp
    try:
        os.mkdir(mochitest_tmp)
        dst =  os.path.join(mochitest_tmp,"test_bug999999.html")
        subprocess.call(['touch',dst])
        print "copy " + str(testpath) + " to " +dst
        shutil.copy(str(testpath),dst)
    except:
        print "Unable to generate test path, quitting. Is your inputted test a valid mochitest?"
        quit()

    # 3. Make mochitest use the commitbuilder directory.
    # TODO Let users run testfiles that exist
    testfile="commitbuilder"

    #DEBUG
    #testfile = "content/base/test/test_CrossSiteXHR.html"

    print "Trying testfile "+str(testfile)
    sts = subprocess.call(['make','-C',objdir,'mochitest-plain'],stdout=open('/dev/null','w'),env={'TEST_PATH': testfile, 'EXTRA_TEST_ARGS':"--close-when-done"})
    shutil.rmtree(mochitest_tmp) #cleanup
    if sts != 0:
        print "============================"
        print "Verdict: FAILED test, bad changeset detected!"
        print "============================"
        return "bad"
    else:
        print "============================"
        print "Verdict: PASSED test, good changeset detected!"
        print "============================"
        return "good"
