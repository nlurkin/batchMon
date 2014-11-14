#!/bin/env python
"""
xxx
"""

from argparse import ArgumentParser, RawDescriptionHelpFormatter
import curses
import os
import socket
import sys

import Pyro4
from batchTool import DisplayClient
import select


server = None
serveruri = ""
client = None

def mainLoop():
    global pyroDaemon, client, stopAll
    while True:
        try:
            pyroSockets = set(pyroDaemon.sockets)
            rs = []  # only the broadcast server is directly usable as a select() object
            rs.extend(pyroSockets)
            #rs.extend()
            rs, _, _ = select.select(rs, [], [], 0.1)
            eventsForDaemon = []
            
            for s in rs:
                if s in pyroSockets:
                    eventsForDaemon.append(s)
                     
                if eventsForDaemon:
                    pyroDaemon.events(eventsForDaemon)
            
            ret,name = client.mainLoop()
            
            if ret==-1:
                server.disconnectClient(name, serveruri)
                l = server.getBatchList()
                client.displayBatchList(l)
            elif ret== +1 and name!=None:
                registerClient(name)
            elif ret==-100 and name!=None:
                server.removeBatch(name)
                l = server.getBatchList()
                client.displayBatchList(l)
            elif ret==-101:
                server.disconnectClient(name, serveruri)
                server.stop()
                break
            elif ret==+100:
                server.resubmitFailed(name)
            elif ret==+101:
                server.submitInit(name)
            elif ret==+102:
                header = server.invertKeepOutput(name)
                client.displayHeader(header)
            

        except KeyboardInterrupt:
            break
            
    server.disconnectClient(client.getName(), serveruri)
    pyroDaemon.close()

def registerClient(name):
    global client, serveruri
    startTime, headers = server.registerClient(name, serveruri)
    
    client.setStartTime(startTime)
    client.displayHeader(headers)
    
def mainInit(scr=None):
    global pyroDaemon, serveruri, client, server
    client = DisplayClient(scr)
    
    pyroDaemon = Pyro4.core.Daemon(host=socket.gethostname())
    # register a server object with the daemon
    serveruri = pyroDaemon.register(client)
    
    l = server.getBatchList()
    client.displayBatchList(l)
    
    #startTime, headers = server.registerClient("xxx", serveruri)
    
    #client.setStartTime(startTime)
    #client.displayHeader(headers)
    
    mainLoop()

def argParser():
    '''Command line options.'''
    
    global server
    
    parser = ArgumentParser(description=__import__('__main__').__doc__.split("\n")[1], formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-q', '--queue', action='store', default="1nh", 
                    help="Indicates on which LXBATCH queue the jobs will be submitted (default:1nh)")
    parser.add_argument('-t', '--test', action='store_true', default="true",
                        help="Test the existence of output files. Do not regenerate jobs for which the output file already exists")
    parser.add_argument('-n', '--name', action='store', default="config", 
                    help="Name of the monitor (used for later recovery, default:config)")
    #parser.add_argument('-x', '--nocurse', action='store_true', 
    #                help="Disable the curse interface")
    parser.add_argument('-k', '--keep', action='store_true',
                    help="Do not delete the LXBATCH output (LSFJOB_xxxxxxx)")
    parser.add_argument('-s', '--submit', action='store_true',
                    help="Submit only and exit")
    groupNew = parser.add_mutually_exclusive_group(required=False)
    groupNew.add_argument("-c", "--config", action="store",
                        help="Configuration file to use (new monitor)")
    groupNew.add_argument("-l", "--load", action="store_true",
                        help="Reload a previous monitor (restart tracking the jobs, do not regenerate them)")
    args = parser.parse_args()

    #with open("/afs/cern.ch/user/n/nlurkin/git/batchMon/ns.cfg", "r") as f:
    with open(os.environ['HOME'] + "/.ns.cfg", "r") as f:
        ip = f.readline()
    print ip
    nameserver = Pyro4.naming.locateNS(host=ip)
    uri = nameserver.lookup("castor.jobServer")
    server = Pyro4.Proxy(uri)
    
    if args.config:
        server.addBatch(args.config, args.name, args.queue, args.test, args.keep)
    
    if args.submit:
        server.submitInit(args.name)
        return 
    
    #if args.nocurse:
    #    mainInit()
    #else:
    curses.wrapper(mainInit)

if __name__ == "__main__":
    sys.exit(argParser())
    
