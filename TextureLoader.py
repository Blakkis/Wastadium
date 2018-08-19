from ConfigsModule import GlobalGameData
#from MessSolver import MessSolver

# Note!
#   Change this module name to better describe it since it does more than texture loading


__all__ = ('TextureLoader', 'EffectsLoader', 'FootSteps', 'uiElements')


class TextureLoader(GlobalGameData):
    """
        Load/Parse all the texture related configs and store them inside class
        Dictionaries
        
    """
    #__slots__ = ()
    
    # All Ground/Low objects textures 
    low_textures = {}
   
    # All Wall/High objects textures
    mid_textures = {}

    # Object which are made of multiple textures
    obj_textures = {}
    
    # All leg textures available for
    legs_textures = {}
    
    # All torso textures avaiable for
    torso_textures = {}
    
    
    @classmethod
    def load_textures(cls, world_textures_only=False):
        """
            Load all textures and assign id number for them to be stored on the
            class dictionaries
            
            return -> None
            
        """

        # Source path for world configs
        src_world_path_cfg = cls.tk_path.join('configs', 'world')

        # World textures path
        world_path_tex = cls.tk_path.join('textures', 'worldtextures')


        # Store the spritesheet, so there's no need to load the spritesheet
        # again to subsurface and disgard it.
        cached_spritesheets = {}

        # NOTE: Allow walls and objects be loaded from spritesheets too?

        linedata = ('tex_main', 'tex_effect_id', 'tex_walk_sound_id', 'tex_collision', 'tex_hit_sound_id')

        for level, loc in enumerate(('floors', 'walls', 'objects'), start=1):
            for cfg in cls.tk_iglob(cls.tk_path.join(cls.tk_path.join(src_world_path_cfg, loc, '*.cfg'))):
                name = cls.tk_path.split(cfg)[-1].split('.')[0]
                tex_data = {}
                for line in cls.tk_readFile(cfg, 'r'):
                    # Floors
                    if level == 1:
                        v = tuple(line[1].split(','))
                        if line[0] == linedata[0]:
                            tex_name, x, y = v[0], int(v[1]), int(v[2])
                            
                            # Check if the sheet was used already
                            if tex_name in cached_spritesheets:
                                subtex = cached_spritesheets[tex_name].subsurface(32 * x, 32 * y, 32, 32)
                            
                            else:
                                sheet = cls.tk_image.load(cls.tk_path.join(world_path_tex, loc, tex_name)).convert() 
                                cached_spritesheets[tex_name] = sheet
                                subtex = sheet.subsurface(32 * x, 32 * y, 32, 32)

                            tex_data[line[0]] = subtex

                        elif line[0] == linedata[1]: tex_data[line[0]] = tuple(v) if v[0] else None                                # Hit Effects
                        elif line[0] == linedata[2]: tex_data[line[0]] = tuple([int(snd) for snd in v if snd]) if v[0] else None   # Walk sound
                        elif line[0] == linedata[4]: tex_data[line[0]] = tuple([int(snd) for snd in v if snd]) if v[0] else None   # Hit sound      

                    
                    # Walls
                    elif level == 2:
                        v = tuple(line[1].split(','))
                        if line[0] == linedata[0]:
                            sheet = cls.tk_image.load(cls.tk_path.join(world_path_tex, loc, v[0])).convert_alpha() 
                            tex_data[0] = sheet

                        elif line[0] == linedata[1]: tex_data[line[0]] = tuple(v) if v[0] else None                                 # Hit Effects
                        elif line[0] == linedata[3]: tex_data[line[0]] = cls.tk_literal_eval(v[0])                                  # Collision
                        elif line[0] == linedata[4]: tex_data[line[0]] = tuple([int(snd) for snd in v if snd]) if v[0] else None    # Hit sound  

                        else:
                            # Rest are subtextures (Which should be from 1 to 6)
                            tex_data[int(line[0])] = tex_data[0].subsurface(32 * int(v[0]), 32 * int(v[1]), 32, 32)    
                        

                    # Objects
                    elif level == 3:
                        v = tuple(line[1].split(','))
                        if line[0] == linedata[0]:
                            sheet = cls.tk_image.load(cls.tk_path.join(world_path_tex, loc, v[0])).convert_alpha()
                            tex_data[line[0]] = sheet

                        elif line[0] == linedata[1]: tex_data[line[0]] = tuple(v) if v[0] else None                         # Hit Effects


                if   level == 1: cls.low_textures[name] = tex_data
                elif level == 2: cls.mid_textures[name] = tex_data
                elif level == 3: cls.obj_textures[name] = tex_data    

        # Editor does not need bodyparts
        if not world_textures_only: cls.load_bodyparts()



    @classmethod
    def load_bodyparts(cls):
        """
            Load all legs/body textures for character building

            return -> None

        """
        # Source path for anim configs
        src_anim_path_cfg = cls.tk_path.join('configs', 'anims')

        # Legs/Torso animations path
        anim_path_tex = cls.tk_path.join('textures', 'anims')


        for enum, layer in enumerate(('legs', 'torsos')):
            # Legs are 32x32 and torso textures are 64x64
            mult = 64 if enum else 32
            for cfg in cls.tk_iglob(cls.tk_path.join(cls.tk_path.join(src_anim_path_cfg, layer), '*.cfg')):
                name = cls.tk_path.split(cfg)[-1].split('.')[0]
                
                if not enum:
                    cls.legs_textures[name] = {}
                else:
                    cls.torso_textures[name] = {}
                
                sheet = None

                for line in cls.tk_readFile(cfg, 'r'):
                    # Texture name should be the first one in config.
                    if line[0] == 'texture':
                        sheet = cls.tk_image.load(cls.tk_path.join(anim_path_tex, layer, line[1])).convert_alpha()
                        continue

                    if sheet is not None:
                        frames = []
                        # Line 0 contains data about the texture set and idle/firing animations
                        if line[0] == '0':
                            data = cls.tk_literal_eval(line[1])
                            if mult & 32:
                                frames.extend(sheet.subsurface(mult * f[0], mult * f[1], mult, mult) for f in data[:-1])
                                frames.append(data[-1])
                            
                            else:
                                # Torsos contain the lasersight base point
                                frames.extend(sheet.subsurface(mult * f[0], mult * f[1], mult, mult) for f in data[:-2])
                                frames.append(data[-2])
                                # Pre-calculate the polarToCartesian (Head track)
                                ptc = data[-1]
                                frames.append((ptc[0], ptc[1], cls.tk_atan2(ptc[0], ptc[1]), cls.tk_hypot(ptc[0], ptc[1]))) 

        
                        else:
                            # From 1 to ... are frames (All diagonal animations)
                            frames.extend([sheet.subsurface(mult*f[0], mult*f[1], mult, mult) for f in cls.tk_literal_eval(line[1])])
                        
                        # Which dictionary the frame is part of
                        if not enum:
                            cls.legs_textures[name][int(line[0])] = frames
                        else:
                            cls.torso_textures[name][int(line[0])] = frames  
        


