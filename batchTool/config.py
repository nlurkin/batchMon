'''
Created on 16 May 2014

@author: Nicolas Lurkin
'''
import copy
import json
import os
import shutil
import time

import FSSelector
import SimpleConfigParser
from batchTool.util import TwoLayerDict, NoIndex_c


class BatchToolExceptions:
	'''
	Exceptions from BatchTool
	'''
	
	class BadCardFileException(Exception):
		'''Unable to parse correctly card file.'''
		pass
	class BadOption(Exception):
		'''Some options are not valid or missing.'''
		pass
	class ErrorMessage(Exception):
		'''Generic error message'''
		def __init__(self, text):
			self.strerror = text

def stringify(obj):
	for key,val in obj.iteritems():
		if type(key) is not str:
			try:
				obj[str(key)] = obj[key]
			except:
				try:
					obj[repr(key)] = obj[key]
				except:
					pass
			del obj[key]
		if type(val) == dict:
			val = stringify(val)
			
	return obj

def encode_dict(obj):
	'''
	Encode a dictionary for json 
	'''
	if isinstance(obj, BatchJob) or isinstance(obj,finalBatchJob):
		return obj.__dict__.__str__()
	if isinstance(obj, TwoLayerDict):
		return obj.__dict__
	if isinstance(obj, NoIndex_c):
		return str(obj)
	return obj

class BatchJob:
	'''
	Class representing a single job
	'''
	
	def __init__(self, data, index):#, seq):
		if data==None:
			self.inputFile = []
			self.index = index
			self.queue = None
			self.jobID = None
			self.status = None
			self.attempts = -2
			self.script = None
			self.jobSeq = index
		else:
			self.__dict__ = data
	
	def addInputFile(self, fileName):
		self.inputFile.append(fileName)
	
	def update(self, dico):
		'''
		Update the job dictionnary
		'''
		
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
	
	def __str__(self):
		return self.__dict__.__str__() 

