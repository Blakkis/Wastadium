from itertools import cycle
from pygame.time import Clock


__all__ = ('EventTriggerConstant', 'EventTriggerCountDown', 'EventTrigger',
           'MsHoldTrigger', 'MsCountdownTrigger', 'MsDelayTrigger')


# NOTE: Switch the delta timer to consumer based delta timer
#       Needs total rework on the game logic
class DeltaTimer(object):

    __dt_clock = Clock()

    dt_deltas = {'delta': 0,
                 'delta_ms': 0}

    @classmethod
    def dt_tick(cls, limit_fps=0):
        dt = cls.__dt_clock.tick(limit_fps) / float(1000)
        dt = max(0.002, min(0.016, dt))
        cls.dt_deltas['delta_ms'] = dt
        
        return dt

    @classmethod
    def dt_fps(cls): return cls.__dt_clock.get_fps()


    @classmethod
    def dt_getDelta(cls): return cls.dt_deltas['delta_ms'] 



class MsCountdownTrigger(DeltaTimer):
    __slots__ = 'ms'

    def __init__(self, ms, ret_type=0):
        self.ms = ms               
        self.ret_type = ret_type   # What to do when timer reaches 0

    def isDone(self):
        if self.ms <= 0:
            if self.ret_type: return 0
            else: raise StopIteration
        
        self.ms -= self.dt_deltas['delta_ms']
        return 1



class MsDelayTrigger(DeltaTimer):
    __slots__ = 'dms', 'ms'

    def __init__(self, delay_ms):
        self.dms = delay_ms     # Default timer value
        self.ms = delay_ms      # Active timer

    def isReady(self):
        if self.ms <= 0: 
            self.ms = self.dms
            return 1
        self.ms -= self.dt_deltas['delta_ms']
        return 0



class MsHoldTrigger(DeltaTimer):
    def __init__(self, delay_ms, state=1):
        self.dms = delay_ms     # Default timer value
        self.ms = delay_ms      # Active timer 
        self.ready = state      # Boolean state of the timer
        self.dstate = state     # Default state of the timer

    def isReady(self, release=0):
        if release and self.ready:
            state = self.ready
            self.ready = 0
            return state

        if self.ready: return 0

        self.ms -= self.dt_deltas['delta_ms']
        if self.ms <= 0: 
            self.ready = 1
            self.ms = self.dms  

    def reset(self):
        self.ms = self.dms; self.ready = self.dstate




# --------------------------------


class EventTriggerConstant(object):

    __slots__ = ('delay', 'default', 'ready', 'timer')

    def __init__(self, delay, state=1):
        self.delay = delay 
        
        self.default = state
        self.ready = state
        
        self.timer = 0

    
    def isReady(self, increment=1, release=0):
        """
            Tick the timer everytime this function is call'd
            and when the timer is greater or equal to delay, set ready True

            increment -> Timer increment (default: once every frame) 
            release -> if 'True' release the internal state

            return -> bool

        """
        if release and self.ready:
            state = self.ready
            self.ready = 0 
            return state
         
        if self.ready: return 0
        
        self.timer += increment
        if self.timer >= self.delay:
            self.ready = 1; self.timer = 0

    def reset(self): self.timer = 0; self.ready = self.default


# --------------------------------


class EventTriggerCountDown(object):
    """
        Creates a countdown trigger which creates an StopIteration exception when generator has exhausted
    """

    __slots__ = ('countdown')

    def __init__(self, countDown):
        # Technically doesn't 'countdown' 
        self.countdown = iter(xrange(countDown))

    def isDone(self):
        """
            This function should be call'd inside try/except block to catch the StopIteration exception

            return -> None

        """
        # Keep .nexting till StopIteration is raised
        self.countdown.next()


# --------------------------------


class EventTrigger(object):
    """
        Creates an timer generator which pulses True when delay (Scene count) has been reached
        and start from the beginning

    """
    
    tk_cycle = cycle

    __slots__ = ('timer')

    def __init__(self, delay):
        self.timer = self.tk_cycle(self.cGenerator(delay))
    
    
    @classmethod
    def cGenerator(cls, delay):
        """
            Creates an generator with the first value 1 and 0 for the rest of the delay

            return -> Generator (bool)
            
        """
        yield 1
        for _ in xrange(delay - 1): yield 0 
    

    def getReady(self):
        """
            Return the bool state from the generator
            pulsing 'True' between the delays

            return -> bool

        """
        return self.timer.next()
            