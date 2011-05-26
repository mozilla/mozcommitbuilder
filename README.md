#Mozilla CommitBuilder

##Summary
Command-line tool for regression finding in Firefox. Uses mozilla-central repository by default but any Mozilla Firefoxhg repository can be used by setting the -r flag. Takes two commit numbers (long form hash or short are both okay) and interactively calls hg bisect on the commits, compiles, and launches each firefox.

##Dependencies
You must have this line in mozconfig right now:  

  mk_add_options MOZ_OBJDIR=@TOPSRCDIR@/obj-ff-dbg

The reason for this is that obj-ff-dbg is the folder we go into to launch compiled firefoxes  
TODO: Export a custom mozconfig so this is no longer necessary

##Usage
Example:

  ./builder.py --good=70170 --bad=70172
