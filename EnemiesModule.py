from ConfigsModule import TkCounter
from TextureLoader import TextureLoader
from Weapons import Weapons
from Timer import DeltaTimer

import PathFinder

# NOTE: Fix Rotation from player back to waypoint 

class Enemies(TextureLoader, Weapons, DeltaTimer):
    """
        TBD
    """
    # This dict holds a blueprint for the enemies
    # gets copied to the map enemy pool and activated
    all_enemies = {}
    
    # Provide all active enemies unique id 
    enemy_id_cnt = TkCounter(0)
    
    # Relative position for enemies (Player position on the map)
    enemy_rel_pos = [0, 0]

    # Provide the enemy copy of the world with all the collisions
    enemy_world_collisions = []     # Currently not in-use
    
    # World size (Number of 32x32 cells per row and column)
    enemy_world_mapsize = 0, 0

    
    def __init__(self, **kws):
        self.enemy_rect   = self.tk_rect(0, 0, 32, 32)
        self.enemy_speed  = kws['e_speed']
        self.enemy_health = kws['e_health']
        self.enemy_name   = kws['name']

        # Distance, Awareness cone, alarmed cone
        self.enemy_fov = kws['e_fovdist'][0], self.tk_radians(kws['e_fovdist'][1]) / 2, self.tk_radians(340) / 2
        
        # Basic form
        self.enemy_weapon = kws['e_weapon']
        self.enemy_legs   = kws['tex_legs']
        self.enemy_torso  = kws['tex_torso']

        # Stuff left behind when moving, getting hit or dying
        self.enemy_blood_frames = kws['tex_bsplat']      # List of blood name strings
        self.enemy_dead_frames =  kws['tex_death']       # List of animations to be when dying
        self.enemy_gore_profile = kws['gore_profile']    # What gibs to spawn based on gore profile
        
        # Sound
        self.enemy_pain_snd = kws['snd_pain']            # Pain sound id's 
        self.enemy_death_snd = kws['snd_death']          # Death sound id's
        self.enemy_hit_snd = kws['snd_hit']              # Getting hit
        
        # 0: Guarding/Idling; 1: Agitated (Looking to murder the player)
        self.enemy_state  = 0
        self.enemy_delete = 0   # Is the enemy dead? Remove it then from the map

        # Targeting related
        self.enemy_targetAngleAbs = 0     # Last angle
        self.enemy_targetAngleDif = 0     # Different between the new angle and old angle (Shortest rotation) 
        
        self.enemy_targetAngleDeg = 0     # Up to date angle (Degrees)  (Used to relay the rotation for others)
        
        self.enemy_targetPos = 0, 0       # Latest waypoint (x, y) world pos
        
        self.enemy_targetInterval = self.tk_trigger_hold(self.tk_enemy_waypoint_get, state=0)         # Fetch new waypoint delay
        self.enemy_targetInterval_alarm = self.tk_trigger_hold(self.tk_enemy_alarm_state, state=0)    # Alarm state time   

        # Collision is building small rects on top/down, right/left and centering them on
        # the direction of the moving
        self.rl_rect = self.tk_rect(0, 0, 4, 28)
        self.tb_rect = self.tk_rect(0, 0, 28, 4)

    

    def load_enemy_animation(self):
        """
            Load and setup animations for the enemy

            (This should be called once and when the enemy has been deepcopied to the active enemy pool)

            return -> None

        """
        # Legs animation
        self.enemy_legs_frame_cycle = self.tk_cycle(xrange(len(self.legs_textures[self.enemy_legs][1])))
        self.enemy_legs_frame_index = 0   
        
        # Torso animation
        self.enemy_torso_frame_cycle = self.tk_cycle(xrange(len(self.torso_textures[self.enemy_torso][1])))
        self.enemy_torso_frame_index = 0  
        
        # Setup enemy firerate
        firerate = self.all_weapons[self.enemy_weapon]['w_firerate']
        self.enemy_weapon_firerate = self.tk_trigger_hold(firerate)

        self.enemy_weapon_dual_cycle = self.tk_deque((0, 1))     # Support for dual guns

        # Figure sets the blit order and contains the rects to center the images and offset
        self.enemy_figure = ((self.enemy_legs, self.tk_rect(0, 0, 32, 32), 
                              self.legs_textures[self.enemy_legs][0][2]),
                             (self.enemy_torso, self.tk_rect(0, 0, 64, 64), 
                              self.torso_textures[self.enemy_torso][0][4]))
        
        # Delay between different animation frames
        self.enemy_anim_delay = self.tk_trigger_const(.04)    

        # Length of the fire animation
        firerate = int(60 * firerate)
        l = [0]
        if firerate > 7: l.extend([1] * 7)      # Cap the fire anim length to 8
        else: l.extend([1] * (firerate - 1))    # Use the firerate - 1 as length
        
        self.enemy_fire_anim_len = self.tk_deque(l)
        self.enemy_fire_anim_timer = self.tk_trigger_const(60 / float(1000) / max(6, len(self.enemy_fire_anim_len))) 
          

    def __repr__(self):
        """
            Easier for debugging
            
            return -> repr(pos, id)

        """
        return repr('(pos:{}, id:{})'.format(self.enemy_pos, self.enemy_id))


    def active_enemy(self, x, y, spatial_index):
        """
            Activate the enemy for active duty

            x, y -> Starting position in map
            spatial_index -> Index of the starting pos in the world map

            return -> self

        """
        # Create 4 coordinates:
        #   - enemy_pos: This is the raw position from topleft of the screen
        #   - enemy_map_pos: This is the position from the map topleft 
        #   - enemy_mov_pos: Additive accumulator for storing its own movement
        self.enemy_pos = x, y
        
        # offset by 16 to center it around 32x32 entity
        self.enemy_map_pos = ((self.enemy_pos[0] - self.tk_res_half[0] + 16), 
                              (self.enemy_pos[1] - self.tk_res_half[1] + 16))
        
        # Set the first waypoint to random cell near the enemy
        self.enemy_targetPos = (self.enemy_map_pos[0] + self.tk_choice((-32, 32)),
                                self.enemy_map_pos[1] + self.tk_choice((-32, 32)))

        # Enemy own accumulating movement
        self.enemy_mov_pos = [0, 0]

        # Cached position on map from player and enemy's own spawn position
        self.enemy_rel_target_pos = (self.enemy_map_pos[0] - self.enemy_pos[0], 
                                     self.enemy_map_pos[1] - self.enemy_pos[1])
        
        # Spatial index on the 2d entity array
        self.enemy_spatial_index = spatial_index 

        # Provide unique id for each enemy
        self.enemy_id = self.enemy_id_cnt(); self.enemy_id_cnt += 1
        return self


    def get_map_pos(self, shift_int=0, origin=1, clamp_to_world=False, offset=(0, 0)):
        """
            Get the map position(From topleft of the map, not screen)
            and round it by given int (Shift)

            shift_int -> Integer, which is used to right shift the map position
            origin -> 0: From the screen topleft
                      1: from the map topleft
            
            clamp_to_world -> Clamp the value within the world (Expects shift_int to be 5)
            offset -> 
                    

            return -> (x, y) enemy position from map topleft rounded by given carry, or
                       enemy position relative to screen topleft not rounded
            
        """
        if origin:
            x = int((self.enemy_map_pos[0] - offset[0]) - self.enemy_mov_pos[0] + 16) >> shift_int
            y = int((self.enemy_map_pos[1] - offset[1]) - self.enemy_mov_pos[1] + 16) >> shift_int
            
            if clamp_to_world: 
                x = self.tk_clamp(x, 1, self.enemy_world_mapsize[0] - 2)
                y = self.tk_clamp(y, 1, self.enemy_world_mapsize[1] - 2)
            
            return x, y
            
        else:
            return self.enemy_pos[0] - self.enemy_mov_pos[0], self.enemy_pos[1] - self.enemy_mov_pos[1]


    def ray_cast_get_walls(self, vecx, vecy, dist):
        """
            Gather 3x3 sample near the world_pos

            vecx, vecy -> Raycast direction
            dist -> Raycast distance

            return -> Rects (walls) near the world_pos

        """
        points = set()
        
        for step in xrange(0, dist, 32):
            pntx, pnty = vecx * step, vecy * step 
            points.add(self.get_map_pos(5, 1, clamp_to_world=1, offset=(pntx, pnty))) 

        near_walls = set()
        
        for x, y in points:
            for cy in xrange(y-1, y + 2):
                if not -1 < cy < self.enemy_world_mapsize[1] - 1:
                    continue 
                
                for cx in xrange(x - 1, x + 2):
                    if not -1 < cx < self.enemy_world_mapsize[0] - 1:
                        pass

                    if self.enemy_world_collisions[cy][cx]: 
                        near_walls.add((cx, cy))

        cx, cy = self.tk_res_half[0] - 16, self.tk_res_half[1] - 16
        return [self.tk_rect((cx + 32 * x) - self.enemy_rel_pos[0], 
                             (cy + 32 * y) - self.enemy_rel_pos[1], 
                              32, 32) for x, y in near_walls]

    
    
    def ray_cast_pos(self, ePos, dist, surface=None, waypoint_track=False, waypoint_angle=None):
        """
            Cast a ray to check if enemy can truly see the player (no walls obscuring the view)
            Also used to validate how far can enemy see that new random waypoint

            ePos -> Self position 
            dist -> Distance to player (Max raycast distance)
            surface -> Debugging
            waypoint_track -> Use the raycast to validate the new fetched waypoint
            waypoint_angle -> Angle to the newpoint

            return -> Bool when hunting player / Position when hunting waypoints

        """
        dist = int(dist)
        
        # Angle to waypoint or calculate angle to player
        angle = waypoint_angle if waypoint_track else (self.tk_atan2(ePos[0] - self.tk_res_half[0], 
                                                                     ePos[1] - self.tk_res_half[1])) 

        px = self.tk_sin(angle); py = self.tk_cos(angle)

        # Get all walls within raycast path
        walls = self.ray_cast_get_walls(px, py, dist)
        #for wall in walls: self.tk_draw_rect(surface, (0xff, 0xff, 0x0), wall, 1)
        
        # rayrect for testing against those walls
        test_rect = self.tk_rect(0, 0, 8, 8)

        for step in xrange(0, dist, 8):
            pntx, pnty = px * step, py * step 
            
            test_rect.center = ePos[0] - pntx, ePos[1] - pnty
            #self.tk_draw_rect(surface, (0xff, 0xff, 0x0), test_rect, 1)  
            
            ix, iy = self.get_map_pos(5, 1, clamp_to_world=1, offset=(pntx, pnty))

            if test_rect.collidelist(walls) != -1: return (ix * 32, iy * 32) if waypoint_track else 0   
            
            #if self.enemy_world_collisions[iy][ix]:
            #    return (ix * 32, iy * 32) if waypoint_track else 0 
        
        # Update the last seen player position as new waypoint
        if not waypoint_track: self.enemy_targetPos = ix * 32, iy * 32; 
        
        return 1 


    def __check_fov_debug(self, ePos, rAngle, surface):
        # Enemy position
        self.tk_draw_circle(surface, (0xff, 0xff, 0x0), ePos, 16, 1)   
        
        # View distance
        self.tk_draw_circle(surface, (0xff, 0xff, 0x0), ePos, self.enemy_fov[0] - 4, 1)

        view_angle = self.enemy_fov[1 + self.enemy_state] 
        # View angle
        self.tk_draw_line(surface, (0x0, 0x0, 0xff), ePos,
                         (ePos[0] - self.tk_sin(rAngle - view_angle) * self.enemy_fov[0],
                          ePos[1] - self.tk_cos(rAngle - view_angle) * self.enemy_fov[0]), 1)

        self.tk_draw_line(surface, (0x0, 0x0, 0xff), ePos,
                         (ePos[0] - self.tk_sin(rAngle) * self.enemy_fov[0],
                          ePos[1] - self.tk_cos(rAngle) * self.enemy_fov[0]), 1)
        
        self.tk_draw_line(surface, (0x0, 0x0, 0xff), ePos,
                         (ePos[0] - self.tk_sin(rAngle + view_angle) * self.enemy_fov[0],
                          ePos[1] - self.tk_cos(rAngle + view_angle) * self.enemy_fov[0]), 1)    
    
    
    def check_fov(self, ePos, rAngle, pAngle, surface=None):
        """
            Check field of view for player

            ePos -> Self position
            rAngle -> AngleRad (Current view angle)
            pAngle -> Angle to player

            return -> None

        """
        #self.__check_fov_debug(ePos, rAngle, surface)

        # See if the player is within enemy fov distance 
        dist = self.tk_hypot(ePos[0] - self.tk_res_half[0], ePos[1] - self.tk_res_half[1])
        
        # Check the distance to player (or ignore it if enemy is enraged)
        if dist < self.enemy_fov[0] or self.enemy_state:
            
            # Angle between self and player
            #angle = self.tk_atan2(ePos[0] - self.tk_res_half[0], ePos[1] - self.tk_res_half[1]) 
            
            # Check within cone or withing "hearing" distance
            if self.check_fov_angle(rAngle, pAngle, self.enemy_fov[1 + self.enemy_state]) or (dist < self.tk_enemy_hearing_dist):
                #self.tk_draw_circle(surface, (0xff, 0xff, 0x0), self.tk_res_half, 16, 1)
                
                # See if the enemy can actually see him
                if self.ray_cast_pos(ePos, dist, surface):

                    self.enemy_targetInterval_alarm.reset() 
                    self.enemy_state = 1
            

    def check_fov_angle(self, v1Angle, v2Angle, cAngle):
        """
            Check if player is inside the fov angle

            v1Angle -> Current view Angle
            v2Angle -> Angle between self and player
            cAngle  -> Cone Angle to trigger if less than this

            return -> Bool

        """
        v1 = [self.tk_cos(v1Angle), self.tk_sin(v1Angle)] 
        v2 = [self.tk_cos(v2Angle), self.tk_sin(v2Angle)]
        
        return self.tk_acos( self.tk_np_dot(v1, v2) ) < cAngle 


    def get_new_waypoint(self, ePos, surface=None):
        """
            In waypoint hunt mode 
            this function is used to get a new valid waypoint within enemy perimeter

            return -> Waypoint index (x, y) and angle to waypoint

        """
        # Get up-to-date cell position when enemy is standing
        w_index = self.get_map_pos(5)

        # Create the waypoint around the old position (Randomly choose new point)
        rx = self.tk_clamp(self.tk_randrange(w_index[0] - 16, w_index[0] + 17), 1, self.enemy_world_mapsize[0] - 2)
        ry = self.tk_clamp(self.tk_randrange(w_index[1] - 16, w_index[1] + 17), 1, self.enemy_world_mapsize[1] - 2)
        
        # Angle to the new waypoint
        angle = self.tk_atan2(w_index[0] - rx, w_index[1] - ry)
        
        rx, ry = rx * 32, ry * 32

        # Distance to the new waypoint
        dist = self.tk_hypot(w_index[0] * 32 - rx, w_index[1] * 32 - ry)
        
        # Check if the enemy can 'see' the waypoint and clamp to the closest wall. This stops humping the walls (To some degree)
        see_waypoint = self.ray_cast_pos(ePos, dist, surface, waypoint_track=1, waypoint_angle=angle)
        if not isinstance(see_waypoint, int): rx, ry = see_waypoint 

        # Update the waypoint index
        self.enemy_targetPos = rx, ry

        return angle


    
    def fetch_target_vector(self, waypoint_track=True, sx=0, sy=0, surface=None):
        """
            Hunt for the target position(Which can be waypoint or player)

            waypoint_track -> Hunt waypoints
            sx, sy -> Enemy coordinates relative to player

            return -> None

        """
        # Waypoint
        if waypoint_track: angle = self.get_new_waypoint((sx, sy), surface=surface)       

        # Player
        else: angle = self.tk_atan2(sx - self.tk_res_half[0], sy - self.tk_res_half[1])    

        # Find the shortest rotation to new angle
        diff = angle - self.enemy_targetAngleAbs
        if   diff >  self.tk_pi: diff -= 2 * self.tk_pi
        elif diff < -self.tk_pi: diff += 2 * self.tk_pi

        # New angle to hunt for
        self.enemy_targetAngleDif = diff


    def handle_enemy(self, env_cols=None, f_cols=None, surface=None):
        """
            Handle enemy logic

            env_cols -> Environment collisions 
            f_col -> Friendly collisions
            surface -> Surface which the enemy is draw on 

            return -> Token of data for firing weapon

        """
        # Add the friendy collisions to the same list as environment collisions
        env_cols.extend(f_cols)
        
        # Position in map  
        x = self.enemy_pos[0] - self.enemy_rel_pos[0] - self.enemy_mov_pos[0]
        y = self.enemy_pos[1] - self.enemy_rel_pos[1] - self.enemy_mov_pos[1]

        cenx, ceny = x + 16, y + 16
        rcenx, rceny = int(cenx), int(ceny)

        # Enemy knows where player is. Hunt him/her
        if self.enemy_state:
            self.fetch_target_vector(waypoint_track=False, sx=cenx, sy=ceny, surface=surface) 
            tri_x, tri_y = x + self.enemy_rel_target_pos[0], y + self.enemy_rel_target_pos[1] 
            
            # Enemy lost sight of the player. Run a timer to go back to hunting waypoints
            if self.enemy_targetInterval_alarm.isReady(release=1):
                self.enemy_targetInterval.reset()
                self.enemy_state = 0 

        # Idling and guarding (Hunting waypoints)
        else:
            if self.enemy_targetInterval.isReady(release=1): self.fetch_target_vector(sx=cenx, sy=ceny, surface=surface)  

            tri_x, tri_y = ((x + self.enemy_rel_target_pos[0] - self.enemy_targetPos[0] + self.enemy_rel_pos[0]), 
                            (y + self.enemy_rel_target_pos[1] - self.enemy_targetPos[1] + self.enemy_rel_pos[1]))
            
            # Debug target waypoint
            #self.tk_draw_circle(surface, (0xff, 0xff, 0x0), (int(cenx - tri_x), 
            #                                                 int(ceny - tri_y)), 16, 1)   
        
        # Distance to player or waypoint
        dist_to_target = self.tk_hypot(tri_x, tri_y)

        delta = self.dt_getDelta()

        # Move orientation toward target based on rotationspeed 
        # (Increase the speed when engaging the player)
        if self.enemy_targetAngleDif > 0:
            self.enemy_targetAngleDif -= (self.tk_enemy_turn_speed * \
                                          (2 if self.enemy_state else 1)) * delta
            # Clamp it, so we wont miss the target
            self.enemy_targetAngleDif = max(0, self.enemy_targetAngleDif)  
        
        else:
            self.enemy_targetAngleDif += (self.tk_enemy_turn_speed * \
                                          (2 if self.enemy_state else 1)) * delta
            # Clamp it, so we wont miss the target
            self.enemy_targetAngleDif = min(0, self.enemy_targetAngleDif)   
        
        
        # Target angle - old_angle (For moving slowly toward the new target)
        angle = self.tk_atan2(tri_x, tri_y) - self.enemy_targetAngleDif  

        # Store for smooth transist between old and new angle 
        # (if new waypoint is acquired before correct orientation is reached)
        self.enemy_targetAngleAbs = angle   
        
        radToAngle = self.tk_degrees(angle) 
        self.enemy_targetAngleDeg = radToAngle 

        baseAx, baseAy = self.tk_sin(angle), self.tk_cos(angle) 

        # Movement direction and speed (Magnitude)
        mov_x = baseAx * self.enemy_speed * delta
        mov_y = baseAy * self.enemy_speed * delta

        # Update the enemy rect
        self.enemy_rect.center = cenx, ceny
        
        # Keep constant track of self to player angle
        angleToPlayer = self.tk_atan2(rcenx - self.tk_res_half[0], rceny - self.tk_res_half[1]) 

        # Check if player is within field-of-view
        self.check_fov((rcenx, rceny), angle, angleToPlayer, surface)

        # Attack target?
        enemy_attack = 0

        # See if the player is within weapon distance or safe distance away from waypoints
        hunt_distance = self.all_weapons[self.enemy_weapon]['w_range'] if \
                        self.enemy_state else self.tk_enemy_safe_distance  
        
        # Check if waypoint/player is in range
        if dist_to_target > hunt_distance:
            
            # Index 9 is the idling/guarding animation
            dir_frames = 9 if not self.enemy_state else 1

            # Fetch the next animation frame when ready
            if self.enemy_anim_delay.isReady():
                self.enemy_legs_frame_index = self.enemy_legs_frame_cycle.next()
                self.enemy_torso_frame_index = self.enemy_torso_frame_cycle.next() 

            self.enemy_mov_pos[0] += mov_x
            self.enemy_mov_pos[1] += mov_y

            self.rl_rect.center = self.enemy_rect.midright if mov_x < 0 else self.enemy_rect.midleft 
            self.tb_rect.center = self.enemy_rect.midbottom if mov_y < 0 else self.enemy_rect.midtop

            check_x = 1; check_y = 1
            # Check each axis once per for loop. This stops humping the walls
            for check in env_cols:
                if check_x:
                    if mov_x < 0:
                        if self.rl_rect.colliderect(check):
                            self.enemy_mov_pos[0] -= mov_x; check_x = 0       
                    
                    if mov_x > 0:
                        if self.rl_rect.colliderect(check):
                            self.enemy_mov_pos[0] -= mov_x; check_x = 0     
                
                if check_y:
                    if mov_y < 0:
                        if self.tb_rect.colliderect(check):
                            self.enemy_mov_pos[1] -= mov_y; check_y = 0     
                    
                    if mov_y > 0:
                        if self.tb_rect.colliderect(check):
                            self.enemy_mov_pos[1] -= mov_y; check_y = 0
        
        # Within weapon range
        else:
            dir_frames = 0

            # Player is within attack range and enemy is hunting player. Kill the player (Or try atleast)
            if self.enemy_state and self.enemy_weapon_firerate.isReady(release=1) and \
                                    self.check_fov_angle(angle, angleToPlayer, .2):
                
                self.enemy_fire_anim_len.rotate(1)      # Begin fire animation
                self.enemy_weapon_dual_cycle.rotate(1)  # Switch hand
                enemy_attack = 1                        # Signal to release weapon fire token


        action = self.enemy_fire_anim_len[0] 
        if self.enemy_fire_anim_timer.isReady() and self.enemy_fire_anim_len[0]: self.enemy_fire_anim_len.rotate(1)  


        # Store the original x, y for attacking to keep the center, so the bodyparts wont mess it 
        attx, atty = cenx, ceny

        for enum, f in enumerate(self.enemy_figure):
            if not enum:
                # Legs
                idle_stance = 0 if self.enemy_state else 1 
                image = self.legs_textures[f[0]][dir_frames][idle_stance if not dir_frames else self.enemy_legs_frame_index]
            
            else:
                # Torso
                idle_stance = 0 if self.enemy_state else 3
                
                if action:
                    image = self.torso_textures[f[0]][0][1 + self.enemy_weapon_dual_cycle[0]]
                
                else: 
                    image = self.torso_textures[f[0]][dir_frames][idle_stance if not dir_frames else self.enemy_torso_frame_index]
                
                # Torso is 64x64 so it needs to be fixed inplace 
                x -= 16; y -= 16
            
            # Move the texture forward or backward based of the offset origin
            if f[2]: x += baseAx * f[2]; y += baseAy * f[2] 
            
            # Render the bodypart
            surface.blit(self.tk_rotateImage(image, radToAngle, f[1]), (x, y))

        # Return token of data for the firing a weapon function 
        if enemy_attack: return (attx, atty, angle, radToAngle, self.enemy_weapon, self.enemy_weapon_dual_cycle[0])  


    @classmethod
    def build_all_enemies(cls, editor_only=False):
        """
            Read/Build all the enemies from config
            Called once during startup

            editor_only -> Load minimalistic data about the enemies for the editor

            return -> None or list of enemies if 'editor_only'
            
        """
        # Source path for enemy configs
        src_path_cfg = cls.tk_path.join('configs', 'enemies')
        

        # Line containing string data
        non_literal_eval = ('tex_legs',   'tex_torso', 'e_weapon', 'snd_death', 
                            'tex_bsplat', 'tex_death', 'gore_profile', 'snd_pain',
                            'snd_hit')

        # Lines which contain multiple data separated by comma
        multi_strings = ('tex_bsplat', 'tex_death', 'gore_profile', 'snd_pain', 'snd_death', 'snd_hit') 

        for cfg in cls.tk_iglob(cls.tk_path.join(src_path_cfg, '*.cfg')):
            e_data = {}
    
            name = cls.tk_path.split(cfg)[-1].split('.')[0]
            e_data['name'] = name

            # Names needed only for the editor
            if editor_only: 
                cls.all_enemies[name] = None
                continue

            for line in cls.tk_readFile(cfg, 'r'):
                if line[0] in non_literal_eval:
                    # Handle lines with multiple data values
                    if line[0] in multi_strings:
                        e_data[line[0]] = [(int(mv) if line[0].startswith('snd') else mv) \
                                            for mv in line[1].split(',') if mv]    
                    else:
                        # These are single strings
                        e_data[line[0]] = line[1]

                else:
                    # Rest are integers/floats which can go through literal_eval
                    e_data[line[0]] = cls.tk_literal_eval(line[1])       
         
            cls.all_enemies[name] = cls(**e_data)

        if editor_only: return cls.all_enemies.keys() 

    
    @classmethod
    def get_enemy(cls, _id):
        """
            Return specific enemy from the factory by id
            and active it

            _id -> id of the enemy

            return -> initiated instance
            
        """
        enemy = cls.tk_deepcopy(cls.all_enemies[_id])
        enemy.load_enemy_animation()
        return enemy

    
    @classmethod
    def update_relative_pos(cls, x, y):
        """
            Update the relative(from player) positioning for enemies

            return -> None

        """
        cls.enemy_rel_pos[0] += x; cls.enemy_rel_pos[1] += y

    
    @classmethod
    def clear_ids(cls):
        """
            Clear all the id's to new patch of fresh ids that
            can be granted for the enemies

            return -> None

        """
        cls.enemy_id_cnt.reset()

    
    @classmethod
    def get_world_collisions(cls, _map):
        """
            Pass a copy of the world collisions for the enemies field of view use and pathfinding

            _map -> 2d array of the world layer which holds the collisions variable

            return -> None
        """
        world = []

        cls.enemy_world_mapsize = len(_map[0]), len(_map)

        for y in xrange(cls.enemy_world_mapsize[1]):
            row = []
            for x in xrange(cls.enemy_world_mapsize[0]):
                row.append(cls.tk_rect(32 * x, 32 * y, 32, 32) if _map[y][x].collision else 0)
            world.append(tuple(row))

        cls.enemy_world_collisions[:] = world

    
    @classmethod
    def initialize_pathfinder(cls):
        """
            Setup the multiprocessing process for the pathfinder

            return -> None
        """
        # 
        PathFinder.tk_freezeSupport()

        # communicate with 2 Queues (input and output)
        cls.__path_queue_input = PathFinder.tk_queue()      # Feed data for the PathFinder
        cls.__path_queue_output = PathFinder.tk_queue()     # Fetch data from the PathFinder
        
        # Setup the Process and start it
        cls.__path_Process = PathFinder.PathFinder(cls.__path_queue_input, 
                                                   cls.__path_queue_output)
        cls.__path_Process.daemon = True
        cls.__path_Process.start()