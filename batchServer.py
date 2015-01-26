#!/bin/env python

'''
Created on 27 Sep 2014

@author: Nicolas
'''
import os
import socket
import sys

import Pyro4
from batchTool import JobServer
from batchTool import pyroObjects
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
                break
        except Pyro4.errors.TimeoutError:
            print "Timeout"
        except KeyboardInterrupt:
            print "Catching the interrupt"
            bServer.kill()
            break
        except Pyro4.errors.CommunicationError as e:
            print e
            bServer.kill()
        except Exception, e:
            print "Unexpected error:", e.__doc__
            print e.message
            bServer.kill()
                
    
    nsDaemon.close()
    broadCastServer.close()
    pyroDaemon.close()


#Starting namespace server
def setNS():
    global nsDaemon, broadCastServer
    
    #nameServerDaemon = Pyro4.naming.locateNS()
    my_ip = Pyro4.socketutil.getIpAddress(None, workaround127=True)
    nameserverUri, nsDaemon, broadCastServer = Pyro4.naming.startNS(host=my_ip)
    assert broadCastServer is not None, "expect a broadcast server to be created"
    print("got a Nameserver, uri=%s" % nameserverUri)
    print("ns daemon location string=%s" % nsDaemon.locationStr)
    print("ns daemon sockets=%s" % nsDaemon.sockets)
    print("bc server socket=%s (fileno %d)" % (broadCastServer.sock, broadCastServer.fileno()))
    #with open("/afs/cern.ch/user/n/nlurkin/git/batchMon/ns.cfg", "w") as f:
    with open(os.environ['HOME'] + "/.ns.cfg", "w") as f:
        f.write(my_ip)

#Starting batch server and associated pyro daemon
def createServer():
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

#Register server with name server
def registerServer(serveruri):
    global nsDaemon 
    nsDaemon.nameserver.register("castor.jobServer", serveruri)
        
def main():
    setNS()
    serveruri = createServer()
    registerServer(serveruri)
    
    mainLoop()

if __name__=="__main__":
    if len(sys.argv)>1:
        sys.settrace(trace_calls)
    main()
    
