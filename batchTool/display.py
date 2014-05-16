'''
Created on 16 May 2014

@author: ncl
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
	summaryBlock = 8
	submitBlock = 16

	debugBlock = 25

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
	
	def getch(self):
		if self.stdscr == None:
			return
		try:
			return self.stdscr.getkey()
		except curses.error:
			return -1
		
	def setScreen(self, scr):
		self.stdscr = scr
		curses.curs_set(0)
		curses.start_color()
		curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
		curses.halfdelay(self.currentDelay*10)
	
	def wipeAttemptsBlock(self):
		for i in range(0,5):
			self.stdscr.move(self.summaryBlock+1+i,0)
			self.stdscr.clrtoeol()
	
	def repaint(self):
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
		self.stdscr.chgat(curses.color_pair(1))
		self.stdscr.addstr(self.headerBlock,0, "Monitoring {0} jobs from card file {1} for a maximum of {2} attempts".format(
												headers["jobNumber"], headers["cardFile"], headers["maxAttempts"]))
		self.stdscr.hline(self.summaryBlock-1, 0, '-', 130)
		self.stdscr.hline(self.submitBlock-1, 0, '-', 130)
		self.stdscr.addstr(self.submitBlock,50, "Job submitting status")
		self.repaint()
	
	def displayTime(self, startTime):
		if self.stdscr == None:
			return
		td = datetime.datetime.now()-datetime.datetime.fromtimestamp(startTime)
		self.stdscr.addstr(self.headerBlock+1,0, "Running since {0} ({1})      ".format(
													datetime.datetime.fromtimestamp(startTime).strftime('%Y-%m-%d %H:%M:%S'), 
													str(td)))
	
	def resetSubmit(self, total):
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
		self.stdscr.addstr(self.summaryBlock,20,"Pending jobs {0}".format(stats["pending"]["value"]))
		self.stdscr.addstr(self.summaryBlock,40,"Running jobs {0}".format(stats["running"]["value"]))
		self.stdscr.addstr(self.summaryBlock,60,"Failed jobs {0}".format(stats["failed"]["value"]))
		self.stdscr.addstr(self.summaryBlock,80,"Finished jobs {0}".format(stats["finished"]))
		self.stdscr.addstr(self.summaryBlock,100,"Unknown status {0}".format(stats["unknown"]))
		
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