class EffectsLoader(GlobalGameData):
    """
        Handles all effects of the game, spawning, rendering

    """

    __slots__ = ('effect_gen',    'effect_id',     'effect_name',
                 'effect_pos',    'effect_rel',    'effect_last_frame', 
                 'effect_size_h', 'effect_offset', 'effect_rot',
                 'effect_angle',  'effect_index',  'effect_timer')
        
    # Textures are stored on the class and instances can request frames by index
    all_effects = {}
    
    # All map effects that are currently being display on the map
    map_effects = {}
    
    # Relative position for effects(Updated when player moves)
    effect_rel_pos = 0, 0

    effect_data = {'id': 0,             # Provide unique id to each effect
                   'offset': (0, 0)}    # Keep effects fixed in-place
    
    def __init__(self, generator, name, _id, pos, ofs_pos, rot, angle):
        self.effect_gen = generator
        self.effect_name = name
        self.effect_id = _id
        
        # Position
        self.effect_pos = pos
        self.effect_rel = ofs_pos
        
        # Which side of the effect to get
        self.effect_rot = rot
        
        # Angle in which the effect is point to
        self.effect_angle = angle
        
        # Get and store halfsize of the texture for positioning it properly
        w, h = self.all_effects[name][0][4].get_size()
        self.effect_size_h = w >> 1, h >> 1
        
        # Offset to center the effect around new origin  
        self.effect_offset = self.all_effects[name][0][1] 
        
        # Animation frame index
        self.effect_index = 0
        
        # Playbackrate timer
        self.effect_timer = self.tk_trigger_const(self.all_effects[name][rot][2])

        # The last casing pos and img needs to be stored before destroyed
        self.effect_last_frame = None

 
    def render_effect_pos(self):
        """
            Get all the data for rendering the effect 

            return -> Token of all effect related data to render it properly

        """
        # Check if the timer can give out the next frame
        if self.effect_timer.isReady():
            self.effect_index = self.effect_gen.next() 
        
        return (self.effect_index, self.effect_size_h, self.effect_pos, 
                self.effect_rel, self.effect_name, self.effect_rot, self.effect_angle)    

    
    @classmethod
    def render_effects(cls, surface):
        """
            Render all effects that needs displaying
            effect are removed once they hit the StopIteration Error

            return -> Yield of all effects
            
        """
        for key in cls.map_effects.keys():
            try:
                index, center, pos, rel, name, rot, angle = cls.map_effects[key].render_effect_pos() 
                
                # Relative fix: When firing and moving decals needs to be fixed in-place
                rel = rel[0] - cls.effect_data['offset'][0], rel[1] - cls.effect_data['offset'][1]
                
                # The first 3 elements in the array are data related to the effect, rest are frames
                # So start counting from 3
                img = cls.all_effects[name][rot][index + 4]
                
                # The effect has an angle, so it needs to be rotated
                if angle: img = cls.tk_rotateImage(cls.all_effects[name][0][index + 4], angle, img.get_rect(), fast_rot=1)       

                x, y = pos[0] - center[0] - rel[0], pos[1] - center[1] - rel[1]  

                # Does the effect contain end_effect? If it does, it needs to blit the end_decal to the ground layer
                if cls.all_effects[name][rot][0] is not None:
                    cls.map_effects[key].effect_last_frame = cls.all_effects[name][rot][0], (x, y), angle
                #else:
                #    cls.map_effects[key].effect_last_frame = None   

                # Blit it
                surface.blit(img, (x, y))
            
            except StopIteration:
                # Check if the effect has end_effect which is a decal that is left behind after the effect is done
                if cls.map_effects[key].effect_last_frame is not None:
                    img, pos, angle = cls.map_effects[key].effect_last_frame
                    
                    # Rotate the end_effect if it doesn't have rot
                    if angle: img = cls.tk_rotateImage(img, angle, img.get_rect()) 
                    
                    # Paint it to ground
                    cls.solveMess(img, pos, sm_rel_pos=(cls.cell_x, cls.cell_y))
               
                # The effect has been done, delete it
                del cls.map_effects[key]


    @classmethod
    def spawn_effect(cls, effect, pos, rot=0, angle=0, frame_skip=1, loop=0):
        """
            Spawn an effect

            effect -> Name of the effect to be spawned
            pos -> Position of the effect on the world(From topleft of the screen)
            rot -> Rotation of the effect 0-3 to face any side
            angle -> Angle of the effect (Overwrites rot)
                     Effects which are spawned in angle use low quality version of the rotate

            frame_skip -> Number of skips on the animation
            loop -> loop the effect forever?
            
            return -> None

        """
        if loop:
            # Create an infinite effect(These are mostly called by the map to decorate the battlefield)
            cls.map_effects[cls.effect_data['id']] = EffectsLoader(cls.tk_cycle(xrange(0, len(cls.all_effects[effect][rot]) - 4, frame_skip)),
                                                 effect, cls.effect_data['id'], pos, cls.effect_data['offset'][:], 
                                                 rot, angle) 
        else:
            # These are finite effects called by the entities
            cls.map_effects[cls.effect_data['id']] = EffectsLoader(iter(xrange(0, len(cls.all_effects[effect][rot]) - 4, frame_skip)),
                                                 effect, cls.effect_data['id'], pos, cls.effect_data['offset'][:], 
                                                 rot, angle)
        # Provide each effect unique id 
        cls.effect_data['id'] += 1

    

    @classmethod
    def load_effects(cls):
        """
            Load all the effects

            return -> None
            
        """
        # Source path for effect cfg
        src_path_cfg = cls.tk_path.join('configs', 'effects')

        # Effect texture path
        effect_path_tex = cls.tk_path.join('textures', 'effects')

        for cfg in cls.tk_iglob(cls.tk_path.join(src_path_cfg, '*.cfg')):
            name = cls.tk_path.split(cfg)[-1].split('.')[0]
            
            # The 4 first data stored in the effect array is: end_decal, offset, playbackrate, leave stain
            cls.all_effects[name] = {0: [None, (0, 0), 0, 0]}
            
            sheet = None        # Effect spritesheet
            
            frame_size = None   # Size of the effect frames
            
            all_side = 0        # Should the effect be precalculated(rotated) to each side? (Used for wallhits)

            # We are looking for texture and frame_size first
            # end_decal is optional, the rest are frames (or SHOULD be)

            for line in cls.tk_readFile(cfg, 'r'):
                if line[0] == 'texture':
                    sheet = cls.tk_image.load(cls.tk_path.join(effect_path_tex, line[1])).convert_alpha()
                    continue
                # frame_size should be after texture
                if sheet is not None:
                    if line[0] == 'frame_size':
                        frame_size = cls.tk_literal_eval(line[1])
                        continue
                    # All important steps has been done
                    # next step is to load the textures we need
                    if frame_size is not None:
                        # Found the optional end_decal
                        # which is the decal that gets blitted to the map
                        # after the effect is done
                        if line[0] == 'end_decal':
                            x, y = cls.tk_literal_eval(line[1])
                            cls.all_effects[name][0][0] = sheet.subsurface(frame_size[0] * x,
                                                                       frame_size[1] * y,
                                                                       frame_size[0],
                                                                       frame_size[1])
                        elif line[0] == 'all_side':
                            all_side = cls.tk_literal_eval(line[1])

                        elif line[0] == 'offset':
                            # Offset is the origin of the effect
                            cls.all_effects[name][0][1] = cls.tk_literal_eval(line[1])

                        elif line[0] == 'playbackrate':
                            cls.all_effects[name][0][2] = cls.tk_literal_eval(line[1])

                        elif line[0] == 'stain':
                            cls.all_effects[name][0][3] = cls.tk_literal_eval(line[1])
                        
                        elif line[0] == 'frame':
                            # Rest are frames
                            x, y = cls.tk_literal_eval(line[1])
                            cls.all_effects[name][0].append(sheet.subsurface(frame_size[0] * x,
                                                                             frame_size[1] * y,
                                                                             frame_size[0],
                                                                             frame_size[1]))
            # If the effect has all_side 'True', rotate the effect to face 4 sides
            # Effects that has this variable are mostly effects spawned when firing a wall or object 
            # and the effect needs to be spawned to face the firing direction
            if all_side:
                # Build the rot rect for the frames to keep them centered
                rot_rect = cls.tk_rect(0, 0, frame_size[0], frame_size[1])

                # The first loaded frames from which the rest are rotated from
                original_frames = cls.all_effects[name][0]

                for key, rot in enumerate((90, 0, -90, 180)):
                    cls.all_effects[name][key] = []
                    cls.all_effects[name][key].extend(original_frames[:4])
                    if cls.all_effects[name][key][0] is not None:
                        # End_effect needs to be rotated aswell
                        cls.all_effects[name][key][0] = cls.tk_rotateImage(cls.all_effects[name][key][0], rot, rot_rect)      
                    for frame in original_frames[4:]:
                        rot_image = cls.tk_rotateImage(frame, rot, rot_rect)
                        cls.all_effects[name][key].append(rot_image)


    @classmethod
    def clear_effects(cls):
        """
            Clear all effects for new map

            return -> None
            
        """
        cls.effect_data['id'] = 0; cls.map_effects = {}; cls.effect_data['offset'] = 0, 0



