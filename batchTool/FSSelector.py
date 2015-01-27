'''
Created on 12 Dec 2014

@author: Nicolas

FS interface. Will select the correct FS API based on the path
'''
import LinuxFS
import EOSFS

def isFile():
    pass

def isDirectory():
    pass

def exists(path, preload=False):
    if "/eos/" in path:
        return EOSFS.exists(path, preload)
    else:
        return LinuxFS.exists(path) 

def mkDir(path):
    if "/eos/" in path:
        return EOSFS.mkDir(path)
    else:
        return LinuxFS.mkDir(path)

def rmTree(path):
    pass
