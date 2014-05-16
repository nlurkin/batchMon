'''
Created on 16 May 2014

@author: ncl
'''
import SimpleConfigParser
import json
import os
import shutil
import time
from bzrlib.util._bencode_py import encode_dict

class BatchToolExceptions:
	class BadCardFileException(Exception):
		'''Unable to parse correctly card file.'''
		pass
	class BadOption(Exception):
		'''Some options are not valid or missing.'''
		pass

def encode_dict(obj):
	if isinstance(obj, BatchJob):
		return obj.__dict__
	return obj

class BatchJob:
	'''
	Class representing a single job
	'''
	
	inputFile = None
	queue = None
	index = None
	jobID = None
	status = None
	attempts = None
	script = None
	
	def __init__(self, inputFile, index):
		self.inputFile = inputFile
		self.index = index
		self.queue = None
		self.jobID = None
		self.status = None
		self.attempts = -1
		self.script = None
	
	def update(self, dico):
		if "inputFile" in dico:
			self.inputFile = dico["inputFile"]
		if "queue" in dico:
			self.queue = dico["queue"]
		if "index" in dico:
			self.index = dico["index"]
		if "jobID" in dico:
			self.jobID = dico["jobID"]
		if "status" in dico:
			self.status = dico["status"]
		if "attempts" in dico:
			self.attempts = dico["attempts"]
		if "script" in dico:
			self.script = dico["script"]

