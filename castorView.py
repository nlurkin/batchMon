#!/usr/bin/python
# encoding: utf-8
'''
batchTool -- LXBATCH monitoring tool

This tool can be used to start and monitor jobs on LXBATCH.
It will monitor every job individually and resubmit it in
ase of failure.
There is a maximum number of trials before the monitor
stops resubmitting the jobs.

@author:     Nicolas Lurkin
		
@contact:    nicolas.lurkin@cern.ch
'''
import curses
import os
import sys

from castorMC import WindowDisplay
from castorMC import FileExplorer, LocalConnector, FEIOError, CastorConnector


__version__ = 0.1
__date__ = '2014-05-15'
__updated__ = '2014-05-19'

fs1 = None
fs2 = None
screen = None

def mainInit(scr=None):
	global screen, fs1, fs2
	
	screen = WindowDisplay(scr)
	fs1 = FileExplorer(LocalConnector(screen), os.getcwd())
	fs2 = FileExplorer(CastorConnector(screen), "")
	screen.displayHeader()
	screen.displayLeftPath(fs1.currPath)
	screen.leftList.displayFiles(fs1.dirList, fs1.fileList)
	screen.displayRightPath(fs2.currPath)
	screen.rightList.displayFiles(fs2.dirList, fs2.fileList)
	screen.rightList.hideCursor()
	
	while True:
		try:
			mainLoop()
			pass
		except FEIOError as e:
			screen.printError(e.value)
		except KeyboardInterrupt:
			sys.exit(0)
			
def mainLoop():
	global screen
	
	screen.repaint()
	k = screen.getch()
	if k != -1:
		if curses.unctrl(k) == "^W":
			screen.switchList()
		elif k == curses.KEY_DOWN:
			screen.currList.goDown()
		elif k == curses.KEY_UP:
			screen.currList.goUp()
		elif curses.unctrl(k) == " ":
			screen.currList.select()
		elif curses.unctrl(k) == "c":
			copy()
		elif curses.unctrl(k) == "d":
			delete()
		elif k == curses.KEY_RIGHT:
			levelDown()
		elif k == curses.KEY_LEFT:
			levelUp()
		elif curses.unctrl(k) == "^D":
			sys.exit(0)

		
def levelDown():
	global screen, fs1, fs2
	if screen.currList == screen.leftList:
		if fs1.goDown(screen.currList.currentCursor):
			screen.leftList.displayFiles(fs1.dirList, fs1.fileList)
			screen.displayLeftPath(fs1.currPath)
	else:
		if fs2.goDown(screen.currList.currentCursor):
			screen.rightList.displayFiles(fs2.dirList, fs2.fileList)
			screen.displayRightPath(fs2.currPath)

def levelUp():
	global screen, fs1, fs2
	if screen.currList == screen.leftList:
		fs1.goUp()
		screen.leftList.displayFiles(fs1.dirList, fs1.fileList)
		screen.displayLeftPath(fs1.currPath)
	else:
		fs2.goUp()
		screen.rightList.displayFiles(fs2.dirList, fs2.fileList)
		screen.displayRightPath(fs2.currPath)

def copy():
	global screen, fs1, fs2
	ret = 0
	if screen.currList == screen.leftList:
		ret = fs1.copy(screen.currList.selected, fs2)
		fs2.refresh()
		screen.rightList.displayFiles(fs2.dirList, fs2.fileList)
	else:
		ret = fs2.copy(screen.currList.selected, fs1)
		fs1.refresh()
		screen.leftList.displayFiles(fs1.dirList, fs1.fileList)
	
	if ret==0:
		screen.printMessage("Copy successful")
		screen.currList.unselectAll()
	else:
		screen.printMessage("Copy failed")
	screen.repaint()

def delete():
	global screen, fs1, fs2
	ret = 0
	if not screen.confirm():
		return
	if screen.currList == screen.leftList:
		ret = fs1.delete(screen.currList.selected)
		fs1.refresh()
		screen.leftList.displayFiles(fs1.dirList, fs1.fileList)
	else:
		ret = fs2.delete(screen.currList.selected)
		fs2.refresh()
		screen.rightList.displayFiles(fs2.dirList, fs2.fileList)

	if ret==0:
		screen.printMessage("Delete successful")
	else:
		screen.printMessage("Delete failed")
	screen.repaint()
	
	
def argParser():
	curses.wrapper(mainInit)

if __name__ == "__main__":
	sys.exit(argParser())
