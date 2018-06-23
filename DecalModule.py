from ConfigsModule import GlobalGameData
from SoundModule import SoundMusic

from pprint import pprint as prn

__all__ = ('MessSolver', 'DecalGibsHandler')


class MessSolver(GlobalGameData):
    """
        Blit decals permanently to the world

    """

    mess_world_data = {'ms_rects': [],      # World sectors turned to rects
                       'ms_wsize': (0, 0),  # World size (32 * n)
                       'ms_wref': None}     # Reference to ground layer of the world

    
    def __init__(self):
        pass

    
    @classmethod
    def solveMess(cls, surface, sm_abs_pos=None, sm_rel_pos=None, debug_surface=None):
        """ 
            Blit surface permanently to ground surface

            Can solve the blit between multiple ground layers

            surface -> Surface image which is draw on the floor
            sm_abs_pos -> Position from topleft of the screen
            sm_rel_pos -> Position relative to world topleft

            return -> None

        """
        if sm_abs_pos is not None:
            # Find the position of the image on the world
            x = int((sm_abs_pos[0] - cls.tk_res_half[0] - sm_rel_pos[0]) + 16) 
            y = int((sm_abs_pos[1] - cls.tk_res_half[1] - sm_rel_pos[1]) + 16)
        else:
            x, y = -int(sm_rel_pos[0]), -int(sm_rel_pos[1]) 

        # Check that the decal is inside the map
        sx, sy = max(0, x >> 8), max(0, y >> 8)     
         
        if not cls.tk_boundaryCheck(sx, sy, cls.mess_world_data['ms_wsize']): return None
        
        # Get the image rect and move it to correct position for testing
        # which surface ground layers it touches
        r = surface.get_rect(); r.move_ip(x, y)

        macro_cell_size = 32 * cls.tk_macro_cell_size 

        if cls.mess_world_data['ms_rects'][sy][sx].contains(r):
            # The decal is fully inside the ground layer (Best case)
            cls.mess_world_data['ms_wref'][sy][sx][1].blit(surface, (x - macro_cell_size * sx, 
                                                                     y - macro_cell_size * sy))  
        else:
            s_size = r.size
            needs_covering = {}
            # The decal overlayers multiple ground layers
            # Positioning is done from the topleft (as always) 
            # so offsets are needed for the others than .topleft to move them to topleft position 
            for c in ((r.topleft, 0, 0),
                      (r.topright, s_size[0], 0), 
                      (r.bottomleft, 0, s_size[1]), 
                      (r.bottomright, s_size[1], s_size[1])):
                
                c_ind = c[0][0] >> 8, c[0][1] >> 8

                # Spawn the effect if the corner is inside the map
                if not cls.tk_boundaryCheck(*c_ind, limit=cls.mess_world_data['ms_wsize']): continue

                needs_covering[c_ind] = ((c[0][0] - c[1]) - macro_cell_size * c_ind[0], 
                                         (c[0][1] - c[2]) - macro_cell_size * c_ind[1])
 
            # 4 blit calls at worst 
            # (Unless the decal is bigger than groundlayer which is going to be horrible to blit. Possible block it?)
            for b, v in needs_covering.iteritems():
                cls.mess_world_data['ms_wref'][b[1]][b[0]][1].blit(surface, v)        

    
    @classmethod
    def convertToRectMap(cls, _map):
        """
            Load the world map and convert the cells to rects
            and store pointer to the ground layer array

            return -> None

        """
        cls.mess_world_data['ms_wref'] = _map
        
        # Create the world map array with (position and surface image) converted to rect
        mess_map = [[]] * len(_map)

        for enum, line in enumerate(_map):
            mess_map[enum] = [cls.tk_rect(32 * cls.tk_macro_cell_size * h,
                                          32 * cls.tk_macro_cell_size * enum,
                                          32 * cls.tk_macro_cell_size,
                                          32 * cls.tk_macro_cell_size) for h, _ in enumerate(line)]

        cls.mess_world_data['ms_rects'] = mess_map
        cls.mess_world_data['ms_wsize'] = len(mess_map[0]), len(mess_map) 


