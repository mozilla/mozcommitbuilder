#Mozilla CommitBuilder

##Summary
Command-line tool for regression finding in Firefox. Uses mozilla-central repository by default but any Mozilla Firefoxhg repository can be used by setting the -r flag. Takes two commit numbers (long form hash or short are both okay) and interactively calls hg bisect on the commits, compiles, and launches each firefox.

##Dependencies
Mercurial

##Usage
Example:

`
./builder.py --good=70170 --bad=70172

`
