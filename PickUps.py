from Inventory import Inventory


__all__ = 'Pickups',


class MessagePickup(object):
    def __init__(self, surface, px, py):
        self.mp_surf = surface
        self.mp_pos_x = px
        self.mp_pos_y = py

    def render_msg(self):
        """
            TBD

            return -> Surface, (x, y)
        """
        return self.mp_surf, (self.mp_pos_x, self.mp_pos_y)


class Pickups(Inventory):

    # All usable pickups
    pu_pickups = {}

    # All active pickups on the world
    pu_all_world_pickups = {}

    # All active rendered messages
    pu_all_pickup_msg = set()

    # Common data for the pickups
    pu_data = {'id': 0,
               'font': None}
    
    
    def __init__(self):
        pass

    
    @classmethod
    def load_pickups(cls, **kw):
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
                        'p_pickup_snd': None,
                        'p_pickup_msg': ''}
            
            for line in cls.tk_readFile(cfg, 'r'):
                if line[0] == 'p_tex': tex_data[line[0]] = cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, line[1])).convert_alpha()

                elif line[0] == 'p_pickup_snd': tex_data[line[0]] = int(line[1])

                elif line[0] == 'p_pickup_msg': tex_data[line[0]] = line[1].replace('_', ' ') 

            cls.pu_pickups[name] = tex_data

        # Setup font for msg rendering
        cls.pu_data['font'] = cls.tk_font(kw['font'], 14)

    
    
    @classmethod
    def spawn_pickups(cls, list_of_pickups):
        """
            Spawn pickups on the map

            list_of_pickups -> List to pickups (x, y, pickup_id, pickup_value)

            return -> None

        """
        for pick in list_of_pickups:
            x, y, item_id, item_value = pick 
            x = ((cls.tk_res_half[0] - 16) + x)
            y = ((cls.tk_res_half[1] - 16) + y)

            msg = cls.pu_pickups[item_id]['p_pickup_msg']
            msg = cls.tk_renderText(cls.pu_data['font'], msg.format(item_value), 1, (0xff, 0x0, 0x0), shadow=1)
            
            cls.pu_all_world_pickups[cls.pu_data['id']] = x, y, item_id, item_value, \
                                                          MessagePickup(msg, cls.tk_res_half[0] - msg.get_width()  / 2, 
                                                                             cls.tk_res_half[1] - msg.get_height() / 2 - 32)    

    
    
    @classmethod
    def clear_pickups(cls):
        """
            Clear and reset all pickups

            return -> None

        """
        cls.pu_all_pickup_msg.clear()
        cls.pu_all_world_pickups.clear()
        cls.pu_data['id'] = 0


    
    @classmethod
    def __render_pickup_msg(cls, surface):
        """
            TBD

            return -> None

        """
        for _id in cls.pu_all_pickup_msg:
            surface.blit(*cls.pu_all_world_pickups[_id][-1].render_msg())
            #if _id in cls.pu_all_world_pickups: 
            #    del cls.pu_all_world_pickups[_id]
    
    
    
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
            x, y, item_id, item_value = cls.pu_all_world_pickups[_id][:-1] 
            tex = cls.pu_pickups[item_id]['p_tex']

            # Get the distance between player and the item for grabbing
            px_1, py_1 = x - cls.tk_res_half[0] + 32, y - cls.tk_res_half[1] + 32
            px_2, py_2 = -(px - 16), -(py - 16)

            if cls.tk_hypot(px_1 - px_2, py_1 - py_2) < 32:
                if cls.pu_pickups[item_id]['p_pickup_snd'] is not None:
                    cls.playSoundEffect(cls.pu_pickups[item_id]['p_pickup_snd'])

                cls.pu_all_pickup_msg.add(_id)    

            surface.blit(tex, (x + px, y + py))


    @classmethod
    def handle_pickups_messages(cls, surface):
        """
            TBD

            return -> None

        """ 
        if cls.pu_all_pickup_msg: 
            cls.__render_pickup_msg(surface)   

            
        
