'''
Created on 16 May 2014

@author: Nicolas Lurkin
'''
from . import ConfigBatch
import re
import subprocess

class Monitor2:
    '''
    Main class for monitoring jobs
    '''

    def __init__(self, keep):
        '''
        Constructor
        '''
        self.submitList = []
        self.keepOutput = keep
        self.config = ConfigBatch()
        self.submitReady = False
        self.keepOutput = False
        self.submitting = False
    
    def newBatch(self, cfgFile, batchName, queue, test):
        self.config.initCardFile(cfgFile, batchName, queue, test)
        self.submitReady = True
    
    def submit(self, job):
        cmd = ["bsub -q " + self.config.queue]
        if self.config.requirement:
            cmd[0] = cmd[0] + " -R \"" + self.config.requirement + "\""
        subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        (subOutput, _) = subCmd.communicate(job.script)
        #f = open("simSubmit", "r")
        #subOutput = f.read()
        #f.close()
        
        m = re.search("Job <([0-9]+)> .*? <(.+?)>.*", subOutput)
        if m:
            job.jobID = m.group(1)
            job.queue = m.group(2)
            job.attempts += 1
            self.config.updateCorrespondance(job.jobID, job.jobSeq)
    
    def generateJobs(self):
        self.submitting = True
        if len(self.submitList)==0:
            subList = [job for job in self.config.jobsList if job.attempts==-1]
        else:
            subList = [self.config.jobsList[i] for i in self.submitList]
        for job in subList:
            yield job
        self.submitList = []
        self.submitReady = False
    
    def reSubmitFailed(self):
        self.config.resetFailed()
        self.submitReady = True
    
    def monitor(self):
        if not self.checkFinalize():
            self.monitorNormal()
        else:
            self.monitorFinal()
    
    def monitorNormal(self):
        cmd = ["bjobs -a"]
        subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (monOutput, _) = subCmd.communicate()
        #f = open("simReq", "r")
        #monOutput = f.read()
        #f.close()
    
        reSubmit = []
        for line in monOutput.splitlines():
            m = re.search("([0-9]+) [a-zA-Z]+ (RUN|PEND|DONE|EXIT) .*", line)
            if m:
                redo,index = self.config.updateJob(m.group(1), {"status":m.group(2)}, self.keepOutput)
                if redo:
                    reSubmit.append(index)
        
        if len(reSubmit)>0:
            self.submitReady = True
            self.submitList += reSubmit
    
    def submitInit(self):
        self.config.enableNew()
        self.submitReady = True
    
    def checkFinalize(self):
        if self.config.finalizeStage==0:
            if self.config.finalJob==None:
                self.config.finalizeStage=2
                return True
            
            cmd = ["bsub -q " + self.config.queue]
            if self.config.requirement:
                cmd[0] = cmd[0] + " -R \"" + self.config.requirement + "\""
            subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
            (subOutput, _) = subCmd.communicate(self.config.finalJob.script)
            
            m = re.search("Job <([0-9]+)> .*? <(.+?)>.*", subOutput)
            if m:
                self.config.updateFinalJob({"jobID":m.group(1),"queue":m.group(2)})
        
        return self.config.finalizeStage>=0
    
    def monitorFinal(self):
        cmd = ["bjobs -a"]
        subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (monOutput, _) = subCmd.communicate()
    
        for line in monOutput.splitlines():
            m = re.search("([0-9]+) [a-zA-Z]+ (RUN|PEND|DONE|EXIT) .*", line)
            if m:
                self.config.updateFinalJob({"jobID":m.group(1), "status":m.group(2)})
        
    def invertKeepOutput(self):
        self.keepOutput = not self.keepOutput
        
