#Mozilla CommitBuilder

##Summary
Command-line tool for regression finding in Firefox. Uses mozilla-central repository by default but any Mozilla Firefoxhg repository can be used by setting the -r flag. Takes two commit numbers (long form hash or short are both okay) and interactively calls hg bisect on the commits, compiles, and launches each firefox. Originally designed for use in mozregression, a regression finder that tests nightlies.

##Dependencies
Mercurial, all Mozilla compilation dependencies

##Install
mozcommitbuilder is available on pypi, so you can install it with easy_install or pip. The recommended method is pip.
sudo pip install mozcommitbuilder

##Usage
Example:

`mozcommitbuilder --good=70170 --bad=70172`
