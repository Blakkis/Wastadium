from ConfigsModule import GlobalGameData, TkWorldDataShared
from MapParser import W_errorToken


__all__ = ('Weapons', 'WeaponCasings')


class Weapons(GlobalGameData):
    """
        Load and setup all weapons for the game

        handles weapon config parsing, textures are handled by 'TextureLoader'

        This class mostly provide read-only data
        subclass this to any other class if it needs weapon data

    """
    # Contains all weapons for the game and their stats
    all_weapons = {}

    # Contains Weapon icon, and ammo type they use + (something more in the future)
    all_weapons_data = {}

    # Contains all ammo data
    all_ammo_data = {}

    
    def __init__(self):
        pass
        
    
    @classmethod
    @W_errorToken("Error Initializing Weapons!")
    def load_weapons(cls, editor_only=False, **kw):
        """
            Loads and setups all weapons/ammo data

            return -> None

        """
        # Source path for ammo configs
        src_ammo_path_cfg = cls.tk_path.join('configs', 'misc')

        # UIElement texture path 
        ui_elem_path_tex = cls.tk_path.join('textures', 'uielements')

        # Source path for weapon configs
        src_weapon_path_cfg = cls.tk_path.join('configs', 'weapons') 
        
        for line in cls.tk_readFile(cls.tk_path.join(src_ammo_path_cfg, 'ammo_types.cfg'), 'r'):
            # Breakdown the ammo data (From left by index)
            # 0 -> Name of ammo in game 
            # 1 -> Price (Minimum is 2 (!Forced)) 
            # 2 - 3 -> Ammo icons which are 32x32 and 64x64
            data = line[1].split(',')

            if editor_only:
                cls.all_ammo_data[int(line[0])] = data[0]
                continue

            cls.all_ammo_data[int(line[0])] = [data[0], max(2, int(data[1]))]

            # Note: Make sure the textures are last so more data can be added and then just shift the data[x:] to start of the textures
            cls.all_ammo_data[int(line[0])].extend([cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, t)).convert_alpha() for t in data[2:]])

        # Lines with multiple data
        multi_strings = ('w_fire_effects', 'w_trail_effects', 'w_explosion_effects', 'w_data')
        
        for weapon in cls.tk_iglob(cls.tk_path.join(src_weapon_path_cfg, '*.cfg')):
            name = weapon.split('\\')[-1].split('.')[0]

            # Editor needs names only (Leave values incase something is needed in the future)
            w_cfg = {}

            for line in cls.tk_readFile(weapon, 'r'):
                # Lines with multiple strings separated by comma dont go through literal_eval
                if line[0] in multi_strings:
                    mstr = tuple(line[1].split(',')) 
                    if line[0] == 'w_data' and not editor_only:
                        # As of this comment: The w_data contains AmmoType, WeaponIcon
                        cls.all_weapons_data[name] = (int(mstr[0]), cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, mstr[1])).convert_alpha())
                    else:
                        w_cfg[line[0]] = mstr
                
                else:
                    # All the offsets are trigonometry values which can be pre-calculated
                    if line[0].endswith('offset'):
                        d = cls.tk_literal_eval(line[1])
                        if line[0] == 'w_casing_offset':
                            w_cfg['w_casing_dist']  = d[1], d[3]
                            w_cfg['w_casing_angle'] = (cls.tk_atan2(d[0], d[1]), cls.tk_atan2(d[2], d[3]))
                        
                        elif line[0] == 'w_fire_effect_offset':
                            w_cfg['w_effect_dist']  = d[1], d[3]
                            w_cfg['w_effect_angle'] = (cls.tk_atan2(d[0], d[1]), cls.tk_atan2(d[2], d[3]))

                    else:
                        # The rest are simple key=value
                        w_cfg[line[0]] = cls.tk_literal_eval(line[1])

            # Store the weapon token
            cls.all_weapons[name] = cls.parse_weapon_content(w_cfg, editor_only) 

    
    @classmethod
    def parse_weapon_content(cls, token, editor_only=False):
        """
            Apply special parsing for tokens which ever needs it

            token -> Dict 
            editor_only -> Remove unused keys, values from the token not needed for the editor

            return -> None

        """
        if editor_only:
            # Add values needed by the editor here
            token = {'w_buyable': token['w_buyable']}
        
        else:
            pass

        return token


