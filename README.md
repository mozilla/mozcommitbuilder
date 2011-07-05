#Mozilla CommitBuilder
The [mozcommitbuilder](http://samliu.github.com/mozcommitbuilder) package is a generic builder library for Mozilla Firefox. It also features interactive regression finding over changesets using local builds.
It is probably most useful when used in combination with custom condition scripts (see below for more information)

#Summary
Downloads the mozilla-central mercurial repository to a local cache and allows operations on that trunk
including interactive regression finding over changeset ranges and building particular revisions of firefox and running them.
In particular, this module was designed for regression hunting and to provide a flexible builder for firefox.

#Dependencies
Mercurial. A correctly-configured mozconfig dotfile is optional. By default, mozcommitbuilder generates its own mozconfig, but you can pass in your own through params/cli if the script fails to build correctly or if you need other configurations..

#Install
mozcommitbuilder is available on pypi, so you can install it with easy_install or pip. The recommended method is pip.

	sudo pip install mozcommitbuilder --upgrade

#Usage
## Command-line Interface

```python
#This is an example of a command to do interactive bisection between
#changesets (you can use the full changeset hash or short numerical id)
mozcommitbuilder -g 70168 -b 70180
```
```python
#If you are on OSX or Linux, this will compile with 8 cores. Multi-core
#compiliation on windows doesn't work, the parameter will be ignored.
mozcommitbuilder -g 70168 -b 70180 -j 8
```

```python
#This will delete the cached trunk and download a new one, then build
#revision 70168 with 8 cores
mozcommitbuilder -f --single=70168 -j 8
```

```python
#This will delete the cached trunk and download a new one, then build
#revision 70168 with 8 cores, then start firefox on completion.
mozcommitbuilder -f -e --single=70168 -j 8
```


## Condition Scripts

Instead of interactively building/running/prompting during bisection,
you may opt to use an automated condition script. Here is some
information about the condition script (you can also see the example
in the examples directory)

```python
Writing a condition script:
====================
1. It needs to contain a function called interesting(args, directory). It takes two arguments, one which will be populated
w/ the arguments, the other which will contain the path of a temporary directory.
2. It needs to return a string "bad" or "good" to indicate if the revision was broken or not.
It can theoretically return a boolean but that is less descriptive and may be confusing.
If you choose to use booleans, True is bad (contains regression), False is good (does not contain regression)
3. args[0] contains the path of the object directory (useful when running tests)
4. args[1] to args[x] contain whatever arguments were supplied
```

```python
#This will bisect using a condition script
#NOTICE THAT THE CONDITION FLAG MUST COME LAST.
mozcommitbuilder -g 70168 -b 70180 -c ~/Desktop/myConditionTest.py arg1 arg2 argX
```


## Python API

```python
#Instantiation
from mozcommitbuilder import Builder
commitBuilder = Builder()

# Optional Constructor Params:
"""
1. makeCommand, default=["make","-f","client.mk","build"]
2. cores, default=1
3. mozconf, default=None (create our own)
4. shellCacheDir, default=~/moz-commitbuilder-cache (where to instantiate the cache)
5. repoURL, default=moz-central repository URL
6. clean, default=False (make clean trunk)
"""

#Example:
commitBuilder = Builder(cores=8, mozconf="~/myDirectory/mozconf") #custom mozconf
                                                                  #build with 8 cores
```

```python
#Remote Trunk Operations:
commitBuilder.getTrunk() # fetches a local trunk
commitBuilder.getBinary("70168") # Builds binary from revision,
                                 # moves into the cache directory
                                 # returns the path to it
```

```python
#Bisection:
commitBuilder.bisect("goodchangesetRev","badchangesetRev") # Interactive bisection
```

```python
#Building and running:
commitBuilder.build(changeset="70168") # Build only
commitBuilder.run() # Run. Warning: ungraceful failure if build hasn't happened yet.
commitBuilder.buildAndRun(changeset="70168") # Build rev and run
```

```python
#Repository information:
mostRecentChangeset = commitBuilder.getTip() #Returns tip's changest number
firstChangesetFromDay = commitBuilder.changesetFromDay(date="2011-06-31") #Get first changeset from date
lastChangesetFromDay = commitBuilder.changesetFromDay(date="2011-06-31",oldest=False) #Last changeset from date
```


#Other
For bisection: if the range of commits spans more than a day, try [mozregression](http://harthur.github.com/mozregression)


#Flags
```
Usage: builder.py --good=[changeset] --bad=[changeset] [options]
       builder.py --single=[changeset] -e


Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit

  Global Options:
    -j [numjobs], --cores=[numjobs]
                        Max simultaneous make jobs (default: 8, the number of
                        cores on this system)
    -f, --freshtrunk    Delete old trunk and use a fresh one

  Bisector Options:
    These are options for bisecting on changesets. Dates are retrieved
    from pushlog and are not as reliable as exact changeset numbers.

    -g [changeset or date], --good=[changeset or date]
                        Last known good revision
    -b [changeset or date], --bad=[changeset or date]
                        Broken commit revision

  Single Changeset Options:
    These are options for building a single changeset

    -s [changeset], --single=[changeset]
                        Build a single changeset
    -e, --run           run the current build -- only works if already built

  Binary building options:
    These are options for building binaries from a single changeset

    -x, --binary        build binary and return path to it
    -q [changeset], --revision=[changeset]
                        revision number for single changeset to build binary
                        from

  Automatic Testing Options (EXPERIMENTAL):
    Options for using an automated test instead of interactive prompting
    for bisection. Please read documentation on how to write testing
    functions for this script.

    -c [condtest.py -opt1 -opt2], --condition=[condtest.py -opt1 -opt2]
                        External condition for bisecting. Note: THIS MUST BE
                        THE LAST OPTION CALLED.

  Broken and Unstable Options:
    Caution: use these options at your own risk.  They aren't recommended.

    -r valid repository url, --repo=valid repository url
                        alternative mercurial repo to bisect NOTE: NEVER BEEN
                        TESTED
    -m path_to_mozconfig, --mozconfig=path_to_mozconfig
                        external mozconfig if so desired NOTE: BROKEN RIGHT
                        NOW
```
