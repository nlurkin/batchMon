#!/usr/bin/python2.6
# encoding: utf-8
'''
batchTool -- shortdesc

batchTool is a description

It defines classes_and_methods

@author:     user_name
		
@copyright:  2014 organization_name. All rights reserved.
		
@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

from batchTool import Display, Monitor
from argparse import ArgumentParser
import curses
import sys
import time

__all__ = []
__version__ = 0.1
__date__ = '2014-05-15'
__updated__ = '2014-05-15'

mon = None

def mainInit(scr=None):
	global mon
	
	screen = Display()
	screen.setScreen(scr)
	screen.displayHeader(mon.config.getHeaders())
	try:
		while True:
			mainLoop(screen)
	except KeyboardInterrupt:
		mon.saveState()
		return
		

def mainLoop(screen):
	mon.monitor()
	screen.displayTime(mon.config.startTime)
	screen.displaySummary(mon.config.getStatusStats())
	time.sleep(2)

def argParser():
	global mon
	'''Command line options.'''
	
	#argv = sys.argv
	
	parser = ArgumentParser()
	parser.add_argument('-q', '--queue', action='store', default="1nh")
	parser.add_argument('-t', '--test', action='store_true')
	parser.add_argument('-n', '--name', action='store', default="config")
	parser.add_argument('-x', '--nocurse', action='store_true')
	groupNew = parser.add_mutually_exclusive_group(required=True)
	groupNew.add_argument("-c", "--config", action="store")
	groupNew.add_argument("-l", "--load", action="store")
	args = parser.parse_args()
	
	mon = Monitor()
	if args.config:
		mon.newBatch(args.config, args.name, args.queue, args.test)
	elif args.load:
		mon.loadBatch(args.load)


	if args.nocurse:
		mainInit()
	else:
		curses.wrapper(mainInit)

if __name__ == "__main__":
	sys.exit(argParser())
