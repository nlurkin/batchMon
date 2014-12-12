'''
Created on 12 Dec 2014

@author: Nicolas

Class to manipulate Linux FS
'''
import os
import subprocess

def isFile():
    pass

def isDirectory():
    pass

def exists(path):
    ret = subprocess.call(["/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select", "ls", path])
    return ret==0

def mkDir(path):
    if not exists(path):
        return subprocess.call(["/afs/cern.ch/project/eos/installation/0.3.15/bin/eos.select", "mkdir", path])

def rmTree(path):
    pass

