#!/bin/env python

'''
Created on 27 Sep 2014

@author: Nicolas
'''
import Pyro4
import select
import socket
from batchTool import JobServer

nsDaemon = None
pyroDaemon = None
broadCastServer = None
bServer = None
stopAll = False

def mainLoop():
    global nsDaemon, broadCastServer, pyroDaemon, bServer, stopAll
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
            if stopAll:
                break
        except KeyboardInterrupt:
            break
        except Pyro4.errors.CommunicationError as e:
            print e
            bServer.disconnectAllClients()
                
    
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
    main()
    
