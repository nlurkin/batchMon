'''
Created on 16 May 2014

@author: Nicolas Lurkin
'''
from . import ConfigBatch, printDebug
import re
import subprocess
import threading

class subCommand(threading.Thread):
    '''
    SubCommand class. Executes a subprocess in a thread to allow for timeout.
    If the command does not return within the allowed time, the thread is 
    terminated (and the subprocess with it).
    '''
    def __init__(self, cmd, cmdInput, timeout):
        threading.Thread.__init__(self)
        self.cmd = cmd
        self.cmdInput = cmdInput
        self.timeout = timeout
        self.subOutput = None
    
    def run(self):
        '''
        Overloaded from thread. Entry point of the Thread.
        '''
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
        (self.subOutput, _) = self.p.communicate(self.cmdInput)
    
    def Run(self):
        '''
        Entry point of the class
        '''
        self.start()
        self.join(self.timeout)

        if self.is_alive():
            self.p.terminate()
            self.join()
        
        return self.subOutput


class Monitor2:
    '''
    Main class for monitoring jobs
    '''

    def __init__(self, keep):
        '''
        Constructor
        '''
        self.submitList = []
        self.reSubmit = []
        self.keepOutput = keep
        self.config = ConfigBatch()
        self.submitReady = False
        self.keepOutput = False
        self.submitting = False
        self.currentlyChecking = False
    
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
    
    def submit(self, job):
        printDebug(3, "Monitor submitting job")
        cmd = ["bsub -q " + self.config.queue]
        if self.config.requirement:
            cmd[0] = cmd[0] + " -R \"" + self.config.requirement + "\""

        subOutput = subCommand(cmd, job.script, 10).Run()
        
        if subOutput==None:
            return

        m = re.search("Job <([0-9]+)> .*? <(.+?)>.*", subOutput)
        if m:
            job.jobID = m.group(1)
            job.queue = m.group(2)
            job.attempts += 1
            self.config.updateCorrespondance(job.jobID, job.jobSeq)
    
    def generateJobs(self):
        printDebug(3, "Monitor generating jobs")
        self.submitting = True
        if len(self.submitList)==0:
            subList = [job for job in self.config.jobsList if job.attempts==-1]
        else:
            subList = [self.config.jobsList[i] for i in self.submitList]
        for job in subList:
            yield job
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
        cmd = ["bjobs -a"]
        subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (monOutput, _) = subCmd.communicate()
            
        for line in monOutput.splitlines():
            m = re.search("([0-9]+) [a-zA-Z]+ (RUN|PEND|DONE|EXIT) .*", line)
            if m:
                redo,index = self.config.updateJob(m.group(1), {"status":m.group(2)}, self.keepOutput)
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
        
