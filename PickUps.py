from ConfigsModule import GlobalGameData


class Pickups(GlobalGameData):

    # All usable pickups
    pu_pickups = {}

    # All active pickups on the world
    pu_all_world_pickups = {}

    # Common data for the pickups
    pu_data = {'id': 0}
    
    
    def __init__(self):
        pass

    
    @classmethod
    def load_pickups(cls):
        """
            TBD

            return -> None

        """
        # Source path for the gadget configs
        src_path_cfg = cls.tk_path.join('configs', 'pickups')

        # Source path for the gadget textures
        ui_elem_path_tex = cls.tk_path.join('textures', 'pickups')

        for cfg in cls.tk_iglob(cls.tk_path.join(src_path_cfg, '*.cfg')):
            name = cls.tk_path.split(cfg)[-1].split('.')[0]
            tex_data = {'p_tex': None}
            
            for line in cls.tk_readFile(cfg, 'r'):
                if line[0] == 'p_tex': tex_data[line[0]] = cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, line[1])).convert_alpha()

            cls.pu_pickups[name] = tex_data

    
    @classmethod
    def spawn_pickups(cls, list_of_pickups):
        """
            Spawn pickups on the map

            list_of_pickups -> List to pickups (x, y, pickup_id, pickup_value)

            return -> None

        """
        pass

    
    @classmethod
    def clear_pickups(cls):
        """
            Clear and reset all pickups

            return -> None

        """
        pu_all_world_pickups.clear()
        cls.pu_data['id'] = 0

    
    
    @classmethod
    def handle_pickups(cls, surface, px, py):
        """
            Render and handle pickups

            surface -> Surface which to render the gibs to
            px, py -> World position (To keep gibs relative to world position) 

            return -> None

        """
        pass
        
