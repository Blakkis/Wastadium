import random
random.seed(0xdeadbeef122)

from ConfigsModule import GlobalGameData
from Weapons import *
from EnemiesModule import Enemies
from SoundModule import SoundMusic
from TextureLoader import *
from ShadowMap import Shadows
from DecalModule import *
from Ui import *
from Menus import MenuManager
from PreProcessor import PreProcessor
from Inventory import Inventory
from Timer import DeltaTimer


# NOTE NOTE NOTE: Investigate map_layers[1] and remove it 
# ITS EFFECT LAYER THUS DISABLED
# CHANGE w_ambientTone to work with ground and walls (See arguements)

# NOTES:
#   Refactor!
#   Remember keys are global too(eg. K_UP)
#   All textures are facing up, so all trig calculations are done with x, y swapped (atan function rest angle is up)

class LaserSightModule(uiElements):
    """
        Cast a lasersight from player position
        with offsets to keep the laser in left eye

        Note: Only player should have this

    """
    def __init__(self):
        # Color of the laser beam
        self.l_color = 0xff, 0x0, 0x0

        # Provide for the cosine a constant increasing value
        self.l_sway = self.tk_counter(0)

        # NOTE: Need to change these to use the head base tracking (with these coming from rest of the frames)

        # Generate lasersight base offsets
        # Keep the lasersight front of the left eye when the head bobbles
        self.l_offsets = {1: [2,  -16],     
                          2: [1,  -15],
                          3: [0,  -9 ],
                          4: [0,  -4 ],
                          5: [2,  -4 ],
                          6: [4,  -4 ],
                          7: [4,  -9 ],
                          8: [4,  -15]}
        for k in self.l_offsets.keys():
            v = self.l_offsets[k] 
            self.l_offsets[k].append(self.tk_atan2(v[0], v[1]))
            self.l_offsets[k].append(self.tk_hypot(v[0], v[1]))

  
    def cast_lasersight(self, surface, angle, dist, base, sway=False, firing=False):
        """
            If player has bought the lasersight module
            cast a small laser beam

            surface -> Surface which receives the beam
            angle -> view angle (Radians)
            dist -> Max distance for the laser ray
            base -> base for the headtracking
            sway -> Sway the lasersight when moving (for added realism)
            firing -> Stable the aim when firing (Doesn't sway the lasersight)

            return -> None

        """
        # Only sway the lasersight when moving
        if sway and not firing: 
            angle += 0.04 * self.tk_cos(self.l_sway())
            self.l_sway += .3

        # Get the lasersight offset
        ofs = base if not sway or firing else self.l_offsets[sway] 

        vecx = self.tk_sin(angle)
        vecy = self.tk_cos(angle)

        # Get all collisions intersecting the ray
        dist = World.get_ray_env_collisions(self.tk_res_half[0], 
                                            self.tk_res_half[1], 
                                            vecx, vecy, dist, 
                                            ret_first_dist=1)

        # Starting point
        sx = self.tk_res_half[0] + self.tk_sin(angle - ofs[2]) * ofs[3] 
        sy = self.tk_res_half[1] + self.tk_cos(angle - ofs[2]) * ofs[3]

        # Endpoint
        ex = self.tk_res_half[0] - vecx * dist 
        ey = self.tk_res_half[1] - vecy * dist  

        # Cast the visuals
        self.tk_draw_aaline(surface, self.l_color, (sx, sy), (ex, ey))

        sight = self.ElementCursors[2]

        surface.blit(sight[0], (ex - sight[1], ey - sight[2]))  



