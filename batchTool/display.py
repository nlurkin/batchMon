'''
Created on 16 May 2014

@author: Nicolas Lurkin
'''
import curses
import datetime

class Display:
	'''
	Class for displaying things on screen
	'''
	titleBlock = 0
	menuBlock = 1
	inputBlock = 2
	headerBlock = 4
	summaryBlock = 9
	submitBlock = 17

	debugBlock = 30
	finalizeBlock = 30

	submitTotal = 0
	submitCurrent = 0
	
	submitIndex = (0,0)
	submitMaxIndex = (4,5)
	
	currentDelay = 2
	
	def __init__(self):
		'''
		Constructor
		'''
		self.stdscr = None
		self.displayList = False
	
	def getch(self):
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
	
	def wipeAttemptsBlock(self):
		for i in range(0,5):
			self.stdscr.move(self.summaryBlock+1+i,0)
			self.stdscr.clrtoeol()
	
	def repaint(self):
		if self.displayList:
			self.batchList.repaint()
			
		self.stdscr.refresh()
	
	def displayHeader(self, headers):
		if self.stdscr == None:
			return
		self.stdscr.addstr(self.titleBlock,50, "LXBATCH job monitoring")
		self.stdscr.move(self.titleBlock,0)
		self.stdscr.chgat(curses.color_pair(1))
		self.stdscr.addstr(self.menuBlock,0, "|",curses.color_pair(1)|curses.A_REVERSE)
		self.stdscr.addstr(" CTRL-G: Generate jobs " ,curses.color_pair(1))
		self.stdscr.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.stdscr.addstr(" CTRL-T: Modify refresh rate " ,curses.color_pair(1))
		self.stdscr.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.stdscr.addstr(" CTRL-R: Reset failed jobs ",curses.color_pair(1))
		self.stdscr.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.stdscr.addstr(" CTRL-C: Save and quit ",curses.color_pair(1))
		self.stdscr.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.stdscr.chgat(curses.color_pair(1))
		self.stdscr.addstr(self.headerBlock,0, "Monitor {0} (saved in {0}.json) on queue {1}".format(headers["name"], headers["queue"]))
		self.stdscr.addstr(self.headerBlock+1,0, "Monitoring {0} jobs from card file {1} for a maximum of {2} attempts".format(
												headers["jobNumber"], headers["cardFile"], headers["maxAttempts"]))
		self.stdscr.hline(self.summaryBlock-1, 0, '-', 130)
		self.stdscr.hline(self.submitBlock-1, 0, '-', 130)
		self.stdscr.addstr(self.submitBlock,50, "Job submission status")
		self.repaint()
	
	def displayTime(self, startTime):
		if self.stdscr == None:
			return
		td = datetime.datetime.now()-datetime.datetime.fromtimestamp(startTime)
		self.stdscr.addstr(self.headerBlock+2,0, "Running since {0} ({1})      ".format(
													datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S'), 
													str(td)))
	
	def resetSubmit(self, total):
		if self.stdscr == None:
			return
		self.stdscr.move(self.submitBlock+2,0)
		self.stdscr.clrtoeol()
		self.wipeSubmitBlock()
		self.submitTotal = total
		self.submitCurrent = 0
		self.submitIndex = (0,0)
	
	def wipeSubmitBlock(self):
		for i in range(0,5):
			self.stdscr.move(self.submitBlock+3+i,0)
			self.stdscr.clrtoeol()
		
	def displaySubmit(self, jobID, jobIndex):
		if self.stdscr == None:
			return
		self.submitCurrent += 1
		progress = (1.0*self.submitCurrent/self.submitTotal)*100
		
		self.stdscr.addstr(self.submitBlock+2, 0, "Total progress: [{2:101}] {0}/{1}".format(self.submitCurrent,self.submitTotal, "#" * int(progress)))
		x,y = self.submitIndex
		self.stdscr.addstr(self.submitBlock+3 + x,y*20, "{0} -> {1}".format(jobIndex, jobID))
		
		if x==self.submitMaxIndex[0]:
			if y==self.submitMaxIndex[1]:
				self.submitIndex = (0, 0)
				self.wipeSubmitBlock()
			else:
				self.submitIndex = (0, y+1)
		else:
			self.submitIndex = (x+1,y)
		#self.stdscr.addstr(0, 0, "Deleting file: {0}                                 ".format(currFile))
		self.repaint()
	
	def displaySummary(self, stats):
		if self.stdscr == None:
			return
		self.stdscr.addstr(self.summaryBlock,0,"Failed attempts")
		self.stdscr.addstr(self.summaryBlock,20,"Pending jobs {0}   ".format(stats["pending"]["value"]))
		self.stdscr.addstr(self.summaryBlock,40,"Running jobs {0}   ".format(stats["running"]["value"]))
		self.stdscr.addstr(self.summaryBlock,60,"Failed jobs {0}   ".format(stats["failed"]["value"]))
		self.stdscr.addstr(self.summaryBlock,80,"Finished jobs {0}   ".format(stats["finished"]))
		self.stdscr.addstr(self.summaryBlock,100,"Unknown status {0}   ".format(stats["unknown"]))
		
		i=0
		self.wipeAttemptsBlock()
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
		self.repaint()
	
	def setWaitingTime(self):
		if self.stdscr == None:
			return
		curses.nocbreak()
		curses.curs_set(2)
		curses.echo()
		self.stdscr.addstr(self.inputBlock, 0, "Please enter a value in seconds (0-25): ")
		value = self.stdscr.getstr()
		try:
			value = int(value)
		except ValueError:
			value = self.currentDelay
		if value > 0 and value <= 25:
			self.currentDelay = value
			curses.halfdelay(value*10)
		curses.curs_set(0)
		curses.noecho()
		self.stdscr.move(self.titleBlock+2, 0)
		self.stdscr.clrtoeol()

	def setError(self, strerr):
		for i,line in enumerate(strerr.splitlines()):
			self.stdscr.addstr(self.debugBlock+i, 0, strerr)
		self.repaint()

	def displayFinalize(self):
		if self.stdscr==None:
			return
		self.stdscr.addstr(self.finalizeBlock, 0, "Finalization job result")
		
	def displayBatchList(self, l):
		self.stdscr.clear()
		self.displayList = True
		self.batchList = FileDisplay(5, 30, 0, 150)
		self.batchList.displayFiles(l)
		
	def reset(self):
		self.displayList = False
		self.stdscr.clear()
		self.stdscr.refresh()
		
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

