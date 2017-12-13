'''
Created on 12 Dec 2014

@author: Nicolas

Class to manipulate Linux FS
'''
import subprocess
import datetime
import os

_preloaded = [None, []]
_preloadTime = None

def isFile():
    pass

def isDirectory():
    pass

def getMGMUrl(path):
    if "/eos/experiment" in path:
        return "root://eosna62.cern.ch/"
    else:
        return "root://eosuser.cern.ch/"
    
def exists(path, preload):
    global _preloaded
    global _preloadTime
    path = os.path.abspath(path)
    #Preload if requested
        
    eos_mgm_url = getMGMUrl(path)
    
    if preload:
        p = subprocess.Popen(["/usr/bin/eos", eos_mgm_url, "ls", path], stdout=subprocess.PIPE)
        (out, _) = p.communicate();
        ret = p.returncode
        #If ret!=0, path do not exist. Cannot preload 
        if ret==0:
            _preloaded[0] = path
            _preloaded[1] = out.splitlines()
            _preloadTime = datetime.datetime.now()
        else:
            _preloaded[0] = path
            _preloaded[1] = []
            _preloadTime = datetime.datetime.now()
    else:
        #Don't preload
        #Check if path already preloaded and if preloaded information has not expired (1 min time)
        if os.path.dirname(path)==_preloaded[0] and (datetime.datetime.now()-_preloadTime)<datetime.timedelta(minutes=1):
            #It is preloaded and not expired
            ret = (os.path.basename(path) in _preloaded[1])
            return ret
        else:
            #Path has not been preloaded or is expired. Check normally
            #ret = subprocess.call(["/usr/bin/eos", "root://eosuser.cern.ch/", "ls", path])
            ret = subprocess.call(["/usr/bin/eos", eos_mgm_url, "ls", path])
    return ret==0

def mkDir(path):
    if not exists(path, False):
        return subprocess.call(["/usr/bin/eos", getMGMUrl(path), "mkdir", path])

def rmTree(path):
    pass

