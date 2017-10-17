'''
Created on Jan 27, 2015

@author: ncl
'''

import threading
import subprocess
import time

#0 = no debug, 1=Error, 2=Warning, 3=Info
_debugLevel = 0

def printDebug(debugLvl, msg):
    if debugLvl <= _debugLevel:
        print msg

class NoIndex_c():
    def __str__(self):
        return "NoIndex"
    def __repr__(self):
        return "NoIndex"

NoIndex = NoIndex_c()

class TwoLayerDict(object):
    def __init__(self):
        self.dico = {}
        
    def iterkeys(self):
        fullList = []
        for k1,v1 in self.dico.iteritems():
            for k2,_ in v1.iteritems():
                fullList.append((k1,k2))
        return fullList 
        
    def iteritems(self):
        fullList = []
        for k1,v1 in self.dico.iteritems():
            for k2,v2 in v1:
                fullList.append((k1,k2,v2))
        return fullList 
    
    def iterLayer1(self):
        return self.dico.iterkeys()
    
    def __getitem__(self, key):
        k1,k2 = self._splitKeys(key)
        
        if not key in self:
            return None
        if k2 is None:
            return self.dico[k1]
        else:
            return self.dico[k1][k2]
    
    def __setitem__(self, key, value):
        k1,k2 = self._splitKeys(key)
        
        if k2 is None:
            k2 = NoIndex
        
        if not k1 in self.dico:
            self.dico[k1] = {}
        self.dico[k1][k2] = value

    def __delitem__(self, key):
        k1,k2 = self._splitKeys(key)
        
        if key in self:
            if not k2 is None:
                del self.dico[k1][k2]
            elif k2 is None or len(self.dico[k1])==0:
                del self.dico[k1]
        
    def _splitKeys(self, key):
        if type(key)==tuple:
            k1,k2 = key
        else:
            k1 = key
            k2 = None
        return k1,k2
    
    def __contains__(self, key):
        k1,k2 = self._splitKeys(key)
        if k1 in self.dico:
            if k2 is None or k2 in self.dico[k1]:
                return True
        return False
    
    #def __str__(self):
    #    if len(self.dico)==0:
    #        return "Empty"
    #    return "\n".join(["{}: {}".format(k, ["{}.{}".format(k1,str(v1)) for k1,v1 in v.iteritems()]) for k,v in self.dico.iteritems()])

class subCommand(threading.Thread):
    '''
    SubCommand class. Executes a subprocess in a thread to allow for timeout.
    If the command does not return within the allowed time, the thread is 
    terminated (and the subprocess with it).
    '''
    def __init__(self, cmd, cmdInput, timeout):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.cmdInput = cmdInput
        self.timeout = timeout
        self.subOutput = None
        self.p = None
    
    def run(self):
        '''
        Overloaded from thread. Entry point of the Thread.
        '''
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (self.subOutput, self.subError) = self.p.communicate(self.cmdInput)
    
    def Run(self):
        '''
        Entry point of the class
        '''
        self.start()
        time.sleep(1)
        self.join(self.timeout)

        if self.is_alive() and not self.p is None:
            self.p.terminate()
            self.join()
       
        if len(self.subError)>0 and not "No job" in self.subError:
        	print self.subError
        return self.subOutput


