from ConfigsModuleEditor import GlobalGameDataEditor 
from TextureLoader import uiElements


__all__ = ('TextureSelectOverlay')




class TextureSelectOverlay(GlobalGameDataEditor):
    """
        Handle and display the texture/object selection frames
        
    """
    # Note: Most of these are used as read-only on mainloop function

    # If the key "Select Texture/Object" has been pressed, display the frame
    tso_textureSelectMode = 0

    # Which Texture/objects are we talking about
    tso_setMode = -1

    # All available modes, number of modes (Texture/Object categories)
    tso_textureFrames = {}; tso_numModes = set(range(4))

    # When texture/object selection frame is open, world does not need to be rendered. Save a static image of it
    tso_staticWorldFrame = None

    # Scroll level for the texture selection window
    tso_scrollLevel = 0

    # Data about the selected texture on each category
    tso_dataTextures= {}

    # Texture preview
    tso_texReview = {}

    # Fonts
    tso_font = None

    # Background used during texture selection
    tso_background = None
    
    # Dimensions for x, y texture blitting limits
    tso_bg_dimensions = None

    # Texture paths
    tso_tex_modes = None
    
    
    def __init__(self, func=None):
        self.func = func

    
    @classmethod
    def tso_createTextureSets(cls):
        """
            Setup basics for the texture selection windows

            return -> None

        """
        cls.tso_tex_modes = [cls.low_textures, cls.obj_textures, cls.mid_textures, cls.dh_all_decals]

        # Create some data places for the texture/object sets
        for lsets in xrange(len(cls.tso_tex_modes)): 
            # Fill the default data
            cls.tso_dataTextures[lsets] = {key:value for key, value in (('size', (0, 0)),
                                                                        ('set',   None),
                                                                        ('name',  ''),
                                                                        ('rot',   0))}
            # Add unique data for the textures here
            if lsets == 2:
                # Applying walls in manual mode needs deque for switching the texture
                cls.tso_dataTextures[lsets]['windex'] = cls.ed_deque(xrange(1, 7))  


        # Create the texture/object selection background
        cls.tso_background = cls.ed_surface((cls.ed_resolution[0] - 128, 
                                             cls.ed_resolution[1] - 128), cls.ed_srcalpha)
        cls.tso_background.fill((0x80, 0x80, 0x80, 0xcc))   # Paint it
        cls.ed_draw_rect(cls.tso_background, (0xff, 0xff, 0xff, 0xaa), 
                         cls.tso_background.get_rect(), 1)  # Highlight the edges

        cls.tso_updateTexturePreview(first_init=True)

        # Store the x limit for filling the texture frame
        cls.tso_bg_dimensions = [cls.tso_background.get_width()  / 32 - 2,   
                                 cls.tso_background.get_height() / 32 - 3, 
                                 cls.tso_background.get_width()  / 64 - 1, 
                                 cls.tso_background.get_height() / 64 - 2]

        cls.tso_font = cls.ed_font(cls.ElementFonts[1], 12)

        # Object, Wallset, Decals share the same display function
        funcs = [cls.__lowTexture, (cls.__midObjectWallDecal, 0), 
                                   (cls.__midObjectWallDecal, 1), 
                                   (cls.__midObjectWallDecal, 2)]

        
        for enum, f, in enumerate(funcs):
            cls.tso_textureFrames[enum] = TextureSelectOverlay(f)

    
    
    @classmethod
    def tso_toolBarHandler(cls, surface, action, click=0):
        """
            Handle the toolbar associated with texture selection
            Display the texture selection window and handle choosing the texture/object from it

            surface -> Surface which receives the texture selection frame
            action -> index of the texture/object button for displaying the correct texture/object set 
            click -> Pass the 'mousebuttonup' event to this function

            return -> None

        """
        cls.tso_setMode = action

        if cls.tso_setMode in cls.tso_numModes:
            
            if cls.tso_textureSelectMode:
                # World does't need to be rendered while texture selection is open
                # blit a static frame to "trick" the user
                surface.blit(cls.tso_staticWorldFrame, (0, 0))

                # Texture selection frame
                surface.blit(cls.tso_background, (64, 64))
                
                # Assign correct texture selection frame for each categories
                if isinstance(cls.tso_textureFrames[cls.tso_setMode].func, tuple):
                    func, mode = cls.tso_textureFrames[cls.tso_setMode].func 
                    func(surface, mode, click)
                else:
                    cls.tso_textureFrames[cls.tso_setMode].func(surface, click)
            else:
                # Blit the review frame
                # Needed as anchor for the data tex about the texture
                prevw = cls.tso_texReview[cls.tso_setMode].get_width() + 4  
                surface.blit(cls.tso_texReview[cls.tso_setMode], (cls.ed_resolution[0] - prevw, 4))

                # Display data about the texture next to preview
                if cls.tso_dataTextures[cls.tso_setMode]['name']:
                    name = cls.tso_font.render(cls.tso_dataTextures[cls.tso_setMode] \
                    						   ['name'], 1, (0xff, 0xff, 0xff))
                    surface.blit(name, (cls.ed_resolution[0] - (prevw + name.get_width() + 4), 0))
                    
                    size = cls.tso_font.render('{}x{}'.format(*cls.tso_dataTextures[cls.tso_setMode] \
                    										  ['size']), 1, (0xff, 0xff, 0xff))
                    surface.blit(size, (cls.ed_resolution[0] - (prevw + size.get_width() + 4), 
                    			 name.get_height() - 4)) 

        else:
            # Reset texture stuff if user 
            cls.tso_setMode = -1; cls.tso_textureSelectMode = 0; cls.tso_scrollLevel = 0



    @classmethod
    def tso_toggleTextureSelection(cls, surface=None):
        """
            Toggle texture selection frame on/off

            surface -> Current window surface as background image during texture selection

            return -> None

        """
        if cls.tso_setMode in cls.tso_numModes: 
            cls.tso_textureSelectMode ^= 1 
            cls.tso_staticWorldFrame = surface.copy()
            cls.tso_scrollLevel = 0 


    @classmethod
    def tso_updateDataTexture(cls, action=0, set_id=-1, **kw):
        """
            Update the texture data

            action:
                    1: Rotate texture
                    2: Walls segment index

            set_id -> Which texture sets data to update

            kw -> Update set of values 

        """
        if action == 1:
            # Id 3 is decals (This is rather forced and undoubly becomes a problem on future updates)
            rot = 45 if set_id == 3 else 90 
            cls.tso_dataTextures[set_id]['rot'] = (cls.tso_dataTextures[set_id]['rot'] + rot) % 360 

        elif action == 2:
            cls.tso_dataTextures[set_id]['windex'].rotate(1 if kw['d'] == 'l' else -1)

        else:  
            cls.tso_dataTextures[set_id].update(kw)

    
    @classmethod
    def tso_updateScrollLevel(cls, level):
        """
            Update the scroll level on texture windows

            level -> 1 (down), -1 (up)

            return -> None

        """
        cls.tso_scrollLevel += level
        cls.tso_scrollLevel = max(0, cls.tso_scrollLevel) # Clamp it from going below 0
        

    
    @classmethod
    def tso_updateTexturePreview(cls, set_id=-1, surface=None, first_init=False):
        """
            Update preview texture

            surface -> surface applied to the texture preview surface

            return -> None

        """
        if first_init:
            for _id in xrange(len(cls.tso_numModes)):
                surf = cls.ed_surface((64, 64), cls.ed_srcalpha)
                surf.fill((0x80, 0x80, 0x80, 0xcc))
                cls.ed_draw_rect(surf, (0xff, 0xff, 0xff, 0xaa), surf.get_rect(), 1)
                cls.tso_texReview[_id] = surf

        else:
            cls.tso_texReview[set_id] = cls.ed_surface((64, 64), cls.ed_srcalpha)
            cls.tso_texReview[set_id].fill((0x80, 0x80, 0x80, 0xcc))
            
            if surface is not None: cls.tso_texReview[set_id].blit(surface, (32 - surface.get_width() / 2, 
                                                                             32 - surface.get_height() / 2))    

            cls.ed_draw_rect(cls.tso_texReview[set_id], (0xff, 0xff, 0xff, 0xaa), 
                             cls.tso_texReview[set_id].get_rect(), 1)    

    
    
    @classmethod
    def __lowTexture(cls, surface, click=0):
        """
            Render all ground textures (32x32)

            surface -> Surface which to draw on
            click -> Pass the 'mousebuttonup' event to this function

            return -> None

        """
        x = -1; y = 0; skip_y = 0

        # Limit scrolling in y direction to last row of textures
        clamp_y = (len(cls.low_textures) - 1) / cls.tso_bg_dimensions[0] - cls.tso_bg_dimensions[1] 
        cls.tso_scrollLevel = min(clamp_y, cls.tso_scrollLevel)  
        
        for name, texture in cls.low_textures.iteritems():
            x += 1
            if x == cls.tso_bg_dimensions[0]: x = 0; y += 1; skip_y += 1

            # Skip the first rows dictated by the scroll level 
            if cls.tso_scrollLevel > skip_y: y = -1; continue

            # Clamp y from going outside of the border and limit scrolling
            if y > cls.tso_bg_dimensions[1]: break

            pos = 96 + 32 * x, 96 + 32 * y 

            surface.blit(texture['tex_main'], pos)
            
            # Provide a test rect for the texture for rect/mouse collision checking
            test_rect = cls.ed_rect(pos[0], pos[1], 32, 32)

            if test_rect.collidepoint(cls.ed_mouse.get_pos()):
                highlight = 0xff, 0xff, 0xff
                if cls.ed_mouse.get_pressed()[0]:
                    cls.tso_updateTexturePreview(0, texture['tex_main'])

                    cls.tso_textureSelectMode = 0

                    cls.tso_updateDataTexture(set_id=0, size=texture['tex_main'].get_size(), 
                    						  set=0, name=name)
                    break       
            else:
                highlight = 0xaa, 0xaa, 0xaa  

            cls.ed_draw_rect(surface, highlight, test_rect, 1)


    
    @classmethod
    def __midObjectWallDecal(cls, surface, mode=0, click=0):
        """
            Render all Objects, wallsets, decals (64x64)

            surface -> Surface which to draw on
            mode -> Which texture set are we using (0:Objects, 1:Walls, 2:Decals)
            click -> Pass the 'mousebuttonup' event to this function

            return -> None

        """
        modes = [cls.obj_textures, cls.mid_textures, cls.dh_all_decals]

        x = -1; y = 0; skip_y = 0

        # Limit scrolling in y direction to last row of textures
        clamp_y = (len(cls.tso_tex_modes[mode + 1]) - 1) / cls.tso_bg_dimensions[2] - cls.tso_bg_dimensions[3] 
        cls.tso_scrollLevel = min(clamp_y, cls.tso_scrollLevel)    

        for name, texture, in cls.tso_tex_modes[mode + 1].iteritems():
            x += 1
            # Clamp x of textures going outside of the border 
            if x == cls.tso_bg_dimensions[2]: x = 0; y += 1; skip_y += 1
            
            # Skip the first rows dictated by the scroll level 
            if cls.tso_scrollLevel > skip_y: y = -1; continue

            # Clamp y from going outside of the border and limit scrolling
            if y > cls.tso_bg_dimensions[3]: break
             
            pos = 96 + 64 * x, 96 + 64 * y
            
            # Every texture is slightly differently in the storages and needs to be loaded differently
            tex = texture['tex_main'] if mode == 0 else texture[0] if mode == 1 else texture 
            
            stex = cls.ed_scaleImage(tex, (56, 56)) 
            surface.blit(stex, (pos[0] + 32 - stex.get_width() / 2, pos[1] + 32 - stex.get_height() / 2))

            # For checking if the mouse can click it
            test_rect = cls.ed_rect(pos[0], pos[1], 64, 64)

            if test_rect.collidepoint(cls.ed_mouse.get_pos()):
                highlight = 0xff, 0xff, 0xff
                if click:
                    cls.tso_updateTexturePreview(mode + 1, stex)
                    
                    cls.tso_textureSelectMode = 0   

                    cls.tso_updateDataTexture(set_id=mode + 1, size=tex.get_size(), 
                    						  set=mode + 1, name=name)
                    break   
            else:
                highlight = 0xaa, 0xaa, 0xaa  

            cls.ed_draw_rect(surface, highlight, test_rect, 1)