class finalBatchJob:
	'''
	Class representing the final job to execute
	'''
	
	def __init__(self, script):
		self.script = script
		self.jobID = None
		self.status = None
		self.queue = None
		self.output = None
		self.jobIndex = None
	
	def update(self, dico):
		'''
		Update the job dictionary
		'''
		
		if "queue" in dico:
			self.queue = dico["queue"]
		if "jobID" in dico:
			self.jobID = dico["jobID"]
		if "status" in dico:
			self.status = dico["status"]
		if "script" in dico:
			self.script = dico["script"]
		if "index" in dico:
			self.jobIndex = dico["index"]
	
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
		
		self.jobCorrespondance = TwoLayerDict()
		
		self.outputDir = None
		self.outputFile = None
		
		self.name = ""
		self.queue = ""
		self.requirement = None
		
		self.finalJob = None
		self.finalizeStage = -1
		
		self.jobsList = []
		
		self.jobsGroup = 1
		
		self.inputFilesList = []

	
	def initCardFile(self, cardFile, name, queue, test=False):
		'''
		Set the card file for the batch. Read it and generate the jobs.
		'''
		self.cardFile = cardFile
		self.name = name
		self.queue = queue
		
		self._readCardFile()

		#Test requires to test the output files in the output directory
		#Therefore needs to know what they are
		if test:
			if not self.outputDir and not self.outputFile:
				raise BatchToolExceptions.BadOption("Unable to test outputs: outputDir or outputFile not specified")
			self._checkOutputDir()
			
		self._readInputList()
		
		if test:
			self._testAndUpdate()
			
	def load(self, jsonFile):
		'''
		Load a json file for an existing batch
		'''
		with open(jsonFile) as f:
			[dd,jobsList, jobcorr] = json.load(f)
			self.__dict__.update(dd)
			self.jobsList = []
			for job in jobsList:
				jsonstring = job.replace("None", 'null').replace("\"", "\\\"").replace("'", '"')
				j = BatchJob(json.loads(jsonstring), None)
				self.jobsList.append(j)
			self.jobCorrespondance = TwoLayerDict()
			for k1,v1 in jobcorr.iteritems():
				for k2,v2 in v1.iteritems():
					if k2 == "NoIndex":
						self.jobCorrespondance[int(k1)] = int(v2)
					else:
						self.jobCorrespondance[(int(k1),int(k2))] = int(v2)
	
	def save(self, fileName):
		'''
		Save batch in json
		'''
		with open(fileName, "wb") as f:
			dic = copy.deepcopy(self.__dict__)
			del dic["jobsList"]
			del dic["jobCorrespondance"]
			json.dump([dic,self.jobsList, stringify(self.jobCorrespondance.dico)], f, default=encode_dict, indent=4, separators=(',', ': '))

	def _buildSearchMap(self, index, fileName):
		'''
		Build map to replace all $-parameters
		'''
		dico = dict(self._templateDico)
		dico["jobIndex"] = index
		if fileName:
			fileList = ""
			for i,f in enumerate(fileName):
				dico["fileNameArr[%s]" % i] = f
				fileList = fileList + ("%s\n" % (f)) 
			dico["fileList"] = fileList.rstrip("\n")
			dico["fileName"] = fileName[0]
		else:
			dico["fileList"] = ""
			dico["fileName"] = None
		dico["outputDir"] = self.outputDir
		dico["outputFile"] = self.outputFile
		
		return dico
	
	def _buildSearchMapArrayed(self, step, fileName):
		'''
		Build map to replace all $-parameters
		'''
		dico = dict(self._templateDico)
		dico["jobIndex"] = "$((${LSB_JOBINDEX}-1))"
		if fileName:
			fileList = ""
			for i,_ in enumerate(fileName):
				dico["fileNameArr[%s]" % i] = "${fileName[$((%i + %i * (${LSB_JOBINDEX}-1)))]}" % (i+1, step)
				fileList = fileList + ("${fileName[$((%i + %i * (${LSB_JOBINDEX}-1)))]}\n" % (i+1, step))
			dico["fileList"] = fileList.rstrip("\n")
			dico["fileName"] = "$fileNameArr[0]"
		else:
			dico["fileList"] = ""
			dico["fileName"] = None
		dico["outputDir"] = self.outputDir
		dico["outputFile"] = self.outputFile
		
		return dico
	
	def _testOutputFile(self, index):
		'''
		Test if the output file exist
		'''
		
		#Output file is the outputDir + replaced template file name
		path = (self.outputDir + "/" + self._readAndReplace(self.outputFile, self._buildSearchMap(index, None))).strip("\n")
		if FSSelector.exists(path):
			return False
		return True
	
	def _checkOutputDir(self):
		'''
		Check if the outputDir exists. If not, create it
		'''
		if not FSSelector.exists(self.outputDir, True):
			FSSelector.mkDir(self.outputDir)
		
	def _readInputList(self):
		'''
		Read the input list file and create one job for jobsGroup entry (1 line = 1 entry)
		'''
		with open(self.listFile,'r') as f:
			group = 0 #keep number of files in job
			i = 0 #keep file index
			job = None #job pointer
			for line in f:
				self.inputFilesList.append(line.strip('\n'))
				#If start index specified, skip the first startIndex groups
				if i>=self.startIndex:
					#Always create the job, if test is requested and the 
					#output file already exists, we update it later
					if group==0:
						job = BatchJob(None, i)
					job.addInputFile(line.strip('\n'))
					group += 1
					if group==self.jobsGroup:
						self.jobsList.append(job)
						group = 0
						i += 1
						job = None
				#If we reach the maximum number of jobs, stop
				if self.maxJobs>0 and len(self.jobsList)>=self.maxJobs:
					break
			if group>0 and job!=None:
				self.jobsList.append(job)
		self.jobNumber = len(self.jobsList)
	
	def _testAndUpdate(self):
		for job in self.jobsList:
			if not self._testOutputFile(job.index):
				job.status = "DONE"
			
	def _readCardFile(self):
		'''
		Read the card file and set the options
		'''
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

		if cp.hasoption("requirement"):
			self.requirement = cp.getoption("requirement")
		
		if cp.hasoption("finalScript"):
			self.finalJob = finalBatchJob(cp.getoption("finalScript"))
		
		if cp.hasoption("jobsGrouping"):
			self.jobsGroup = int(cp.getoption("jobsGrouping"))


	def _readAndReplace(self, string, searchMap):
		'''
		Read the string and replace every known $-parameter by its dictionary value
		'''
		
		sReturn = ""
		for line in string.splitlines():
			replacedAll = False
			#Dictionary value can also be a $-parameter so loop until no known $-parameter found
			while not replacedAll:
				replacedAll = True
				for old in searchMap:
					if "$"+old in line:
						line = line.replace("$"+old, str(searchMap[old]))
						replacedAll = False
			sReturn += line + "\n"
		
		return sReturn
	
	def _generateJobScript(self, jobIndex):
		sReturn = "#Pre \n%s \n#Command \n%s \n#Post \n%s"

		#Generate the $-parameter dictionary
		dico = self._buildSearchMap(self.jobsList[jobIndex].index, self.jobsList[jobIndex].inputFile)
		#Apply the dictionary for the 3 parts of the script
		pre = self._readAndReplace(self.preExecute, dico)
		command = self._readAndReplace("%s %s" % (self.executable, self.optTemplate), dico)
		post = self._readAndReplace(self.postExecute, dico)
		#Set the script
		self.jobsList[jobIndex].script = sReturn % (pre, command, post)
			
	def _generateBashArray(self):
		listString = "fileName[0]=aligning\n"
		for i,f in enumerate(self.inputFilesList):
			listString = listString + "fileName[%i]=%s\n" % (i+1, f)
		
		return listString
		
	def _generateJobScriptArrayed(self, jobIndex):
		sReturn = "#File lists array \n%s \n#Pre \n%s \n#Command \n%s \n#Post \n%s"
		sFileList = self._generateBashArray()
		indexList = range(0,self.jobNumber)
		
		if len(indexList)>0:
			#Generate the $-parameter dictionary
			dico = self._buildSearchMapArrayed(len(self.jobsList[jobIndex].inputFile), self.jobsList[jobIndex].inputFile)
			#Apply the dictionary for the 3 parts of the script
			pre = self._readAndReplace(self.preExecute, dico)
			command = self._readAndReplace("%s %s" % (self.executable, self.optTemplate), dico)
			post = self._readAndReplace(self.postExecute, dico)
			#Set the script
			self.jobsList[jobIndex].script = sReturn % (sFileList, pre, command, post)
	
	def _generateFinalJobScript(self):
		indexList = range(0,self.jobNumber)	
		#Create the final job script if exists
		if len(indexList)>0 and self.finalJob:
			dico = self._buildSearchMapArrayed(len(self.jobsList[0].inputFile), self.jobsList[0].inputFile)
			self.finalJob.script = self._readAndReplace(self.finalJob.script, dico)
		
	def __str__(self):
		'''
		String representation
		'''
		files = "" 
		for job in self.jobsList:
			files += str(job) + "\n"
		return self._reprTemplate % (hex(id(self)), self.cardFile, self.jobNumber, self.preExecute, self.executable, self.optTemplate, self.postExecute, files)
	
	def generateScripts(self, jobsList):
		if len(jobsList)>1:
			for job in jobsList:
				self._generateJobScriptArrayed(job.index)
		elif len(jobsList)==1:
			self._generateJobScript(jobsList[0].index)

	def parseFailReason(self, job):
		'''
		Parse the output to determine the reason of the failure and decide whether it is worth retsarting the job 
		'''
		#if false
		#job["attempts"] = -2
		return True
	
	def updateJob(self, jobID, dico, keep, jobArraySeq=None):
		'''
		Update job with the information in the dico
		'''
		reSubmit = False
		seq = -1
		
		#Does this job exist
		if jobID in self.jobCorrespondance:
			#Get the job index and the job itself
			if jobArraySeq==None:
				jobSeq = self.jobCorrespondance[jobID]
			else:
				jobSeq = jobArraySeq-1
			job = self.jobsList[jobSeq]
			
			#test state change
			if jobArraySeq==None:
				lsfPath = os.path.abspath(os.curdir) + "/LSFJOB_" + str(job.jobID)
			else:
				lsfPath = os.path.abspath(os.curdir) + "/LSFJOB_" + str(job.jobID) + "." + str(jobArraySeq)
			if job.status!=dico["status"]:
				if dico["status"]=="DONE":
					#clean output
					if os.path.exists(lsfPath) and not keep:
						shutil.rmtree(lsfPath, True)
				if dico["status"]=="EXIT":
					if job.attempts>=0 and job.attempts<self.maxAttempts and self.parseFailReason(job):
						#clean output
						if os.path.exists(lsfPath) and not keep:
							shutil.rmtree(lsfPath, True)
						reSubmit = True
						seq = jobSeq
						del self.jobCorrespondance[jobID]
			
			#do the update
			job.update(dico)
		return (reSubmit,seq)
	
	def updateCorrespondance(self, jobID, jobSeq):
		'''
		Update the correspondance between jobID and jobSequence
		jobID = id from lxbatch
		jobSequence = index in the job array
		'''
		self.jobCorrespondance[jobID] = jobSeq
	
	def getJobSeq(self, jobID):
		'''
		Return the job sequence corresponding to the jobID. Or -1 if is not found.
		'''
		if jobID in self.jobCorrespondance:
			return self.jobCorrespondance[jobID]
		return -1

	def getStatusStats(self):
		'''
		Return statistics about the batch: 
			number attempts
				Pending
				Running
				Exited
				Unknown
				Done 
		'''
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
		
		if finished==self.jobNumber and (unknown==0 and pending["value"]==0 and running["value"]==0 and failed["value"]==0) and self.finalizeStage==-1:
			self.finalizeStage = 0
			
		return {"unknown":unknown, "pending":pending, "running":running, "failed":failed, "finished":finished}
	
	def getHeaders(self):
		'''
		Return the header info of the batch: number of jobs, cardfile, maximum number of attemps, name, queue
		'''
		return {"jobNumber":self.jobNumber, "cardFile":self.cardFile, "maxAttempts":self.maxAttempts, "name":self.name, "queue":self.queue}
	
	def resetFailed(self):
		'''
		Reset (enable) the failed jobs for which the maximum number of attemps have been reached (permanently failed)
		'''
		for job in self.jobsList:
			if job.attempts==-2 or job.attempts==self.maxAttempts and job.status=="EXIT":
				job.attempts=-1
				job.status = None
	
	def enableNew(self):
		'''
		Enable jobs that are not yet running
		'''
		for job in self.jobsList:
			if job.attempts==-2 and not job.status:
				job.attempts=-1
	
	def getJobsNumberReady(self):
		'''
		Return the number of jobs ready to be submitted (enabled)
		'''
		return len([0 for job in self.jobsList if job.attempts==-1])
	
	def updateFinalJob(self, dico):
		'''
		Update the final job with the dictionary values
		'''
		if "status" in dico:
			if dico["jobID"]==self.finalJob.jobID and self.finalJob.status!=dico["status"]:
				lsfPath = os.path.abspath(os.curdir) + "/LSFJOB_" + str(self.finalJob.jobID)
				if dico["status"]=="DONE":
					#get output, save it and clean
					if os.path.exists(lsfPath):
						#read
						with open("%s/STDOUT" % (lsfPath), 'r') as f:
							self.finalJob.output = f.read()
						
						#clean
						shutil.rmtree(lsfPath)
						self.finalizeStage = 2
				if dico["status"]=="EXIT":
					#miserably failed: do something about it
					self.finalizeStage = -2
		
		#do the update
		self.finalJob.update(dico)
		if self.finalizeStage == 0:
			self.finalizeStage = 1
	
	def finalizeFinished(self):
		'''
		Is the final job finished
		'''
		return self.finalizeStage==2 or self.finalizeStage==-2


if __name__=='__main__':
	config = ConfigBatch()
	config.initCardFile("test/testConfig", "xxx", "8nm", False)
	for f in config.jobsList:
		config._generateJobScript(f.index)
		print f.script
	