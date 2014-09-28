from argparse import ArgumentParser, RawDescriptionHelpFormatter
from batchServer import jobServer
from batchTool.xxx import DisplayClient
import Pyro4
import curses
import select
import socket
import sys

server = Pyro4.Proxy("PYRONAME:castor.jobServer")
serveruri = ""
client = None

def mainLoop():
    global pyroDaemon, client, stopAll
    while True:
        try:
            pyroSockets = set(pyroDaemon.sockets)
            rs = []  # only the broadcast server is directly usable as a select() object
            rs.extend(pyroSockets)
            rs, _, _ = select.select(rs, [], [], 3)
            eventsForDaemon = []
            for s in rs:
                if s in pyroSockets:
                    eventsForDaemon.append(s)
                
                if eventsForDaemon:
                    pyroDaemon.events(eventsForDaemon)
                    
            client.mainLoop()

        except KeyboardInterrupt:
            break
            
    server.disconnectClient("xxx", serveruri)
    pyroDaemon.close()

def mainInit(scr=None):
    global pyroDaemon, serveruri, client
    client = DisplayClient(scr)
    
    pyroDaemon = Pyro4.core.Daemon(host=socket.gethostname())
    # register a server object with the daemon
    serveruri = pyroDaemon.register(client)
    print("server uri=%s" % serveruri)
    
    server.registerClient("xxx", serveruri)
    
    mainLoop()

def argParser():
    '''Command line options.'''
    
    parser = ArgumentParser(description=__import__('__main__').__doc__.split("\n")[1], formatter_class=RawDescriptionHelpFormatter)
    parser.add_argument('-q', '--queue', action='store', default="1nh", 
                    help="Indicates on which LXBATCH queue the jobs will be submitted (default:1nh)")
    parser.add_argument('-t', '--test', action='store_true', 
                    help="Test the existence of output files. Do not regenerate jobs for which the output file already exists (non-tested feature)")
    parser.add_argument('-n', '--name', action='store', default="config", 
                    help="Name of the monitor (used for later recovery, default:config)")
    parser.add_argument('-x', '--nocurse', action='store_true', 
                    help="Disable the curse interface")
    parser.add_argument('-k', '--keep', action='store_true',
                    help="Do not delete the LXBATCH output (LSFJOB_xxxxxxx)")
    groupNew = parser.add_mutually_exclusive_group(required=True)
    groupNew.add_argument("-c", "--config", action="store",
                        help="Configuration file to use (new monitor)")
    groupNew.add_argument("-l", "--load", action="store",
                        help="Reload a previous monitor (restart tracking the jobs, do not regenerate them)")
    args = parser.parse_args()
    
    
    
    if args.config:
        #mon.newBatch(args.config, args.name, args.queue, args.test)
        server.addBatch("testConfig", "xxx", "1nh", True, False)
    elif args.load:
        #mon.loadBatch(args.load)
        pass

    if args.nocurse:
        mainInit()
    else:
        curses.wrapper(mainInit)

if __name__ == "__main__":
    sys.exit(argParser())
    