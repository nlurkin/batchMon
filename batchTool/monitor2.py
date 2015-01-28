'''
Created on 16 May 2014

@author: Nicolas Lurkin
'''
from . import ConfigBatch
from util import printDebug
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
        #Signal a submit is ongoing (block other submit threads to start for the same batch) 
        self.submitting = True
        
        #Check if the monitor itself has some jobs to re-generate (submitList != 0)
        if len(self.submitList)==0:
            #No personal jobs to create
            #Gather all jobs from the config that have never been generated (attempts=-1)
            subList = [job for job in self.config.jobsList if job.attempts==-1]
        else:
            #Some jobs to resubmit, we only have their index. Get them from the config
            subList = [self.config.jobsList[i] for i in self.submitList]
            #Free the submitList for further jobs  
            self.submitList = []
        for job in subList:
            yield job
        
        #Notify that we are not submitting anymore. New threads are free to restart submitting if needed. 
        self.submitReady = False
        self.submitting = False
    
    def reSubmitFailed(self):
        printDebug(3, "Monitor resubmitting failed jobs")
        #Request config to reset the attempts and notify that jobs are ready
        self.config.resetFailed()
        self.submitReady = True
    
    def monitor(self):
        #Check that we are not already checking in a different thread
        if not self.currentlyChecking:
            #Notify others that a monitor procedure is ongoing.
            self.currentlyChecking = True
            #Check final job or regular jobs?
            if not self.checkFinalize():
                self.monitorNormal()
            else:
                self.monitorFinal()
            self.currentlyChecking = False
    
    def monitorNormal(self):
        
        #Run the bjobs command and get the output
        cmd = ["bjobs -a"]
        subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (monOutput, _) = subCmd.communicate()
            
        #Read output (one job per line) and parse it to identify the job and get its status
        for line in monOutput.splitlines():
            m = re.search("([0-9]+) [a-zA-Z]+ (RUN|PEND|DONE|EXIT) .*", line)
            if m:
                #Update job in config. Might not exist, we don't care.
                redo,index = self.config.updateJob(m.group(1), {"status":m.group(2)}, self.keepOutput)
                if redo:
                    #Job has exited and config considers that the job can be resubmitted
                    self.reSubmit.append(index)
        
        #If we are not currently submitting and we have jobs to resubmit, add them to the
        # submitList and notify that jobs are ready.
        if self.submitting == False and len(self.reSubmit)>0:
            self.submitReady = True
            self.submitList.extend(self.reSubmit[:])
            self.reSubmit = []
    
    def submitInit(self):
        printDebug(3, "Monitor initial submit")
        self.config.enableNew()
        self.submitReady = True
    
    def checkFinalize(self):
        #Submit final job if everything else is over
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
        #Monitor final job
        cmd = ["bjobs -a"]
        subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        (monOutput, _) = subCmd.communicate()
    
        for line in monOutput.splitlines():
            m = re.search("([0-9]+) [a-zA-Z]+ (RUN|PEND|DONE|EXIT) .*", line)
            if m:
                self.config.updateFinalJob({"jobID":m.group(1), "status":m.group(2)})
        
    def invertKeepOutput(self):
        self.keepOutput = not self.keepOutput
        