class FootSteps(GlobalGameData):
    """
        Load and setup footsteps 
    """

    # All footsteps by id (Keep 0 as None)
    all_footsteps = {0: None}

    
    def __init__(self):
        pass


    @classmethod
    def setup_footsteps(cls):
        """ 
            Build and store all footsteps that player and enemies can spawn

            return -> None

        """
        # Source path for footstep configs
        src_path_cfg = cls.tk_path.join('configs', 'misc')

        # Footstep texture path
        foot_path_tex = cls.tk_path.join('textures', 'footsteps') 


        for line in cls.tk_readFile(cls.tk_path.join(src_path_cfg, 'footsteps.cfg'), 'r'):
            # All the footstep are single left footstep
            _id = cls.tk_literal_eval(line[0])
            foot = cls.tk_image.load(cls.tk_path.join(foot_path_tex, line[1])).convert_alpha()

            # Note: The decals may have different range of alphas if created separately from the Blender version of the footstep

            # Create a footsteps which fade out overtime
            # (surfarray used here to alter the alpha of the images)
            frames = [None] * 8     # First 8 slots are reserved for data about the footprint (Not all are in-use)

            frames[0] = foot.get_rect()     # Rect for rotation
            frames[1] = frames[0].center    # Half the size of the foot texture (Center)       
            frames[2] = cls.tk_pi / 2       # Additional angle to blit the footstep sideways to the character
            
            # Create the fade out footsteps
            for opaque in xrange(1, 17):
                # Create a copy of the original foot decal
                temp = foot.copy()
                
                # Creates a reference to the temp, so any changes to this will alter the temp image
                alpha_array = cls.tk_surfarray.pixels_alpha(temp) 
                alpha_array /= opaque   # Divide each alpha in the array by the opaque 
                
                # Create a unique copy of the altered image
                final = temp.copy() 
                
                # Side angle
                sAngle = cls.tk_pi / 2

                # Total of 32 images are created, 16 left and 16 flipped to right 
                frames.extend(((final, sAngle), (cls.tk_flip(final, 1, 0), -sAngle)))
            
            # Store and create a copy of the same footstep flipped
            cls.all_footsteps[_id] = frames



