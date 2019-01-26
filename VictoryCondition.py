from ConfigsModule import GlobalGameData, TkWorldDataShared
from Timer import DeltaTimer


# Note: Currently the game contains 2 victory conditions.
#	1: Kill all enemies
#	2: Reach the endgoal(Also kill all enemies satisfies this condition)

class BookKeeping(object):
    """
        Record data for after report and score calculations

    """
    
    task_record = {'condition_kill_all':     0,
                   'condition_waypoint': False,
                   'complete':           False,}

    # Level report
    level_report = {'time': None,     # Completion time
                    'name': None,     # Name of the level
                    'kill': [0, 0],   # Kills   (Value, Max)
                    'pcup': [0, 0]}   # Pickups (Value, Max)

    @classmethod
    def getSetRecord(cls, name, value=None):
        """
            Use this function to fetch data/record from other places for after report

            name  -> Key on the level_report dictionary (It needs to exists there!)
            value -> If value is None, return value and key
                     else set it.

            return -> None
        """
        assert name in cls.level_report, "Name does not exists"
        if value is None:
            return name, '-' if cls.level_report[name] is None else cls.level_report[name]
        else:
            if isinstance(cls.level_report[name], list):
                cls.level_report[name] = [0, value]
            else:
                cls.level_report[name] = value

    
    @classmethod
    def enemyKilled(cls, enemy_name=None):
        """
            Call me, when enemy is killed

            enemy_name -> Name(id) of the enemy killed

            return -> None

        """
        cls.task_record['condition_kill_all'] -= 1
        cls.level_report['kill'][0] += 1
        
        if enemy_name is not None:
            pass

    
    @classmethod
    def pickupKilled(cls, pickup_name=None):
        """
            Call me, when pickup is killed

            pickup_name -> Name(id) of the pickup killed

            return -> None

        """
        cls.level_report['pcup'][0] += 1

        if pickup_name is not None:
            pass

    
    @classmethod
    def resetRecord(cls, enemy_count, endpoint):
        """
            Reset level records

            enemy_count -> see 'reset_victory_condition' 
            endpoint ->    see 'reset_victory_condition' 

            return -> None

        """
        cls.task_record['condition_kill_all'] = enemy_count
        cls.task_record['condition_waypoint'] = endpoint



class VictoryCondition(GlobalGameData, DeltaTimer, TkWorldDataShared, BookKeeping):
    """
        Handles mostly visual aspect for completing level
    
    """

    victory_data = {'msg_font':        None,  # Font
                    'msg_completed':   None,  # Pre-renderer "Mission Complete" message
                    'msg_spiral_dist': None}  # Radius from the message starts spiral to center  


    @classmethod
    def setup_victory_module(cls, font=None):
    	"""
    	    Setup victory module

    	    font -> Font(path) used to render messages

    	    return -> None

    	"""
    	cls.victory_data['font'] = cls.tk_font(font, 18)
        cls.victory_data['msg_completed'] = cls.tk_renderText(cls.victory_data['font'], 
                                                              "Mission Completed", True, 
                                                              (0xff, 0x0, 0x0), shadow=True)

        cls.victory_data['msg_objective'] = cls.tk_renderText(cls.victory_data['font'],
                                                              "Kill All Or Find Exit", True,
                                                              (0xff, 0x0, 0x0), shadow=True)
    

    @classmethod
    def reset_victory_condition(cls, enemy_count, endpoint=None):
        """
            Reset the victory condition for next level

            enemy_count -> Number of enemies on the map 
            endpoint -> Exit point on the map

            return -> None

        """
        cls.victory_data['msg_spiral_dist'] = cls.tk_res_half[1]
        
        cls.resetRecord(1 if enemy_count <= 0 else enemy_count,
                        None if endpoint is None else (endpoint.x, endpoint.y))

        # If the map doesn't have anything to kill or exit point. Set to complete
        cls.task_record['complete'] = True if enemy_count <= 0 and endpoint is None else False 


    @classmethod
    def display_endpoint_beacon(cls, surface):
        """
            TBD

            return -> None

        """
        scale = cls.dt_getTicks() * 0.008
        x, y = cls.w_share['WorldPosition']
        ofs_x, ofs_y = cls.w_share['WorldPositionDelta']

        x = int(cls.tk_res_half[0] + x - ofs_x) + cls.task_record['condition_waypoint'][0] * 32
        y = int(cls.tk_res_half[1] + y - ofs_y) + cls.task_record['condition_waypoint'][1] * 32

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
        if not cls.task_record['complete']:
            if cls.task_record['condition_kill_all'] <= 0 or \
            cls.getWorldIndex() == cls.task_record['condition_waypoint']:
                cls.task_record['complete'] = True 

            if cls.task_record['condition_waypoint'] is not None:
                cls.display_endpoint_beacon(surface)
            
        if cls.task_record['complete']:
            if quick_exit_key:
                cls.victory_data['msg_spiral_dist'] = 0    

            msg_completed = cls.victory_data['msg_completed'] 
            ticks = cls.dt_getTicks() * 0.002

            # End the map when the spiral message reaches center (Gives player enough time to collect items)
            cls.victory_data['msg_spiral_dist'] -= 32 * cls.dt_getDelta()
            cls.victory_data['msg_spiral_dist'] = max(0, cls.victory_data['msg_spiral_dist'])

            x = cls.tk_res_half[0] - msg_completed.get_width() / 2 
            x += cls.tk_cos(ticks) * cls.victory_data['msg_spiral_dist']

            y = cls.tk_res_half[1] - msg_completed.get_height() / 2
            y += cls.tk_sin(ticks) * cls.victory_data['msg_spiral_dist']

            surface.blit(msg_completed, (x, y))

            done = bool(cls.victory_data['msg_spiral_dist'])
            return done if done else -1

        return False

        
