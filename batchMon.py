#!/usr/bin/env python
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

__version__ = 0.1
__date__ = '2014-05-15'
__updated__ = '2014-05-19'

from batchTool import Display2, Monitor
from batchTool import BatchToolExceptions as BatchToolException
try:
	from argparse import ArgumentParser, RawDescriptionHelpFormatter
except ImportError:
	from batchTool.argparse import ArgumentParser, RawDescriptionHelpFormatter
import curses
import sys

mon = None

def mainInit(scr=None):
	global mon
	
	screen = Display2()
	screen.setScreen(scr)
	screen.displayHeader(mon.config.getHeaders())
	try:
		while True:
			try:
				mainLoop(screen)
			except BatchToolException.ErrorMessage as e:
				screen.setError(e.strerror)

	except KeyboardInterrupt:
		mon.saveState()
		return
	except Exception:
		mon.saveState()
		raise
		

def mainLoop(screen):
	mon.monitor(screen)
	screen.displayTime(mon.config.startTime)
	screen.displaySummary(mon.config.getStatusStats())
	
	if mon.config.finalizeFinished():
		screen.displayFinalResult(mon.config.finalJob)
	
	if mon.submitReady:
		if len(mon.submitList)==0:
			screen.resetSubmit(mon.config.getJobsNumberReady())
		else:
			screen.resetSubmit(len(mon.submitList))
		for job in mon.generateJobs():
			mon.submit(job)
			screen.displaySubmit(job.jobID, job.index)
	
	screen.repaint()
	k = screen.getch()
	if k != -1:
		if screen.stdscr!=None:
			if curses.unctrl(k) == "^R":
				mon.reSubmitFailed()
			if curses.unctrl(k) == "^T":
				screen.setWaitingTime()
			if curses.unctrl(k) == "^G":
				mon.submitInit()
	
def argParser():
	global mon
	'''Command line options.'''
	
	parser = ArgumentParser(description=__import__('__main__').__doc__.split("\n")[1], formatter_class=RawDescriptionHelpFormatter)
	parser.add_argument('-q', '--queue', action='store', default="1nh", 
					help="Indicates on which LXBATCH queue the jobs will be submitted (default:1nh)")
	parser.add_argument('-t', '--test', action='store_true', 
					help="Test the existence of output files. Do not regenerate jobs for which the output file already exists (non-tested feature)")
	parser.add_argument('-n', '--name', action='store', default="config", 
					help="Name of the monitor (used for later recovery, default:config)")
	parser.add_argument('-x', '--nocurse', action='store_true', 
					help="Disable the curse interface")
	parser.add_argument('-k', '--keep', action='store_true',
					help="Do not delete the LXBATCH output (LSFJOB_xxxxxxx)")
	groupNew = parser.add_mutually_exclusive_group(required=True)
	groupNew.add_argument("-c", "--config", action="store",
						help="Configuration file to use (new monitor)")
	groupNew.add_argument("-l", "--load", action="store",
						help="Reload a previous monitor (restart tracking the jobs, do not regenerate them)")
	args = parser.parse_args()
	
	mon = Monitor(args.keep)
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
