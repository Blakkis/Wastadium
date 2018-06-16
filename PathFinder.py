import multiprocessing
from Queue import Empty

# Queues for processing to be communicate between processes
tk_queue = multiprocessing.Queue

# Support for creating executables
tk_freezeSupport = multiprocessing.freeze_support

# Exception
tk_emptyQueue = Empty   


class PathFinder(multiprocessing.Process):
    """
        Pathfinding algorithm is run in parallel where enemy can fetch player position and calculate the 
        shortest path to him/her
        
    """
    def __init__(self, iQueue, oQueue):
        super(PathFinder, self).__init__()
        
        # World map is binary map where cells with collisions are marked with 1 else 0
        self.binmap = None
        self.binmap_size = 0, 0
        
        self.iqueue = iQueue    # Fetch data from this
        self.oqueue = oQueue    # Feed data to this

        # Dict containing all actions to take with msg token being keys
        self.action = {'0': self.loadBinMap}
    
    
    def loadBinMap(self, binmap, binmapsize):
        """
            Load new binary map 
        """
        self.binmap = binmap
        self.binmap_size = mapsize

    
    def run(self):
        while 1:
            pass