class uiElements(GlobalGameData):
    
    # All available cursors
    ElementCursors = {}
    
    # All available fonts (Note: Contains font paths! not actual font objects)
    ElementFonts = {}

    # All available texture elements Eg. Weapon icons, Ammo icons and additional texture icons
    ElementTextures = {}

    # Icon for the game
    ElementIcon = None

    
    @classmethod
    def load_elements(cls):
        """
            Load and setup UiElements such as fonts, cursors, icons

            return -> None
            
        """
        # Source path for UIElements configs
        src_path_cfg = cls.tk_path.join('configs', 'ui')

        # Font texture path
        fnt_path_tex = cls.tk_path.join('textures', 'fonts')

        # UIElement texture path 
        ui_elem_path_tex = cls.tk_path.join('textures', 'uielements')

        # Load all cursor textures
        for line in cls.tk_readFile(cls.tk_path.join(src_path_cfg, 'cursors.cfg'), 'r'):
            data = line[1].split(',')
            cls.ElementCursors[int(line[0])] = (cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, 
                                                data[0])).convert_alpha(), int(data[1]), int(data[2]))

        # Load all fonts (path only)
        for line in cls.tk_readFile(cls.tk_path.join(src_path_cfg, 'fonts.cfg'), 'r'):
            cls.ElementFonts[int(line[0])] = cls.tk_path.join(fnt_path_tex, line[1])

        # Load all UIElement textures
        for line in cls.tk_readFile(cls.tk_path.join(src_path_cfg, 'elements.cfg'), 'r'):
            cls.ElementTextures[int(line[0])] = cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, 
                                                line[1])).convert_alpha() 

    
    @classmethod
    def set_basic_window_elements(cls, mouse_visibility=True):
        """
            Control the basic stuff of pygame display

            Mouse visibility, window caption and icon

            return -> None

        """ 
        cls.tk_display.set_caption(cls.tk_name)

        cls.tk_mouse_vis(mouse_visibility)

        try:
            cls.ElementIcon = cls.tk_image.load(cls.tk_path.join('textures', 'uielements', 'gameicon.png'))

            cls.ElementIcon.set_colorkey((0x0, 0x0, 0x0))   # Use colorkey transparency
            
            cls.tk_display.set_icon(cls.ElementIcon)
        except Exception:
            # Resort to default pygame icon 
            pass



if __name__ == '__main__':
    pass
                
                    
