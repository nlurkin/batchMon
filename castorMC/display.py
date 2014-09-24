'''
Created on Sep 24, 2014

@author: ncl
'''

import curses

class WindowDisplay(object):
	'''
	classdocs
	'''

	class WinPositions:
		headerBlock = 0
		pathBlock = 3
		fileListBlock = 4
		fileListEnd = 30
		fileMiddle = 60
		messageBlock = 40
		errorBlock = 50
		

	currentDelay = 2
	
	headerWindow = None
	pathWindow = None
	fileListWindow = None
	messageWindow = None
	errorWindow = None

	leftList = None
	rightList = None
	
	currList = None
		
	def __init__(self, scr):
		'''
		Constructor
		'''
		self.stdscr = scr
		
		curses.curs_set(0)
		curses.start_color()
		curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
		curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
		curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)
		#curses.halfdelay(self.currentDelay*10)
		
		#setup all windows
		self.headerWindow = curses.newwin(8, self.stdscr.getmaxyx()[1], self.WinPositions.headerBlock, 0)
		#self.stdscr.hline(self.WinPositions.headerBlock+self.headerWindow.getmaxyx()[0], 0, '-', 130)
		self.pathWindow = curses.newwin(7, self.stdscr.getmaxyx()[1], self.WinPositions.pathBlock, 0)
		self.leftList = FileDisplay(self.WinPositions.fileListBlock, self.WinPositions.fileListEnd, 0)
		self.rightList = FileDisplay(self.WinPositions.fileListBlock, self.WinPositions.fileListEnd, self.WinPositions.fileMiddle)
		self.currList = self.leftList
		self.focusLeftPath()
		
		self.messageWindow = curses.newwin(4, self.stdscr.getmaxyx()[1], self.WinPositions.messageBlock, 0)
		self.errorWindow = curses.newwin(10, self.stdscr.getmaxyx()[1], self.WinPositions.errorBlock, 0)
		#self.fileListWindow = curses.newwin(0, self.stdscr.getmaxyx()[1], self.WinPositions.fileListBlock, 0)
		#self.fileListWindow = curses.newpad(3, self.stdscr.getmaxyx()[1])
		#self.stdscr.hline(self.WinPositions.summaryBlock+self.jobsWindow.getmaxyx()[0], 0, '-', 130)
		#self.submitWindow = curses.newwin(8, self.stdscr.getmaxyx()[1], self.WinPositions.submitBlock, 0)
		#self.submitWindow.addstr(0,50, "Job submission status")
		#self.stdscr.hline(self.WinPositions.submitBlock+self.submitWindow.getmaxyx()[0], 0, '-', 130)
		
		#self.erroWindow = curses.newwin(5, self.stdscr.getmaxyx()[1], self.WinPositions.debugBlock, 0)
		
		self.stdscr.nooutrefresh()
		self.repaint()
	
	def getch(self):
		try:
			return self.stdscr.getch()
		except curses.error:
			return -1

	def repaint(self):
		self.headerWindow.nooutrefresh()
		self.pathWindow.nooutrefresh()
		self.leftList.repaint()
		self.rightList.repaint()
		self.messageWindow.nooutrefresh()
		self.errorWindow.nooutrefresh()
		curses.doupdate()
	
	def displayHeader(self, headers):
		self.headerWindow.addstr(0,50, "CASTOR operation")
		self.headerWindow.move(0,0)
		self.headerWindow.chgat(curses.color_pair(1))
		#self.headerWindow.addstr(1,0, "|",curses.color_pair(1)|curses.A_REVERSE)
		#self.headerWindow.addstr(" CTRL-G: Generate jobs " ,curses.color_pair(1))
		#self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		#self.headerWindow.addstr(" CTRL-T: Modify refresh rate " ,curses.color_pair(1))
		#self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		#self.headerWindow.addstr(" CTRL-R: Reset failed jobs ",curses.color_pair(1))
		#self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		#self.headerWindow.addstr(" CTRL-C: Save and quit ",curses.color_pair(1))
		#self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		#self.headerWindow.chgat(curses.color_pair(1))
		#self.headerWindow.addstr(4,0, "Monitor {0} (saved in {0}.json) on queue {1}".format(headers["name"], headers["queue"]))
		#self.headerWindow.addstr(5,0, "Monitoring {0} jobs from card file {1} for a maximum of {2} attempts".format(
												#headers["jobNumber"], headers["cardFile"], headers["maxAttempts"]))

	def displayLeftPath(self, path):
		self.pathWindow.addstr(0, 5, "Dir: ")
		self.pathWindow.addstr(path)
		if self.currList == self.leftList:
			self.focusLeftPath()
		elif self.currList == self.rightList:
			self.focusRightPath()

	def displayRightPath(self, path):
		self.pathWindow.addstr(0, self.WinPositions.fileMiddle+5, "Dir: ")
		self.pathWindow.addstr(path)
		if self.currList == self.leftList:
			self.focusLeftPath()
		elif self.currList == self.rightList:
			self.focusRightPath()
	
	def printMessage(self, message):
		self.messageWindow.erase()
		self.messageWindow.addstr(0, 0, message)
		
	def printError(self, err):
		self.errorWindow.erase()
		self.errorWindow.addstr(0,0, err)
		self.errorWindow.refresh()
		
	def focusLeftPath(self):
		self.pathWindow.move(0,0)
		self.pathWindow.chgat(10, curses.color_pair(1))
		self.pathWindow.move(0,10)
		self.pathWindow.chgat(self.WinPositions.fileMiddle-10,curses.color_pair(2))
		self.pathWindow.move(0,self.WinPositions.fileMiddle)
		self.pathWindow.chgat(10, curses.color_pair(0))
		self.pathWindow.move(0,self.WinPositions.fileMiddle+10)
		self.pathWindow.chgat(self.WinPositions.fileMiddle-10, curses.color_pair(2))


	def focusRightPath(self):
		self.pathWindow.move(0,0)
		self.pathWindow.chgat(10, curses.color_pair(0))
		self.pathWindow.move(0,10)
		self.pathWindow.chgat(self.WinPositions.fileMiddle-10, curses.color_pair(2))
		self.pathWindow.move(0,self.WinPositions.fileMiddle)
		self.pathWindow.chgat(10, curses.color_pair(1))
		self.pathWindow.move(0,self.WinPositions.fileMiddle+10)
		self.pathWindow.chgat(self.WinPositions.fileMiddle-10, curses.color_pair(2))


	def switchList(self):
		if self.currList == self.leftList:
			self.currList = self.rightList
			self.focusRightPath()
		else:
			self.currList = self.leftList
			self.focusLeftPath()


