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

output = {jobName}/$(ClusterId).$(JobId).out
error  = {jobName}/$(ClusterId).$(JobId).err
log    = {jobName}/$(ClusterId).$(JobId).log
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
    
    
    def submitJob(self, jobs, config):
        
        if len(jobs)>1:
            indexArray = []
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
            scriptFile.writelines(jobs[0].script)
        os.chmod("{0}.sh".format(jobName), stat.S_IRWXU | stat.S_IRGRP | stat.IROTH)
        cmd = ["condor_submit -batch-name {0} {0}.sub".format(jobName)]

        #Run the command with timeout
        subOutput = subCommand(cmd, None, 10).Run()
        
        #If failed, return
        if subOutput==None:
            return
        
        #Gather information about the job that was created (id + queue)
        m = re.search(".* submitted to cluster ([0-9]+)\.", subOutput)
        jobID = "";
        if m:
            jobID = int(m.group(1))

        if len(jobs)>1:
            for j in jobs:
                j.jobID = jobID
                j.queue = config.queue
                j.attempts += 1
                #Update the job with the information
                config.updateCorrespondance((j.jobID, j.jobSeq), j.jobSeq)
                jobIndex = -1
        else:
            jobs[0].jobID = jobID
            jobs[0].queue = config.queue
            jobs[0].attempts += 1
            #Update the job with the information
            config.updateCorrespondance(jobs[0].jobID, jobs[0].jobSeq)
            jobIndex = jobs[0].index
        
        return jobID,jobIndex
    
    def deleteJobs(self, clusterID):
        for cid in clusterID:
            cmd = ["condor_rm " + cid] #name here is the cluster
            _ = subCommand(cmd, None, 30).Run()
        
    def refreshInfo(self):
        cmd = ["condor_q -nobatch"]
        monOutput = subCommand(cmd, None, 10).Run()
        
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
            
            job = HTCondorMonitor.HTCondorJob()
            job.lsfStatus = elements[5]
            job.lsfID = int(elements[0].split(".")[0])
            job.arrayIndex = int(elements[0].split(".")[1])
            job.lsfName = "" #TODO to find out how to get that
            self.jobsList[job.lsfID,job.arrayIndex] = job
            
    def getInfoByJobID(self, jobID, jobIndex=None):
        if jobIndex is None:
            return self.jobsList[jobID]
        else:
            return self.jobsList[jobID,jobIndex]
    
    def __str__(self, *args, **kwargs):
        return str(self.jobsList)
    
    
    
