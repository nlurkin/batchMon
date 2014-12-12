'''
Created on 12 Dec 2014

@author: Nicoas
'''
import os


class FSSelector(object):
    '''
    FS interface. Will select the correct FS API based on the path
    '''
    
    def __init__(self, params):
        pass

    def isFile(self):
        pass
    
    def isDirectory(self):
        pass
    
    def exists(self, path):
        if "/eos/" in path:
            pass
        else:
            LinuxFS.exists(self, path) 
    
    def mkDir(self, path):
        if "/eos/" in path:
            pass
        else:
            LinuxFS.mkDir(self, path) 

    
    def rmTree(self, path):
        pass
        
class LinuxFS(object):
    '''
    Class to manipulate Linux FS
    '''


    def __init__(self, params):
        '''
        Constructor
        '''
    
    def isFile(self):
        pass
    
    def isDirectory(self):
        pass
    
    def exists(self, path):
        os.path.exists(path)
    
    def mkDir(self, path):
        os.mkdir(path)
    
    def rmTree(self, path):
        pass
    
