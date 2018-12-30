from ConfigsModule import GlobalGameData, TkWorldDataShared
from Timer import DeltaTimer

# Note: Currently the game contains 2 victory conditions.
#	1: Kill all enemies
#	2: Reach the endgoal(Also kill all enemies satisfies this condition)


class VictoryCondition(GlobalGameData, DeltaTimer, TkWorldDataShared):

    victory_data = {'msg_font':            None,  # Font
                    'msg_completed':       None,  # Pre-renderer "Mission Complete" message
                    'msg_spiral_dist':     None,  # Radius from the message starts spiral to center 
                    'condition_kill_all':  None,  #    
                    'condition_waypoint': False,  # 
                    'complete':           False}  #

    @classmethod
    def setup_victory_module(cls, font=None):
    	"""
    	    Setup victory module

    	    font -> Font(path) used to render messages

    	    return -> None
    	"""
    	cls.victory_data['font'] = cls.tk_font(font, 14)
        cls.victory_data['msg_completed'] = cls.tk_renderText(cls.victory_data['font'], 
                                                              "Mission Completed", 1, 
                                                              (0xff, 0x0, 0x0), shadow=1)



    @classmethod
    def reset_victory_condition(cls, enemy_count, endpoint=None):
        """
            Reset the victory condition for next level

            return -> None

        """
        cls.victory_data['msg_spiral_dist'] = cls.tk_res_half[1]
        cls.victory_data['condition_kill_all'] = enemy_count
        
        if endpoint is not None:
            cls.victory_data['condition_waypoint'] = endpoint.x, endpoint.y
        else:
            cls.victory_data['condition_waypoint'] = None

        cls.victory_data['complete'] = False

    
    @classmethod
    def check_if_victory_achieved(cls, surface, quick_exit_key=False):
        """
            Check if any victory conditions has been reached

            surface -> Active screen surface
            quick_exit_key -> Skip the mission complete sequency

            return -> 'True' if the mission complete sequency is going else 'False'
                      '-1' if sequency complete  

        """
        if cls.victory_data['condition_kill_all'] <= 0 or \
        cls.getWorldIndex() == cls.victory_data['condition_waypoint']:
            cls.victory_data['complete'] = True 
            
        if cls.victory_data['complete']:
            msg_completed = cls.victory_data['msg_completed'] 
            ticks = cls.dt_getTicks() * 0.002

            # End the map when the spiral message reaches center (Gives player enough time to collect items)
            cls.victory_data['msg_spiral_dist'] -= 32 * cls.dt_getDelta()
            cls.victory_data['msg_spiral_dist'] = max(0, cls.victory_data['msg_spiral_dist'])

            # Swap the cos, sin to send the message from top -> ccw
            x = cls.tk_res_half[0] - msg_completed.get_width() / 2 
            x += cls.tk_sin(ticks) * cls.victory_data['msg_spiral_dist']

            y = cls.tk_res_half[1] - msg_completed.get_height() / 2
            y += cls.tk_cos(ticks) * cls.victory_data['msg_spiral_dist']

            surface.blit(msg_completed, (x, y))

            return True

        return False

        
