from itertools import cycle
from pygame.time import Clock


__all__ = ('EventTriggerConstant', 'EventTriggerCountDown', 'EventTrigger')


class DeltaTimer(object):

    _dt_clock = Clock()

    @classmethod
    def dt_tick(cls, limit_fps=0):
        dt = cls._dt_clock.tick(limit_fps)
        return dt, dt / float(1000)

    @classmethod
    def dt_fps(cls): return cls._dt_clock.get_fps() 


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
        state = self.ready
        if release and state:
            self.ready = 0 
            return state
         
        if state: return 0
        
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
            