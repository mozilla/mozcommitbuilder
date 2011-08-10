#!/usr/bin/python

# Caller class for mozremotebuilder's remote socket server

import socket
import sys
from utils import get_platform
from optparse import OptionParser

from multiprocessing import Queue

#For monitoring if build is done via Pulse
from threading import Thread, Condition
from pulsebuildmonitor import PulseBuildMonitor

# Keep a queue of pulse messages as they come in.
# We pop them off and check if they're relevant to us.
lastCompleted = Queue()

# Condition Variable for knowing if a new try build has completed
cv = Condition()

class BuildMonitor(PulseBuildMonitor, Thread):
    '''
    This class signals via condition variable that our build is done
    Uses Pulse (http://pulse.mozilla.org)
    '''
    def __init__(self, logger=None, port=8034, **kwargs):
        self.logger = logger
        self.port = port
        self.builds = {}
        PulseBuildMonitor.__init__(self, logger=self.logger, **kwargs)
        Thread.__init__(self)

    def onBuildComplete(self, builddata):
        #Called when a pulse message comes in

        #print "=============================="
        #print "DEBUG: "+ str(builddata['buildurl'])
        #print json.dumps(builddata)
        #print "=============================="

        lastCompleted.put(str(builddata['buildurl']))
        cv.acquire()
        cv.notifyAll() #let thread know that a build came in!
        cv.release()

class BuildCaller():
    def __init__(self, host="localhost", port=9999, data="1"):
        self.host = host
        self.port = port

        # Create a socket (SOCK_STREAM means a TCP socket)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        system_platform = self.getPlatformString()

        self.data = str(data)+":macosx64" #default string

    def send(self):
        # Send data to server
        self.sock.connect((str(self.host), int(self.port)))
        self.sock.send(self.data + "\n")

    def getResponse(self):
        # Receive response data from the builder's socket server
        # Server sends (2) responses, first an ack after queue'ing
        # the changeset and the second is the built changeset
        confirm = self.sock.recv(1024)
        changeset = self.sock.recv(1024)

        self.sock.close()
        return changeset

    def getChangeset(self):
        # Returns response from server
        self.send()
        print "Sent request for changeset " + self.data
        print "Waiting for response from server..."
        return self.getResponse()

    def getPlatformString(self):
        platform = get_platform()
        if platform['name'] == "Windows":
            return "win32"
        elif platform['name'] == "Linux":
            if platform['bits'] == '64':
                return "linux64"
            return "linux"
        elif platform['name'] == "Mac":
            return "macosx64"

        print "ERROR, couldn't get platform."
        quit()

    def getURLResponse(self,response):
        #First, set up the listener for Pulse in another thread
        monitor = BuildMonitor(tree=['try'], label='woo@mozilla.com|latest_build_monitor_' + socket.gethostname())
        monitor.start()
        monitor_thread = Thread(target=monitor.listen)
        monitor_thread.setDaemon(True)
        monitor_thread.start()

        cv.acquire()
        downloadURL = lastCompleted.get()
        while downloadURL.count(response) < 1:
            print "Waiting for " + response + " to show up in the build log..."
            cv.wait()
            downloadURL = lastCompleted.get()
        cv.release()

        print downloadURL + " is the URL we need to download from! yep."
        return downloadURL



def cli():
    parser = OptionParser()
    parser.add_option("-c", "--changeset", dest="changeset",help="requested changeset",
                      metavar="", default=1)
    parser.add_option("-s", "--server", dest="hostname",help="build server to request from",
                      metavar="xxx.xxx.xxx.xxx", default="localhost")
    parser.add_option("-p", "--port", dest="port",help="server port",
                      metavar="9999", default=9999)
    (options, args) = parser.parse_args()

    #this is how you use it
    caller = BuildCaller(host=options.hostname, port=options.port, data=options.changeset)
    response = caller.getChangeset()
    url = caller.getURLResponse(response)

if __name__ == "__main__":
    cli()
