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

def exists(path, preload):
    global _preloaded
    global _preloadTime
    path = os.path.abspath(path)
    #Preload if requested
    if preload:
        p = subprocess.Popen(["/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select", "ls", path], stdout=subprocess.PIPE)
        (out, _) = p.communicate();
        ret = p.returncode
        #If ret!=0, path do not exist. Cannot preload 
        if ret==0:
            _preloaded[0] = path
            _preloaded[1] = out.splitlines()
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
            ret = subprocess.call(["/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select", "ls", path])
    return ret==0

def mkDir(path):
    if not exists(path):
        return subprocess.call(["/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select", "mkdir", path])

def rmTree(path):
    pass

