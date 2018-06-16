from itertools import cycle
from pygame.time import get_ticks


__all__ = ('EventTriggerConstant', 'EventTriggerCountDown', 'EventTrigger')

# Note: Come up with solution to implement the DeltaTimer in the game too

class DeltaTimer(object):

    # Note: *Use pygame's clock.tick and clock.get_fps to calculate framerate

    # Replace with any ticks counter
    dt_ticks = get_ticks

    # Store now and after timers to get the final delta
    dt_suffix_tick = 0
    dt_prefix_tick = 0
    

    @classmethod  
    def dt_tick(cls, d):
        """
            Use to calculate delta time between actions 
            
            d -> 'now': 'Store tick to prefix', 
                 'after': 'Store tick to suffix', 
                 'reset': 'Store suffix to prefix'

            return -> None

        """
        if d == 'now': cls.dt_prefix_tick = cls.dt_ticks()
        elif d == 'after': cls.dt_suffix_tick = cls.dt_ticks()
        elif d == 'reset': cls.dt_prefix_tick = cls.dt_suffix_tick


    @classmethod    
    def dt_getDelta(cls): return cls.dt_suffix_tick - cls.dt_prefix_tick


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
            