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
		finalizeBlock = 30

	submitTotal = 0
	submitCurrent = 0
	
	submitIndex = (0,0)
	submitMaxIndex = (4,5)
	
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
	
	def getch(self):
		if self.stdscr == None:
			return
		try:
			return self.stdscr.getkey()
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
			
			self.stdscr.nooutrefresh()
			self.repaint()
	
	def repaint(self):
		self.headerWindow.nooutrefresh()
		self.jobsWindow.nooutrefresh()
		self.submitWindow.nooutrefresh()
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
		self.headerWindow.addstr(0,50, "LXBATCH job monitoring")
		self.headerWindow.move(0,0)
		self.headerWindow.chgat(curses.color_pair(1))
		self.headerWindow.addstr(1,0, "|",curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" CTRL-G: Generate jobs " ,curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" CTRL-T: Modify refresh rate " ,curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" CTRL-R: Reset failed jobs ",curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.addstr(" CTRL-C: Save and quit ",curses.color_pair(1))
		self.headerWindow.addch(ord('|'),curses.color_pair(1)|curses.A_REVERSE)
		self.headerWindow.chgat(curses.color_pair(1))
		self.headerWindow.addstr(4,0, "Monitor {0} (saved in {0}.json) on queue {1}".format(headers["name"], headers["queue"]))
		self.headerWindow.addstr(5,0, "Monitoring {0} jobs from card file {1} for a maximum of {2} attempts".format(
												headers["jobNumber"], headers["cardFile"], headers["maxAttempts"]))

	def displayTime(self, startTime):
		if self.stdscr == None:
			return
		td = datetime.datetime.now()-datetime.datetime.fromtimestamp(startTime)
		self.headerWindow.addstr(6,0, "Running since {0} ({1})      ".format(
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
	
	def displaySubmit(self, jobID, jobIndex):
		if self.stdscr == None:
			return
		self.submitCurrent += 1
		progress = (1.0*self.submitCurrent/self.submitTotal)*100
		
		self.submitWindow.addstr(1, 0, "Total progress: [{2:101}] {0}/{1}".format(self.submitCurrent,self.submitTotal, "#" * int(progress)))
		x,y = self.submitIndex
		self.submitWindow.addstr(2 + x,y*20, "{0} -> {1}".format(jobIndex, jobID))
		
		if x==self.submitMaxIndex[0]:
			if y==self.submitMaxIndex[1]:
				self.submitIndex = (0, 0)
				self.wipeSubmitBlock()
			else:
				self.submitIndex = (0, y+1)
		else:
			self.submitIndex = (x+1,y)
		self.repaint()
		
	
	def resetSubmit(self, total):
		return
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

'''	
	def displayFinalize(self):
		if self.stdscr==None:
			return
		self.stdscr.addstr(self.WinPositions.finalizeBlock, 0, "Finalization job result")
'''