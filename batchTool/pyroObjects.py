'''
Created on Sep 30, 2014

@author: ncl
'''

import threading

import Pyro4

from . import Monitor2, Display2
from util import printDebug
from batchTool.display2 import DCommands, DObject
from batchTool.lsfMonitor import getLSFMonitorInstance

stopAll = False
class JobServer:
    '''
    Jobserver. Pyro object connected by the client.
    '''
    
    def __init__(self):
        self.listBatch = {}
        self.mutex = threading.Lock()
    
    #==================
    # Called by client
    #==================
    def addBatch(self, cardFile, name, queue, test, keep, limit):
        printDebug(3, "Adding new batch %s" % name)
        if name in self.listBatch:
            printDebug(2, "Batch %s already exists" % name)
            return
        batch = Monitor2(keep, limit)
        batch.newBatch(cardFile, name, queue, test)
        self.listBatch[name] = {"monitor":batch, "clients":[]}
    
    def loadBatch(self, jsonFile, name, keep, limit):
        printDebug(3, "Loading new batch %s from %s" % (name, jsonFile))
        if name in self.listBatch:
            printDebug(2, "Batch %s already exists" % name)
            return
        batch = Monitor2(keep, limit)
        batch.loadBatch(str(jsonFile))
        self.listBatch[name] = {"monitor":batch, "clients":[]}
        
    def removeBatch(self, name):
        printDebug(3, "Removing batch %s" % name)
        t = threading.Thread(target=self.doRemove, args=(name,))
        t.setName(name)
        t.daemon = True
        t.start()
        
    def doRemove(self, name):
        if name in self.listBatch:
            if self.listBatch[name]['monitor'].activeJobs>0:
                self.listBatch[name]['monitor'].deleteJobs()
            del self.listBatch[name]
            
    def registerClient(self, name, clientUri):
        printDebug(3, "Registering client %s for %s" % (clientUri, name))
        if name in self.listBatch:
            #List of clients can be manipulated only by one thread at a time
            self.mutex.acquire()
            client = Pyro4.Proxy(clientUri)
            #Set the timeout for the calls. Client might not be running anymore and cannot block server indefinitely. 
            client._pyroTimeout = 1
            
            self.listBatch[name]["clients"].append(client)
            
            #Get the basic info about the batch and return them to the client
            header = self.listBatch[name]["monitor"].config.getHeaders()
            header['keep'] = self.listBatch[name]["monitor"].keepOutput
            self.mutex.release()
            return self.listBatch[name]["monitor"].config.startTime, header, len(self.listBatch[name]["monitor"].config.jobsList), self.listBatch[name]["monitor"].config.getStatusStats()
    
    def disconnectClient(self, name, clientUri):
        printDebug(3, "Disconnecting client %s for %s" % (clientUri, name))
        if name in self.listBatch:
            #list of clients can be manipulated by one thread at a time
            self.mutex.acquire()
            for client in self.listBatch[name]["clients"]:
                if client._pyroUri == clientUri:
                    client._pyroRelease()
                    self.listBatch[name]["clients"].remove(client)
            self.mutex.release()
    
    def getBatchList(self):
        printDebug(3, "Sending batch list")
        l = []
        orderedNames = sorted(self.listBatch.keys())
        for name in orderedNames:
            l.append({'name':name, 'stats':self.listBatch[name]["monitor"].config.getStatusStats()})
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
    
    def stop(self):
        global stopAll
        printDebug(3, "Stopping server")
        stopAll = True

    #=======================
    # Called by server main
    #=======================
    
    def disconnectAllClients(self):
        printDebug(3, "Disconnecting all clients")
        for _,batch in self.listBatch.iteritems():
            #list of clients can be manipulated by one thread at a time
            self.mutex.acquire()
            for client in batch["clients"]:
                client._pyroRelease()
                batch["clients"].remove(client)
            self.mutex.release()
        
    def mainLoop(self):
        #Start monitor function for each batch in its own thread because can be very slow and block the server
        tMon = threading.Thread(target=getLSFMonitorInstance().refreshInfo)
        tMon.daemon = True
        tMon.start()
        
        for name,batch in self.listBatch.items():
            
            #Update info for each monitor
            batch["monitor"].monitor()
            
            #Send summary to all clients
            for clients in batch["clients"]:
                clients.displaySummary(batch["monitor"].config.getStatusStats())
            
            #We some jobs ready and we are not submitting 
            if batch["monitor"].submitReady and batch["monitor"].submitting==False:
                
                #Reset either the jobs that are ready if the monitor does not have its own jobs or the monitor's jobs
                if len(batch["monitor"].submitList)==0:
                    for clients in batch["clients"]:
                        clients.resetSubmit(batch["monitor"].config.getJobsNumberReady())
                else:
                    for clients in batch["clients"]:
                        clients.resetSubmit(len(batch["monitor"].submitList))
                
                #Start the submit loop in its own thread because can take a very long time again.
                t = threading.Thread(target=self.submitLoopArrayed, args=(batch,))
                t.setName(name)
                t.daemon = True
                t.start()

    def submitLoopArrayed(self, batch):
        cThread = threading.currentThread()
        printDebug(3, "["+cThread.name+"] Enter submit loop")
        try:
            #Reset submit flag
            batch["monitor"].submitting = False
            printDebug(3, "["+cThread.name+"] Number of jobs in Ready state: " + str(batch["monitor"].config.getJobsNumberReady()))
            
            #Go through all the jobs that are ready and submit them
            jList = [];
            for i, job in enumerate(batch["monitor"].generateJobs()):
                        printDebug(3, "["+cThread.name+"] Generate job " + str(i))
                        jList.append(job)
            
            lsfID,index = batch["monitor"].submit(jList)
            printDebug(3, "["+cThread.name+"] acquire mutex")
                        
            #Notify the clients that the job was submitted
            if self.mutex.acquire():
                try:
                    for clients in batch["clients"]:
                        clients.displayJobSent(lsfID, index, len(jList)-1)
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
        self.lastIndex = -1
    
        self.screen.activateMainWindow()

    #==================
    # Called by server
    #==================
    def displayJobSent(self, jobId, jobIndex, currentID):
        self.screen.updateContent(DObject(jobSubmit=True, jobID=jobId, jobIndex=jobIndex, currentID=currentID))
    
    def displaySummary(self, stats):
        self.screen.updateContent(DObject(jobStats=stats))
    
    def resetSubmit(self, number):
        self.screen.resetSubmit(number)    
    
    #=======================
    # Called by client main
    #=======================
    
    def setStartTime(self, time):
        self.startTime = time
    
    def updateStartTime(self):
        self.screen.updateContent(DObject(startTime=self.startTime))
    
    def deleteBatch(self, index):
        if(index>=len(self.batchList)):
            return None
        self.lastIndex = index
        return self.batchList[index]['name']
    
    def selectBatch(self, index):
        if(index>=len(self.batchList)):
            return None
        self.lastIndex = index
        self.batchName = self.batchList[index]['name']
        return self.batchName
    
    def disconnectBatch(self):
        batch = self.batchName
        self.batchName = ""
        return batch
    
    def displayHeader(self, headers):
        if headers!=None:
            self.screen.updateContent(DObject(jobHeader=headers))
    
    def displayBatchList(self, l, index=None):
        self.batchList = l[:]
        self.screen.activateMainWindow()
        self.screen.updateContent(DObject(batchList=l, lastIndex=self.lastIndex))
    
    def getName(self):
        return self.batchName
    
    def setTotalJobs(self, total):
        self.screen.submitTotal = total

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
                    self.lastIndex = retCmd.index
                    retCmd.name = self.batchName
                elif retCmd.command == DCommands.Resubmit:
                    retCmd.name = self.batchName
                elif retCmd.command == DCommands.Submit:
                    retCmd.name = self.batchName
                elif retCmd.command == DCommands.Switch:
                    retCmd.name = self.batchName
        else:
            retCmd = DCommands(DCommands.NoCMD)
            
        return retCmd
