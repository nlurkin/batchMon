import curses

from batchTool.display import Display


class DisplayClient(object):
    """
    xxx
    """    
    def __init__(self, scr):
        self.startTime = None
        self.screen = Display()
        self.screen.setScreen(scr)
        self.batchList = []
        self.batchName = ""
    
    def setStartTime(self, time):
        self.startTime = time
    
    def updateStartTime(self):
        self.screen.displayTime(self.startTime)
    
    def displayJobSent(self, jobId, jobIndex):
        self.screen.displaySubmit(jobId, jobIndex)
    
    def displaySummary(self, stats):
        self.screen.displaySummary(stats)
    
    def resetSubmit(self, number):
        self.screen.resetSubmit(number)
    
    def mainLoop(self):
        if self.batchName != "":
            self.updateStartTime()
        self.screen.repaint()
        k = self.screen.getch()
        if k != -1:
            if self.screen.displayList:
                if k == curses.KEY_DOWN:
                    self.screen.batchList.goDown()
                if k == curses.KEY_UP:
                    self.screen.batchList.goUp()
                if k == curses.KEY_RIGHT:
                    return +1,self.selectBatch(self.screen.batchList.currentCursor)
                if k == curses.KEY_LEFT:
                    return -1, self.disconnectBatch()
            else:
                if curses.unctrl(k) == "^R":
                    return +100, self.batchName
                if curses.unctrl(k) == "^G":
                    return +101, self.batchName
                
        
        return 0,""

    def selectBatch(self, index):
        self.screen.reset()
        self.batchName = self.batchList[index]
        return self.batchName
    
    def disconnectBatch(self):
        self.screen.reset()
        batch = self.batchName
        self.batchName = ""
        return batch
    
    def displayHeader(self, headers):
        self.screen.displayHeader(headers)

    def displayBatchList(self, l):
        self.batchList = l[:]
        self.screen.displayBatchList(l)
    
    def getName(self):
        return self.batchName