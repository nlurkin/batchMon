'''
Created on 16 May 2014

@author: Nicolas Lurkin
'''
from . import ConfigBatch
from util import printDebug
import re
#from batchTool.lsfMonitor import getLSFMonitorInstance
from batchTool.htcondorMonitor import getHTCondorMonitorInstance
import subprocess

class Monitor2:
    '''
    Main class for monitoring jobs
    '''

    def __init__(self, keep, limit):
        '''
        Constructor
        '''
        self.submitList = []
        self.reSubmit = []
        self.keepOutput = keep
        self.jobsLimit = int(limit)
        self.config = ConfigBatch()
        self.submitReady = False
        self.keepOutput = False
        self.submitting = False
        self.currentlyChecking = False
        self.activeJobs = 0
    
    def newBatch(self, cfgFile, batchName, queue, test):
        printDebug(3, "Monitor creating new batch")
        self.config.initCardFile(cfgFile, batchName, queue, test)
        self.submitReady = False

    def loadBatch(self, jsonFile):
        printDebug(3, "Monitor loading new batch")
        self.config.load(jsonFile)
        self.submitReady = False
    
    def saveBatch(self, jsonFile):
        printDebug(3, "Saving batch")
        self.config.save(jsonFile)
    
    def submit(self, jobs):
        printDebug(3, "Monitor submitting jobs")
        return getHTCondorMonitorInstance().submitJob(jobs, self.config)
    
    def generateJobs(self):
        printDebug(3, "Monitor generating jobs")
        self.submitting = True
        if len(self.submitList)==0:
            subList = [job for job in self.config.jobsList if job.attempts==-1]
        else:
            subList = [self.config.jobsList[i] for i in self.submitList]
        for job in subList:
            yield job
            self.activeJobs+=1
            if self.jobsLimit>0 and self.activeJobs>=self.jobsLimit:
                break
        self.submitList = []
        self.submitReady = False
        self.submitting = False
    
    def reSubmitFailed(self):
        printDebug(3, "Monitor resubmitting failed jobs")
        self.config.resetFailed()
        self.submitReady = True
    
    def monitor(self):
        if not self.currentlyChecking:
            self.currentlyChecking = True
            if not self.checkFinalize():
                self.monitorNormal()
            else:
                self.monitorFinal()
            self.currentlyChecking = False
    
    def monitorNormal(self):
        self.activeJobs = 0
        for key in self.config.jobCorrespondance.iterLayer1():
            jobInfo = getHTCondorMonitorInstance().getInfoByJobID(key)
            if not jobInfo is None:
                for jobKey, job in jobInfo.iteritems():
                    if job.lsfStatus=="R" or job.lsfStatus=="I":
                        self.activeJobs += 1
                    redo,index = self.config.updateJob((job.lsfID,jobKey), {"status":job.lsfStatus}, self.keepOutput)
                    if redo:
                        self.reSubmit.append(index)
            
        if self.submitting == False and len(self.reSubmit)>0:
            self.submitReady = True
            self.submitList.extend(self.reSubmit[:])
            self.reSubmit = []
    
    def submitInit(self):
        printDebug(3, "Monitor initial submit")
        self.config.enableNew()
        self.submitReady = True
    
    def deleteJobs(self):
        printDebug(3, "Delete jobs " + self.config.name)
        getHTCondorMonitorInstance().deleteJobs(self.config.getAllClusterIDs())
        
    #def checkFinalize(self):
    #    if self.config.finalizeStage==0:
    #        if self.config.finalJob==None:
    #            self.config.finalizeStage=2
    #            return True
    #        
    #        cmd = ["bsub -q " + self.config.queue]
    #        if self.config.requirement:
    #            cmd[0] = cmd[0] + " -R \"" + self.config.requirement + "\""
    #        subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
    #        (subOutput, _) = subCmd.communicate(self.config.finalJob.script)
    #        
    #        m = re.search("Job <([0-9]+)> .*? <(.+?)>.*", subOutput)
    #        if m:
    #            self.config.updateFinalJob({"jobID":m.group(1),"queue":m.group(2)})
    #    
    #    return self.config.finalizeStage>=0
    #
    #def monitorFinal(self):
    #    cmd = ["bjobs -a"]
    #    subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    #    (monOutput, _) = subCmd.communicate()
    #
    #    for line in monOutput.splitlines():
    #        m = re.search("([0-9]+) [a-zA-Z]+ (RUN|PEND|DONE|EXIT) .*", line)
    #        if m:
    #            self.config.updateFinalJob({"jobID":m.group(1), "status":m.group(2)})
        
    def invertKeepOutput(self):
        self.keepOutput = not self.keepOutput
        
