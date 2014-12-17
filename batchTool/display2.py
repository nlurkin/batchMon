'''
Created on 16 May 2014

@author: Nicolas Lurkin
'''
import curses
import datetime

class Display2:
	'''
	Class for displaying things on screen
	'''
	
	class WinPositions:
		headerBlock = 0
		summaryBlock = 9
		submitBlock = 17

		debugBlock = 50
		finalizeBlock = 20

	submitMaxIndex = (4,4)
	
	currentDelay = 2
	
	headerWindow = None
	jobsWindow = None
	submitWindow = None
	finalWindow = None
	erroWindow = None
	
	def __init__(self):
		'''
		Constructor
		'''
		self.stdscr = None
		self.displayList = False
		self.submitTotal = 0
		self.submitCurrent = 0
		self.submitIndex = (-1,0)

	
	def getch(self):
		if self.stdscr == None:
			return
		try:
			return self.stdscr.getch()
		except curses.error:
			return -1
		
	def setScreen(self, scr):
		self.stdscr = scr
		if self.stdscr != None:
			curses.curs_set(0)
			curses.start_color()
			curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
			curses.halfdelay(self.currentDelay*10)
			
			#setup all windows
			self.headerWindow = curses.newwin(8, self.stdscr.getmaxyx()[1], self.WinPositions.headerBlock, 0)
			self.stdscr.hline(self.WinPositions.headerBlock+self.headerWindow.getmaxyx()[0], 0, '-', 130)
			self.jobsWindow = curses.newwin(7, self.stdscr.getmaxyx()[1], self.WinPositions.summaryBlock, 0)
			self.stdscr.hline(self.WinPositions.summaryBlock+self.jobsWindow.getmaxyx()[0], 0, '-', 130)
			self.submitWindow = curses.newwin(8, self.stdscr.getmaxyx()[1], self.WinPositions.submitBlock, 0)
			self.submitWindow.addstr(0,50, "Job submission status")
			self.stdscr.hline(self.WinPositions.submitBlock+self.submitWindow.getmaxyx()[0], 0, '-', 130)
			
			self.erroWindow = curses.newwin(5, self.stdscr.getmaxyx()[1], self.WinPositions.debugBlock, 0)
			self.finalWindow = curses.newwin(3, self.stdscr.getmaxyx()[1], self.WinPositions.finalizeBlock, 0)
			self.finalWindow.addstr(0, 50, "Finalization job result")
			self.stdscr.hline(self.WinPositions.finalizeBlock+self.submitWindow.getmaxyx()[0], 0, '-', 130)
						
			self.stdscr.nooutrefresh()
			self.repaint()
	
	def repaint(self):
		if self.stdscr==None:
			return
		if self.displayList:
			self.headerWindow.nooutrefresh()
			self.batchList.repaint()
		else:
			self.headerWindow.nooutrefresh()
			self.jobsWindow.nooutrefresh()
			self.submitWindow.nooutrefresh()
			self.finalWindow.nooutrefresh()
			self.erroWindow.nooutrefresh()
		curses.doupdate()
	
	def wipeJobsWindow(self):
		self.jobsWindow.erase()
	
	def wipeSubmitBlock(self):
		self.submitWindow.clear()
		self.submitWindow.addstr(0,50, "Job submission status")
			
	def displayHeader(self, headers):
		if self.stdscr == None:
			return
		self.headerWindow.clear()
		self.headerWindow.addstr(0,50, "LXBATCH job monitoring")
		self.headerWindow.move(0,0)
		self.headerWindow.chgat(curses.color_pair(1))
		self.headerWindow.addstr(1,0, "|",curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" CTRL-G: Generate jobs " ,curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		#self.headerWindow.addstr(" CTRL-T: Modify refresh rate " ,curses.color_pair(1))
		#self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" CTRL-R: Reset failed jobs ",curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" LEFT: Return to batch menu ",curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" CTRL-K: Invert keep output ",curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.chgat(curses.color_pair(1))
		self.headerWindow.addstr(4,0, "Monitor {0} (saved in {0}.json) on queue {1}, keepOutput={2}".format(headers["name"], headers["queue"], headers['keep']))
		self.headerWindow.addstr(5,0, "Monitoring {0} jobs from card file {1} for a maximum of {2} attempts".format(
												headers["jobNumber"], headers["cardFile"], headers["maxAttempts"]))
	
	def displayMainHeader(self):
		if self.stdscr == None:
			return
		self.headerWindow.clear()
		self.headerWindow.addstr(0,50, "LXBATCH job monitoring")
		self.headerWindow.move(0,0)
		self.headerWindow.chgat(curses.color_pair(1))
		self.headerWindow.addstr(1,0, "|",curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" K: Kill server " ,curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" RIGHT: Details of selected job " ,curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" UP/DOWN: Navigate jobs ",curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" DEL: Remove batch ",curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.chgat(curses.color_pair(1))
		
	def displayTime(self, startTime):
		if self.stdscr == None:
			return
		td = datetime.datetime.now()-datetime.datetime.fromtimestamp(startTime)
		self.headerWindow.addstr(6,0, "Running since {0} ({1})	  ".format(
													datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S'), 
													str(td)))

	def displaySummary(self, stats):
		if self.stdscr == None:
			return
		
		self.wipeJobsWindow()
		
		self.jobsWindow.addstr(0,0,"Failed attempts")
		self.jobsWindow.addstr(0,20,"Pending jobs {0}   ".format(stats["pending"]["value"]))
		self.jobsWindow.addstr(0,40,"Running jobs {0}   ".format(stats["running"]["value"]))
		self.jobsWindow.addstr(0,60,"Failed jobs {0}   ".format(stats["failed"]["value"]))
		self.jobsWindow.addstr(0,80,"Finished jobs {0}   ".format(stats["finished"]))
		self.jobsWindow.addstr(0,100,"Unknown status {0}   ".format(stats["unknown"]))
		
		i=0
		for aNumber,[pend,run,fail] in enumerate(zip(stats["pending"]["attempts"], stats["running"]["attempts"], stats["failed"]["attempts"])):
			if aNumber==0 or i>= self.jobsWindow.getmaxyx()[0]-1:
				continue
			if pend>0:
				self.jobsWindow.addstr(1+i,25,str(pend))
			if run>0:
				self.jobsWindow.addstr(1+i,45, str(run))
			if fail>0:
				self.jobsWindow.addstr(1+i,65,str(fail))
			if pend>0 or run>0 or fail>0:
				self.jobsWindow.addstr(1+i,5,"{0} attempts:".format(aNumber))
				i+=1
		if stats["failed"]["permanent"]>0:
			self.jobsWindow.addstr(1+i,5,"Permanent:".format(aNumber))
			self.jobsWindow.addstr(1+i,65,str(stats["failed"]["permanent"]))
	
	def displaySubmit(self, jobID, jobIndex, currentID):
		if self.stdscr == None:
			return
		#self.submitCurrent += 1
		progress = ((1.0*currentID+1)/self.submitTotal)*100
		
		x,y = self.submitIndex

		#print self.submitIndex
		if x>=self.submitMaxIndex[0]:
			#print "pass1"
			if y>self.submitMaxIndex[1]:
				#print "pass2"
				#print "wipe"
				self.submitIndex = (0, 0)
				self.wipeSubmitBlock()
			else:
				#print "not pass 2"
				self.submitIndex = (0, y+1)
		else:
			#print "not pass 1"
			self.submitIndex = (x+1,y)
		
		#print self.submitIndex
		self.submitWindow.addstr(1, 0, "Total progress: [{2:101}] {0}/{1}".format(currentID+1,self.submitTotal, "#" * int(progress)))
		self.submitWindow.addstr(2 + self.submitIndex[0],self.submitIndex[1]*20, "{0} -> {1}".format(jobIndex, jobID))
		
		self.repaint()
		
	
	def resetSubmit(self, total):
		if self.stdscr == None:
			return
		self.wipeSubmitBlock()
		self.submitTotal = total
		self.submitCurrent = 0
		self.submitIndex = (0,0)
	
	def setWaitingTime(self):
		if self.stdscr == None:
			return
		curses.nocbreak()
		curses.curs_set(2)
		curses.echo()
		self.headerWindow.addstr(2, 0, "Please enter a value in seconds (0-25): ")
		self.headerWindow.refresh()
		value = self.headerWindow.getstr()
		try:
			value = int(value)
		except ValueError:
			value = self.currentDelay
		if value > 0 and value <= 25:
			self.currentDelay = value
			curses.halfdelay(value*10)
		curses.curs_set(0)
		curses.noecho()
		self.headerWindow.move(2, 0)
		self.headerWindow.clrtoeol()

	def setError(self, strerr):
		self.erroWindow.addstr(0, 0, strerr)

	def displayBatchList(self, l):
		if self.stdscr==None:
			return
		self.stdscr.clear()
		self.stdscr.refresh()
		self.displayList = True
		self.displayMainHeader()
		self.batchList = FileDisplay(5, 30, 0, 150)
		self.batchList.displayFiles(l)
		#self.repaint()
		
	def reset(self):
		self.displayList = False
		self.stdscr.clear()
		self.stdscr.refresh()
	
	def displayFinalJob(self, job):
		if self.stdscr==None:
			return
			
		self.finalWindow.addstr(1, 0, "JobID: %s" % job.jobID)
		self.finalWindow.addstr(1, 30, "Status: %s" % job.status)
	
	def displayFinalResult(self, job):
		if self.stdscr==None:
			return
		

class FileDisplay(object):
	'''
	classdocs
	'''
	
	class fieldsSize:
		nameField = 50
		sizeField = 20
		timeField = 20

	def __init__(self, start, end, leftCorner, width):
		'''
		Constructor
		'''
		self.currentCursor = 0
		self.listLength = 0
		self.currentFileWinPos = 0
	
		self.fileListWindow = curses.newpad(100, width)
		self.winStart = start
		self.winEnd = end
		self.winLeft = leftCorner
		self.width = width
		self.selected = []

	def repaint(self):
		#raise Exception(self.currentFileWinPos.__str__() + "0" + self.winStart.__str__() + self.winLeft.__str__() + self.winEnd.__str__() + (self.winLeft+self.width).__str__())
		self.fileListWindow.nooutrefresh(self.currentFileWinPos, 0, self.winStart, self.winLeft, self.winEnd, self.winLeft+self.width)
	
	def displayFiles(self, bList):
		self.fileListWindow.clear()
		
		self.selected = []
		
		i = 0
		for f in bList:
			self.fileListWindow.addstr(i, 2, "[ ] ")
			self.fileListWindow.addnstr(f, self.fieldsSize.nameField)
			i = i + 1
		
		self.listLength = len(bList)
		
		self.goTop()
	
	def goReset(self):
		for i in range(0,self.listLength):
			self.setStateChar(i, False)
		
	def goCheck(self, index):
		if self.listLength==0:
			return False
		if index < 0:
			return False
		if index >= self.listLength:
			return False
		self.goCheckScrolling(index)
		return True
	
	def goCheckScrolling(self, cursor):
		if cursor > (self.currentFileWinPos + (self.winEnd - self.winStart)):
			self.currentFileWinPos += 1
		elif cursor < self.currentFileWinPos:
			self.currentFileWinPos -= 1
		
	def goTop(self):
		self.goReset()
		self.currentFileWinPos = 0
		if not self.goCheck(0):
			return
		self.currentCursor = 0
		self.setStateChar(self.currentCursor, True)
		
	def goDown(self):
		if not self.goCheck(self.currentCursor+1):
			return
		self.goReset()
		self.currentCursor += 1
		self.setStateChar(self.currentCursor, True)
		
	def goUp(self):
		if not self.goCheck(self.currentCursor-1):
			return
		self.goReset()
		self.currentCursor -= 1
		self.setStateChar(self.currentCursor, True)
	
	def select(self):
		if self.currentCursor in self.selected:
			self.selected.remove(self.currentCursor)
			self.setStateChar(self.currentCursor, True)
		else:
			self.selected.append(self.currentCursor)
			self.setStateChar(self.currentCursor, False)
	
	def unselectAll(self):
		cp = self.selected
		self.selected = []
		for i in cp:
			self.setStateChar(i, i==self.currentCursor)
	
	def hideCursor(self):
		self.setStateChar(self.currentCursor, False)

	def showCursor(self):
		self.setStateChar(self.currentCursor, True)
		
	def setStateChar(self, index, coming):
		if coming:
			self.fileListWindow.addstr(index, 3, "*")
		else:
			if index in self.selected:
				self.fileListWindow.addstr(index, 3, "x")
			else:
				self.fileListWindow.addstr(index, 3, " ")
		
	def getSize(self, nBytes):
		for x in ['bytes','KB','MB','GB','TB']:
			if nBytes < 1024.0:
				return "%3.1f %s" % (nBytes, x)
			nBytes /= 1024.0
	
	def getTime(self, mtime):
		return datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
