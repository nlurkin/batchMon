'''
Created on 16 May 2014

@author: Nicolas Lurkin
'''
import curses
import datetime
import sys

first = True
def log(*text):
	global first
#	return
	mode = "a"
	if first:
		mode = "w"
		first = False
	with open("xxx",mode) as fd:
		fd.write("{}\n".format(str(text)))

class MyWindow(object):
	'''
	Base class for curses windows.
	''' 
	def __init__(self, px, py, screen):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self._stdscr = screen
		self._blockPosition = (px,py)
		self._windowHandles = []
		self._subWindows = []
		
	def repaint(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		for handle in self._windowHandles:
			handle.noutrefresh()
		for handle in self._subWindows:
			handle.repaint()
	
	def keyPressed(self, key):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		for handle in self._subWindows:
			ret = handle.keyPressed(key)
			if not ret is None:
				return ret
		return None
	
	def repaintFull(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		for handle in self._windowHandles:
			handle.redrawwin()
		for handle in self._subWindows:
			handle.repaintFull()
	
	def clear(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		for handle in self._windowHandles:
			handle.clear()
		for handle in self._subWindows:
			handle.clear()
		
	
class Header(MyWindow):
	'''
	Generic header window containing a title and a menu
	'''
	def __init__(self, vpos, screen, title):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		super(Header, self).__init__(0, vpos, screen)
		self._title = title
		self._menuList = []
	
	def addMenuEntry(self, key, text):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self._menuList.append((key,text))

	def generate(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		handle = curses.newwin(8, self._stdscr.getmaxyx()[1], self._blockPosition[0], self._blockPosition[1])
		
		handle.addstr(0,50, self._title)
		handle.move(0,0)
		handle.chgat(curses.color_pair(1))
		handle.move(1,0)
		for key,text in self._menuList:
			handle.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
			handle.addstr(" {}: {} ".format(key,text) ,curses.color_pair(1))
		handle.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		handle.chgat(curses.color_pair(1))
		
		self._windowHandles.append(handle)
		
class DCommands(object):
	NoCMD      = 0
	Select     = +1
	Back       = -1
	Delete     = -100
	Kill       = -101
	Refresh    = +100
	Submit     = +101
	Switch     = +102
	
	def __init__(self, Command, **kwargs):
		self.command = Command
		self.__dict__.update(kwargs)

###########################
# Classes for main display
#  - Main display as main container. Contains a header and a ListWindow
#  - ListWindow to display the job list
#
#  -------------------------------------------------------------------
#  |                            Header                               |
#  |-----------------------------------------------------------------|
#  |       ListWindow             |                                  |
#  -------------------------------------------------------------------
###########################
class ListWindow(MyWindow):
	
	class fieldsSize:
		nameField = 50
		sizeField = 20
		timeField = 20

	def __init__(self, px, py, dwidth, dheight, pwidth, pheight, screen):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		super(ListWindow, self).__init__(px, py, screen)
		
		# Window and pad sizes
		self._displayWidth = dwidth
		self._displayHeight = dheight
		self._padWidth = pwidth
		self._padHeight = pheight
		
		# Currently displayed
		self._currentWindowPos = 0
		self._currentCursorPos = 0
		
		# Elements
		self._listElements = []
		self._selectedElements = []
	
	def generate(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		
		self._windowHandles.append(curses.newpad(self._padHeight, self._padWidth))
	
	def repaint(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self._windowHandles[0].nooutrefresh(self._currentWindowPos, 0, self._blockPosition[1], self._blockPosition[0], self._blockPosition[1]+self._displayHeight, self._blockPosition[0]+self._displayWidth)
	
	def addElement(self, name):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self._listElements.append(name)
		
	def updateList(self, bList):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		
		self.selected = []
		
		for f in bList:
			self.addElement(f)

	def clearList(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		del self._listElements[:]
			
	def generateList(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		i = 0
		self._windowHandles[0].clear()
		for el in self._listElements:
			self._windowHandles[0].addstr(i, 2, "[ ] ")
			self._windowHandles[0].addnstr(el, ListWindow.fieldsSize.nameField)
			i = i + 1
		
		self.goTop()
	
	def goReset(self):
		''' Reset the display of the cursors '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		for i in range(0,len(self._listElements)):
			self.setStateChar(i, False)
	
	def goCheck(self, index):
		''' Verify that given index is valid, than call the scrolling check '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if len(self._listElements) == 0:
			return False
		if index < 0:
			return False
		if index >= len(self._listElements):
			return False
		self.goCheckScrolling(index)
		return True

	def goCheckScrolling(self, cursor):
		''' Verify if pad needs scrolling '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if cursor > (self._currentWindowPos + self._displayHeight):
			self._currentWindowPos += 1
		elif cursor < self._currentWindowPos:
			self._currentWindowPos -= 1

	def goTop(self):
		''' Go at the first element '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self.goReset()
		self._currentWindowPos = 0
		if not self.goCheck(0):
			return
		self._currentCursorPos = 0
		self.setStateChar(self._currentCursorPos, True)
	
	def goDown(self):
		''' Go down one element '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if not self.goCheck(self._currentCursorPos+1):
			return
		self.goReset()
		self._currentCursorPos += 1
		self.setStateChar(self._currentCursorPos, True)
		
	def goUp(self):
		''' Go up one element '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if not self.goCheck(self._currentCursorPos-1):
			return
		self.goReset()
		self._currentCursorPos -= 1
		self.setStateChar(self._currentCursorPos, True)
	
	def select(self):
		''' Select the current element '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if self._currentCursorPos in self._selectedElements:
			self._selectedElements.remove(self._currentCursorPos)
			self.setStateChar(self._currentCursorPos, True)
		else:
			self._selectedElements.append(self._currentCursorPos)
			self.setStateChar(self._currentCursorPos, False)
	
	def unselectAll(self):
		''' Deselect all elements '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		cp = self._selectedElements
		self._selectedElements = []
		for i in cp:
			self.setStateChar(i, i==self._currentCursorPos)

	def hideCursor(self):
		''' Hide the cursor '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self.setStateChar(self._currentCursorPos, False)

	def showCursor(self):
		''' Show the cursor '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self.setStateChar(self._currentCursorPos, True)

	def setStateChar(self, index, coming):
		''' Set the display of the cursor '''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if coming:
			self._windowHandles[0].addstr(index, 3, "*")
		else:
			if index in self.selected:
				self._windowHandles[0].addstr(index, 3, "x")
			else:
				self._windowHandles[0].addstr(index, 3, " ")
		
	def keyPressed(self, key):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if key == curses.KEY_DOWN:
			self.goDown()
		elif key == curses.KEY_UP:
			self.goUp()
		elif key == curses.KEY_RIGHT:
			return DCommands(DCommands.Select,index=self._currentCursorPos)
		elif key == curses.KEY_DC:
			return DCommands(DCommands.Delete, index=self._currentCursorPos)

class MainDisplay(MyWindow):
	def __init__(self, vpos, screen):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		super(MainDisplay, self).__init__(0, vpos, screen)
	
	def generate(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		header = Header(self._blockPosition[1], self._stdscr, "LXBATCH job monitoring")
		header.addMenuEntry("K", "Kill server")
		header.addMenuEntry("RIGHT", "Details of selected job")
		header.addMenuEntry("UP/DOWN", "Navigate jobs")
		header.addMenuEntry("DEL", "Remove batch")
		header.generate()
		self._subWindows.append(header)

		jobsList = ListWindow(0, self._blockPosition[1]+5, 150, 30, 150, 100, self._stdscr)
		jobsList.generate()
		self._subWindows.append(jobsList)
	
	def updateList(self, l):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self._subWindows[1].clearList()
		self._subWindows[1].updateList(l)
		self._subWindows[1].generateList()
	
	def keyPressed(self, key):
		if curses.unctrl(key) == "K":
			return DCommands(DCommands.Kill)

		return MyWindow.keyPressed(self, key)


##########################
# Classes to display single job
##########################


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
