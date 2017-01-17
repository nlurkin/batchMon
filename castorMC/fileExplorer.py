'''
Created on Sep 24, 2014

@author: ncl
'''
from operator import itemgetter
import os
import subprocess
import sys
import time
import datetime

import fcntl


class FEIOError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)
	
def getCopyCommand(conn1, conn2):
	if conn1.__class__.__name__ == "CastorConnector" or conn2.__class__.__name__ == "CastorConnector":
		return "xrdcp"
	else:
		return "cp"

def setNonBlocking(fd):
	"""
	Set the file description of the given file descriptor to non-blocking.
	"""
	flags = fcntl.fcntl(fd, fcntl.F_GETFL)
	flags = flags | os.O_NONBLOCK
	fcntl.fcntl(fd, fcntl.F_SETFL, flags)

def execute(command, scr):
	try:
		cmd= subprocess.Popen(command, stderr=subprocess.PIPE)
	except OSError as e:
		raise FEIOError("Unable to run command [Error {0}]: {1}".format(e.errno, e.strerror))
		
	#setNonBlocking(cmd.stdout)
	for line in iter(cmd.stderr.readline, ""):
#		sys.__stdout__.write(line),
		scr.printError(line)
	
	cmd.communicate()	
	#
	#line = ""
	#while True:
		#while True:
			#try:
				#line = cmd.stdout.readline()
			#except IOError:
				#break
			#else:
				#break
		#if line=="":
			#break;
		#line = line.rstrip('\n')
		#sys.__stdout__.write(line)
	
	#cmd.
	return cmd.returncode

def executeGet(command):
	#try:
	cmd= subprocess.Popen(command, stdout=subprocess.PIPE)
	#except OSError as e:
	#	raise FEIOError("Unable to run command [Error {0}]: {1}".format(e.errno, e.strerror))
		
	(out, _) = cmd.communicate()
	return (out.splitlines(), cmd.returncode)

class FileExplorer(object):
	'''
	classdocs
	'''
	
	def __init__(self, connector, initPath):
		'''
		Constructor
		'''
		self.currPath = ""
		self.fileList = []
		self.dirList = []

		self.connector = connector
		
		self.cd(initPath)
	
	
	def cd(self, path):
		self.currPath = self.connector.makePath(path)
		self.fillPath()
		
	def fillPath(self):
		if not self.connector.exists(self.currPath):
			#error
			pass
		
		(self.dirList, self.fileList) = self.connector.listFiles(self.currPath)
	
	def goDown(self, index):
		(ftype, path) = self.getPath(index)
		if ftype==1:
			return False
		self.currPath = path
		self.fillPath()
		return True
	
	def goUp(self):
		self.currPath = os.path.dirname(self.currPath)
		self.fillPath()

		
	def refresh(self):
		self.fillPath()
		
	def getPath(self, index):
		if index < len(self.dirList):
			return (0, self.currPath + "/" + self.dirList[index]["name"])
		else:
			return (1, self.currPath + "/" + self.fileList[index - len(self.dirList)]["name"])
	
	def delete(self, indices):
		ret = 0
		for index in indices:
			ret = self.connector.delete(self.getPath(index))
		return ret
	
	def copy(self, indices, otherfs):
		ret = 0
		for index in indices:
			path = self.getPath(index)
			fname = os.path.basename(path[1])
			ret = ret + self.connector.copy(path, otherfs.connector.makeCPPath(otherfs.currPath + "/" + fname), getCopyCommand(self.connector, otherfs.connector))
		return ret

class CastorConnector(object):
	'''
	classdocs
	'''
	
	protocol = "xroot://castorpublic.cern.ch/"
	prefix = "/castor/cern.ch/user/n/nlurkin"
	
	def __init__(self, screen):
		self.scr = screen
	
	def copy(self, (ftype,path), otherPath, command):
		cmd = [command]
		if ftype==0:
			cmd.append("-r")
		cmd.append(self.protocol + path)
		cmd.append(otherPath)
		
		return execute(cmd, self.scr)
	
	def exists(self, path):
		(_,ret) = executeGet(["nsls", path])
		if ret==0:
			return True
		else:
			return False
			
	def listFiles(self, path):
		(entryList,_) = executeGet(["nsls", "-l", path])
		dirList = []
		fileList = []
		for f in entryList:
			l = f.split()
			if l[8].startswith("."):
				continue
			if l[0][0]=="d":
				if ":" in l[7]:
					dt = datetime.datetime.strptime(("%s %s %s")%(l[5], l[6],l[7]), "%b %d %H:%M")
					dt.replace(year=2014)
				else:
					dt = datetime.datetime.strptime(("%s %s %s")%(l[5], l[6],l[7]), "%b %d %Y")
				t = time.mktime(dt.timetuple())
				dirList.append({"name":l[8], "type":"d", "mtime":t})
			else:
				if ":" in l[7]:
					dt = datetime.datetime.strptime(("%s %s %s")%(l[5], l[6],l[7]), "%b %d %H:%M")
					dt.replace(year=2014)
				else:
					dt = datetime.datetime.strptime(("%s %s %s")%(l[5], l[6],l[7]), "%b %d %Y")
				t = time.mktime(dt.timetuple())
				fileList.append({"name":l[8], "type":"f", "size":int(l[4]), "mtime":t})
		
		dirList.sort(key=lambda k: k['name'].lower())
		fileList.sort(key=lambda k: k['name'].lower())
		return (dirList, fileList)
	
	def makePath(self, path):
		return self.prefix + "/" + path

	def makeCPPath(self, path):
		return self.protocol + path
	
	def delete(self, (ftype,path)):
		try:
			if ftype==0:
				execute(["nsrm" , "-r", path], self.scr)
			elif ftype==1:
				execute(["nsrm" , path], self.scr)
		except:
			return -1
		
		return 0
	

class LocalConnector(object):
	'''
	classdocs
	'''
	
	def __init__(self, screen):
		self.scr = screen
	
	def copy(self, (ftype,path), otherPath, command):
		cmd = [command]
		if ftype==0:
			cmd.append("-r")
		cmd.append(path)
		cmd.append(otherPath)
		
		return execute(cmd, self.scr)
	
	def exists(self, path):
		if not os.path.exists(path):
			return False
		else:
			return True
			
	def listFiles(self, path):
		entryList = os.listdir(path)
		dirList = []
		fileList = []
		for f in entryList:
			if f.startswith("."):
				continue
			if os.path.isdir(path + "/" + f):
				dirList.append({"name":f, "type":"d", "mtime":os.stat(path+"/"+f).st_mtime})
			else:
				info = os.stat(path + "/" + f)
				fileList.append({"name":f, "type":"f", "size":info.st_size, "mtime":info.st_mtime})
		
		dirList.sort(key=lambda k: k['name'].lower()) 
		fileList.sort(key=lambda k: k['name'].lower())
		return (dirList, fileList)
	
	def makePath(self, path):
		return path
		
	def makeCPPath(self, path):
		return path

	
	def delete(self, (ftype,path)):
		try:
			if ftype==0:
				os.rmdir(path)
			elif ftype==1:
				os.remove(path)
		except:
			return -1
		
		return 0
	