class FileDisplay(object):
	'''
	classdocs
	'''
	

	def __init__(self, start, end, leftCorner):
		'''
		Constructor
		'''
		self.currentCursor = 0
		self.listLength = 0
		self.currentFileWinPos = 0
	
		self.fileListWindow = curses.newpad(100, 50)
		self.winStart = start
		self.winEnd = end
		self.winLeft = leftCorner

	def repaint(self):
		self.fileListWindow.nooutrefresh(self.currentFileWinPos, 0, self.winStart, self.winLeft, self.winEnd, self.winLeft+50)
	
	def displayFiles(self, dirList, fileList):
		self.fileListWindow.clear()
		
		i = 0
		for d in dirList:
			self.fileListWindow.addstr(i, 2, "[ ] ", curses.color_pair(3))
			self.fileListWindow.addstr(d, curses.color_pair(3))
			i = i + 1
		
		for f in fileList:
			self.fileListWindow.addstr(i, 2, "[ ] ")
			self.fileListWindow.addstr(f)
			i = i + 1
		
		self.listLength = len(dirList) + len(fileList)
		
		self.goTop()
	
	def goReset(self):
		for i in range(0,self.listLength):
			self.fileListWindow.addstr(i, 3, " ")
		
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
		self.fileListWindow.addstr(self.currentCursor, 3, "*")
		
	def goDown(self):
		if not self.goCheck(self.currentCursor+1):
			return
		self.goReset()
		self.currentCursor += 1
		self.fileListWindow.addstr(self.currentCursor, 3, "*")
		
	def goUp(self):
		if not self.goCheck(self.currentCursor-1):
			return
		self.goReset()
		self.currentCursor -= 1
		self.fileListWindow.addstr(self.currentCursor, 3, "*")