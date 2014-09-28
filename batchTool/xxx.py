from batchTool.display import Display


class DisplayClient(object):
    """
    xxx
    """    
    def __init__(self, scr):
        self.startTime = None
        self.screen = Display()
        self.screen.setScreen(scr)
    
    def setStartTime(self, time):
        print "Setting start time " + str(time)
        self.startTime = time
    
    def updateStartTime(self):
        print "Update start time"
        self.screen.displayTime(self.startTime)
    
    def displayJobSent(self, jobId, jobIndex):
        #print "%s -> %s" % (jobId, jobIndex)
        self.screen.displaySubmit(jobId, jobIndex)
    
    def displaySummary(self, stats):
        self.screen.displaySummary(stats)
    
    def resetSubmit(self, number):
        self.screen.resetSubmit(number)
    
    def mainLoop(self):
        pass
    
    def displayHeader(self, headers):
        self.screen.displayHeader(headers)
