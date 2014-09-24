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
from castorMC import FileExplorer, LocalConnector, FEIOError


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
	fs2 = FileExplorer(LocalConnector(screen), "")
	screen.displayHeader("xxx")
	screen.displayLeftPath(fs1.currPath)
	screen.leftList.displayFiles(fs1.dirList, fs1.fileList)
	screen.displayRightPath(fs2.currPath)
	screen.rightList.displayFiles(fs2.dirList, fs2.fileList)
	
	while True:
		try:
			mainLoop()
		except FEIOError as e:
			screen.printError(e.value)
			
def mainLoop():
	global screen
	
	screen.repaint()
	k = screen.getch()
	if k != -1:
		if curses.unctrl(k) == "^D":
			sys.exit(0)
		if curses.unctrl(k) == "^W":
			screen.switchList()
		if k == curses.KEY_DOWN:
			screen.currList.goDown()
		if k == curses.KEY_UP:
			screen.currList.goUp()
		if curses.unctrl(k) == "c":
			copy()
		if curses.unctrl(k) == "d":
			delete()


def copy():
	global screen, fs1, fs2
	ret = 0
	if screen.currList == screen.leftList:
		ret = fs1.copy(screen.currList.currentCursor, fs2)
		fs2.refresh()
		screen.rightList.displayFiles(fs2.dirList, fs2.fileList)
	else:
		ret = fs2.copy(screen.currList.currentCursor, fs1)
		fs1.refresh()
		screen.leftList.displayFiles(fs1.dirList, fs1.fileList)

	if ret==0:
		screen.printMessage("Copy successful")
	else:
		screen.printMessage("Copy failed")
	screen.repaint()

def delete():
	global screen, fs1, fs2
	ret = 0
	if screen.currList == screen.leftList:
		ret = fs1.delete(screen.currList.currentCursor)
		fs1.refresh()
		screen.leftList.displayFiles(fs1.dirList, fs1.fileList)
	else:
		ret = fs2.delete(screen.currList.currentCursor)
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
