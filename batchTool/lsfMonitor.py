'''
Created on 17 Jan 2017

@author: ncl
'''
import re
from util import subCommand, TwoLayerDict

lsfMonitorInstance = None

def getLSFMonitorInstance():
    global lsfMonitorInstance
    if lsfMonitorInstance is None:
        lsfMonitorInstance = LSFMonitor()
    return lsfMonitorInstance

    
def formatArray(idList):
    startRun = -1
    currRun = -1
    
    listRuns = []
    idList.sort()
    for arrId in idList:
        if startRun==-1:
            startRun = arrId
            currRun = arrId
            continue
        if arrId == currRun+1:
            currRun = arrId
        else:
            if startRun==arrId:
                listRuns.append("%i" % (startRun+1))
            else:
                listRuns.append("%i-%i" % (startRun+1, arrId+1))
            startRun = -1
            currRun = -1
    if startRun==currRun and startRun!=-1:
        listRuns.append("%i" % (startRun+1))
    else:
        listRuns.append("%i-%i" % (startRun+1, currRun+1))
    
    arrString = ""
    for el in listRuns:
        arrString = arrString + el + ","
    
    arrString = "[" + arrString[:-1] + "]"
    return arrString

class LSFMonitor(object):
    '''
    classdocs
    '''

    class LSFJob(object):
        def __init__(self):
            self.lsfID = None
            self.arrayIndex = None
            self.lsfName = None
            self.lsfStatus = None
        
        #def __str__(self):
        #    return self.lsfStatus
        
    def __init__(self):
        '''
        Constructor
        '''
        self.jobsList = TwoLayerDict()
    
    
    def submitJob(self, jobs, config):
        
        if len(jobs)>1:
            indexArray = []
            for j in jobs:
                indexArray.append(j.jobSeq)
            jobName = config.name + formatArray(indexArray)
        else:
            jobName = config.name
        
        config.generateScripts(jobs)
        #Create the bsub command
        cmd = ["bsub -q " + config.queue]
        cmd[0] = cmd[0] + " -J \"" + jobName + "\""
        if config.requirement:
            cmd[0] = cmd[0] + " -R \"" + config.requirement + "\""
        
        #Run the command with timeout
        #print jobs[0].script
        subOutput = subCommand(cmd, jobs[0].script, 10).Run()
        
        #If failed, return
        if subOutput==None:
            return
        
        #Gather information about the job that was created (id + queue)
        m = re.search("Job <([0-9]+)> .*? <(.+?)>.*", subOutput)
        jobID = "";
        queue = "";
        if m:
            jobID = int(m.group(1))
            queue = m.group(2)

        if len(jobs)>1:
            for j in jobs:
                j.jobID = jobID
                j.queue = queue
                j.attempts += 1
                #Update the job with the information
                config.updateCorrespondance((j.jobID, j.jobSeq+1), j.jobSeq)
                jobIndex = -1
        else:
            jobs[0].jobID = jobID
            jobs[0].queue = queue
            jobs[0].attempts += 1
            #Update the job with the information
            config.updateCorrespondance(jobs[0].jobID, jobs[0].jobSeq)
            jobIndex = jobs[0].index
        
        return jobID,jobIndex
    
    def refreshInfo(self):
        cmd = ["bjobs -wa"]
        monOutput = subCommand(cmd, None, 10).Run()
        
        for line in monOutput.splitlines():
            elements = line.split()
            if elements[0]=="JOBID":
                continue
            
            job = LSFMonitor.LSFJob()
            job.lsfStatus = elements[2]
            job.lsfID = int(elements[0])
            m = re.search("(.*)\[([0-9]+)\]", elements[6])
            if m:
                job.lsfName = m.group(1)
                job.arrayIndex = int(m.group(2))
                self.jobsList[job.lsfID,job.arrayIndex] = job
            else:
                job.lsfName = elements[6]
                self.jobsList[job.lsfID] = job
            
    def getInfoByJobID(self, jobID, jobIndex=None):
        if jobIndex is None:
            return self.jobsList[jobID]
        else:
            return self.jobsList[jobID,jobIndex]
    
    def __str__(self, *args, **kwargs):
        return str(self.jobsList)
    
if __name__=="__main__":
    mon = LSFMonitor()
    mon.refreshInfo()
    print str(mon)
    
    print mon.getInfoByJobID(33333, 0)
    print mon.getInfoByJobID(3914)
    
    
    
    