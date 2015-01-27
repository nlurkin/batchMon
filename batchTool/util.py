'''
Created on Jan 27, 2015

@author: ncl
'''

#0 = no debug, 1=Error, 2=Warning, 3=Info
_debugLevel = 0

def printDebug(debugLvl, msg):
    if debugLvl <= _debugLevel:
        print msg