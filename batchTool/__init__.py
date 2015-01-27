from config import ConfigBatch, BatchToolExceptions
from monitor2 import Monitor2
from monitor import Monitor
from display2 import Display2
from pyroObjects import JobServer, DisplayClient

#0 = no debug, 1=Error, 2=Warning, 3=Info
_debugLevel = 0

def printDebug(debugLvl, msg):
    if debugLvl >= _debugLevel:
        print msg