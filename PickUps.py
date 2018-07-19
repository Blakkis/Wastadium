from Inventory import Inventory


class Pickups(Inventory):

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
            tex_data = {'p_tex': None,
                        'p_pickup_snd': None}
            
            for line in cls.tk_readFile(cfg, 'r'):
                if line[0] == 'p_tex': tex_data[line[0]] = cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, line[1])).convert_alpha()

                elif line[0] == 'p_pickup_snd': tex_data[line[0]] = int(line[1])

            cls.pu_pickups[name] = tex_data

    
    @classmethod
    def spawn_pickups(cls, list_of_pickups, player_spw_pos):
        """
            Spawn pickups on the map

            list_of_pickups -> List to pickups (x, y, pickup_id, pickup_value)
            player_spw_pos -> Player spawn position

            return -> None

        """
        for pick in list_of_pickups:
            x, y, item_id, item_value = pick 
            x = ((cls.tk_res_half[0] - 16) + x)
            y = ((cls.tk_res_half[1] - 16) + y)
            
            cls.pu_all_world_pickups[cls.pu_data['id']] = x, y, item_id, item_value    

    
    @classmethod
    def clear_pickups(cls):
        """
            Clear and reset all pickups

            return -> None

        """
        cls.pu_all_world_pickups.clear()
        cls.pu_data['id'] = 0

    
    
    @classmethod
    def handle_pickups(cls, surface, px, py):
        """
            Render and handle pickups

            surface -> Surface which to render the gibs to
            px, py -> World position (To keep gibs relative to world position) 

            return -> None

        """
        c_keys = cls.pu_all_world_pickups.keys() 
        for _id in c_keys:
            x, y, item_id, item_value = cls.pu_all_world_pickups[_id] 
            tex = cls.pu_pickups[item_id]['p_tex']

            # Get the distance between player and the item for grabbing
            px_1, py_1 = x - cls.tk_res_half[0] + 32, y - cls.tk_res_half[1] + 32
            px_2, py_2 = -(px - 16), -(py - 16)

            if cls.tk_hypot(px_1 - px_2, py_1 - px_2) < 32:
                if cls.pu_pickups[item_id]['p_pickup_snd'] is not None:
                    cls.playSoundEffect(cls.pu_pickups[item_id]['p_pickup_snd'])
                del cls.pu_all_world_pickups[_id]

            surface.blit(tex, (x + px, y + py))

            
        
