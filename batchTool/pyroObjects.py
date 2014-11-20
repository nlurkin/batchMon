'''
Created on Sep 30, 2014

@author: ncl
'''

import curses
import threading

import Pyro4

from . import Monitor2, Display2
import time

stopAll = False
class JobServer:
    '''
    xxx
    '''
    
    def __init__(self):
        self.listBatch = {}
        self.mutex = threading.Lock()
    
    def addBatch(self, cardFile, name, queue, test, keep):
        print "adding new batch"
        if name in self.listBatch:
            #error
            return
        batch = Monitor2(keep)
        batch.newBatch(cardFile, name, queue, test)
        self.listBatch[name] = {"monitor":batch, "clients":[]}
        
    def removeBatch(self, name):
        print "removing batch"
        if name in self.listBatch:
            del self.listBatch[name]
            
    def registerClient(self, name, clientUri):
        print "registering new client"
        if name in self.listBatch:
            self.mutex.acquire()
            client = Pyro4.Proxy(clientUri)
            self.listBatch[name]["clients"].append(client)
            header = self.listBatch[name]["monitor"].config.getHeaders()
            header['keep'] = self.listBatch[name]["monitor"].keepOutput
            self.mutex.release()
            return self.listBatch[name]["monitor"].config.startTime, header, len(self.listBatch[name]["monitor"].config.jobsList)
    
    def disconnectClient(self, name, clientUri):
        print "disconnecting client"
        if name in self.listBatch:
            self.mutex.acquire()
            for client in self.listBatch[name]["clients"]:
                if client._pyroUri == clientUri:
                    client._pyroRelease()
                    self.listBatch[name]["clients"].remove(client)
            self.mutex.release()
    
    def disconnectAllClients(self):
        print "Disconnecting all clients"
        for _,batch in self.listBatch.iteritems():
            for client in batch["clients"]:
                client._pyroRelease()
                batch["clients"].remove(client)
        
    def getBatchList(self):
        print "Sending batch list"
        l = []
        for name,_ in self.listBatch.iteritems():
            l.append(name)
        return l
    
    def submitInit(self, name):
        print "Init submiting batch"
        if name in self.listBatch:
            self.listBatch[name]["monitor"].submitInit()
    
    def resubmitFailed(self, name):
        print "resubmiting failed batch"
        if name in self.listBatch:
            self.listBatch[name]["monitor"].reSubmitFailed()
    
    def invertKeepOutput(self, name):
        print "Invert keep output"
        if name in self.listBatch:
            self.listBatch[name]["monitor"].invertKeepOutput()
            header = self.listBatch[name]["monitor"].config.getHeaders()
            header['keep'] = self.listBatch[name]["monitor"].keepOutput
            return header
    
    def mainLoop(self):
        for _,batch in self.listBatch.items():
            batch["monitor"].monitor()
            
            for clients in batch["clients"]:
                clients.displaySummary(batch["monitor"].config.getStatusStats())
                
            if batch["monitor"].submitReady and batch["monitor"].submitting==False:
                if len(batch["monitor"].submitList)==0:
                    for clients in batch["clients"]:
                        clients.resetSubmit(batch["monitor"].config.getJobsNumberReady())
                else:
                    for clients in batch["clients"]:
                        clients.resetSubmit(len(batch["monitor"].submitList))
                t = threading.Thread(target=self.submitLoop, args=(batch,))
                t.daemon = True
                t.start()
                #self.submitLoop(batch)

    def submitLoop(self, batch):
        try:
            batch["monitor"].submitting = False
            for job in batch["monitor"].generateJobs():
                        print "submitting"
                        batch["monitor"].submit(job)
                        print len(batch["clients"])
                        if self.mutex.acquire():
                            time.sleep(5)
                            for clients in batch["clients"]:
                                print "clients display"
                                print clients
                                clients.displayJobSent(job.jobID, job.index)
                                print "end display"
                            self.mutex.release()
        except Exception:
            print "".join(Pyro4.util.getPyroTraceback())
        
    def stop(self):
        global stopAll
        print "Stopping server"
        stopAll = True
#        raise KeyboardInterrupt

class DisplayClient(object):
    """
    xxx
    """    
    def __init__(self, scr):
        self.startTime = None
        self.screen = Display2()
        self.screen.setScreen(scr)
        self.batchList = []
        self.batchName = ""
    
    def setStartTime(self, time):
        self.startTime = time
    
    def updateStartTime(self):
        self.screen.displayTime(self.startTime)
    
    def displayJobSent(self, jobId, jobIndex):
        self.screen.displaySubmit(jobId, jobIndex)
    
    def displaySummary(self, stats):
        self.screen.displaySummary(stats)
    
    def resetSubmit(self, number):
        self.screen.resetSubmit(number)
    
    def mainLoop(self):
        if self.batchName != "":
            self.updateStartTime()
        self.screen.repaint()
        k = self.screen.getch()
        if k != -1:
            if curses.unctrl(k) == "K":
                return -101, ""
            if self.screen.displayList:
                if k == curses.KEY_DOWN:
                    self.screen.batchList.goDown()
                elif k == curses.KEY_UP:
                    self.screen.batchList.goUp()
                elif k == curses.KEY_RIGHT:
                    return +1,self.selectBatch(self.screen.batchList.currentCursor)
                elif k == curses.KEY_DC:
                    return -100, self.deleteBatch(self.screen.batchList.currentCursor)
            else:
                if k == curses.KEY_LEFT:
                    return -1, self.disconnectBatch()
                elif curses.unctrl(k) == "^R":
                    return +100, self.batchName
                elif curses.unctrl(k) == "^G":
                    return +101, self.batchName
                elif curses.unctrl(k) == "^K":
                    return +102, self.batchName
                 
                
        
        return 0,""
    
    def deleteBatch(self, index):
        if(index>=len(self.batchList)):
            return None
        return self.batchList[index]
    
    def selectBatch(self, index):
        if(index>=len(self.batchList)):
            return None
        self.screen.reset()
        self.batchName = self.batchList[index]
        return self.batchName
    
    def disconnectBatch(self):
        self.screen.reset()
        batch = self.batchName
        self.batchName = ""
        return batch
    
    def displayHeader(self, headers):
        if headers!=None:
            self.screen.displayHeader(headers)
    
    def displayBatchList(self, l):
        self.batchList = l[:]
        self.screen.displayBatchList(l)
    
    def getName(self):
        return self.batchName
    
    def setTotalJobs(self, total):
        self.screen.submitTotal = total