class Hero(TextureLoader, FootSteps, SoundMusic, Inventory):
    """
        Provide all import data for player character

    """
    def __init__(self):

        self.char_rect = self.tk_rect((0, 0, 32, 32))   # Collision box
        self.char_center = self.tk_res_half[0] - 16, self.tk_res_half[1] - 16
        self.char_rect.move_ip(self.char_center)

        self.player_data = {'speed':  3.5,            # Speed
                            'legs':   'legs_prison',  # Legs str id
                            'torso':  'hero',         # Torso str id 
                            'model':  ''}             # Torso + weapon
        
        self.player_data['model'] = '_'.join((self.player_data['torso'], self.i_playerStats['weapon'])) 
        
        # Model animation 
        self.figure = [[self.player_data['legs'],  self.tk_rect(0, 0, 32, 32)], 
                       [self.player_data['model'], self.tk_rect(0, 0, 64, 64)]]

        # Animation 
        self.hero_load_animation(self.player_data['legs'], self.player_data['model'])
        self.animation_delay = self.tk_event_trigger(3)    # Delay between each animation frames

        # Footsteps 
        self.footstep_id = 0    # Id of the footstep left behind
        self.footstep_cycle = iter(xrange(8, 40))       # First 0 to 7 indexes are data about the footstep and the rest are footstep textures 
        self.footstep_delay = self.tk_event_trigger(8)  # Frames between each footstep +
        self.footstep_delay_sound = self.tk_event_trigger(2)    # Frames between each footstep soundeffect 

        # Laser cast module (During in-game if player has bought it)
        self.lmodule = LaserSightModule() 


    def hero_footstep(self, angle):
        """
            Leave footsteps behind
            (Bloody footprints or anything up to 32 steps which fade)

            angle -> Radians 

            return -> None
        """
        
        wx = -int(World.cell_x - 16) >> 5
        wy = -int(World.cell_y - 16) >> 5
        
        if self.tk_boundaryCheck(wx, wy, World.w_map_size):
            if self.footstep_delay_sound.getReady(): 
                # Get the ground material sound effect for walking over it
                self.playSoundEffect(self.tk_choice(World.w_micro_cells[wy][wx].w_sound_walk)) 
            # Get the id for the bloody foot texture
            stain_id = World.w_micro_cells[wy][wx].w_footstep_stain_id 
            if stain_id > 0:
                self.footstep_id = stain_id
                self.footstep_cycle = iter(xrange(8, 40))   

        if self.footstep_id:
            try:
                cx, cy = self.all_footsteps[self.footstep_id][1]    # Center of the footstep decal
                img, sAngle = self.all_footsteps[self.footstep_id][self.footstep_cycle.next()] 
                
                # Move the footstep decals sideways to the character
                fx, fy = self.tk_PolarToCartesian(World.cell_x - cx, 
                                                  World.cell_y - cy, 
                                                  angle + sAngle, 4) 

                World.solveMess(self.tk_rotateImage(img, self.tk_degrees(angle), 
                                self.all_footsteps[self.footstep_id][0]),
                                sm_rel_pos=(fx, fy))

            except StopIteration:
                self.footstep_id = 0 


    def hero_load_animation(self, legs_name=None, torso_name=None):
        """
            Handles and setups skin/animations for the character

            legs_name -> Name of the legs texture 
            torso_name -> This one is a bit tricky 
                          since torso textures are tied to specific weapon
                          this function is perfect for handling and setting up
                          weapon related stuff 

            return -> None
            
        """
        # Load frame lengths of the both animation sequences 
        # (Get the animation length from the first row of animations)
        if legs_name is not None:
            self.legs_frame_cycle = self.tk_cycle(xrange(len(self.legs_textures[legs_name][1])))
            self.legs_frame_index = 0   # Frame index
        
        if torso_name is not None:
            self.torso_frame_cycle = self.tk_cycle(xrange(len(self.torso_textures[torso_name][1])))
            self.torso_frame_index = 0  # Frame index
            self.figure[1][0] = torso_name 

        # Get/Set the weapons firerate from the configs
        firerate = self.all_weapons[self.i_playerStats['weapon']]['w_firerate'] 
        self.weaponfire_delay = self.tk_event_trigger_cons(firerate)
        
        # Cycle for dual gun usage
        self.weapon_dual_cycle = self.tk_deque((0, 1))

        # Length of the fire animation
        l = [0]
        if firerate > 7: l.extend([1] * 7)      # Cap the fire anim length to 8
        else: l.extend([1] * (firerate - 1))    # Use the firerate - 1 as length
        
        self.fire_anim_len = self.tk_deque(l)


    def hero_handle(self, surface):
        """
            Handle everything related to player 

            return -> None

        """
        m_pos = self.tk_mouse_pos()
        
        angle = self.tk_atan2(self.tk_res_half[0] - m_pos[0],
                              self.tk_res_half[1] - m_pos[1])
        
        radToAngle = self.tk_degrees(angle)

        baseAx, baseAy = self.tk_sin(angle), self.tk_cos(angle) 

        # Movement direction and speed (Magnitude)
        x = baseAx * self.player_data['speed']
        y = baseAy * self.player_data['speed']

        # Used to control how firing and animation playback is handled (Bitwise)
        play_fire_frame = 0
        
        fire_key = self.tk_mouse_pressed()[0] 

        # Handle weapon firing
        if self.weaponfire_delay.isReady(release=fire_key):
            ammo_id = self.all_weapons_data[self.i_playerStats['weapon']][0]    # Get the ammo used by the weapon
            
            if ammo_id == -1 or self.i_playerAmmo[ammo_id] > 0:
                self.playSoundEffect(self.tk_choice(self.all_weapons[self.i_playerStats['weapon']]['w_fire_sound']))
                
                World.fire_weapon(self.tk_res_half[0], self.tk_res_half[1],
                                  angle, 
                                  radToAngle, 
                                  self.i_playerStats['weapon'], 
                                  dual_index=self.weapon_dual_cycle[1],
                                  surface=surface) 
                
                play_fire_frame |= 1
                
                if ammo_id != -1: self.i_playerAmmo[ammo_id] -= 1

                self.weapon_dual_cycle.rotate(1)    # Switch hand
                
                self.fire_anim_len.rotate(1)        # Begin the fire animation

            else:
                # Trying to fire an empty weapon
                self.playSoundEffect(self.all_weapons[self.i_playerStats['weapon']]['w_fire_sound_empty'])    

        # Player is moving while holding firekey down display the point weapon animation
        if fire_key: play_fire_frame |= 2 

        dir_frames = 0    # Animation key to load from correct animation set
        
        # Handle the player movement(Moving Back/Side gets slowed to 3/4 of the speed)
        keys = self.tk_key_pressed()
        if keys[self.tk_user['up']]:
            dir_frames = 1
            World.move_map(x, y, obj_col=self.char_rect)

        elif keys[self.tk_user['down']]:
            dir_frames = 5
            World.move_map(-(x - x / 4), -(y - y / 4), obj_col=self.char_rect)

        if keys[self.tk_user['right']]:
            dir_frames = 3
            World.move_map(-(y - y / 4), x - x / 4, obj_col=self.char_rect)

        elif keys[self.tk_user['left']]:
            dir_frames = 7
            World.move_map(y - y / 4, -(x - x / 4), obj_col=self.char_rect) 

        # Character is moving. Fetch the next animation frame when ready and check for diagonal movements
        if dir_frames:

            if self.animation_delay.getReady():
                # Update the animation index keys for the next frame
                self.legs_frame_index = self.legs_frame_cycle.next()
                self.torso_frame_index = self.torso_frame_cycle.next()

            # Leave footsteps behind 
            if self.footstep_delay.getReady(): self.hero_footstep(angle)       

            # Diagonal movement
            dir_frames = 2 if keys[self.tk_user['up']]   and keys[self.tk_user['right']] else dir_frames
            dir_frames = 8 if keys[self.tk_user['up']]   and keys[self.tk_user['left']]  else dir_frames
            dir_frames = 4 if keys[self.tk_user['down']] and keys[self.tk_user['right']] else dir_frames
            dir_frames = 6 if keys[self.tk_user['down']] and keys[self.tk_user['left']]  else dir_frames

        # Position where the hero will be built on
        x, y = self.char_center
        
        # Rotate the layers to view direction and render (This should be flatten if no more layers are needed)
        for enum, f in enumerate(self.figure):
            # ---- Legs
            if not enum:
                # Get the texture offset fixes (The origin which upon to center the texture)
                offset = self.legs_textures[f[0]][0][2]  
                image = self.legs_textures[f[0]][dir_frames][0 if not dir_frames else self.legs_frame_index]
            
            # ---- Torso
            else:
                # Get the torso offsets to push back/forward the torso to keep them top of the legs
                offset = self.torso_textures[f[0]][0][4]
                
                # Handle if player is (moving and shooting) or
                #                     (standing and shooting) or
                #                     (just moving) and keep attack posture between firing weapon
                mov = 0 if not dir_frames or not play_fire_frame & 2 else 1

                # Take proper action/animation if the player has fired the weapon
                #action = play_fire_frame & 1
                
                action = self.fire_anim_len[0]
                if self.fire_anim_len[0]: self.fire_anim_len.rotate(1)
 
                if mov:
                    # Moving and shooting (Keep the attack posture between executing attack) 
                    image = self.torso_textures[f[0]][0][(action + self.weapon_dual_cycle[0]) if self.fire_anim_len[0] else action]
                    
                else: 
                    if action:
                        # Standing still and shooting
                        image = self.torso_textures[f[0]][0][action + self.weapon_dual_cycle[0]]
                    
                    else:
                        # Standing still or moving but not firing (Display normal moving animations or idle standing frame)    
                        image = self.torso_textures[f[0]][dir_frames][0 if not dir_frames else self.torso_frame_index]
                
                # Torso is 64 x 64 so it needs to be fixed inplace 
                x -= 16; y -= 16
            
            # Move the texture forward or backward based on the offset origin
            if offset: x += baseAx * offset; y += baseAy * offset 
            
            surface.blit(self.tk_rotateImage(image, radToAngle, f[1]), (x, y))

        # Cast constant lasersight ray if player owns the goggles
        if self.i_playerStats['mod_laser']:
            self.lmodule.cast_lasersight(surface, angle, 
                                         self.all_weapons[self.i_playerStats['weapon']]['w_range'],
                                         self.torso_textures[self.player_data['model']][0][-1], 
                                         dir_frames, play_fire_frame)



