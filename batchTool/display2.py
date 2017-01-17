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
	
	def doUpdate(self, dataObject):
		pass
	
	def updateContent(self, dataObject):
		self.doUpdate(dataObject)
		for handle in self._subWindows:
			handle.updateContent(dataObject)
	
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

class DObject(object):
	
	def __init__(self, **kwargs):
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
			self._windowHandles[0].addnstr(el["name"], self.fieldsSize.nameField)
			self._windowHandles[0].addstr(i, self.fieldsSize.nameField, "{pending[value]} {running[value]} {failed[value]} {finished}".format(**el["stats"]))
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

	def goTo(self, index):
		if not self.goCheck(index):
			return
		self.goReset()
		self._currentCursor = index
		self.setStateChar(self._currentCursor, True)

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
	
	def doUpdate(self, dataObject):
		if hasattr(dataObject, "batchList"):
			self._updateList(dataObject.batchList)
	
	def _updateList(self, l):
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
class JobDisplay(MyWindow):
	def __init__(self, vpos, screen):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		super(JobDisplay, self).__init__(0, vpos, screen)
	
	def generate(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		header = Header(self._blockPosition[1]+0, self._stdscr, "LXBATCH job monitoring")
		header.addMenuEntry("CTRL-G", "Generate jobs")
		header.addMenuEntry("CTRL-T", "Modify refresh rate")
		header.addMenuEntry("CTRL-R", "Reset failed jobs")
		header.addMenuEntry("LEFT",   "Return to batch menu")
		header.addMenuEntry("CTRL-K", "Invert keep output")
		header.generate()
		self._subWindows.append(header)
		
		self._subWindows.append(JobHeaderWindow(4, self._stdscr))
		self._subWindows[1].generate()
		
		self._subWindows.append(SummaryWindow(9, self._stdscr))
		self._subWindows[2].generate()
		
		self._subWindows.append(SubmitWindow(17, self._stdscr))
		self._subWindows[3].generate()
		self._subWindows[3].clear()
		
		self._windowHandles.append(curses.newwin(1, self._stdscr.getmaxyx()[1], self._blockPosition[1]+3, self._blockPosition[0]))
	
	def hideSubmission(self):
		self._subWindows[3].clear()
	
	def updateSummary(self, headers):
		self._subWindows[1].updateContent(headers)
	
	def updateTime(self, startTime):
		self._subWindows[1].updateTime(startTime)
	
	def updateStats(self, stats):
		self._subWindows[2].updateContent(stats)
	
	def keyPressed(self, key):
		if key == curses.KEY_LEFT:
			return DCommands(DCommands.Back)
		elif curses.unctrl(key) == "^R":
			return DCommands(DCommands.Refresh)
		elif curses.unctrl(key) == "^G":
			return DCommands(DCommands.Submit)
		elif curses.unctrl(key) == "^K":
			return DCommands(DCommands.Switch)
		elif curses.unctrl(key) == "^T":
			self.setWaitingTime()
		return MyWindow.keyPressed(self, key)

	def initSubmission(self, total):
		self._subWindows[3].initSubmission(total)
		
	def updateSubmission(self, jobID, jobIndex, currentID):
		self._subWindows[3].addSubmission(jobID, jobIndex, currentID)
		
	def setWaitingTime(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		curses.nocbreak()
		curses.curs_set(2)
		curses.echo()
		self._windowHandles[0].addstr(0, 0, "Please enter a value in seconds (0-25): ")
		self._windowHandles[0].refresh()
		value = self._windowHandles[0].getstr()
		try:
			value = int(value)
		except ValueError:
			pass
		if value > 0 and value <= 25:
			curses.halfdelay(value*10)
		curses.curs_set(0)
		curses.noecho()
		self._windowHandles[0].clear()
		
class JobHeaderWindow(MyWindow):
	def __init__(self, vpos, screen):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		super(JobHeaderWindow, self).__init__(0, vpos, screen)
		
	def generate(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self._windowHandles.append(curses.newwin(7, self._stdscr.getmaxyx()[1], self._blockPosition[1], 0))
	
	def _updateHeader(self, headers):
		self._windowHandles[0].addstr(0,0, "Monitor {0} (saved in {0}.json) on queue {1}, keepOutput={2}".format(headers["name"], headers["queue"], headers['keep']))
		self._windowHandles[0].addstr(1,0, "Monitoring {0} jobs from card file {1} for a maximum of {2} attempts".format(
								headers["jobNumber"], headers["cardFile"], headers["maxAttempts"]))

	def doUpdate(self, dataObject):
		if hasattr(dataObject, "startTime"):
			self._updateTime(dataObject.startTime)
		if hasattr(dataObject, "jobHeader"):
			self._updateHeader(dataObject.jobHeader)
		
	def _updateTime(self, startTime):
		td = datetime.datetime.now()-datetime.datetime.fromtimestamp(startTime)
		self._windowHandles[0].addstr(2,0, "Running since {0} ({1})	  ".format(
							datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S'),
							str(td)))

class SummaryWindow(MyWindow):
	def __init__(self, vpos, screen):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		super(SummaryWindow, self).__init__(0, vpos, screen)
	
	def generate(self):
		self._windowHandles.append(curses.newwin(8, self._stdscr.getmaxyx()[1], self._blockPosition[1], 0))

	def doUpdate(self, dataObject):
		if hasattr(dataObject, "jobStats"):
			self._updateStats(dataObject.jobStats)

	def _updateStats(self, stats):
		self._windowHandles[0].addstr(0,0,"Failed attempts")
		self._windowHandles[0].addstr(0,20,"Pending jobs {0}   ".format(stats["pending"]["value"]))
		self._windowHandles[0].addstr(0,40,"Running jobs {0}   ".format(stats["running"]["value"]))
		self._windowHandles[0].addstr(0,60,"Failed jobs {0}   ".format(stats["failed"]["value"]))
		self._windowHandles[0].addstr(0,80,"Finished jobs {0}   ".format(stats["finished"]))
		self._windowHandles[0].addstr(0,100,"Unknown status {0}   ".format(stats["unknown"]))
		
		i=0
		for aNumber,[pend,run,fail] in enumerate(zip(stats["pending"]["attempts"], stats["running"]["attempts"], stats["failed"]["attempts"])):
			if aNumber==0 or i>= self._windowHandles[0].getmaxyx()[0]-1:
				continue
			if pend>0:
				self._windowHandles[0].addstr(1+i,25,str(pend))
			if run>0:
				self._windowHandles[0].addstr(1+i,45, str(run))
			if fail>0:
				self._windowHandles[0].addstr(1+i,65,str(fail))
			if pend>0 or run>0 or fail>0:
				self._windowHandles[0].addstr(1+i,5,"{0} attempts:".format(aNumber))
				i+=1
		if stats["failed"]["permanent"]>0:
			self._windowHandles[0].addstr(1+i,5,"Permanent:".format(aNumber))
			self._windowHandles[0].addstr(1+i,65,str(stats["failed"]["permanent"]))

class SubmitWindow(MyWindow):
	_submitMaxIndex = (4,4)
	
	def __init__(self, vpos, screen):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		super(SubmitWindow, self).__init__(0, vpos, screen)
		
		self._submitTotal = 0
		self._submitCurrent = 0
		self._submitIndex = (0,0)
		
	
	def generate(self):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		
		self._windowHandles.append(curses.newwin(8, self._stdscr.getmaxyx()[1], self._blockPosition[1], self._blockPosition[0]))
		self._windowHandles[0].addstr(0,0, "Job submission status")

	def initSubmission(self, total):
		self._submitTotal = total
		self.clear()
		self.repaintFull()
		
	def doUpdate(self, dataObject):
		if hasattr(dataObject, "jobSubmit"):
			self._addSubmission(dataObject.jobID, dataObject.jobIndex, dataObject.currentID)

	def _addSubmission(self, jobID, jobIndex, currentID):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		progress = ((1.0*currentID+1)/self._submitTotal)*100
		
		x,y = self._submitIndex

		if x>=self._submitMaxIndex[0]:
			if y>self._submitMaxIndex[1]:
				self._submitIndex = (0, 0)
				self.wipeSubmitBlock()
			else:
				self._submitIndex = (0, y+1)
		else:
			self._submitIndex = (x+1,y)
		
		self._windowHandles[0].addstr(1, 0, "Total progress: [{2:101}] {0}/{1}".format(currentID+1,self._submitTotal, "#" * int(progress)))
		self._windowHandles[0].addstr(2 + self._submitIndex[0],self._submitIndex[1]*20, "{0} -> {1}".format(jobIndex, jobID))
		
		self.repaint()

	

class Display2:
	'''
	Class for displaying things on screen
	'''
	
	finalWindow = None
	erroWindow = None
	
	def __init__(self):
		'''
		Constructor
		'''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self.stdscr = None
		
		self.mainWindow = None
		self.jobWindow = None

		self.active = None
	
	def getch(self):
		'''
		Get a typed keyboard character
		'''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if self.stdscr == None:
			return
		try:
			return self.stdscr.getch()
		except curses.error:
			return -1
		
	def setScreen(self, scr):
		'''
		Set the screen and create the different windows 
		'''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self.stdscr = scr
		if self.stdscr != None:
			curses.curs_set(0)
			curses.start_color()
			curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
			curses.halfdelay(2*10)
			
			#setup all windows
			self.mainWindow = MainDisplay(0, self.stdscr)
			
			#self.stdscr.hline(self.WinPositions.headerBlock+self.headerWindow.getmaxyx()[0], 0, '-', 130)
			self.jobWindow = JobDisplay(0, self.stdscr)
			#self.stdscr.hline(self.WinPositions.summaryBlock+self.jobsWindow.getmaxyx()[0], 0, '-', 130)
			##self.stdscr.hline(self.WinPositions.submitBlock+self.submitWindow.getmaxyx()[0], 0, '-', 130)

			
			##self.erroWindow = curses.newwin(5, self.stdscr.getmaxyx()[1], self.WinPositions.debugBlock, 0)
			##self.finalWindow = curses.newwin(3, self.stdscr.getmaxyx()[1], self.WinPositions.finalizeBlock, 0)
			##self.finalWindow.addstr(0, 50, "Finalization job result")
			##self.stdscr.hline(self.WinPositions.finalizeBlock+self.submitWindow.getmaxyx()[0], 0, '-', 130)
			##			
			##self.stdscr.nooutrefresh()
			##self.repaint()
			
			self.mainWindow.generate()
			self.jobWindow.generate()
			self.stdscr.refresh()
			self.activateMainWindow()
	
	def repaint(self):
		'''
		Repaint the screen.
		'''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if self.stdscr==None or self.active==None:
			return
		
		self.active.repaint()
		curses.doupdate()
	
	def activateMainWindow(self):
		'''
		Set the main window as the currently displayed window
		'''
		if self.active == self.mainWindow:
			return
		self.active = self.mainWindow
		self.mainWindow.repaintFull()
		self.repaint()
	
	def activateJobWindow(self):
		'''
		Set the job window as the currently displayed window
		'''
		if self.active == self.jobWindow:
			return
		self.active = self.jobWindow
		self.jobWindow.repaintFull()
		self.repaint()
	
	
	def updateContent(self, dataObject):
		self.active.updateContent(dataObject)
	
	def resetSubmit(self, total):
		'''
		Reset job submissions
		'''
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self.jobWindow.initSubmission(total)
	
	def keyPressed(self, k):
		'''
		Propagate pressed key to the active window 
		'''
		return self.active.keyPressed(k)
		
	def _setError(self, strerr):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		self.erroWindow.addstr(0, 0, strerr)

	def _displayFinalJob(self, job):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if self.stdscr==None:
			return
			
		self.finalWindow.addstr(1, 0, "JobID: %s" % job.jobID)
		self.finalWindow.addstr(1, 30, "Status: %s" % job.status)
	
	def _displayFinalResult(self, job):
		log(self.__class__.__name__, sys._getframe().f_code.co_name)
		if self.stdscr==None:
			return