class GoreSystem(GlobalGameData):

    # Profiles which define how enemies gets gibbed
    gs_profiles = {}


    @classmethod
    def gs_load_goreProfiles(cls):
        """
            Load and parse gore profiles

            return -> None

        """
        src_gore_path_cfg = cls.tk_path.join('configs', 'decalgibs', 'gore_profiles')


        for cfg in cls.tk_iglob(cls.tk_path.join(src_gore_path_cfg, '*.cfg')):
            name = cls.tk_path.split(cfg)[-1].split('.')[0]
            
            token = {'tex_blood_splash': None,
                     'snd_blood_splash': None,
                     'foot_blood_id': None}
            
            token_gibs = {}
            token_gibs_cnt = 0
            
            for line in cls.tk_readFile(cfg, 'r'):
                if line[0] == 'tex_blood_splash': 
                    token[line[0]] = tuple([tex for tex in line[1].split(',') if tex])

                elif line[0] == 'snd_blood_splash': 
                    token[line[0]] = tuple([int(snd) for snd in line[1].split(',') if snd])

                elif line[0] == 'foot_blood_id':
                    token[line[0]] = int(line[1])
                
                elif line[0] == 'gib':
                    t = line[1].split(',')
                    x, y = int(t[1]), int(t[2])
                    
                    angle = cls.tk_degrees(cls.tk_atan2(x, y))
                    dist = cls.tk_hypot(x, y)

                    token_gibs["{}_{}".format(line[0], token_gibs_cnt)] = (t[0], angle, dist) 
                    token_gibs_cnt += 1

            cls.gs_profiles[name] = (token, token_gibs)

    
    @classmethod
    def gs_gib_now(cls, sx, sy, wx, wy, enemy_vector, g_profile):
        """
            sx, sy -> Screen coords
            wx, wy -> World coords
            enemy_vector -> Enemy view vector(in degrees)
            g_profile -> gore profile id


            return -> None

        """
        # Does the gibbing leave active stains to the world?
        stain_ground = None

        # Add more blood splashes by adding more offsets
        # The offsets are used to give more visually pleasing effect for gibbing the enemy
        # and randomizing it
        if cls.gs_profiles[g_profile][0]['tex_blood_splash'] is not None: 
            for offset in (32, -32):
                splash = cls.tk_choice(cls.gs_profiles[g_profile][0]['tex_blood_splash']) 
                cls.spawn_effect(splash, (sx, sy), angle=enemy_vector + offset)

            if cls.gs_profiles[g_profile][0]['foot_blood_id'] is not None:
                stain_ground = cls.gs_profiles[g_profile][0]['foot_blood_id']  
        
        cls.playSoundEffect(cls.tk_choice(cls.gs_profiles[g_profile][0]['snd_blood_splash']))

        for v in cls.gs_profiles[g_profile][1].itervalues():
            gib, angle, dist = v 
            angle = cls.tk_radians((90 - enemy_vector) - angle)
            offx, offy = cls.dh_all_gibs[gib]['texture'].get_size()
            
            cos = cls.tk_cos(angle) * dist
            sin = cls.tk_sin(angle) * dist
            cls.gib_spawn(gib, (sx - offx - cos, sy - offy - sin, wx, wy), angle)

        return stain_ground



