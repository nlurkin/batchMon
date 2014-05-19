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
	submitReady = False
	keepOutput = False

	def __init__(self, keep):
		'''
		Constructor
		'''
		self.submitList = []
		self.keepOutput = keep
	
	def newBatch(self, cfgFile, batchName, queue, test):
		self.config.initCardFile(cfgFile, batchName, queue, test)
		self.saveState()
		self.submitReady = True
	
	def loadBatch(self, jsonFile):
		self.config.load(jsonFile)
		self.submitReady = False
	
	def submit(self, job):
		cmd = ["bsub", "-q", self.config.queue]
		subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
		(subOutput, _) = subCmd.communicate(job.script)
		
		m = re.search("Job <([0-9]+)> .*? <(.+?)>.*", subOutput)
		if m:
			job.jobID = m.group(1)
			job.queue = m.group(2)
			job.attempts += 1
			self.config.updateCorrespondance(job.jobID, job.index)
	
	def generateJobs(self):
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
		cmd = ["bjobs -a"]
		subCmd = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
		(monOutput, _) = subCmd.communicate()
	
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
	
	def saveState(self):
		self.config.save("%s.json" % (self.config.name))
	
	def submitInit(self):
		self.config.enableNew()
		self.submitReady = True
	
