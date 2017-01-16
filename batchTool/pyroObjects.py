'''
Created on Sep 30, 2014

@author: ncl
'''

import curses
import threading

import Pyro4

from . import Monitor2, Display2
from util import printDebug
from batchTool.display2 import DCommands

stopAll = False
class JobServer:
    '''
    Jobserver. Pyro object connected by the client.
    '''
    
    def __init__(self):
        self.listBatch = {}
        self.mutex = threading.Lock()
    
    def addBatch(self, cardFile, name, queue, test, keep):
        printDebug(3, "Adding new batch %s" % name)
        if name in self.listBatch:
            printDebug(2, "Batch %s already exists" % name)
            return
        batch = Monitor2(keep)
        batch.newBatch(cardFile, name, queue, test)
        self.listBatch[name] = {"monitor":batch, "clients":[]}
    
    def loadBatch(self, jsonFile, name, keep):
        printDebug(3, "Loading new batch %s from %s" % (name, jsonFile))
        if name in self.listBatch:
            printDebug(2, "Batch %s already exists" % name)
            return
        batch = Monitor2(keep)
        batch.loadBatch(jsonFile)
        self.listBatch[name] = {"monitor":batch, "clients":[]}
        
    def removeBatch(self, name):
        printDebug(3, "Removing batch %s" % name)
        if name in self.listBatch:
            del self.listBatch[name]
            
    def registerClient(self, name, clientUri):
        printDebug(3, "Registering client %s for %s" % (clientUri, name))
        if name in self.listBatch:
            self.mutex.acquire()
            client = Pyro4.Proxy(clientUri)
            client._pyroTimeout = 5
            self.listBatch[name]["clients"].append(client)
            header = self.listBatch[name]["monitor"].config.getHeaders()
            header['keep'] = self.listBatch[name]["monitor"].keepOutput
            self.mutex.release()
            return self.listBatch[name]["monitor"].config.startTime, header, len(self.listBatch[name]["monitor"].config.jobsList), self.listBatch[name]["monitor"].config.getStatusStats()
    
    def disconnectClient(self, name, clientUri):
        printDebug(3, "Disconnecting client %s for %s" % (clientUri, name))
        if name in self.listBatch:
            self.mutex.acquire()
            for client in self.listBatch[name]["clients"]:
                if client._pyroUri == clientUri:
                    client._pyroRelease()
                    self.listBatch[name]["clients"].remove(client)
            self.mutex.release()
    
    def disconnectAllClients(self):
        printDebug(3, "Disconnecting all clients")
        for _,batch in self.listBatch.iteritems():
            for client in batch["clients"]:
                client._pyroRelease()
                batch["clients"].remove(client)
        
    def getBatchList(self):
        printDebug(3, "Sending batch list")
        l = []
        for name,_ in self.listBatch.iteritems():
            l.append(name)
        return l
    
    def submitInit(self, name):
        printDebug(3, "Initial submit for batch %s" % name)
        if name in self.listBatch:
            self.listBatch[name]["monitor"].submitInit()
    
    def resubmitFailed(self, name):
        printDebug(3, "Resubmiting failed jobs for batch %s" % name)
        if name in self.listBatch:
            self.listBatch[name]["monitor"].reSubmitFailed()
    
    def invertKeepOutput(self, name):
        printDebug(3, "Invert keep output for batch %s" % name)
        if name in self.listBatch:
            self.listBatch[name]["monitor"].invertKeepOutput()
            header = self.listBatch[name]["monitor"].config.getHeaders()
            header['keep'] = self.listBatch[name]["monitor"].keepOutput
            return header
    
    def mainLoop(self):
        for name,batch in self.listBatch.items():
            tMon = threading.Thread(target=batch["monitor"].monitor)
            tMon.daemon = True
            tMon.start()
            
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
                t.setName(name)
                t.daemon = True
                t.start()

    def submitLoop(self, batch):
        cThread = threading.currentThread()
        printDebug(3, "["+cThread.name+"] Enter submit loop")
        try:
            batch["monitor"].submitting = False
            printDebug(3, "["+cThread.name+"] Number of jobs in Ready state: " + str(batch["monitor"].config.getJobsNumberReady()))
            for i, job in enumerate(batch["monitor"].generateJobs()):
                        printDebug(3, "["+cThread.name+"] Generate job " + str(i))
                        batch["monitor"].submit(job)
                        printDebug(3, "["+cThread.name+"] acquire mutex")
                        if self.mutex.acquire():
                            try:
                                for clients in batch["clients"]:
                                    clients.displayJobSent(job.jobID, job.index, i)
                            except Exception:
                                printDebug(1, "["+cThread.name+"] Exception:")
                                printDebug(1, "".join(Pyro4.util.getPyroTraceback()))
                            finally:
                                printDebug(3, "["+cThread.name+"] release mutex")
                                self.mutex.release()
        except Exception:
            printDebug(1, "["+cThread.name+"] Exception")
            printDebug(1, "".join(Pyro4.util.getPyroTraceback()))
    
    def saveAllBatches(self):
        for name,b in self.listBatch.items():
            b['monitor'].saveBatch("%s.json" % name)
            
    def stop(self):
        global stopAll
        printDebug(3, "Stopping server")
        stopAll = True
        
    def kill(self):
        printDebug(3, "Killing server properly")
        self.disconnectAllClients()
        self.saveAllBatches()
        

class DisplayClient(object):
    """
    Display client. Pyro object connected by the server.
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
        self.screen.updateJobTime(self.startTime)
    
    def displayJobSent(self, jobId, jobIndex, currentID):
        self.screen.displaySubmit(jobId, jobIndex, currentID)
    
    def displaySummary(self, stats):
        self.screen.updateJobSummary(stats)
    
    def resetSubmit(self, number):
        self.screen.resetSubmit(number)
    
    def mainLoop(self):
        if self.batchName != "":
            self.updateStartTime()
        self.screen.repaint()
        k = self.screen.getch()
        if k != -1:
            retCmd = self.screen.keyPressed(k)
            if retCmd is None:
                retCmd = DCommands(DCommands.NoCMD)
            else:
                if retCmd.command == DCommands.Select:
                    retCmd.name = self.selectBatch(retCmd.index)
                elif retCmd.command == DCommands.Kill:
                    retCmd.name = self.disconnectBatch()
                elif retCmd.command == DCommands.Delete:
                    retCmd.name = self.deleteBatch(retCmd.index)
                elif retCmd.command == DCommands.Back:
                    retCmd.name = self.disconnectBatch()
                elif retCmd.command == DCommands.Refresh:
                    retCmd.name = self.batchName
                elif retCmd.command == DCommands.Submit:
                    retCmd.name = self.batchName
                elif retCmd.command == DCommands.Switch:
                    retCmd.name = self.batchName
        else:
            retCmd = DCommands(DCommands.NoCMD)
            
        return retCmd
    
    def deleteBatch(self, index):
        if(index>=len(self.batchList)):
            return None
        return self.batchList[index]
    
    def selectBatch(self, index):
        if(index>=len(self.batchList)):
            return None
        self.batchName = self.batchList[index]
        return self.batchName
    
    def disconnectBatch(self):
        batch = self.batchName
        self.batchName = ""
        return batch
    
    def displayHeader(self, headers):
        if headers!=None:
            self.screen.updateJobHeader(headers)
    
    def displayBatchList(self, l):
        self.batchList = l[:]
        self.screen.displayBatchList(l)
    
    def getName(self):
        return self.batchName
    
    def setTotalJobs(self, total):
        self.screen.submitTotal = total