class DecalGibsHandler(MessSolver, SoundMusic, GoreSystem):

    # All active gibs on the battlefield
    dh_all_PhysicsGibs = None

    # All spawnable decals
    dh_all_decals = {}

    # All Physics based spawnable gibs
    dh_all_gibs = {}

    # Binary world copy for collision testing against gibs
    #dh_phys_world = []

    # Size for the collision map
    #dh_phys_world_size = 0, 0

    dh_decal_data = {'dh_wsize': (0, 0),
                     'dh_world': []}    
    

    def __init__(self, gib_id, x, y, wx, wy):
        self.x = x
        self.y = y
        self.wpos = wx, wy
        self.velocity = 0
        self.anglex = 0
        self.angley = 0
        self.angler = 0

        self.damp = 0
        self.mass = self.dh_all_gibs[gib_id]['mass']  # Get the mass of the gib
        
        # Surf data
        self.gib_id = gib_id    # Id to fetch the correct gib image
        self.gib_smear_id = self.dh_all_gibs[self.gib_id]['effector']    # Surface used as smear effector

        # Store some dimensions about the gib
        self.gib_full = self.dh_all_gibs[gib_id]['texture'].get_size()
        self.gib_half = (self.gib_full[0] >> 1,
                         self.gib_full[1] >> 1)

        # Sound effect to be played when kicked
        self.gib_sound = self.dh_all_gibs[self.gib_id]['kick_sound']


    def gib_render(self, force=0, angle=0, wpos=None):
        """
            Render gib 

            force -> Apply force to the gib 
            angle -> In which direction the gib is moved (radians)
            wpos ->  World position (Keeping gibs relative to world's topleft)

            return -> Gib texture, position
        """
        if self.velocity:
            length = 2 + int(self.velocity) 

            self.x -= self.anglex * self.velocity
            self.y -= self.angley * self.velocity

            # Slow the gib down gradually
            self.velocity /= 1.1 - self.damp
            
            # Friction wins over
            if self.velocity < .1: self.velocity = 0

            self.damp += self.tk_gib_linear_damp

            if self.gib_smear_id is not None: 
                x, y = self.gib_get_wPos(wpos, 1, 1)
                x, y = -x - self.gib_full[0], -y - self.gib_full[1]   
                self.solveMess(self.gib_create_smear(2 + length), 
                               sm_rel_pos=(x, y))

                # Collision testing is very crude one with gibs
                # Just test if the center of the gib is inside wall and then
                # Mirror the angle to deflect it
                # Note: Possible dump the velocity more when hitting a wall?
                ix, iy = int(-x) >> 5, int(-y) >> 5
                if self.tk_boundaryCheck(ix, iy, self.dh_decal_data['dh_wsize']):
                    # Gib inside wall, deflect it
                    if self.dh_decal_data['dh_world'][iy][ix]:
                        wall_pos = 32 * ix + 16, 32 * iy + 16
                        
                        # Determine from which side the gib came in (The decimal is 45 in degrees)
                        angle = (self.tk_atan2(-y - wall_pos[1], -x - wall_pos[0]) + 0.7853981633974483) % self.tk_pi2

                        # Get the sector the gib came inside the wall
                        sector = int(self.tk_degrees(angle) / 90)
                        
                        if sector in (0, 2): self.anglex = -self.anglex      # R, L
                        elif sector in (1, 3): self.angley = -self.angley    # B, T           
                
        # Apply force (Kick the gib)
        if force and not self.velocity: self.gib_apply_force(force, angle)  

        return self.dh_all_gibs[self.gib_id]['texture'], self.gib_get_wPos(wpos)


    def gib_apply_force(self, force, angle, kick_snd=1):
        """
            Apply force to the gib to kick it around

            force -> Amount of force applied to the gib
            angle -> Direction angle for the gib
            kick_snd -> Play the kick sound when player is kicking the gib

            return -> None

        """
        self.velocity = force / self.mass
        self.anglex = self.tk_cos(angle); self.angley = self.tk_sin(angle)
        self.angler = angle
        self.damp = 0

        # Play a sound of kicking the gibs
        if kick_snd and self.gib_sound is not None: 
            self.playSoundEffect(self.tk_choice(self.gib_sound))

    
    def gib_create_smear(self, length):
        """
            TBD

            return -> None

        """
        # Effect used to create the smear
        smear_effector = self.dh_all_decals[self.gib_smear_id] 

        # Create the base surf for the smear effect
        surf = self.tk_surface((length, length), self.tk_srcalpha)

        # Lets get smearing
        surf.blit(smear_effector, (length - (smear_effector.get_width() >> 1) - 4,
                                  (length >> 1) - (smear_effector.get_height() >> 1)))

        # Smear it using surface scrolling
        for smear in xrange(length - smear_effector.get_width()): surf.scroll(-1, 0)

        return self.tk_rotateImage(surf, self.tk_degrees(-self.angler), surf.get_rect(), 1) 

        
    def gib_get_wPos(self, w_offs, world_rel=False, center=False):
        """
            Get world position of the gib
            
            w_offs -> Up-to-date world position
            world_rel -> Return position relative to the world topleft
            center -> Use the gibs half dimensions to center the origin

            return -> World position
        """
        x = (self.x - (self.wpos[0] - w_offs[0]))
        y = (self.y - (self.wpos[1] - w_offs[1]))

        if world_rel:
            x -= (self.tk_res_half[0] + w_offs[0])
            y -= (self.tk_res_half[1] + w_offs[1])

        if center: x += self.gib_half[0]; y += self.gib_half[1]

        return x, y

    
    @classmethod
    def gib_reset(cls, _map=None):
        """
            Clear all gibs from the map and rebuild collision map

            _map -> World that is converted to 2d binary map

            return -> None

        """
        cls.dh_all_PhysicsGibs.clear()

        w, h = len(_map[0]), len(_map) 
        cls.dh_decal_data['dh_wsize'] = w, h

        final = []
        # Cells with collisions are marked with 1 else 0
        for y in xrange(h):
            row = []
            for x in xrange(w):
                row.append(1 if _map[y][x].collision else 0)
            final.append(tuple(row))

        cls.dh_decal_data['dh_world'] = final   

    
    @classmethod
    def gib_render_all(cls, surface, px, py):
        """
            Render gibs on the world

            surface -> Surface which to render the gibs to
            px, py -> World position (To keep gibs relative to world position) 

            return -> None

        """
        # Note: Gibs could be optmized with spatial map to determine which ones to render
        # But since there's so few of them active at the same time
        # I didn't bother to implement one. Only optimize is checking if the gib is within screen

        for gib in cls.dh_all_PhysicsGibs:
            tx, ty = gib.gib_get_wPos((px, py), center=1)
            if not (0 < tx < cls.tk_resolution[0]) or not (0 < ty < cls.tk_resolution[1]):
                continue

            x, y = gib.gib_get_wPos((px, py), 1, 1)

            dist = cls.tk_hypot(-px - x, -py - y)
            kick_angle = cls.tk_atan2(-py - y, -px - x) if dist < 32 else 0

            surface.blit(*gib.gib_render(cls.tk_gib_force_max if kick_angle else 0, kick_angle, (px, py)))


    @classmethod
    def load_decalsGibs(cls):
        """
            Load all decals and gibs

            return -> None

        """
        # Source path for decal configs 
        src_dec_path_cfg = cls.tk_path.join('configs', 'decalgibs')

        # Source path for the gibs configs
        src_gib_path_cfg = cls.tk_path.join('configs', 'decalgibs', 'gibs') 

        # Decals texture path
        dec_path_tex = cls.tk_path.join('textures', 'decals')

        # Gibs texture path
        gib_path_tex = cls.tk_path.join('textures', 'gibs')


        # Set the type of container for the active decals
        cls.dh_all_PhysicsGibs = cls.tk_deque()

        # Passive decals 
        for line in cls.tk_readFile(cls.tk_path.join(src_dec_path_cfg, 'decals.cfg'), 'r'):
            data = line[1].split(',')
            cls.dh_all_decals[line[0]] = cls.tk_image.load(cls.tk_path.join(dec_path_tex, data[0])).convert_alpha()


        # Active gibs
        for cfg in cls.tk_iglob(cls.tk_path.join(src_gib_path_cfg, '*.cfg')):
            name = cls.tk_path.split(cfg)[-1].split('.')[0]
            token = {}
            
            for line in cls.tk_readFile(cfg, 'r'):
                if line[0]   == 'texture': 
                    token[line[0]] = cls.tk_image.load(cls.tk_path.join(gib_path_tex, line[1])).convert_alpha()
                
                elif line[0] == 'mass': 
                    token[line[0]] = cls.tk_clamp(float(line[1]), 2.5, 10.0)                
                
                elif line[0] == 'effector': 
                    token[line[0]] = line[1]
                
                elif line[0] == 'kick_sound': 
                    token[line[0]] = tuple([int(snd) for snd in line[1].split(',') if snd])

            cls.dh_all_gibs[name] = token

        # Load and init all gore profiles for gibbing
        cls.gs_load_goreProfiles()


    @classmethod
    def gib_spawn(cls, gib, pos, pre_vector=None):
        """
            Spawn gib

            gib -> Id of the gib
            pos -> Initial position
            pre_vector -> Apply movement vector to gib during spawning

            return -> None

        """
        gib = DecalGibsHandler(gib, *pos)
        
        if pre_vector:
            r_force = cls.tk_randrange(cls.tk_gib_force_min, cls.tk_gib_force_max)  
            gib.gib_apply_force(r_force, pre_vector, 0) 
        
        cls.dh_all_PhysicsGibs.append(gib)

        # Exceeded maximum active gibs
        # Blit the first ones permanently to ground
        if len(cls.dh_all_PhysicsGibs) > cls.tk_gib_max_gibs:
            x, y = cls.dh_all_PhysicsGibs[0].gib_get_wPos((0, 0), 1)

            x = -x - cls.dh_all_PhysicsGibs[0].gib_full[0]
            y = -y - cls.dh_all_PhysicsGibs[0].gib_full[1]    
            gib = cls.dh_all_gibs[cls.dh_all_PhysicsGibs[0].gib_id]['texture']

            cls.solveMess(gib, sm_rel_pos=(x, y))

            cls.dh_all_PhysicsGibs.popleft()



if __name__ == '__main__':
    pass