class WeaponCasings(GlobalGameData, TkWorldDataShared):
    """
        Handles casings and shells spawned by the weapons

    """

    # (Dear god, what is a good word to describe case and shell?)
    all_casings = {}

    # All live casings on the map being rendered
    casings_map = {}

    # Common data for the casings
    casing_data = {'id': 0}    # Provide all casings unique id

    # The number of frames on every casing texture array is based from 360 / deg
    # (Lower = Smoother casings flying animation)
    __casing_deg = 15

    # Number of frames for every casing animation 
    casing_num_of_frames = 360 / __casing_deg - 1

    
    def __init__(self, x, y, _id, angle, ofs_pos):
        self.casing_x = x
        self.casing_y = y
        self.casing_rel = ofs_pos
        self.casing_id = _id
        self.casing_angle = angle

        # The last casing pos and img needs to be stored before destroyed
        self.casing_last_frame = None
        
        # Distance 
        self.casing_dist = 0
        self.casing_step = 4
        
        # Frames 
        self.casing_frames = self.tk_cycle(xrange(self.casing_num_of_frames))
        self.casing_rotation = self.tk_trigger_const(self.tk_uniform(.001, .003))
        self.casing_index = 0

        self.casing_timer = self.tk_trigger_const(self.tk_uniform(.05, .08))    # 
        self.casing_flytime = self.tk_trigger_down(self.tk_uniform(1.2, 1.4))   # For how long the case is moving


    def render_casing_pos(self):
        """
            Return data for rendering the casing

            return -> Surface, Pos, rPos

        """
        # Once the casing flytime is done, raise StopIteration Error
        self.casing_flytime.isDone()

        # Throw the casing in the direction dictated by the angle
        x = self.casing_x + self.tk_sin(self.casing_angle) * self.casing_dist   
        y = self.casing_y + self.tk_cos(self.casing_angle) * self.casing_dist 

        if self.casing_timer.isReady():
            # Slowdown the stepping to give the illusion of height for the casings
            self.casing_step -= .5
            self.casing_dist += self.tk_ceil(self.casing_step)
            if self.casing_step <= 0:
                # Take the pos where the casing landed and store it
                self.casing_x = x; self.casing_y = y
                
                # Reset the casing distance to half the original 
                self.casing_dist = 0; self.casing_step = 2
                
                # give the casing a small angle offset
                self.casing_angle = self.tk_uniform(self.casing_angle - 1, self.casing_angle + 1)
        
        if self.casing_rotation.isReady():
            self.casing_index = self.casing_frames.next()         

        return self.all_casings[self.casing_id][self.casing_index], (x, y), self.casing_rel   

    
    @classmethod
    def spawn_casing(cls, _id, x, y, angle):
        """
            Spawn casing and store inside the class for rendering

            _id -> Which casing to fetch from the all_casings
            x, y -> Position
            angle -> Angle in which the casing is flying (Radians)

            return -> None

        """
        cls.casings_map[cls.casing_data['id']] = WeaponCasings(x, y, _id, angle, cls.w_share['WorldPosition'])

        # Calculate all casings in the map for after report
        cls.casing_data['id'] += 1

    
    @classmethod
    def setup_casings(cls):
        """
            Build and store all casings and shells the weapons are going to spawn
            Creates an array of casing images rotating full 360

            return -> None
            
        """
        # Casings are build from top-to-down with 3 pixel in the middle of the surface 
        # reserved for the casing (if None that pixel is left for alpha background)
        # - These are the color of the casings
        case_inputs = ((None,              (0xff, 0xaa, 0x0), (0xff, 0xaa, 0x0)),   # Pistol/Smg    
                       ((0xff, 0xaa, 0x0), (0xff, 0xaa, 0x0), (0xaa, 0xaa, 0x0)),   # Rifles
                       ((0xff, 0x0, 0x0),  (0xff, 0x0, 0x0),  (0xff, 0xaa, 0x0)))   # Shotguns

        # Create all the casings and rotate them to create 
        # the animated rotating casing flying out from the weapon
        for _id, c in enumerate(case_inputs, start=1):
            imgs = []
            # All ammo should fit in 5x5 surface, it provides nice center too 
            base_surf = cls.tk_surface((5, 5)); base_surf.set_colorkey((0x0, 0x0, 0x0), cls.tk_casing_rleaccel)
            base_surf_rect = base_surf.get_rect()
            
            # Paint the pixels 
            for enum, p in enumerate(c, start=1):
                if p is None: continue
                base_surf.set_at((2, enum), p)

            # First frame doesn't need rotating
            imgs.append(base_surf)
            
            # Rest are rotated version of the base_surf
            for d in xrange(cls.__casing_deg, 360, cls.__casing_deg):
                imgs.append(cls.tk_rotateImage(base_surf, d, base_surf_rect, fast_rot=1))

            cls.all_casings[_id] = tuple(imgs)


    @classmethod
    def render_casings(cls, surface):
        """
            Render all casings
            surface -> Surface which to draw on

            return -> None
            
        """
        for key in cls.casings_map.keys():
            try:
                img, pos, ofs = cls.casings_map[key].render_casing_pos()
                
                # Fix the casings in-place
                diff = ofs[0] - cls.w_share['WorldPosition'][0], ofs[1] - cls.w_share['WorldPosition'][1]
                x, y = pos[0] - diff[0], pos[1] - diff[1]
    
                # Store the img and position so we can work with the last frame before it gets destroyed
                cls.casings_map[key].casing_last_frame = img, (x, y)
                
                offs_x, offs_y = cls.w_share['WorldPositionDelta']
                surface.blit(img, (x - offs_x, y - offs_y))
            
            except StopIteration:
                # Blit the casing to the ground forever
                cls.solveMess(*cls.casings_map[key].casing_last_frame, sm_rel_pos=(cls.cell_x, cls.cell_y))
                
                # Delete it from the active pool
                del cls.casings_map[key]            

    
    @classmethod
    def clear_casings(cls):
        """
            Clear all casings for new map

            return -> None

        """
        cls.casing_data['id'] = 0; cls.casings_map = {} 


if __name__ == '__main__':
    pass