class World(TextureLoader, EffectsLoader, Inventory, Weapons, 
            WeaponCasings, DecalGibsHandler, MessSolver, 
            FootSteps, uiElements, SoundMusic):
    """
        Setup and handle all world related and external modules loading

    """

    #__slots__ = ()
    
    # Holds all the enemies of the map by ID
    w_enemies = {}

    # Holds all the map layers (With keys 0-2: [])  1: Not in-use       
    w_map_layers = {}
    
    # Holds each cell as single 32x32 cell
    w_micro_cells = []        
    
    # Dynamic map entities (eg. Enemies)
    w_entities_dynamic = []

    # Static entities (eg. Map effects, pickups)
    w_entities_static = []
    
    # World position
    cell_x, cell_y = 0, 0
    
    # Current mapsize 
    w_map_size = 0, 0
    
    # Boundaries for the mapsize divided by tk_macro_cell_size
    w_map_size_macro = 0, 0
    
    # Boundaries for entities_cell divided by tk_entity_sector_s
    w_ent_cell_size = 0, 0
    
    # Used to sync world layers together since player movement (which alters the world position) 
    # might throw them off eachother 
    w_offset = 0, 0


    def __init__(self, x, y, low_id='', mid_id=''):
        self.texture = self.low_textures[low_id]['tex_main']
        self.pos = (x * 32 + self.tk_res_half[0] - 16,
                    y * 32 + self.tk_res_half[1] - 16)
        self.texture_effect = self.low_textures[low_id]['tex_effect_id'] 
        
        # These will get replaced (Currently random cell collision)
        if any((x, y)):
            self.collision = self.tk_choice((False, False, False, False, False, True, False, False, False, False, False, False))
            self.collision = self.tk_rect(self.pos[0], self.pos[1], 32, 32) if self.collision else False
            if self.collision:
                self.texture = self.mid_textures[mid_id][6]
                self.texture_effect = self.mid_textures[mid_id]['tex_effect_id']         
        else:
            self.collision = False


        self.w_texture_low = self.low_textures[low_id]['tex_main']
        self.w_texture_obj = None
        self.w_texture_mid = self.mid_textures[mid_id][6]
        
        self.w_collision = False
        self.w_occluder = False
        
        self.w_sound_walk = self.low_textures[low_id]['tex_walk_sound_id']
        # Corpses can stain this cell with guts
        self.w_footstep_stain_id = 0
    

    def __repr__(self):
        """
            Easier for print debugging

            return -> repr(cell.position)
            
        """
        return repr('{}x{}'.format(*self.pos))


    @classmethod
    def initVisualsAndExtModules(cls):
        """
            Load, build and initialize all textures used by the world

            return -> None
            
        """
        # Create 4 surfaces with black color gradienting toward the other side
        temp = cls.tk_surface((32 * cls.tk_macro_cell_size, 32 * cls.tk_macro_cell_size), cls.tk_srcalpha)
        span = 16
        r, g, b = cls.tk_bg_color
        for enum, alpha in enumerate(xrange(255, 0, -255 / span)):
            # Draw Vertical lines from left to right by 'span' amount
            cls.tk_draw_gfx_line(temp, enum, 0, enum, 32 * cls.tk_macro_cell_size, (r, g, b, alpha))
        
        # Rotate the original one to create the same effect for eachside
        cls.grad_textures = [cls.tk_rotate(temp, -r) for r in xrange(0, 360, 90)]

        # Init/load all external modules

        # 
        cls.load_textures()
        
        # 
        cls.load_effects()

        # 
        cls.setup_casings()

        # 
        cls.load_weapons()

        #
        cls.inv_Reset()

        # 
        cls.setup_footsteps()

        # 
        Enemies.build_all_enemies()

        # 
        cls.shadow_map = Shadows()

        # 
        cls.hero = Hero()

        #
        cls.load_elements() 

        # 
        cls.uioverlay = uiOverlay() 

        # 
        cls.readSoundMusic()

        # 
        cls.load_decalsGibs()

        # 
        cls.Menus = MenuManager()
        
      
    @classmethod
    def move_map(cls, x, y, obj_col=None, surface=None):
        """
            Move the map to give illusion of player moving

            x -> Horizontal movement
            y -> Vertical movement
            obj_col -> Player's hitbox
            surface -> Main surface for debugging purposes if needed

            return -> None
            
        """
        # Get all near environment/enemy collisions
        collisions = cls.get_env_col(-int(cls.cell_x - 16) >> 5,
                                     -int(cls.cell_y - 16) >> 5)

        collisions.extend(cls.get_ent_col(-int(cls.cell_x - 16) >> 6,
                                          -int(cls.cell_y - 16) >> 6))

        # Normalize the speed when going diagonally
        keys = cls.tk_key_pressed()
        if (keys[cls.tk_user['up']] or keys[cls.tk_user['down']]) and \
           (keys[cls.tk_user['right']] or keys[cls.tk_user['left']]):
            # Or perhaps don't..?
            x /= cls.tk_sqrt(2)
            y /= cls.tk_sqrt(2)

        # Store before updating to relay the world position for enemies.
        rel_pos = cls.cell_x, cls.cell_y
        
        # Move the world(Player)
        cls.cell_x += x; cls.cell_y += y

        # Create testing rects for collision
        rl_rect = cls.tk_rect(0, 0, 4, 28)
        tb_rect = cls.tk_rect(0, 0, 28, 4)

        # Move the collision boxes either side of the box for collision testing
        rl_rect.center = obj_col.midright if x < 0 else obj_col.midleft 
        tb_rect.center = obj_col.midbottom if y < 0 else obj_col.midtop
        
        check_x = 1; check_y = 1
        # Check each axis once-per loop. This stops humping the walls
        for check in collisions:
            if check_x:
                if x < 0:
                    if rl_rect.colliderect(check):
                        cls.cell_x -= x; check_x = 0       
                if x > 0:
                    if rl_rect.colliderect(check):
                        cls.cell_x -= x; check_x = 0      
            if check_y:
                if y < 0:
                    if tb_rect.colliderect(check):
                        cls.cell_y -= y; check_y = 0      
                if y > 0:
                    if tb_rect.colliderect(check):
                        cls.cell_y -= y; check_y = 0
        
        # Update all the relative positions
        Enemies.update_relative_pos(rel_pos[0] - cls.cell_x, rel_pos[1] - cls.cell_y)
        cls.effect_rel_pos = cls.cell_x, cls.cell_y
        cls.casing_rel_pos = cls.cell_x, cls.cell_y 


    @classmethod
    def build_map(cls, map_path=None):
        """
            Build the world around the player and populate it with stuff to kill
            also handles the cleaning of the last map and resets everything

            return -> None

        """

        cls.clear_effects()     

        cls.clear_casings()

        cls.cell_x, cls.cell_y = 0, 0 

        player_spawn_pos = 0, 0 # is read from the mapfile
        cls.w_map_size = 32, 32   # is read from the mapfile

        cls.cell_x -= 32 * player_spawn_pos[0]
        cls.cell_y -= 32 * player_spawn_pos[1]

        # Update the player(world) position for enemies
        Enemies.update_relative_pos(32 * player_spawn_pos[0], 32 * player_spawn_pos[1])

        # Reset dynamic entities arrays
        cls.w_entities_dynamic = [[set() for x in xrange(cls.w_map_size[0] / cls.tk_entity_sector_s)] \
                                         for y in xrange(cls.w_map_size[1] / cls.tk_entity_sector_s)]

        # Set the entities boundaries
        cls.w_ent_cell_size = (cls.w_map_size[0] / cls.tk_entity_sector_s,
                               cls.w_map_size[1] / cls.tk_entity_sector_s)
 
        
        cls.w_micro_cells[:] = []
        for y in xrange(cls.w_map_size[1]):
            row = []
            for x in xrange(cls.w_map_size[0]):
                row.append(cls(x, y, 'debug_floor', 'concrete_wall_01'))
            cls.w_micro_cells.append(row)

        cls.gib_reset(cls.w_micro_cells)
        
        # Next step is to combine the smaller cells in to bigger ones to make world rendering faster
        # and have easier way to blit stuff on the world layer
        frag_s = cls.tk_macro_cell_size    # Max fragment size
       
        macro_cells = []        # Ground layer
        macro_cells_walls = []  # Walls layer
        
        # Effect layer is optional which holds sun shadows, pointlights and other static world effects 
        if not cls.tk_no_effect_layer: macro_cells_effects = []     # Not in-use

        # Turn the smaller cells in to bigger cells by combining them 
        #
        #       [[1,2,3,4]                   
        #        [2,2,3,4]                   [[1,2,2,2], [3,4,3,4]]
        #        [3,3,3,4] Converted to ->   [[3,3,4,4], [3,4,4,4]]
        #        [4,4,4,4]                                    

        frag_w = cls.w_map_size[0] / frag_s
        frag_h = cls.w_map_size[1] / frag_s
        cls.w_map_size_macro = frag_w, frag_h
        w_cnt = 0
        h_cnt = 0
        
        while h_cnt <= cls.w_map_size[1] - frag_s:
            w_cnt = 0
            while w_cnt <= cls.w_map_size[0] - frag_s:
                # Combine the smaller cells to bigger cells
                layer_1 = cls.tk_surface((32 * frag_s, 32 * frag_s))                    # Ground
                
                if not cls.tk_no_effect_layer:
                    layer_2 = cls.tk_surface((32 * frag_s, 32 * frag_s))                # Effects (Currently not in-use)
                
                layer_3 = cls.tk_surface((32 * frag_s, 32 * frag_s), cls.tk_srcalpha)   # Walls/Effects
                
                pos = 0, 0
                for d in xrange(0, frag_s):
                    for enum, cell in enumerate(cls.w_micro_cells[d+h_cnt][w_cnt:cls.tk_macro_cell_size+w_cnt]):
                        # Store the first TopLeft cell pos as main coordinates
                        if not d and not enum:
                            pos = cell.pos

                        if cell.collision:
                            layer_3.blit(cell.texture, (32 * enum, 32 * d))
                        else:
                            layer_1.blit(cell.texture, (32 * enum, 32 * d))
                        
                        # # Remove the texture from the cells, they dont need it anymore
                        # if isinstance(cell.texture, tuple):
                        #     # (Cell.texture, Cell.Effects)
                        #     buf = cell.texture[1]
                        #     del cell.texture
                        #     cell.texture = buf
                        # else:
                        #     # The texture doesn't contain any effects,
                        #     # None is the default value to indicate skip 
                        #     # spawning effect from firing an object with gun
                        #     cell.texture = None 
                
                # Create a copy of the original, so no surface bonds are formed
                #cls.tk_draw_rect(layer_1, (0xff, 0xff, 0x0), layer_1.get_rect(), 1)
                macro_cells.append((pos, layer_1.copy()))
                macro_cells_walls.append((pos, layer_3.copy()))
                
                if not cls.tk_no_effect_layer: 
                    macro_cells_effects.append((pos, layer_2.copy()))
                
                w_cnt += frag_s
            h_cnt += frag_s

        # Each cell is ((pos), texture) format
        # Last step is to organize the list to chunks so the spatial alg can work on it
        # Layer_0 = Ground
        cls.w_map_layers[0] = [macro_cells[i:i+cls.w_map_size[0] / frag_s] 
                               for i in xrange(0, len(macro_cells), cls.w_map_size[1] / frag_s)]

        cls.shadow_map.s_loadSurfaceMap(cls.w_map_layers[0])

        # Layer_2 = Walls which cast shadows and contains map effects layer also 
        cls.w_map_layers[2] = [macro_cells_walls[i:i+cls.w_map_size[0] / frag_s] \
                               for i in xrange(0, len(macro_cells_walls), cls.w_map_size[1] / frag_s)]  

        if not cls.tk_no_effect_layer:
            # Layer_1 = Map effects
            #cls.w_map_layers[1] = [macro_cells_effects[i:i+cls.w_map_size[0] / frag_s] \
            #                       for i in xrange(0, len(macro_cells_effects),
            #                                          cls.w_map_size[1] / frag_s)] 
            
            # Map ambient tone
            cls.w_ambientTone(True, True)

            # Shadows
            cls.w_applyStaticShadows()

            # Lights
            # Pos, size(Min: 32), color
            lights = [(32  + 16, 32  + 16, 64  + 32, (0xff, 0x0, 0xff,  0)),
                      (160 + 16, 32  + 16, 128 + 32, (0xff, 0x0, 0xff,  0)),
                      (512 + 16, 512 + 16, 128 + 32, (0xff, 0xaa, 0xff, 0)),
                      (640 + 16, 608 + 16, 128 + 32, (0xff, 0xff, 0xff, 0))]

            cls.w_applyLights(lights)
            
        # Gradient the world boundaries to darkness
        cls.w_applyEdgeGradient(frag_w, frag_h)

        # Time to fill the world with stuff to kill.
        #enemies_locations = [(4, 5, 'rifleman') for _ in xrange(1)] 

        enemies_locations = [(cls.tk_randrange(1, cls.w_map_size[0] - 1), 
                              cls.tk_randrange(1, cls.w_map_size[1] - 1), 'rifleman') for _ in xrange(16)]

        cls.w_spawnEnemies(enemies_locations)
        
        # Build the lightmap...
        if not cls.tk_no_shadow_layer: Shadows.s_load_lightmap(cls.w_micro_cells)

        # Build the MessSolve map
        cls.convertToRectMap(cls.w_map_layers[0])
    
    
    @classmethod
    def w_spawnEnemies(cls, enemy_positions):
        """
            Spawn enemies to the world

            enemy_positions -> list of tuples containing (x, y, id)

            return -> None

        """
        # Time to fill the world with stuff to kill.
        cls.w_enemies.clear() 
        
        for p in enemy_positions:
            # Move the enemy to the correct living_entities cell via index (Spatial position)
            ent_x, ent_y = ((32 * p[0] + 16) / (32 * cls.tk_entity_sector_s),
                            (32 * p[1] + 16) / (32 * cls.tk_entity_sector_s))
            
            # Setup the proper spawn pos
            pos_x = 32 * p[0] + cls.tk_res_half[0] - 16
            pos_y = 32 * p[1] + cls.tk_res_half[1] - 16 
            
            # Spawn an enemy, activate it and store it.
            enemy = Enemies.get_enemy(p[2]).active_enemy(pos_x, pos_y, (ent_x, ent_y))
            e_id = enemy.enemy_id 

            cls.w_entities_dynamic[ent_y][ent_x].add(e_id)
            cls.w_enemies[e_id] = enemy

        # Build collision map for the enemies
        Enemies.get_world_collisions(cls.w_micro_cells)


    
    @classmethod
    def w_ambientTone(cls, ground=True, walls=False):
        """
            Apply ambient coloring to the world

            ground -> Apply ambient tone to the ground?
            walls  -> Apply ambient tone to the walls?

            return -> None

        """
        if not any((ground, walls)): return None
        
        for column in xrange(len(cls.w_map_layers[0])):
            for row in xrange(len(cls.w_map_layers[0][0])):
                ambient_surface = cls.tk_surface(cls.w_map_layers[0][column][row][1].get_size(), cls.tk_srcalpha)
                ambient_surface.fill(cls.tk_ambient_color_tone)
                
                if ground: cls.w_map_layers[0][column][row][1].blit(ambient_surface, (0, 0), 
                                                                    special_flags=cls.tk_blend_rgba_mult)

                if walls: cls.w_map_layers[2][column][row][1].blit(ambient_surface, (0, 0), 
                                                                   special_flags=cls.tk_blend_rgba_mult) 
    
    
    @classmethod
    def w_applyLights(cls, list_of_lights):
        """
            Apply lights to the world

            list_of_lights -> List of tuples (pos, size, color)

            return -> None

        """
        static_light_map = cls.tk_surface((32 * cls.w_map_size[0], 
                                           32 * cls.w_map_size[1]), cls.tk_srcalpha)

        # Note: Editing these may bring some artifacts to the spotlights
        light_intensity = 0x3
        light_powermap  = 0x3

        for l in list_of_lights: 
            # Spotlight surface
            light_map = cls.tk_surface((l[2], l[2]), cls.tk_srcalpha)
            
            # Half the size of the original spotlight to create a corona effect
            light_map_power = cls.tk_surface((l[2] >> 1, l[2] >> 1), cls.tk_srcalpha)

            cx, cy = light_map.get_size()
            cx, cy = cx >> 1, cy >> 1   # Half the size for positioning
            
            # The spotlight is build in steps to intensify the effect smaller the spotlight gets
            for s in xrange(l[2] >> 1, 32, -1):
                color = list(l[3]); color[3] = light_intensity
                cls.tk_draw_gfx_circle(light_map, cx, cy, s, color)

                color = list(l[3]); color[3] = light_powermap
                # The inner corona is half the size of the original spotlight
                cls.tk_draw_gfx_circle(light_map_power, cx >> 1, cy >> 1, s >> 1, color)

            # Cut out all the lights from the surface which walls block
            light_map = cls.__lightspotBuild(l[0], l[1], light_map)

            static_light_map.blit(light_map, (l[0] - cx, l[1] - cy), 
                                  special_flags=cls.tk_blend_rgba_add)

            # Apply the same lightsource again, but half the size off the original (But more power) 
            static_light_map.blit(light_map_power, (l[0] - (cx >> 1), l[1] - (cy >> 1)), 
                                  special_flags=cls.tk_blend_rgba_add)

        # Blit the lights to the ground surface
        for enum1, y in enumerate(cls.w_map_layers[0]):
            for enum2, x in enumerate(y):
                size = 32 * cls.tk_macro_cell_size
                
                light_surface = static_light_map.subsurface((size * enum2, size * enum1, size, size)) 
                cls.w_map_layers[0][enum1][enum2][1].blit(light_surface, (0, 0), 
                                                          special_flags=cls.tk_blend_rgba_add)    
    
    
    @classmethod
    def __lightspotBuild(cls, x, y, light_surf):
        """
            Cut the visibility of the lights with wall segments

            x, y -> position in the world
            light_surf -> surface with the gradient light

            return -> Surface with wall shadows applied to it
            
        """
        ofs32 = False       # A check if the light spot size is not divisible by 64
        add_angle = 0.08    # Additional angle for the quadrilateral casted by walls(Fixes peeking)
        pos = x - 16, y - 16
            
        # Get all walls near the spotlight
        surf = light_surf
        
        radius = surf.get_width()

        spatial_len = (radius >> 5) >> 1
        
        walls = cls.get_env_col(pos[0] >> 5, pos[1] >> 5, 
                                min_x=spatial_len, max_x=spatial_len + 1, 
                                min_y=spatial_len, max_y=spatial_len + 1)

        # Topleft spatial pos
        topleftPos = (pos[0] >> 5) - spatial_len, (pos[1] >> 5) - spatial_len
        
        for draw in walls:
            # Center the wall properly
            wall_pos = list(draw.center)
            wall_pos[0] -= cls.tk_res_half[0] + cls.cell_x + 32 * topleftPos[0]
            wall_pos[1] -= cls.tk_res_half[1] + cls.cell_y + 32 * topleftPos[1]     

            if radius % 64:
                ofs32 = True 
                wall_pos[0] += 16; wall_pos[1] += 16    # Wall segments needs to be pushed back towards center

            # Get all endpoints of the wall (All wall_pos are centered on the walls, so we need to offset them to corner points)
            wallX = ((wall_pos[0] - 16, wall_pos[1] - 16),      # Topleft 
                     (wall_pos[0] + 16, wall_pos[1] + 16),      # Bottomright
                     (wall_pos[0] + 16, wall_pos[1] - 16),      # Topright
                     (wall_pos[0] - 16, wall_pos[1] + 16))      # Bottomleft
            
            #for enp in wallX: cls.tk_draw_circle(surf, (0xff, 0xff, 0x0), enp, 2)  # Debug
            shadow_dist = 256

            # Angle to every endpoint
            rads = [cls.tk_atan2(w[0] - (pos[0] - 32 * topleftPos[0]) - (16 if ofs32 else 0), 
                                 w[1] - (pos[1] - 32 * topleftPos[1]) - (16 if ofs32 else 0)) for w in wallX]

            endpoints1 = ((wallX[0][0] + cls.tk_sin(rads[0] + add_angle) * shadow_dist,     
                           wallX[0][1] + cls.tk_cos(rads[0] + add_angle) * shadow_dist),    
                          (wallX[1][0] + cls.tk_sin(rads[1] - add_angle) * shadow_dist,     
                           wallX[1][1] + cls.tk_cos(rads[1] - add_angle) * shadow_dist))    
            
            cls.tk_draw_polygon(surf, (0x0, 0x0, 0x0), (wallX[0], wallX[1], endpoints1[1], endpoints1[0]))

            endpoints2 = ((wallX[2][0] + cls.tk_sin(rads[2] + add_angle) * shadow_dist,     
                           wallX[2][1] + cls.tk_cos(rads[2] + add_angle) * shadow_dist),    
                          (wallX[3][0] + cls.tk_sin(rads[3] - add_angle) * shadow_dist,     
                           wallX[3][1] + cls.tk_cos(rads[3] - add_angle) * shadow_dist))    

            cls.tk_draw_polygon(surf, (0x0, 0x0, 0x0), (wallX[2], wallX[3], endpoints2[1], endpoints2[0]))

        return surf

    
    @classmethod
    def w_applyStaticShadows(cls):
        """
            TBD

            return -> None

        """
        # The entire map at once gets build in memory for shadowing and then cut in to sections
        static_shadow_map = cls.tk_surface((32 * cls.w_map_size[0], 32 * cls.w_map_size[1]), cls.tk_srcalpha)

        # Length of the shadows
        sl = 16

        # Shadows are casted topleft(Allow customize?)
        for enum1, y in enumerate(cls.w_micro_cells):
            for enum2, x in enumerate(y):
                # Which layer this wall is part of
                pos = 32 * enum2, 32 * enum1
                if x.collision:
                    # Build a quadrilateral stretching from each block to topleft
                    cls.tk_draw_polygon(static_shadow_map, cls.tk_wall_shadow_color, 
                                        ((pos[0],                 pos[1]),
                                         (pos[0],                 pos[1] + 32),
                                         (pos[0] - sl,            pos[1] + 24 - (sl - 8)),
                                         (pos[0] - sl,            pos[1] - sl),
                                         (pos[0] + 24 - (sl - 8), pos[1] - sl),
                                         (pos[0] + 32,            pos[1])))

        # Cut the entire map in to sections and replace the original one's with the  map effects applied
        for enum1, y in enumerate(cls.w_map_layers[0]):
            for enum2, x in enumerate(y):
                size = 32 * cls.tk_macro_cell_size
                shadow_surface = static_shadow_map.subsurface((size * enum2, 
                                                               size * enum1,
                                                               size, size))
                # Get the pos of the cell and replace the original surface with the modified surface 
                #cls.w_map_layers[1][enum1][enum2] = x[0], shadow_surface

                # Apply the shadows to first layer aswell so they can be seen in the areas hidden to player
                cls.w_map_layers[0][enum1][enum2][1].blit(shadow_surface, (0, 0))


    @classmethod
    def w_applyEdgeGradient(cls, wx, wy):
        """
            Apply gradient effect to egdes of the map

            return -> None

        """
        for e1, row in enumerate(cls.w_map_layers[2]):
            for e2, cell in enumerate(row):
                if e1 == 0:      cell[1].blit(cls.grad_textures[1], (0, 0))     # Top 
                if e1 == wy - 1: cell[1].blit(cls.grad_textures[3], (0, 0))     # Bottom 
                if e2 == 0:      cell[1].blit(cls.grad_textures[0], (0, 0))     # Left
                if e2 == wx - 1: cell[1].blit(cls.grad_textures[2], (0, 0))     # Right


    @classmethod
    def render_enemies(cls, surface=None):
        """
            Render enemies near the player using spatial method

            surface -> Surface which to draw on

            return -> None
            
        """
        # Remove the enemies who have been killed
        e_killed = []

        near_x, near_y = -int(cls.cell_x) >> 6, -int(cls.cell_y) >> 6 
        
        for y in xrange(near_y - 6, near_y + 7):
            if y < 0 or y > cls.w_ent_cell_size[1] - 1:
                continue
            
            for x in xrange(near_x - 10, near_x + 11):
                if x < 0 or x > cls.w_ent_cell_size[0] - 1:
                    continue
                
                if len(cls.w_entities_dynamic[y][x]) > 0:
                    for _id in cls.w_entities_dynamic[y][x].copy():
                        # Sanity check
                        # Just to make sure no enemies has avoided the death sequence
                        if _id not in cls.w_enemies:
                            cls.w_entities_dynamic[y][x].discard(_id)
                            continue    
                        
                        # Gather all collisions near the enemy
                        env_col = cls.get_env_col(*cls.w_enemies[_id].get_map_pos(5))
                        
                        # Gather all friendly collisions near the enemy
                        ent_col = cls.get_ent_col(*cls.w_enemies[_id].get_map_pos(6),
                                                  ignore_id=cls.w_enemies[_id].enemy_id)
                        
                        # Update the enemy position on the spatial map if needed
                        new_index = cls.w_enemies[_id].get_map_pos(6)
                        old_index = cls.w_enemies[_id].enemy_spatial_index
                        
                        # Lets not update it if we go out of bounds
                        if old_index != new_index and cls.tk_boundaryCheck(*new_index, limit=cls.w_ent_cell_size):

                            cls.w_enemies[_id].enemy_spatial_index = new_index
                            # Remove the id from the old list and update it to the new cell
                            cls.w_entities_dynamic[old_index[1]][old_index[0]].discard(cls.w_enemies[_id].enemy_id)
                            cls.w_entities_dynamic[new_index[1]][new_index[0]].add(cls.w_enemies[_id].enemy_id)
                            
                        token = cls.w_enemies[_id].handle_enemy(env_col, ent_col, surface=surface)
                        
                        # Check if enemy is firing and display the effects and test for hits
                        if token is not None: cls.fire_weapon(*token, surface=surface, ignore_id=_id)

                        if cls.w_enemies[_id].enemy_delete: 
                            e_killed.append((_id, x, y, cls.w_enemies[_id].enemy_id))     
                
                else:
                    continue
        
        # Remove all dead enemies
        if e_killed: 
            for d in e_killed:
                # Since the entities_dynamic check is based on copy, an
                # error can occur. Protection is provided with this sanity check 
                if d[0] not in cls.w_enemies: continue 
                
                cls.w_entities_dynamic[d[2]][d[1]].discard(d[3])
                del cls.w_enemies[d[0]]
        
        

    @classmethod
    def render_map(cls, layer, surface):
        """
            The map is handled as spatial hashmap with index working as key

            Key is the player location (which is center of the map)
            so render only the cells near the player

            layer -> Which layer to draw
                    1: ground
                    2: effects (Not in-use)
                    3: walls

            surface -> On which surface to draw the layers on

            return -> None
            
        """
        # Save for the second layer since it gets blitted after the player code
        if layer: offx = cls.w_offset[0] - cls.cell_x; offy = cls.w_offset[1] - cls.cell_y
        else:
            # First layer. Store the ground layer position
            offx = 0; offy = 0
            cls.w_offset = cls.cell_x, cls.cell_y

        near_x, near_y = -int(cls.cell_x) >> 8, -int(cls.cell_y) >> 8 
        
        for y in xrange(near_y - 2, near_y + 3):
            if y < 0 or y > cls.w_map_size_macro[1]-1:
                continue
            for x in xrange(near_x - 3, near_x + 4):
                if x < 0 or x > cls.w_map_size_macro[0]-1:
                    continue
                cell_x, cell_y = cls.w_map_layers[layer][y][x][0]
                
                # Combine the cell spawn pos and world pos
                cell_x += cls.cell_x + offx; cell_y += cls.cell_y + offy
                
                # The tiles on the left and top offsets by one when they go
                # out of bounds, so they need to be pushed back by one pixel
                # (Comment this section out and see what happens) (Might be a bug with pygame?)
                cell_x -= 1 if cell_x < 0 else 0
                cell_y -= 1 if cell_y < 0 else 0
                
                surface.blit(cls.w_map_layers[layer][y][x][1], (cell_x, cell_y))



    @classmethod
    def fire_weapon(cls, x, y, angle, f_angle, weapon, dual_index=0, surface=None, player=1, ignore_id=-1):
        """
            Cast a ray from the origin towards the aim direction
            and find the first thing it collides with

            x -> Cast origin X
            y -> Cast origin Y
            angle -> Angle(radians)
            f_angle -> Fixed_Angle (Degrees)
            weapon -> Weapon used to fire the shot
            dual_index -> If the weapon has 2 different firing frames, you can toggle this between 0, 1 to control
                          Which one to spawn
            player -> Controls who is firing the weapon and what collisions to check for
            ignore_id -> Enemy id to ignore when firing the weapon (So enemy doesn't shoot itself)

            return -> None
            
        """
        # Note: Break this down to smaller functions

        # Handle effects spawned by the weapon
        efx, efy = cls.tk_PolarToCartesian(x, y, angle - cls.all_weapons[weapon]['w_effect_angle'][dual_index], 
                                           cls.all_weapons[weapon]['w_effect_dist'][dual_index])
        
        # Fetch random effect from the array defined by the weapon cfg
        cls.spawn_effect(cls.tk_choice(cls.all_weapons[weapon]['w_fire_effects']), 
                        (efx, efy), angle=f_angle)

        # Handle casings spawned by the weapon
        cx, cy = cls.tk_PolarToCartesian(x, y, angle - cls.all_weapons[weapon]['w_casing_angle'][dual_index],
                                         cls.all_weapons[weapon]['w_casing_dist'][dual_index])

        # Spawn the casing and give the spawn angle some offset
        casing = cls.all_weapons[weapon]['w_casing'][0]
        if casing: cls.spawn_casing(casing, cx, cy, angle + cls.tk_uniform(0.9, 1.2))

        # Weapon projectile blast size (No need to edit this one)
        # How big the projectile rect is during raycasting
        w_blast_size = 8 
        
        w_range =  cls.all_weapons[weapon]['w_range']        # Weapon max range
        w_spread = cls.all_weapons[weapon]['w_inaccuracy']   # Weapon hit accuracy

        # Give the weapon some inaccuracy based on weapon's stats
        angle -= cls.tk_uniform(-w_spread, w_spread)

        baseAx, baseAy = cls.tk_sin(angle), cls.tk_cos(angle)
        
        # NOTE: All the ray intersection task are done using raycasting (Possible change to DDA)

        # Convert the set to dict with the rects being keys
        collisions = dict.fromkeys(cls.get_ray_env_collisions(x, y, baseAx, baseAy, w_range), -1)

        # Gather all enemies for testing if the ray struck any of them
        # Walls values are -1 and enemies values start from 0 and up (enemy ids)
        
        # Add the enemy collisions with the env_collisions and move to test the bullet rect against them
        collisions.update({k:v for k, v in cls.get_ray_ent_collisions(x, y, baseAx, baseAy, w_range, ignore_id)})

        # Cast a rect towards the aim direction step-by-step
        # To find collision with environment or enemy/player
        test_rect = cls.tk_rect(x, y, w_blast_size, w_blast_size)  
        
        for cast in xrange(16, w_range, w_blast_size >> 2):
            dx, dy = (int(x - baseAx * cast),
                      int(y - baseAy * cast))
            
            # This is the 'bullet' rect
            test_rect.x = dx - (w_blast_size >> 1)
            test_rect.y = dy - (w_blast_size >> 1)
            
            # If a positive collision is found, return (key, value) with the
            # key being the rect what we are looking for
            pair = test_rect.collidedict(collisions)
            if pair is not None:
                if pair[1] == -1:
                    # Hitscan
                    if cls.all_weapons[weapon]['w_type'] == 1:
                        if cls.all_weapons[weapon]['w_hitwall']:
                            # Collision found, find the closest surface normal we struck
                            orx, ory = test_rect.center

                            normals = [pair[0].midleft,  pair[0].midtop,
                                       pair[0].midright, pair[0].midbottom]

                            # Calculate distance to each surface normal midpoint (Find the normal we most likely hit)
                            dists = [round(cls.tk_hypot(orx - x, ory - y), 1) for x, y in normals]
                            
                            # Get the index of the closest surface normal
                            index = dists.index(min(dists))
                        
                            # Get the hit effect of the Wall/Object we got, if it has one
                            # Pinpoint the location of the wall so we can examine its data
                            ex = (int(pair[0].x - cls.tk_res_half[0] - cls.cell_x) >> 5) + 1
                            ey = (int(pair[0].y - cls.tk_res_half[1] - cls.cell_y) >> 5) + 1
                            hit_effect = cls.w_micro_cells[ey][ex].texture_effect 
                            
                            if hit_effect is not None:
                                # Choose random effect from the list of effect from the wall/object
                                hit_effect = cls.tk_choice(hit_effect)
                                
                                # Get the origin of the effect
                                offset = cls.all_effects[hit_effect][0][1]
                                
                                # Trying to spawn an effect with no all_side variable creates an KeyError since its not rotated
                                # to face each side, so default the side/face to key 0
                                dface = 0 if len(cls.all_effects[hit_effect].keys()) == 1 else index 
                                pos = normals[index]
                                
                                if index == 0:
                                    # Left side of the wall
                                    l = normals[index][1] - ory 
                                    cls.spawn_effect(hit_effect, (pos[0] - offset[0], pos[1] - l), dface)
                                elif index == 1:
                                    # Top
                                    l = normals[index][0] - orx
                                    cls.spawn_effect(hit_effect, (pos[0] - l, pos[1] - offset[1]), dface)
                                elif index == 2:
                                    # Right
                                    l = normals[index][1] - ory
                                    cls.spawn_effect(hit_effect, (pos[0] + offset[0] - 2, pos[1] - l), dface)
                                else:
                                    # Down
                                    l = normals[index][0] - orx 
                                    cls.spawn_effect(hit_effect, (pos[0] - l, pos[1] + offset[1] - 2), dface)
                    else:
                        # Run damage check to see if projectile weapon Area-of-effect hit anything
                        print 'Aoe Damage Check: Hit Wall!'
                        cls.calc_aoe_taken(*test_rect.center, weapon=weapon)
                
                else:
                    # Hit the target! spawn (blood or whatever you want) indicating it 
                    cls.calc_dmg_taken(*pair[0].center, tx=x, ty=y, weapon=weapon, enemy_id=pair[1])
                
                # This makes somewhat interesting effect. If you remove the break
                # it allows bullets to pass through multiple objects (Walls/Enemies) 
                break
        else:
            # Went through the loop without any wall/enemy hits. 
            if cls.all_weapons[weapon]['w_type'] == 2:
                print 'Aoe Damage Check: Hit Nothing'
                cls.calc_aoe_taken(*test_rect.center, weapon=weapon)

            else:
                # Nothing to hit but ground
                if cls.all_weapons[weapon]['w_hitground']:  
                    gx, gy = cls.get_spatial_pos(dx, dy)
                    
                    if cls.tk_boundaryCheck(gx, gy, cls.w_map_size):
                        # Blit the groundeffect to ground
                        if cls.w_micro_cells[gy][gx].texture_effect is not None:
                            cls.spawn_effect(cls.tk_choice(cls.w_micro_cells[gy][gx].texture_effect), (dx, dy),
                                             angle=f_angle)   
                else:
                    # Energy dispatched went out from this world
                    pass
        
        # Trail/End_effects
        raw_dist = int(cls.tk_hypot(efx - test_rect.center[0], 
                                    efy - test_rect.center[1]))

        if cls.all_weapons[weapon]['w_type'] == 1:
            # Hitscan weapons

            # Change the trailing start position randomly
            r_dist = cls.tk_randrange(max(1, raw_dist))
        
            if r_dist < 64: return None     # Skip the trailing if the distance is too short

            # And keep the trails on the bullet path
            sx, sy = int(efx - baseAx * r_dist), int(efy - baseAy * r_dist)

            # Display bullet trails
            cls.tk_draw_gfx_line(surface, sx, sy, 
                                int(sx + baseAx * 48), 
                                int(sy + baseAy * 48), 
                                cls.tk_bullet_trail_color)

        else:
            # Projectile weapons trailing and end effect 
            for l in xrange(1, raw_dist, 8):
                # Leave a (Smoke or whatever you want) trail
                ef = cls.tk_choice(cls.all_weapons[weapon]['w_trail_effects'])
                cls.spawn_effect(ef, (efx - baseAx * l, 
                                      efy - baseAy * l + cls.tk_randrange(-4, 4))) 
            
            # End effect of the projectile (Usually explosion but anything goes)
            cls.spawn_effect(cls.tk_choice(cls.all_weapons[weapon]['w_explosion_effects']), test_rect.center)


    @classmethod
    def get_ray_env_collisions(cls, x, y, bx, by, dist, ret_first_dist=False):
        """
            Get environment collisions from x, y to dist

            x, y -> origin
            bx, by -> angle x, y
            dist -> max ray distance

            ret_first_dist -> if 'True' -> return distance to the first rect within the ray
            return -> 'set' of all collisions found on the rays path

        """
        env_collisions = set()
        for step in xrange(0, dist + 1, 32):
            dx = int(x - bx * step)
            dy = int(y - by * step)
            
            ray_x = -int((cls.cell_x - 16)) + (dx - cls.tk_res_half[0]) >> 5 
            ray_y = -int((cls.cell_y - 16)) + (dy - cls.tk_res_half[1]) >> 5
            env_collisions.update(cls.get_env_col(ray_x, ray_y))

        if ret_first_dist:
            if not env_collisions: return dist
            # Rect doesn't take sets, so convert to list
            l = list(env_collisions)
            test_rect = cls.tk_rect(x, y, 8, 8)
            
            for step in xrange(0, dist, 8):
                dx = x - bx * step
                dy = y - by * step
                test_rect.center = dx, dy
                
                if test_rect.collidelist(l) != -1:
                    return cls.tk_hypot(dx - x, dy - y) - 4   

            return dist

        return env_collisions


    @classmethod
    def get_ray_ent_collisions(cls, x, y, bx, by, dist, ignore_id):
        """
            Get entities collisions from x, y to dist

            x, y -> Origin
            bx, by -> angle x, y
            dist -> max ray distance
            ignore -> Ignore this id from the list

            return ->  'Set' of all collisions found on the rays path
            
        """
        ent_collisions = set()  
        for step in xrange(0, dist + 1, 64):
            dx, dy = (int(x - bx * step), 
                      int(y - by * step))
            
            ray_x = -int((cls.cell_x - 32)) + (dx - cls.tk_res_half[0]) >> 6 
            ray_y = -int((cls.cell_y - 32)) + (dy - cls.tk_res_half[1]) >> 6
            ent_collisions.update(cls.get_ent_col(ray_x, ray_y, ignore_id=ignore_id, get_ids=1))

        return ent_collisions 

    
    
    @classmethod
    def get_spatial_pos(cls, wx, wy, shift=5):
        """
            Convert world position to spatial position index

            wx, wy -> World position

            return -> World cell index (x, y)

        """
        return (int(-(cls.cell_x - (wx - cls.tk_res_half[0] + 16))) >> shift,
                int(-(cls.cell_y - (wy - cls.tk_res_half[1] + 16))) >> shift)


    
    @classmethod
    def calc_dmg_taken(cls, sx, sy, tx, ty, weapon=None, enemy_id=None):
        """
            Calculate weapon damage against enemies or player

            sx, sy -> Source (x, y) 
            tx, ty -> Target (x, y) 
            weapon -> Weapon id 
            enemy_id -> Id of the enemy who took the hit

            return -> None
             
        """
        srx, sry = sx, sy

        # Calculate the angle between shooter and target, and give it small offset angle
        e_angle = cls.tk_atan2(tx - srx, ty - sry) + cls.tk_uniform(-.5, .5)

        srx -= cls.tk_sin(e_angle) * 20; sry -= cls.tk_cos(e_angle) * 20

        # Spawn blood on hit
        cls.spawn_effect(cls.tk_choice(cls.w_enemies[enemy_id].enemy_blood_frames), (srx, sry), 
                         angle=cls.tk_degrees(e_angle))

        # Wake up enemy to hunt for player
        cls.w_enemies[enemy_id].enemy_state = 1
        
        # Decrease weapon damage from the enemy health pool
        cls.w_enemies[enemy_id].enemy_health -= cls.all_weapons[weapon]['w_damage']
        if cls.w_enemies[enemy_id].enemy_health <= 0:
            enemy_vector = cls.w_enemies[enemy_id].enemy_targetAngleDeg 

            # Delete the enemy from the map
            cls.w_enemies[enemy_id].enemy_delete = 1

            cx, cy = cls.get_spatial_pos(sx, sy)
            inside_world = cls.tk_boundaryCheck(cx, cy, cls.w_map_size) 

            # Spawn body or gib the corpse based on weapons chance
            if cls.tk_randrange(0, 100) < cls.all_weapons[weapon]['w_gibchance']:
                stain = cls.gs_gib_now(sx, sy, cls.cell_x, cls.cell_y, enemy_vector, 
                                       cls.tk_choice(cls.w_enemies[enemy_id].enemy_gore_profile))

                if stain is not None and inside_world:
                    cls.w_micro_cells[cy][cx].w_footstep_stain_id = stain    
                
            else:
                # Spawn normal dead corpse animation
                corpse = cls.tk_choice(cls.w_enemies[enemy_id].enemy_dead_frames) 
                cls.spawn_effect(corpse, (sx, sy), angle=enemy_vector)

                # Make the ground stain player's boots
                if cls.all_effects[corpse] > 0 and inside_world: 
                    cls.w_micro_cells[cy][cx].w_footstep_stain_id = cls.all_effects[corpse][0][3]  # Get the stain index
 
            # See if there is dash in the name for indication of dual weapons (2 guns need to be dropped)
            w = cls.w_enemies[enemy_id].enemy_weapon 
            if cls.all_weapons[w]['w_buyable']:
                w = w.split('-')    # Use the '-dual' suffix to spawn 2 guns 

                for _ in xrange(len(w)):
                    # Give some randomness for the weapon drops (Angle and distance)
                    drop_vector = cls.tk_radians(enemy_vector) + cls.tk_uniform(-cls.tk_pi, cls.tk_pi) 
                    drop_dist = cls.tk_randrange(16, 32) 
                    
                    cls.spawn_effect('{}_drop'.format(w[0]), 
                                    (sx - cls.tk_sin(drop_vector) * drop_dist, 
                                     sy - cls.tk_cos(drop_vector) * drop_dist), 
                                     angle=enemy_vector)

        # Add Aoe damage top of the normal hit damage if projectile weapon
        if cls.all_weapons[weapon]['w_type'] == 2: 
            print 'Aoe Damage Check: Hit Enemy'
            cls.calc_aoe_taken(sx, sy, weapon)

    
    @classmethod
    def calc_aoe_taken(cls, ex, ey, weapon):
        """
            Calculate Area of effect for projectile weapons

            ex, ey -> Effect location (x, y)
            weapon -> Weapon id

            return -> None
        """ 
        # Get the groundzero cell for the explosion
        gx, gy = cls.get_spatial_pos(ex, ey, 6) 
        
        if cls.tk_boundaryCheck(gx, gy, cls.w_ent_cell_size):
            print cls.all_weapons[weapon]['w_aoe_range']


    
    @classmethod
    def get_env_col(cls, x, y, min_x=1, max_x=2, min_y=1, max_y=2, surface=None):
        """
            Get all the collisions around the x, y position from the cells
            
            x -> Origin (Divided by Cellsize)
            y -> Origin (Divided by Cellsize)

            min, max -> Boundaries around the source (x, y)
            
            return -> A list of all near cells collisions near the origin
            
        """
        near_collisions = []
        for cy in xrange(y - min_y, y + max_y):
            if not -1 < cy < cls.w_map_size[1]:
                continue 

            for cx in xrange(x - min_x, x + max_x):
                if not -1 < cx < cls.w_map_size[0]:
                    continue 

                if cls.w_micro_cells[cy][cx].collision:
                    rect = cls.w_micro_cells[cy][cx].collision 
                    near_collisions.append(cls.tk_rect(rect.x + cls.cell_x,
                                                       rect.y + cls.cell_y,
                                                       32, 32))
        return near_collisions


    
    @classmethod
    def get_ent_col(cls, x, y, ignore_id=-1, get_ids=0, surface=None):
        """
            Get all the living collisions around the x, y position from the cells
            
            x -> Origin (Divided by Cellsize)
            y -> Origin (Divided by Cellsize)
            ignore_id -> This is used by enemies to ignore their own collision
            get_ids -> Get the enemy rect and its id
            surface -> Debug surface

            return -> A list of all living entities near the origin
            
        """
        near_collisions = []
        for ry in xrange(y - 1, y + 2):
            if ry < 0 or ry > cls.w_ent_cell_size[1] - 1:
                continue
            for rx in xrange(x - 1, x + 2):
                if rx < 0 or rx > cls.w_ent_cell_size[0] - 1:
                    continue
                if len(cls.w_entities_dynamic[ry][rx]) > 0:
                    for get_id in cls.w_entities_dynamic[ry][rx]:
                        if get_id not in cls.w_enemies or get_id == ignore_id: continue 
                        
                        e_pos = cls.w_enemies[get_id].get_map_pos(0, 0)
                        rect = cls.tk_rect(e_pos[0] + cls.cell_x, e_pos[1] + cls.cell_y, 32, 32)

                        near_collisions.append((rect, get_id) if get_ids else rect)

        return near_collisions



