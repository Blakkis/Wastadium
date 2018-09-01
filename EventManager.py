from ConfigsModule import GlobalGameData, TkCounter


# Note: Add deleting event if its no longer needed


class EventManager(GlobalGameData):
    """
        Create an Instance of the EventManager inside target class to expose the functions
        inside the class

        This class also solves the problem of keeping track number of userevents created across all modules and
        that no overwriting can happen

        Events are between 24 - 32 (With '24' as index 0 reserved for Menus) 

    """
    # Number of event 'should' be between USEREVENT(24) and NUMEVENTS(32) 
    # With the '24' reserved for menus
    __event_num_of_events = TkCounter(0)
    
    
    def __init__(self):
        self.__Event_instanceEvents = {}

    
    def Event_newEvent(self, ms, action):
        """
            Creates an event inside the target class and hooks it to pygame eventqueue

            the events can be caught via pygame's own event methods
            
            pass all the pygame's event to 'self.Event_handleEvents' function for execution

            ms -> time (milliseconds) when the event is placed in pygame eventqueue
            action -> Function to call when the event has been caught  

            return -> None 
        """
        self.__event_num_of_events += 1
        if self.__event_num_of_events() >= self.tk_uEventMax:
            raise ValueError("Max user Events reached!") 

        if not callable(action):
            # Support for string based code objects maybe?
            raise ValueError("Action needs to be a function!")

        eventid = self.tk_uEvent + self.__event_num_of_events() 
        
        self.__Event_instanceEvents[eventid] = action
        
        # Hook the eventid part of pygames eventqueue
        self.tk_time.set_timer(eventid, ms) 
        
    
    
    def Event_handleEvents(self, event=None):
        """
            
            event -> event.type(id) to check if the event is stored in this instance and if so, 
                     execute the function associated with the eventid

            return -> None

        """
        # Improvement note: Check the event.type before calling this function 
        #                   

        if event in self.__Event_instanceEvents:
            self.__Event_instanceEvents[event]()     
