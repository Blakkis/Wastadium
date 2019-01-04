from ConfigsModule import GlobalGameData, TkWorldDataShared
from Timer import DeltaTimer


# Note: Currently the game contains 2 victory conditions.
#	1: Kill all enemies
#	2: Reach the endgoal(Also kill all enemies satisfies this condition)


class VictoryCondition(GlobalGameData, DeltaTimer, TkWorldDataShared):

    victory_data = {'msg_font':            None,  # Font
                    'msg_completed':       None,  # Pre-renderer "Mission Complete" message
                    'msg_spiral_dist':     None,  # Radius from the message starts spiral to center 
                    'condition_kill_all':     0,  #     
                    'condition_waypoint': False,  # 
                    'complete':           False}  #

    @classmethod
    def subtractEnemyCountForVictory(cls): cls.victory_data['condition_kill_all'] -= 1 


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

            enemy_count -> Number of enemies on the map
            endpoint -> Exit point on the map

            return -> None

        """
        cls.victory_data['msg_spiral_dist'] = cls.tk_res_half[1]
        
        # Note: Set the enemy count 1 if there are no enemies at all (Hopefully there is endpoint)
        # Just so the count being zero can't trigger the complete sequence
        cls.victory_data['condition_kill_all'] = 1 if enemy_count <= 0 else enemy_count 
        cls.victory_data['condition_waypoint'] = None if endpoint is None else (endpoint.x, endpoint.y)

        # If the map doesn't have anything to kill or exit point. Set to complete
        cls.victory_data['complete'] = True if enemy_count <= 0 and endpoint is None else False 


    @classmethod
    def display_endpoint_beacon(cls, surface):
        """
            TBD

            return -> None

        """
        scale = cls.dt_getTicks() * 0.008
        x, y = cls.w_share['WorldPosition']

        x = int(cls.tk_res_half[0] + x) + cls.victory_data['condition_waypoint'][0] * 32
        y = int(cls.tk_res_half[1] + y) + cls.victory_data['condition_waypoint'][1] * 32

        cls.tk_draw_gfx_aacircle(surface, x, y, 19 + int(4 * cls.tk_cos(scale)), (0x00, 0x0, 0x0))
        cls.tk_draw_gfx_aacircle(surface, x, y, 20 + int(4 * cls.tk_cos(scale)), (0xff, 0x0, 0x0))

    
    @classmethod
    def check_if_victory_achieved(cls, surface, quick_exit_key=None):
        """
            Check if any victory conditions has been reached

            surface -> Active screen surface
            quick_exit_key -> Skip the mission complete sequency

            return -> 'True' if the mission complete sequency is going, else 'False'
                      '-1' if sequency is complete (Signal for the gameloop to quit)  

        """
        if not cls.victory_data['complete']:
            if cls.victory_data['condition_kill_all'] <= 0 or \
            cls.getWorldIndex() == cls.victory_data['condition_waypoint']:
                cls.victory_data['complete'] = True 

            if cls.victory_data['condition_waypoint'] is not None:
                cls.display_endpoint_beacon(surface)
            
        if cls.victory_data['complete']:
            if quick_exit_key:
                cls.victory_data['msg_spiral_dist'] = 0    

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

            done = bool(cls.victory_data['msg_spiral_dist'])
            return done if done else -1

        return False

        
