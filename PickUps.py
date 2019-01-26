from Inventory import Inventory
from Timer import DeltaTimer
from ConfigsModule import TkWorldDataShared
from MapParser import W_errorToken
from VictoryCondition import BookKeeping


__all__ = 'Pickups',


class MessagePickup(DeltaTimer):
    def __init__(self, surface, px, py, timer):
        self.mp_surf = surface
        self.mp_pos_x = px
        self.mp_pos_y = py
        self.mp_timer = timer

    
    def render_msg(self):
        """
            Render vertically rising message about the pickup

            return -> Surface, (x, y)

        """
        self.mp_pos_y -= 16 * self.dt_getDelta()

        if not self.mp_timer.isDone(): return 0    # End the msg display

        return self.mp_surf, (self.mp_pos_x, self.mp_pos_y)



class Pickups(Inventory, BookKeeping):
    # All usable pickups
    pu_pickups = {}

    # All active pickups on the world
    pu_all_world_pickups = {}

    # All active rendered messages
    pu_all_pickup_msg = set()

    # Common data for the pickups
    pu_data = {'id': 0,
               'font': None,
               'pickup_range': 48}

    def __init__(self):
        pass

    
    @classmethod
    @W_errorToken("Error Initializing Pickups Module!")
    def load_pickups(cls, editor_only=False, **kw):
        """
            Load and parse pickups

            editor_only -> Load minimalistic data about the pickups for the editor

            return -> None

        """
        # Source path for the gadget configs
        src_path_cfg = cls.tk_path.join('configs', 'pickups')

        # Source path for the gadget textures
        ui_elem_path_tex = cls.tk_path.join('textures', 'pickups')

        
        for cfg in cls.tk_iglob(cls.tk_path.join(src_path_cfg, '*.cfg')):
            name = cls.tk_path.split(cfg)[-1].split('.')[0]
            tex_data = {'p_tex':            None,
                        'p_pickup_snd':     None,
                        'p_pickup_msg':     None,
                        'p_pickup_type':    None,
                        'p_pickup_content': None}
            
            for line in cls.tk_readFile(cfg, 'r'):

                if not editor_only and line[0] == 'p_tex': tex_data[line[0]] = \
                cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, line[1])).convert_alpha()

                elif line[0] == 'p_pickup_snd': tex_data[line[0]] = int(line[1])

                elif line[0] == 'p_pickup_msg': tex_data[line[0]] = line[1].replace('_', ' ') 

                elif line[0] == 'p_pickup_type': tex_data[line[0]] = line[1]

                elif line[0] == 'p_pickup_content': tex_data[line[0]] = tuple([int(v) for v in line[1].split(',') if v])  

            cls.pu_pickups[name] = cls.parse_pickup_content(tex_data, editor_only)

        
        if editor_only:
            return cls.pu_pickups
        
        else:
            # Setup font for msg rendering
            cls.pu_data['font'] = cls.tk_font(kw['font'], 14)


    @classmethod
    def parse_pickup_content(cls, token, editor_only=False):
        """
            Apply special parsing for tokens which ever needs it

            token -> Dict 
            editor_only -> Remove unused keys, values from the token not needed for the editor

            return -> None

        """
        if editor_only:
            cls.load_weapons(editor_only)

            if token['p_pickup_type'] == 't_weapon':
                # Get all the weapons id's from the weapon class
                token['p_pickup_weapons'] = tuple([wpn for wpn in cls.all_weapons.keys() if cls.all_weapons[wpn]['w_buyable'] and \
                                                                                            not wpn.endswith(cls.weapon_dual_tag)])

            elif token['p_pickup_type'] == 't_ammo':
                # Get all the ammo id's from the ammo class
                token['p_pickup_ammo'] = {cls.all_ammo_data[key]:key for key, value in cls.all_ammo_data.iteritems()}

            # Get rid of unnecessary data from the pickups
            del token['p_pickup_snd'], token['p_pickup_msg'], token['p_tex']

        return token
    
    
    @classmethod
    def spawn_pickups(cls, list_of_pickups):
        """
            Spawn pickups on the map

            list_of_pickups -> List to pickups (x, y, pickup_id, pickup_value)

            return -> None

        """
        cls.getSetRecord('pcup', len(list_of_pickups))

        for pick in list_of_pickups:
            x, y = pick.x, pick.y 
            
            x = ((cls.tk_res_half[0] - 16) + x)
            y = ((cls.tk_res_half[1] - 16) + y)

            msg = cls.pu_pickups[pick.id]['p_pickup_msg']

            d_msg = pick.value if pick.id == 'cash_suitcase' else pick.content
            msg = cls.tk_renderText(cls.pu_data['font'], msg.format(d_msg), 1, (0xff, 0x0, 0x0), shadow=1)

            w = cls.tk_res_half[0] - msg.get_width() / 2 
            h = cls.tk_res_half[1] - msg.get_height() / 2 - 32 
            
            cls.pu_all_world_pickups[cls.pu_data['id']] = x, y, pick, \
                                                          MessagePickup(msg, w, h, cls.tk_trigger_down(3, 1)) 

            cls.pu_data['id'] += 1


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
    def parse_pickup(cls, pickup_id=None):
        """
            TBD

            return -> None

        """
        cls.pickupKilled()
        
        token = cls.pu_all_world_pickups[pickup_id][2]
        
        if token.id in ('body_armor', 'health_pack', 'hot_meal'):
            # Both health_pack and hot_meal gives health
            stat = 'armor' if token.id == 'body_armor' else 'health'
            if cls.i_playerStats[stat][0] == cls.i_playerStats[stat][1]:
                # Health or armor is full, no need to pickup the item
                return False
            else: 
                v = min(cls.i_playerStats[stat][1], cls.i_playerStats[stat][0] + token.value) 
                cls.i_playerStats[stat][0] = v
                return True

        elif token.id == 'cash_suitcase':
            cls.i_playerStats['credits'] += token.value
            return True

        elif token.id == 'ammo_cache':
            ammo_id = [k for k, v in cls.all_ammo_data.items() if v[0] == token.content][0]
            cls.i_playerAmmo[ammo_id] += token.value 
            return True

        elif token.id == 'weapon_cache':
            # Copy-pasted from Menu shop
            weapon = token.content
            w_cat = 'w_{}'.format(cls.all_weapons[weapon]['w_class'])
            dual_weapon = '{}{}'.format(weapon, cls.weapon_dual_tag) 
            check_for_dual = dual_weapon in cls.all_weapons

            weapon_choice = None
            if check_for_dual and weapon in cls.i_playerStats[w_cat] and dual_weapon not in cls.i_playerStats[w_cat]:
                weapon_choice = dual_weapon
            else:
                if weapon not in cls.i_playerStats[w_cat]: 
                    weapon_choice = weapon

            if weapon_choice is not None:
                cls.i_playerStats[w_cat].append(weapon_choice)
                return True    

        # Unknown item. Dont pick it up
        return False

    

    @classmethod
    def handle_pickups(cls, surface):
        """
            Render and handle pickups

            surface -> Active screen surface

            return -> None

        """
        px, py = cls.w_share['WorldPosition']

        c_keys = cls.pu_all_world_pickups.keys() 
        for _id in c_keys:
            if _id in cls.pu_all_pickup_msg: continue

            x, y, pick = cls.pu_all_world_pickups[_id][:-1] 
            tex = cls.pu_pickups[pick.id]['p_tex']

            # Get the distance between player and the item for grabbing
            px_1, py_1 = x - cls.tk_res_half[0] + 32, y - cls.tk_res_half[1] + 32
            px_2, py_2 = -(px - 16), -(py - 16)

            if cls.tk_hypot(px_1 - px_2, py_1 - py_2) <= cls.pu_data['pickup_range'] and cls.parse_pickup(_id):
                if cls.pu_pickups[pick.id]['p_pickup_snd'] is not None:
                    cls.playSoundEffect(cls.pu_pickups[pick.id]['p_pickup_snd'])
                cls.pu_all_pickup_msg.add(_id)    

            surface.blit(tex, (x + px, y + py))
 

    @classmethod
    def handle_pickups_messages(cls, surface):
        """
            Handle messages spawned by picking up the goodies

            surface -> Active screen surface
            delta -> Delta time

            return -> None

        """ 
        _del = set()

        if cls.pu_all_pickup_msg: 
            for _id in cls.pu_all_pickup_msg:
                msg = cls.pu_all_world_pickups[_id][-1].render_msg()
                if not msg: _del.add(_id); continue

                surface.blit(*msg)  

        # Pickups ready to be deleted
        if _del:
            for _id in _del:
                cls.pu_all_pickup_msg.discard(_id)
                del cls.pu_all_world_pickups[_id]

            
        
