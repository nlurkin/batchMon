'''
Created on 16 May 2014

@author: ncl
'''
from . import ConfigBatch
import re
import subprocess

class Monitor:
	'''
	Main class for monitoring jobs
	'''

	config = ConfigBatch()

	def __init__(self):
		'''
		Constructor
		'''
	
	def newBatch(self, cfgFile, batchName, queue, test):
		self.config.initCardFile(cfgFile, batchName, queue, test)
		self.saveState()
		self.submitJobs()
	
	def loadBatch(self, jsonFile):
		self.config.load(jsonFile)
	
	def submitJobs(self, jList=[]):
		for job, script in self.config.generateScript(jList):
			cmd = ["bsub", "-q", self.config.queue]
			subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
			(subOutput, _) = subCmd.communicate(script)
			
			m = re.search("Job <([0-9]+)> .*? <(.+?)>.*", subOutput)
			if m:
				job["jobID"] = m.group(1)
				job["queue"] = m.group(2)
				if len(jList)==0:
					job["attempts"] = 0
				else:
					job["attempts"] += 1
				self.config.updateCorrespondance(job["jobID"], job["index"])
	
	def monitor(self):
		cmd = ["bjobs -a"]
		subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(monOutput, _) = subCmd.communicate()
	
		reSubmit = []
		for line in monOutput.splitlines():
			m = re.search("([0-9]+) [a-zA-Z]+ (RUN|PEND|DONE|EXIT) .*", line)
			if m:
				redo,index = self.config.updateJob(m.group(1), {"status":m.group(2)})
				if redo:
					reSubmit.append(index)
		
		if len(reSubmit)>0:
			self.submitJobs(reSubmit)
	
	def saveState(self):
		self.config.save("%s.json" % (self.config.name))
