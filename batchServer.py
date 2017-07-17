#!/bin/env python

'''
Created on 27 Sep 2014

@author: Nicolas Lurkin

batchServer is a central instance that monitors batches of jobs on lxbatch.
batchClients can connect to it to submit jobs or display monitoring information.
'''

__version__ = '3.0'

import os
import socket
import sys

import Pyro4
from batchTool import JobServer, pyroObjects, printDebug, util
import select


nsDaemon = None
pyroDaemon = None
broadCastServer = None
bServer = None

def trace_calls(frame, event, arg):
    if event != 'call':
        return
    co = frame.f_code
    func_name = co.co_name
    func_filename = co.co_filename
    if "Python" in func_filename:
        #ignore python calls
        return
    if "Pyro4" in func_filename:
        #ignore Pyro calls
        return
    if "serpent" in func_filename:
        #ignore Pyro calls
        return
    if func_name == 'write':
        # Ignore write() calls from print statements
        return
    func_line_no = frame.f_lineno
    caller = frame.f_back
    caller_line_no = caller.f_lineno
    caller_filename = caller.f_code.co_filename
    print 'Call to %s on line %s of %s from line %s of %s' % \
        (func_name, func_line_no, func_filename,
         caller_line_no, caller_filename)
    return

def mainLoop():
    global nsDaemon, broadCastServer, pyroDaemon, bServer
    while True:
        try:
            # create sets of the socket objects we will be waiting on
            # (a set provides fast lookup compared to a list)
            nameserverSockets = set(nsDaemon.sockets)
            pyroSockets = set(pyroDaemon.sockets)
            rs = [broadCastServer]  # only the broadcast server is directly usable as a select() object
            rs.extend(nameserverSockets)
            rs.extend(pyroSockets)
            rs, _, _ = select.select(rs, [], [], 3)
            eventsForNameserver = []
            eventsForDaemon = []
            for s in rs:
                if s is broadCastServer:
                    broadCastServer.processRequest()
                elif s in nameserverSockets:
                    eventsForNameserver.append(s)
                elif s in pyroSockets:
                    eventsForDaemon.append(s)
                
                if eventsForNameserver:
                    nsDaemon.events(eventsForNameserver)
                if eventsForDaemon:
                    pyroDaemon.events(eventsForDaemon)
            bServer.mainLoop()
            if pyroObjects.stopAll:
                bServer.kill()
                break
        except Pyro4.errors.TimeoutError:
            printDebug(3, "Timeout")
        except KeyboardInterrupt:
            printDebug(3, "Catching the interrupt")
            bServer.kill()
            break
        except Pyro4.errors.CommunicationError as e:
            printDebug(1, e)
            bServer.kill()
        except Exception, e:
            printDebug(1, ("Unexpected error:", e.__doc__))
            print e.message
            bServer.kill()
                
    
    nsDaemon.close()
    broadCastServer.close()
    pyroDaemon.close()


def setNS():
    '''
    Starting namespace server
    '''
    global nsDaemon, broadCastServer
    
    my_ip = Pyro4.socketutil.getIpAddress(None, workaround127=True)
    nameserverUri, nsDaemon, broadCastServer = Pyro4.naming.startNS(host=my_ip)
    assert broadCastServer is not None, "expect a broadcast server to be created"
    print("got a Nameserver, uri=%s" % nameserverUri)
    print("ns daemon location string=%s" % nsDaemon.locationStr)
    print("ns daemon sockets=%s" % nsDaemon.sockets)
    print("bc server socket=%s (fileno %d)" % (broadCastServer.sock, broadCastServer.fileno()))
    with open(os.environ['HOME'] + "/.ns.cfg", "a") as f:
        f.write("{0}\n".format(my_ip))

def createServer():
    '''
    Starting batch server and associated pyro daemon
    '''
    global bServer, pyroDaemon
    # create a Pyro daemon
    pyroDaemon = Pyro4.core.Daemon(host=socket.gethostname())
    print("daemon location string=%s" % pyroDaemon.locationStr)
    print("daemon sockets=%s" % pyroDaemon.sockets)

    bServer = JobServer()
    
    # register a server object with the daemon
    serveruri = pyroDaemon.register(bServer)
    print("server uri=%s" % serveruri)
    
    return serveruri

def registerServer(serveruri):
    global nsDaemon 
    nsDaemon.nameserver.register("castor.jobServer", serveruri)
        
def main():
    setNS()
    serveruri = createServer()
    registerServer(serveruri)
    
    mainLoop()

def tryint(val):
    try:
        return int(val)
    except ValueError:
        return False

def printUsage():
    print __doc__
    print "\nUsage:"
    print "\t -d\033[4mn\033[0m:  Print debugging information according to the debug level \033[4mn\033[0m: 0=No debug, 1=Error, 2=Warning, 3=Info"
    print "\t -t: Activate tracing"
    print "\t -h: Print this help"
    
if __name__=="__main__":
    useTrace = False
    if len(sys.argv)>1:
        for arg in sys.argv:
            if arg.startswith('-d') and tryint(arg[2:])!=False:
                util._debugLevel = tryint(arg[2:])
            elif arg.startswith('-t'):
                useTrace = True
            elif arg.startswith("-h") or arg.startswith("h"):
                printUsage()
                sys.exit(0)
    if useTrace:
        sys.settrace(trace_calls)
    else:
        main()
    
    try:
        sys.stdout.close()
    except:
        pass
    try:
        sys.stderr.close()
    except:
        pass
    
