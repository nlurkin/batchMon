#!/bin/env python
'''
Created on 27 Sep 2014

@author: Nicolas Lurkin

batchClient can connect to a central batchServer instance. It can create new batches, 
load existing batches and display monitoring informations sent by the server.
'''
from batchTool.display2 import DCommands

__version__ = '3.0'

try:
    from argparse import ArgumentParser, RawDescriptionHelpFormatter
except ImportError:
    from batchTool.argparse import ArgumentParser, RawDescriptionHelpFormatter

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
            
            retCmd = client.mainLoop()
            
            if retCmd.command==DCommands.Back:
                server.disconnectClient(retCmd.name, serveruri)
                l = server.getBatchList()
                client.displayBatchList(l)
            elif retCmd.command== DCommands.Select and retCmd.name!=None:
                registerClient(retCmd.name)
            elif retCmd.command==DCommands.Delete and retCmd.name!=None:
                server.removeBatch(retCmd.name)
                l = server.getBatchList()
                client.displayBatchList(l)
            elif retCmd.command==DCommands.Kill:
                server.disconnectClient(retCmd.name, serveruri)
                server.stop()
                break
            elif retCmd.command==DCommands.Refresh:
                server.resubmitFailed(retCmd.name)
            elif retCmd.command==DCommands.Submit:
                server.submitInit(retCmd.name)
            elif retCmd.command==DCommands.Switch:
                header = server.invertKeepOutput(retCmd.name)
                client.displayHeader(header)
            

        except KeyboardInterrupt:
            break
            
    server.disconnectClient(client.getName(), serveruri)
    pyroDaemon.close()

def registerClient(name):
    global client, serveruri
    startTime, headers, totalJobs, summary = server.registerClient(name, serveruri)
    
    client.setStartTime(startTime)
    client.displayHeader(headers)
    client.setTotalJobs(totalJobs)
    client.displaySummary(summary)
    
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
    parser.add_argument('-t', '--test', action='store_true', default=False,
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
    groupNew.add_argument("-l", "--load", action="store",
                        help="Reload a previous monitor (restart tracking the jobs, do not regenerate them)")
    args = parser.parse_args()

    with open(os.environ['HOME'] + "/.ns.cfg", "r") as f:
        ip = f.readline()
    print ip
    nameserver = Pyro4.naming.locateNS(host=ip)
    uri = nameserver.lookup("castor.jobServer")
    server = Pyro4.Proxy(uri)
    
    if args.config:
        try:
            if not os.path.isabs(args.config):
                args.config = os.getcwd()+"/"+args.config
            server.addBatch(args.config, args.name, args.queue, args.test, args.keep)
        except Exception:
            print "".join(Pyro4.util.getPyroTraceback())
            raise Exception()
    elif args.load:
        try:
            if not os.path.isabs(args.load):
                args.load = os.getcwd()+"/"+args.load
            server.loadBatch(args.load, args.name, args.keep)
        except Exception:
            print "".join(Pyro4.util.getPyroTraceback())        
            raise Exception()
    if args.submit:
        server.submitInit(args.name)
        return 
    
    #if args.nocurse:
    #    mainInit()
    #else:
    curses.wrapper(mainInit)

if __name__ == "__main__":
    sys.exit(argParser())
    
