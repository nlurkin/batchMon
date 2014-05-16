'''
Created on 16 May 2014

@author: ncl
'''
import datetime

class Display:
	'''
	Class for displaying things on screen
	'''
	titleBlock = 0
	summaryBlock = 5
	submitBlock = 12

	debugBlock = 20


	def __init__(self, scr):
		'''
		Constructor
		'''
		self.stdscr = None
	
	def setScreen(self, scr):
		self.stdscr = scr
	
	def wipeAttemptsBlock(self):
		for i in range(0,5):
			self.stdscr.move(self.summaryBlock+1+i,0)
			self.stdscr.clrtoeol()
	
	def repaint(self):
		self.stdscr.refresh()
	
	def displayHeader(self, headers):
		if self.stdscr == None:
			return
		self.stdscr.addstr(self.titleBlock,20, "LXBATCH job monitoring")
		self.stdscr.addstr(self.titleBlock+2,0, "Monitoring {0} jobs from card file {1} for a maximum of {2} attempts".format(
												headers["jobNumber"], headers["cardFile"], headers["maxAttempts"]))
		self.repaint()
	
	def displayTime(self, startTime):
		if self.stdscr == None:
			return
		td = datetime.datetime.now()-datetime.datetime.fromtimestamp(startTime)
		self.stdscr.addstr(self.titleBlock+3,0, "Running since {0} ({1})      ".format(
													datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S'), 
													str(td)))
	def displaySubmit(self, total, fileNumber, currFile):
		if self.stdscr == None:
			return
		progress = (1.0*fileNumber/total)*100
		
		"""progress: 0-100"""
		self.stdscr.addstr(0, 0, "Deleting file: {0}                                 ".format(currFile))
		self.stdscr.addstr(1, 5, "Total progress: [{2:101}] {0}/{1}".format(fileNumber,total, "#" * int(progress)))
		self.repaint()
	
	def displaySummary(self, stats):
		if self.stdscr == None:
			return
		self.stdscr.addstr(self.summaryBlock,0,"Failed attempts")
		self.stdscr.addstr(self.summaryBlock,20,"Pending jobs {0}".format(stats["pending"]["value"]))
		self.stdscr.addstr(self.summaryBlock,40,"Running jobs {0}".format(stats["running"]["value"]))
		self.stdscr.addstr(self.summaryBlock,60,"Failed jobs {0}".format(stats["failed"]["value"]))
		self.stdscr.addstr(self.summaryBlock,80,"Finished jobs {0}".format(stats["finished"]))
		self.stdscr.addstr(self.summaryBlock,100,"Unknown status {0}".format(stats["unknown"]))
		
		i=0
		self.wipeAttemptsBlock(self)
		for aNumber,[pend,run,fail] in enumerate(zip(stats["pending"]["attempts"], stats["running"]["attempts"], stats["failed"]["attempts"])):
			if aNumber==0 or i>= 4:
				continue
			if pend>0:
				self.stdscr.addstr(self.summaryBlock+1+i,25,str(pend))
			if run>0:
				self.stdscr.addstr(self.summaryBlock+1+i,45, str(run))
			if fail>0:
				self.stdscr.addstr(self.summaryBlock+1+i,65,str(fail))
			if pend>0 or run>0 or fail>0:
				self.stdscr.addstr(self.summaryBlock+1+i,5,"{0} attempts:".format(aNumber))
				i+=1
		if stats["failed"]["permanent"]>0:
			self.stdscr.addstr(self.summaryBlock+1+i,5,"Permanent:".format(aNumber))
			self.stdscr.addstr(self.summaryBlock+1+i,65,str(stats["failed"]["permanent"]))
		self.stdscr.hline(self.summaryBlock+1+5, 0, '-', 130)
		self.repaint()
