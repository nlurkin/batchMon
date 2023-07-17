'''
Created on 17 Jan 2017

@author: ncl
'''
import re
from util import subCommand, TwoLayerDict
import os
import stat

htcondorMonitorInstance = None

def getHTCondorMonitorInstance():
    global htcondorMonitorInstance
    if htcondorMonitorInstance is None:
        htcondorMonitorInstance = HTCondorMonitor()
    return htcondorMonitorInstance


subFormat = """

executable = {jobName}.sh

output = {jobName}/$(ClusterId).$(ProcId).out
error  = {jobName}/$(ClusterId).$(ProcId).err
log    = {jobName}/$(ClusterId).$(ProcId).log
transfer_output_files = ""
+JobFlavour = "{queue}"

{requirements}

queue arguments in {indexList}
"""

class HTCondorMonitor(object):
    '''
    classdocs
    '''

    class HTCondorJob(object):
        def __init__(self):
            self.lsfID = None
            self.arrayIndex = None
            self.lsfName = None
            self.lsfStatus = None
        
    #    #def __str__(self):
    #    #    return self.lsfStatus
        
    def __init__(self):
        '''
        Constructor
        '''
        self.jobsList = TwoLayerDict()
        self.shedulerHost = None
    
    def setScheduler(self, number):
        self.shedulerHost = "bigbird{0:0>2}.cern.ch".format(number)
        os.putenv("_CONDOR_SCHEDD_HOST", self.shedulerHost)
        os.putenv("_CONDOR_CREDD_HOST", self.shedulerHost)
        # _CONDOR_SCHEDD_HOST=bigbird04.cern.ch _CONDOR_CREDD_HOST=bigbird04.cern.ch
    
    def submitJob(self, jobs, config):
        
        if len(jobs)==0:
            return None,None

        indexArray = []
        #if len(jobs)>1:
        for j in jobs:
            indexArray.append(str(j.jobSeq))
        jobName = config.name
        
        config.generateScripts(jobs)
        #Create the bsub command
        #config.queue
        if not os.path.exists("{jobName}".format(jobName=jobName)):
            os.mkdir("{jobName}".format(jobName=jobName))
        with open("{0}.sub".format(jobName), "w") as subFile:
            requirements = ""
            if config.requirement:
                requirements = "requirements = ({0})".format(config.requirement)

            subFile.writelines(subFormat.format(jobName=jobName, queue=config.queue, requirements=requirements, indexList=", ".join(indexArray)))

        with open("{0}.sh".format(jobName), "w") as scriptFile:
            scriptFile.write("#!/bin/sh\n")
            scriptFile.writelines(jobs[0].script)
        os.chmod("{0}.sh".format(jobName), stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        cmd = ["condor_submit -batch-name {0} {0}.sub".format(jobName)]

        #Run the command with timeout
        #print "submitting command", cmd
        subOutput = subCommand(cmd, None, 60).Run()
        #print "Condor output",subOutput 
        #If failed, return
        if subOutput==None:
            return None,None
        
        #Gather information about the job that was created (id + queue)
        m = re.search(".* submitted to cluster ([0-9]+)\.", subOutput)
        jobID = "";
        if m:
            jobID = int(m.group(1))

        #if len(jobs)>1:
        for index,j in enumerate(jobs):
            j.jobID = jobID
            j.queue = config.queue
            j.attempts += 1
            #Update the job with the information
            config.updateCorrespondance((j.jobID, index), j.jobSeq)
            jobIndex = -1
        #else:
        #    jobs[0].jobID = jobID
        #    jobs[0].queue = config.queue
        #    jobs[0].attempts += 1
        #    #Update the job with the information
        #    config.updateCorrespondance(jobs[0].jobID, jobs[0].jobSeq)
        #    jobIndex = jobs[0].index
        
        os.remove("{0}.sub".format(jobName))
        return jobID,jobIndex
    
    def deleteJobs(self, clusterID):
        print clusterID
        for cid in clusterID:
            cmd = ["condor_rm " + cid] #name here is the cluster
            _ = subCommand(cmd, None, 30).Run()
        
    def refreshInfo(self):
        cmd = ["condor_q -nobatch"]
        monOutput = subCommand(cmd, None, 10).Run()
        #cmd = ["condor_history nlurkin"]
        #monOutput += subCommand(cmd, None, 10).Run()
       
        #print "Full list", self.jobsList
        oldDict = set([(k1,k2) for k1,k2,v in self.jobsList.iteritems() if v.lsfStatus!="C"])
        oldSize = len(oldDict)
        #print "Before", oldDict
        for line in monOutput.splitlines():
            if len(line)==0:
                continue
            if "Schedd" in line:
                continue
            if "SUBMITTED" in line:
                continue
            if "jobs;" in line:
                continue
            elements = line.split()

            if len(elements)<6:
                continue
            
            job = HTCondorMonitor.HTCondorJob()
            job.lsfStatus = elements[5]
            job.lsfID = int(elements[0].split(".")[0])
            job.arrayIndex = int(elements[0].split(".")[1])
            job.lsfName = "" #TODO to find out how to get that
            self.jobsList[job.lsfID,job.arrayIndex] = job
            
            if (job.lsfID,job.arrayIndex) in oldDict:
                oldDict.remove((job.lsfID,job.arrayIndex))
        
        #print "After", oldDict
        if len(oldDict)==1 or len(oldDict)!=oldSize:
            #print "Job are being removed"
            for jobIndex in oldDict:
                #print "Removing ", jobIndex
                self.jobsList[jobIndex].lsfStatus = "C"

    def getInfoByJobID(self, jobID, jobIndex=None):
        if jobIndex is None:
            return self.jobsList[jobID]
        else:
            return self.jobsList[jobID,jobIndex]
    
    def __str__(self, *args, **kwargs):
        return str(self.jobsList)
    
    
    