class Main(World, DeltaTimer):
    """
        Main stage

    """
    def __init__(self):
        # Center the windowed mode on screen
        self.tk_environ['SDL_VIDEO_CENTERED'] = '1'
        
        # Audio needs to be initialized before pygame.init 
        # so arguments can be used for the audio init
        self.tk_mixer.init(self.tk_audio_frequency, -16, self.tk_audio_channel, self.tk_audio_buffersize)
        self.tk_mixer.set_num_channels(self.tk_audio_max_channels)

        self.tk_init()  
        self.set_basic_window_elements(mouse_visibility=False)    
        
        self.screen = self.tk_display.set_mode(self.tk_resolution, 0, 32)
        
        # Initialize everything 
        World.initVisualsAndExtModules()

        self.Menus.all_menus[5].run(self.screen)
        
        # Note: Move this to campaign and next map function menu
        World.build_map()


        
    def gameloop(self):
        """
            Mainloop

            return -> None
            
        """
        while 1:
            delta, delta_ms = self.dt_tick(self.tk_fps)

            self.screen.fill(self.tk_bg_color)

            for event in self.tk_eventDispatch():
                self.uioverlay.Event_handleEvents(event.type)      

            # Render ground
            self.render_map(0, self.screen)
            
            if not self.tk_no_shadow_layer:
                self.shadow_map.s_fetchDelta(self.cell_x, self.cell_y)

            self.gib_render_all(self.screen, self.cell_x, self.cell_y)
            
            self.render_enemies(self.screen)
                
            self.hero.hero_handle(self.screen)
                    
            self.render_effects(self.screen)

            self.render_casings(self.screen)

            if not self.tk_no_shadow_layer:
                self.shadow_map.s_applyShadows(self.cell_x, self.cell_y, self.screen)

            # Render walls
            self.render_map(2, self.screen)

            self.uioverlay.drawOverlay(self.screen)

            self.tk_display.set_caption('{}, FPS: {}'.format(self.tk_name, round(self.dt_fps(), 2)))

            self.tk_display.flip()
             

if __name__ == '__main__':
    #Enemies.initialize_pathfinder()
    Main().gameloop()