class ConfigBatch:
	_templateDico = {"jobIndex":0, "fileName":"", "outputDir":"", "outputFile":""}
	
	_reprTemplate = """
<
configCard instance at %s
From cardFile: %s
Contains: %s jobs
To run with:
\" 
%s
%s %s
%s
\"

fileList:
%s
> 
"""
	jobsList = []
	def __init__(self):
		self.startTime = time.time()
		self.jobNumber = 0
		self.listFile = ""
		
		self.executable = ""
		self.optTemplate = ""
		self.preExecute = ""
		self.postExecute = ""
		
		self.cardFile = ""
		
		self.startIndex = 0
		self.maxJobs = 0
		self.maxAttempts = 5
		
		self.jobCorrespondance = {}
		
		self.outputDir = None
		self.outputFile = None
		
		self.name = ""
		self.queue = ""

	
	def initCardFile(self, cardFile, name, queue, test=False):
		self.cardFile = cardFile
		self.name = name
		self.queue = queue
		
		self._readCardFile()

		if test:
			if not self.outputDir and not self.outputFile:
				raise BatchToolExceptions.BadOption("Unable to test outputs: outputDir or outputFile not specified")
		
		self._readInputList(test)
		self._generateScript()
	
	def load(self, jsonFile):
		with open(jsonFile) as f:
			[self.__dict__,jobsList] = json.load(f)
			for job in jobsList:
				j = BatchJob(None, None)
				j.__dict__ = job 
				self.jobsList.append(j)
	
	def save(self, fileName):
		with open(fileName, "wb") as f:
			json.dump([self.__dict__,self.jobsList], f, default=encode_dict)

	def _buildSearchMap(self, index, fileName):
		dico = dict(self._templateDico)
		dico["jobIndex"] = index
		dico["fileName"] = fileName
		dico["outputDir"] = self.outputDir
		dico["outputFile"] = self.outputFile
		return dico
	
	def _testOutputFile(self, index):
		if os.path.exists(self.outputDir + "/" + self._readAndReplace(self.outputFile, self._buildSearchMap(index, None))):
			return False
		return True
		
	def _readInputList(self, test):
		with open(self.listFile,'r') as f:
			for i,line in enumerate(f):
				if i>=self.startIndex:
					if(self._testOutputFile(i)):
						self.jobsList.append(BatchJob(line.strip('\n'), i))
				if self.maxJobs>0 and len(self.jobsList)>=self.maxJobs:
					break
		
		self.jobNumber = len(self.jobsList)
		
	def _readCardFile(self):
		cp = SimpleConfigParser.SimpleConfigParser()
		cp.read(self.cardFile)
		
		#Test mandatory options
		if not cp.hasoption('listFile'):
			raise BatchToolExceptions.BadCardFileException("Missing listFile")
		if not cp.hasoption('executable'):
			raise BatchToolExceptions.BadCardFileException("Missing executable")
		
		self.listFile = cp.getoption("listFile")
		self.executable = cp.getoption("executable")
		
		if cp.hasoption("optTemplate"):
			self.optTemplate = cp.getoption("optTemplate")

		if cp.hasoption("preExecute"):
			self.preExecute = cp.getoption("preExecute")

		if cp.hasoption("postExecute"):
			self.postExecute = cp.getoption("postExecute")
	
		if cp.hasoption("startIndex"):
			self.startIndex = int(cp.getoption("startIndex"))

		if cp.hasoption("maxJobs"):
			self.maxJobs = int(cp.getoption("maxJobs"))

		if cp.hasoption("maxAttempts"):
			self.maxAttempts = int(cp.getoption("maxAttempts"))
		
		if cp.hasoption("outputDir"):
			self.outputDir = cp.getoption("outputDir")

		if cp.hasoption("outputFile"):
			self.outputFile = cp.getoption("outputFile")

	def _readAndReplace(self, string, searchMap):
		sReturn = ""
		for line in string.splitlines():
			replacedAll = False
			while not replacedAll:
				replacedAll = True
				for old in searchMap:
					if "$"+old in line:
						line = line.replace("$"+old, str(searchMap[old]))
						replacedAll = False
			sReturn += line + "\n"
		
		return sReturn
	
	def _generateScript(self):
		sReturn = "#Pre \n%s \n#Command \n%s \n#Post \n%s"
		indexList = range(0,self.jobNumber)
		for i in indexList:
			dico = self._buildSearchMap(i, self.jobsList[i].inputFile)
			pre = self._readAndReplace(self.preExecute, dico)
			command = self._readAndReplace("%s %s" % (self.executable, self.optTemplate), dico)
			post = self._readAndReplace(self.postExecute, dico)
			self.jobsList[i].script = sReturn % (pre, command, post)
	
	def __str__(self):
		files = "" 
		for job in self.jobsList:
			files += str(job) + "\n"
		return self._reprTemplate % (hex(id(self)), self.cardFile, self.jobNumber, self.preExecute, self.executable, self.optTemplate, self.postExecute, files)
	
	def parseFailReason(self, job):
		#if false
		#job["attempts"] = -2
		return True
	
	def updateJob(self, jobID, dico):
		reSubmit = False
		index = -1
		if jobID in self.jobCorrespondance:
			jobNumber = self.jobCorrespondance[jobID]
			job = self.jobsList[jobNumber]
			#test state change
			lsfPath = os.path.abspath(os.curdir) + "/LSFJOB_" + str(job.jobID)
			if job.status!=dico["status"]:
				if dico["status"]=="DONE":
					#clean output
					if os.path.exists(lsfPath):
						shutil.rmtree(lsfPath)
				if dico["status"]=="EXIT":
					#clean output
					if os.path.exists(lsfPath):
						shutil.rmtree(lsfPath)
					if job.attempts>=0 and job.attempts<self.maxAttempts and self.parseFailReason(job):
						reSubmit = True
						job.attemps = -1
						index = jobNumber
						del self.jobCorrespondance[jobID]
			
			#do the update
			job.update(dico)
		return (reSubmit,index)
	
	def updateCorrespondance(self, jobID, jobIndex):
		self.jobCorrespondance[jobID] = jobIndex
	
	def getJobIndex(self, jobID):
		if jobID in self.jobCorrespondance:
			return self.jobCorrespondance[jobID]
		return -1

	def getStatusStats(self):
		unknown = 0
		pending = {"value": 0, "attempts":[0]*(self.maxAttempts+1)}
		running = {"value": 0, "attempts":[0]*(self.maxAttempts+1)}
		failed = {"value": 0, "attempts":[0]*(self.maxAttempts+1), "permanent":0}
		finished = 0
		
		for job in self.jobsList:
			if not job.status:
				unknown += 1
			elif job.status=="PEND":
				pending["value"] += 1
				if job.attempts >= 0:
					pending["attempts"][job.attempts] += 1
			elif job.status=="RUN":
				running["value"] += 1
				if job.attempts >= 0:
					running["attempts"][job.attempts] += 1
			elif job.status=="EXIT":
				failed["value"] += 1
				if job.attempts >= 0:
					failed["attempts"][job.attempts] += 1
				elif job.attempts == -2:
					failed["permanent"] += 1
			elif job.status=="DONE":
				finished += 1
		return {"unknown":unknown, "pending":pending, "running":running, "failed":failed, "finished":finished}
	
	def getHeaders(self):
		return {"jobNumber":self.jobNumber, "cardFile":self.cardFile, "maxAttempts":self.maxAttempts}
	
	def resetFailed(self):
		for job in self.jobsList:
			if job.attempts==-2 or job.attempts==self.maxAttempts:
				job.attempts=-1
			
