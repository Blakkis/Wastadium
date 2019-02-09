from TextureLoader import uiElements
from ConfigsModule import GlobalGameData
from ConfigsModuleEditor import ed_BitToggle
from EventManager import EventManager
from SoundModule import SoundMusic
from Inventory import Inventory
from MenuUtils import * 
from _3d_models import Model3D
from Tokenizers import MenuEventDispatch
from Timer import DeltaTimer
from MapParser import EpisodeParser
from VictoryCondition import BookKeeping

from functools import partial


__all__ = ('MenuManager', )


class JaaBabeBackgrounds(GlobalGameData):

    __backgrounds = {} 
    
    @classmethod
    def load_backgrounds(cls, base_background):
        """
            TBD

            return -> None

        """
        cls.__backgrounds['default'] = base_background
        
        src_path_png = cls.tk_path.join('textures', 'background', 'jaababe')

        for image_path in cls.tk_iglob(cls.tk_path.join(src_path_png, '*.png')):
            name = cls.tk_path.split(image_path)[-1].split('.')[0]
            
            # Load and scale to resolution
            base_image = cls.tk_smoothscale(cls.tk_image.load(image_path).convert(), cls.tk_resolution)
            
            # We need fresh copy of the background for each image
            background_copy = base_background.copy()

            # Blit and store
            background_copy.blit(base_image, (0, 0), special_flags=cls.tk_blend_rgba_mult)
            cls.__backgrounds[name] = background_copy


    @classmethod
    def render_background(cls, background_id):
        try:
            return cls.__backgrounds[background_id]
        except KeyError: 
            return cls.__backgrounds['default']



class PagesHelp(uiElements, SoundMusic, DeltaTimer, JaaBabeBackgrounds):

    
    @classmethod
    def ph_initData(cls):
        """
            Setup common data used by all the pages

            return -> None

        """
        # Provide global scale for all UI elements (Except in-game)
        cls.menu_scale = cls.tk_resolution_scale    # Possible add some correction here for the menu items?

        # Provide a same background for all the menus (Default one)
        cls.menu_background = cls.__ph_createBackground(flags=1)

        # Note: What the fuck was i thinging here? - Replace this menu_timer bullshit with get_ticks()
        # Provide common timer for every menu class
        cls.menu_base_event = cls.tk_uEvent 
        cls.menu_timer = MenuEventDispatch(get_event=lambda t=None: cls.menu_base_event if t is None \
                                                     else cls.menu_timer.get_ticks.m_add(.05) if t == cls.menu_base_event else 0,  
                                           get_ticks=cls.tk_counter(0)) 
        # Start the common event timer
        cls.tk_time.set_timer(cls.menu_timer.get_event(), 10)

        # Provide common background effects for the menus
        cls.interactive_background = ActiveBackGround()
        cls.scanline_effect = ScanLineGenerator(8, 4)   # Currently Mainmenu uses this effect

        cls.load_backgrounds(cls.__ph_createBackground(flags=1, color=(0xff, 0x0, 0x0)))


    # This could be changed to config module function
    # With more advanced features as "multi color text rendering" 
    @classmethod
    def two_color_text(cls, font, _str, sep=':', color_t=(0xff, 0x0, 0x0), color_v=(0xff, 0x0, 0x80), invert_color=False):
        """
            Render 2 color text with 'sep' separating the colors

            font -> Font used to render the text
            _str -> String with 'sep' in somewhere to separate the 2 colors
            sep  -> color separator
            color_t -> prefix color
            color_v -> suffix color

            return -> Final surface with both pre and suffix blitted
        """
        text_surf = cls.tk_surface(font.size(_str), cls.tk_srcalpha)
        
        pre, suf = _str.split(sep, 1)
        if invert_color: color_t, color_v = color_v, color_t
        pre = cls.tk_renderText(font, pre + sep, True, color_t, shadow=True)
        suf = cls.tk_renderText(font, suf, True, color_v, shadow=True)

        text_surf.blit(pre, (0, 0))
        text_surf.blit(suf, (text_surf.get_width() - suf.get_width(), 0))

        return text_surf

    
    @classmethod
    def ph_common_soundeffect(cls, return_type=None, not_enough=False):
        """
            Provide common sound effects for menus and return carriage 

            return -> None
        """
        if not not_enough:
            # return from menu
            cls.playSoundEffect(188)
            return return_type
        else:
            # Not enough cash
            cls.playSoundEffect(189)

    
    @classmethod
    def ph_flash_effect(cls, surface, pos):
        """
            Wiggle surface around (Try it to see the effect)

            surface -> Which surface receives the effect

            return -> Affected surface, x, y

        """
        px, py = pos
        vx, vy = surface.get_size()

        # Wiggle the selected option around
        surface = cls.tk_rotozoom(surface, 8 * cls.tk_sin(cls.menu_timer.get_ticks()), 
                                  1.0 + (0.2 * abs(cls.tk_sin(cls.menu_timer.get_ticks()))))
        
        # Fix the surface in-place
        vx = surface.get_width()  - vx
        vy = surface.get_height() - vy
        px -= vx / 2; py -= vy / 2

        return surface, px, py


    @classmethod
    def __ph_createBackground(cls, flags=1, color=(0x40, 0x0, 0x0), shift_y=2, shift_x=2):
        """
            Create a common background for all the menus
            Change this function to create you're own or 
            add support for loading custom image as background

            flags -> 1: Stripe background
                  2: Faded background

            return -> Surface

        """
        if flags & 1: 
            background = cls.tk_surface(cls.tk_resolution)

            # Access the pixel arrays of the surface for effects
            background_array = cls.tk_surfarray.pixels3d(background)

            # Added every second horizontal line as dark red for fitting the theme of the game 
            background_array[::shift_x, ::shift_y] = color

        if flags & 2:
            background = cls.tk_surface(cls.tk_resolution, cls.tk_srcalpha)
            background.fill((0x40, 0x0, 0x0, 0x80))

        return background


class MenuEnd(PagesHelp, BookKeeping):
    def __init__(self):
        self.font_0 = self.tk_font(self.ElementFonts[0], int(48 * self.menu_scale))
        self.font_1 = self.tk_font(self.ElementFonts[1], int(32 * self.menu_scale))
        self.pre_text = {'time_h': self.tk_renderText(self.font_0, "Total Completion Time", 
                                                      True, (0xff, 0x0, 0x0), shadow=1)}

    def run(self, surface):
        time_b = self.tk_seconds_to_hms(self.getSetRecord('time', end=True), to_string=True)
        time_b = self.tk_renderText(self.font_1, time_b, True, (0xff, 0x0, 0x80), shadow=1) 
        
        while 1:
            #surface.fill(self.tk_bg_color)

            surface.blit(self.render_background('end'), (0, 0))

            time_h = self.pre_text['time_h']
            surface.blit(time_h, (self.tk_res_half[0] - time_h.get_width() / 2, 0))

            surface.blit(time_b, (self.tk_res_half[0] - time_b.get_width() / 2, time_h.get_height()))
            
            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        return None

            self.tk_display.flip()



class MenuIntro(PagesHelp, EventManager):
    """
        Display the Dev Intro (Which ALWAYS should be skippable!)

    """
    def __init__(self):
        self.intro_time = 4500    # Milliseconds
        self.intro_exit_flag = ed_BitToggle(1)
        # Quit the intro takes 2 escape presses
        # First step finishes the fadein animation
        # Second quits the full intro (Or timer kills the intro)
        self.intro_exit_proceed = 0     

        self.font_0 = self.tk_font(self.ElementFonts[0], int(128 * self.menu_scale))
 
        w, h = self.font_0.size(self.tk_dev_name)
        self.fsurf = self.tk_surface((w, h))
        self.fsurf.blit(self.font_0.render(self.tk_dev_name, 1, (0xff, 0x0, 0x0)), (0, 0))

        # Generate the logo gear (Because why not?)
        self.dsurf = self.__mi_generateGear()
        self.dsurf_pos = (self.tk_res_half[0] - ((self.dsurf.get_width()  / 2 + self.fsurf.get_width())  / 2),
                          self.tk_res_half[1] - ((self.dsurf.get_height() / 2 + self.fsurf.get_height()) / 2)) 

        self.fsurf_pos = (self.dsurf_pos[0] + self.dsurf.get_width()  / 2,
                          self.dsurf_pos[1] + self.dsurf.get_height() / 2 - self.fsurf.get_height())

        self.fader_surf = self.tk_surface(self.tk_resolution, self.tk_srcalpha)
        self.fader_surf.fill((0x0, 0x0, 0x0, 0xff)) 

        # Quitting the intro either via quit key or timer
        EventManager.__init__(self)
        self.Event_newEvent(self.intro_time, lambda: self.intro_exit_flag.bit_toggle(force_value=0))

    
    def run(self, surface):
        """
            Run the Intro

            surface -> Active screen surface

            return -> None

        """
        channel = self.playSoundEffect(400)
        
        while self.intro_exit_flag:
            surface.fill(self.tk_bg_color)
            
            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        if self.intro_exit_proceed:
                            # Quit the intro
                            self.intro_exit_flag.bit_toggle(force_value=0)
                        else:
                            # Stop the fadein animation
                            self.intro_exit_proceed = 1

                self.menu_timer.get_event(event.type)

                self.Event_handleEvents(event.type) 
            
            tick_t = self.menu_timer.get_ticks() 
            
            # Render gear
            surface.blit(self.tk_rotateImage(self.dsurf, tick_t * (64 - tick_t * 1.5), 
                                             self.dsurf.get_rect()), self.dsurf_pos)
            # Render name
            surface.blit(self.fsurf, self.fsurf_pos)

            # Render Fader
            surface.blit(self.fader_surf, (0, 0))
            # Since im not using any pre-rendered intro video
            # All these values are chosen based on the intro soundeffect
            fade_alpha = int(self.tk_clamp(0xff - tick_t * (32 - tick_t * 1.5), 0x0, 0xff)) \
                         if not self.intro_exit_proceed else 0x54
     
            self.fader_surf.fill((0x0, 0x0, 0x0, fade_alpha))

            self.tk_display.flip()

        if channel.get_busy(): channel.stop()

    
    def __mi_generateGear(self):
        """
            Generate the gear (Why not?)

            return -> Surface with the gear image on it

        """
        # Obviously it would easier just to create the image and load that 
        # (But good training)

        #clamp = lambda v: max(-16 * self.menu_scale, min(16 * self.menu_scale, v))
        theta = 0
        teeth = 0
        scale = self.menu_scale

        gear_surf = self.tk_surface((int((128 * 2 + 48) * scale), 
                                     int((128 * 2 + 48) * scale))) 

        # Store the Outer ring and inner ring old x, y on the same list 
        old_x = [gear_surf.get_width()  / 2 + int(self.tk_cos(theta) * (128 * scale)), 
                 gear_surf.get_width()  / 2 + int(self.tk_cos(theta) * (32  * scale))]
        
        old_y = [gear_surf.get_height() / 2 + int(self.tk_sin(theta) * (128 * scale)), 
                 gear_surf.get_height() / 2 + int(self.tk_sin(theta) * (32  * scale))]

        # Generate the outer ring (Do few passes) (Original idea was animated gear draw)
        for r in xrange(360 * 8):
            theta += .005
            teeth += .05
            x = gear_surf.get_width()  / 2 + int(self.tk_cos(theta) * ((128 * scale) + 
                self.tk_clamp(self.tk_asin(self.tk_sin(teeth)) * (32 * scale), -16 * scale, 16 * scale)))  
            
            y = gear_surf.get_height() / 2 + int(self.tk_sin(theta) * ((128 * scale) + 
                self.tk_clamp(self.tk_asin(self.tk_sin(teeth)) * (32 * scale), -16 * scale, 16 * scale)))  

            if x != old_x[0] and y != old_y[0]:
                self.tk_draw_aaline(gear_surf, (0xff, 0x0, 0x0), (old_x[0], old_y[0]), (x, y))
                old_x[0] = x; old_y[0] = y

        # Generate the inner ring
        self.tk_draw_gfx_aacircle(gear_surf, gear_surf.get_width()  / 2,
                                             gear_surf.get_height() / 2, 
                                             int(32 * scale), 
                                             (0xff, 0x0, 0x0))

        return gear_surf



class MenuMain(PagesHelp, EventManager):
    # Note: There's room for 2 lines of text under different categories of items (Weapons, ammo, gadgets)
    
    __ref_functions = {} 

    def __init__(self):
        self.font_0 = self.tk_font(self.ElementFonts[0], int(96 * self.menu_scale))
        self.font_1 = self.tk_font(self.ElementFonts[0], int(48 * self.menu_scale))
        self.font_2 = self.tk_font(self.ElementFonts[1], int(16 * self.menu_scale))

        
        self.gfont = self.font_0.render(self.tk_name, 1, (0xff, 0x0, 0x0))
        self.gfont_pos = (self.tk_res_half[0] - self.gfont.get_width()  / 2,
                          self.tk_res_half[1] - self.gfont.get_height() / 2)


        self.gfont_bg = self.font_0.render(self.tk_name, 1, (0xaa, 0x0, 0x0)) 
        self.gfont_bg_pos = (self.tk_res_half[0] - self.gfont_bg.get_width()  / 2,
                             self.tk_res_half[1] - self.gfont_bg.get_height() / 2)  
        
        self.version_id = self.font_2.render('ver: ' + self.tk_version, 1, (0xff, 0x0, 0x0)) 

        #self.scanline = ScanLineGenerator(8, 4)

        self.last_select = -1  # Keep the last selected option highlighted even if mouse is not hovering on it
        
        # Note: Move the lambdas inside the RectSurface function call
        self.options = self.tk_ordereddict()
        self.options[0] = (RectSurface(self.font_1.render("New Game", 1, (0xff, 0x0, 0x0)), 
                           snd_hover_over=180, snd_click=181),  
                           lambda surface: self.__ref_functions['episode'].run(surface))
        
        self.options[1] = (RectSurface(self.font_1.render("Options", 1, (0xff, 0x0, 0x0)), 
                           snd_hover_over=180, snd_click=181),   
                           lambda surface: self.__ref_functions['options'].run(surface, enable_quit=False))
        
        self.options[2] = (RectSurface(self.font_1.render("Exit Game", 1, (0xff, 0x0, 0x0)), snd_hover_over=180), 
                           lambda *args: self.tk_quitgame())

        # Get the total height of all the options
        self.options_height = (sum([h[0].rs_getSize()[1] for h in self.options.itervalues()]) + self.gfont.get_height()) / 2
        
        # Update scanline y position
        EventManager.__init__(self)
        self.Event_newEvent(self.scanline_effect.slg_speed, self.scanline_effect.slg_update)
    
    
    def menu_set_references(self, **kw): 
        """
            Set reference functions for the buttons on the menu

            return -> None
        """
        self.__ref_functions.update(**kw)
    
    
    def run(self, surface):
        """
            Mainmenu

            surface -> Surface on which to display the contents

            return -> None

        """
        if self.__ref_functions['intro'] is not None: self.__ref_functions['intro'].run(surface)
        
        self.playMusic(0, -1)
        
        while 1:
            #surface.fill(self.tk_bg_color)
            surface.blit(self.render_background('JaaBabe_Main'), (0, 0))

            click = 0; tick = 0

            for event in self.tk_eventDispatch():
                self.Event_handleEvents(event.type)

                if self.menu_timer.get_event(event.type): tick = 1

                if event.type == self.tk_event_mouseup: 
                    if event.button == 1:
                        click = 1

            self.interactive_background.ab_render(surface, tick)

            # Give some random wiggle for certain ui elements
            if tick: twitch = 4 if self.tk_randrange(0, 100) > 95 else 0
            else: twitch = 0 

            surface.blit(self.gfont_bg, (self.gfont_bg_pos[0] + twitch,
                                         self.gfont_bg_pos[1] - (self.options_height + twitch)))
 

            surface.blit(self.gfont, (self.gfont_pos[0] - twitch,
                                      self.gfont_pos[1] - (self.options_height - twitch)))
            
            mx, my = self.tk_mouse_pos()
            
            for key, surf in self.options.iteritems():
                surf = surf[0].rs_renderSurface()
                x = self.tk_res_half[0] - surf.get_width() / 2 
                y =  self.gfont_pos[1] + self.gfont.get_height()
                
                # Spacing between logo and options 
                y += 64 * self.menu_scale - self.options_height
                
                # Spacing between options text 
                y += (surf.get_height() + 16 * self.menu_scale) * key  
                
                self.options[key][0].rs_updateRect(x, y)

                if self.options[key][0].rs_hover_over((mx, my)):
                    if self.last_select != key:
                        self.last_select = key    
                        self.menu_timer.get_ticks.reset()

                    if click: 
                        self.options[key][0].rs_click()     # Just to make the sound when clicked
                        result = self.options[key][1](surface)
                        # Player died. Restart the menu music
                        if result == -1: self.playMusic(0, -1)       

                if key == self.last_select:
                    surf, x, y = self.ph_flash_effect(surf, (x, y))

                surface.blit(surf, (x, y))

            # -- Set everything above this function to be affected by the scanline --
            self.scanline_effect.slg_scanlineEffect(surface)

            surface.blit(self.version_id, (8, self.tk_resolution[1] - (self.version_id.get_height() + 4)))

            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))
                
            self.tk_display.flip()  



class MenuCampaign(PagesHelp, EpisodeParser):

    __ref_functions = {}
    
    def __init__(self):
        self.parseEpisodeFiles()
        
        self.font_0 = self.tk_font(self.ElementFonts[0], int(24 * self.menu_scale))
        self.font_1 = self.tk_font(self.ElementFonts[0], int(32 * self.menu_scale))

        self.episodes = {key: RectSurface(self.tk_renderText(self.font_0, key, True, (0xff, 0x0, 0x0), shadow=True),
                                          snd_hover_over=180, snd_click=181, 
                                          func=lambda episode, surface: self.__ref_functions['episode_roll'](episode, surface)) \
                         for key in self.all_valid_campaigns.iterkeys()}

        self.selection_bg = self.tk_draw_rounded_rect(int(320 * self.menu_scale), 
                                                      (self.tk_resolution[1] - 8) - int(64 * self.menu_scale), 
                                                      8, (0xff, 0x0, 0x0), 0x60, False) 
        
        self.selection_bg_pos = (self.tk_res_half[0] - self.selection_bg.get_width()  / 2,
                                (self.tk_res_half[1] - self.selection_bg.get_height() / 2) + 8 * self.menu_scale)

        self.pre_text = {'select_ep': self.tk_renderText(self.font_1, "Select Episode", True, 
                                                        (0xff, 0x0, 0x0), shadow=True)}
        
        # Max number of items inside the selection rect
        self.selection_bg_max_items = 8
        
        # Items showed, but can't be clicked and fades out 
        self.selection_bg_max_hide_items = 5
        
        # Scroll level 
        self.selection_bg_scroll = 0
        
        # Last selected value
        self.last_select = -1 


    def campaign_set_references(self, **kw): 
        """
            Set reference functions for the buttons on the menu

            return -> None
        """
        self.__ref_functions.update(**kw)
    
    
    def run(self, surface):
        while 1:
            #surface.fill(self.tk_bg_color)
            #surface.blit(self.menu_background, (0, 0))

            surface.blit(self.render_background('JaaBabe_Main'), (0, 0))

            tick = click = 0
            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        return self.ph_common_soundeffect()

                elif event.type == self.tk_event_mouseup:
                    if event.button == 1:
                        click = 1

                    elif event.button == 4:    # Wheel up
                        self.selection_bg_scroll -= 1

                    elif event.button == 5:  # Wheel down
                        self.selection_bg_scroll += 1

                    self.selection_bg_scroll = max(0, min(len(self.episodes) - self.selection_bg_max_items, 
                                                          self.selection_bg_scroll))

                if self.menu_timer.get_event(event.type): tick = 1

            self.interactive_background.ab_render(surface, tick)

            surface.blit(self.pre_text['select_ep'], (self.tk_res_half[0] - self.pre_text['select_ep'].get_width() / 2, 0))

            surface.blit(self.selection_bg, self.selection_bg_pos)

            mx, my = self.tk_mouse_pos() 
            for enum, episode in enumerate(sorted(self.episodes.keys())):
                if self.selection_bg_scroll > enum:
                    continue

                enum -= self.selection_bg_scroll 
                
                ep_surf = self.episodes[episode] 
                x = self.tk_res_half[0] - ep_surf.rs_getSize()[0] / 2
                y = (self.selection_bg_pos[1] + 16 * self.menu_scale) + (ep_surf.rs_getSize()[1] + 8 * self.menu_scale) * enum
                
                # *Highlight* the last selected value
                if enum == self.last_select:
                    x += self.tk_sin(self.menu_timer.get_ticks()) * 8

                surf = ep_surf.rs_renderSurface()

                if enum < self.selection_bg_max_items:
                    if ep_surf.rs_hover_over((mx, my)):
                        if self.last_select != enum:
                            self.last_select = enum    
                            self.menu_timer.get_ticks.reset()

                        if click: 
                            # This calls the episode_roller
                            # once player has played all the levels
                            # return to mainmenu
                            return ep_surf.rs_click(episode, surface)

                elif enum < self.selection_bg_max_items + self.selection_bg_max_hide_items:
                    alpha_level = enum - self.selection_bg_max_items 
                    surf = self.tk_set_surface_alpha(surf, max(0, 0x20 - 10 * alpha_level))  
                
                else:
                    break

                ep_surf.rs_updateRect(x, y)
                surface.blit(surf, (x, y))

            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))

            self.tk_display.flip() 



class MenuShop(PagesHelp, Inventory):
    
    # Since the class works as decorator, the data needed has not been
    # initialized yet, call the init once during first __call__
    __shop_initialized = False
    
    # Enums
    __E_WEAPON = 0
    __E_AMMO   = 1
    __E_GADGET = 2

    # Bulk buying/selling amount
    __BULK_AMOUNT = 16

    # Health and armor refill costs (Per point)
    __ARMOR_REFILL  = 4
    __HEALTH_REFILL = 1

    # Gadget price increase per level (Base * __GADGET_PRICE_INC * level)
    __GADGET_PRICE_INC = 0.3

    # Gadget level incementor
    __GADGET_LEVEL_INC = 16 


    def __init__(self, function=None):
        self.function = function


    def __get__(self, obj, type=None):
        return partial(self, obj)

    
    def __call__(self, *args, **kw):
        if not self.__shop_initialized:
            self.__shop_initialized = self.init_shop_data()    

        surface = self.function(*args, **kw)

        if isinstance(surface, tuple) and surface[1] == 1:
            return surface

        self.run(surface)
        return surface

   
    def init_shop_data(self):
        """
            Initialize shop

            return -> 'True' 

        """
        self.font_0 = self.tk_font(self.ElementFonts[1], int(16 * self.menu_scale))
        self.ms_font_height = self.font_0.get_height() 
        
        # Pre-rendered texts (Color/Text doesn't change)
        # text starting with 'help' is special
        self.ms_pre_text = {'w_id':       self.font_0.render('Id: ',         1, (0xff, 0x0, 0x0)), 
                            'w_price':    self.font_0.render('| Price: ',    1, (0xff, 0x0, 0x0)),
                            'w_damage':   self.font_0.render('| Damage: ',   1, (0xff, 0x0, 0x0)),
                            'w_range':    self.font_0.render('| Range: ',    1, (0xff, 0x0, 0x0)),
                            'w_firerate': self.font_0.render('| RPM: ',      1, (0xff, 0x0, 0x0)),
                            'dual_n':     self.font_0.render('Dual',         1, (0x80, 0x0, 0x0)),
                            'dual_y':     self.font_0.render('Dual',         1, (0xff, 0x0, 0x80)),
                            'owned_n':    self.font_0.render('Own',          1, (0x80, 0x0, 0x0)),
                            'owned_y':    self.font_0.render('Own',          1, (0xff, 0x0, 0x80)),
                            'help_3':     self.two_color_text(self.font_0, "LMB/RMB: Buy/Sell", invert_color=True),
                            'help_2':     self.two_color_text(self.font_0, 
                                          "+ LSHIFT: Buy/Sell In Bulk of '{}'".format(self.__BULK_AMOUNT), invert_color=True),
                            'help_1':     self.two_color_text(self.font_0, "+ LCTRL: Sell All", invert_color=True)}  

        # Provide much nicer background for the icons (32x32, 64x64)
        # Since my antialising method is slow, its betters to build one and pass that to everyone
        _64 = int(64 * self.menu_scale) 
        csurf_64 = self.tk_draw_rounded_rect(_64, _64, 8, (0xff, 0x0, 0x0), 0x60, True)

        # Does the player own the item? (Visual backgroun for it)
        self.ms_have_item = self.tk_gradient_rect(_64, _64, (0xff, 0x0, 0x80), 0xaa, 
                                                  invert=1, both_sides=1, length=12, cut_corners=True) 
        
        _32 = int(32 * self.menu_scale) 
        csurf_32 = self.tk_draw_rounded_rect(_32, _32, 8, (0xff, 0x0, 0x0), 0x60, True) 

        self.ms_setupWeaponsAmmo(csurf_64)

        self.ms_setupSpecialGadgets(csurf_64)

        self.ms_setup_credits(csurf_32)
        
        self.ms_setup_healthArmor()

        return True
    

    # Note: Currency
    def ms_setup_credits(self, bg):
        """
            Credits ui

            bg -> Background for the credits icon

            return -> None

        """
        csurf_32 = bg
        csurf_32_d = bg.get_size()

        credits_icon = self.tk_scaleSurface(self.ElementTextures[3], self.menu_scale) 

        c_surf = csurf_32.copy()
        c_surf.blit(credits_icon, (csurf_32_d[0] / 2 - credits_icon.get_width() / 2, 
                                   csurf_32_d[1] / 2 - credits_icon.get_height() / 2))

        self.ms_creditsIcon = RectSurface(c_surf)
        self.ms_creditsIcon.rs_updateRect(self.tk_resolution[0] - csurf_32.get_width()  - 16, 
                                          self.tk_resolution[1] - csurf_32.get_height() - 16)


    def ms_setup_healthArmor(self):
        """
            Setup health/armor texture section

            return -> None

        """ 

        healthArmor_icon = self.tk_scaleSurface(self.ElementTextures[1], self.menu_scale)

        self.ms_armorHealthIcon = RectSurface(healthArmor_icon)
        self.ms_armorHealthIcon.rs_updateRect(8, self.tk_resolution[1] - (self.ms_armorHealthIcon.rs_getSize()[1] + 8))

        bar_bg = self.tk_surface((128 * self.menu_scale, 
                                 self.ms_armorHealthIcon.rs_getSize()[1] / 2 - (40 * self.menu_scale)), self.tk_srcalpha)
        bar_bg.fill((0xff, 0x0, 0x0, 0x80))
        
        self.ms_healthBar = RectSurface(bar_bg, snd_hover_over=181, snd_click=183, func=self.ms_validate_hparm_buy)
        self.ms_healthBar.rs_updateRect(self.ms_armorHealthIcon.rs_getPos('right'),
                                        self.ms_armorHealthIcon.rs_getPos('top') + \
                                        self.ms_armorHealthIcon.rs_getSize()[1] / 4 - bar_bg.get_height() / 2)

        self.ms_armorBar = RectSurface(bar_bg, snd_hover_over=181, snd_click=182, func=self.ms_validate_hparm_buy) 
        self.ms_armorBar.rs_updateRect(self.ms_armorHealthIcon.rs_getPos('right'),
                                       self.ms_armorHealthIcon.rs_getPos('centery') + \
                                       self.ms_armorHealthIcon.rs_getSize()[1] / 4 - bar_bg.get_height() / 2)
       
    
    def run(self, surface):
        """
            Shop

            surface -> Surface on which to display the contents

            return -> None

        """
        quit_shop = False

        surface, level_count = surface

        # Shop can be skipped since the episode has been played
        if level_count[0] == level_count[1]:
            return surface

        while 1:
            #surface.fill(self.tk_bg_color)
            #surface.blit(self.menu_background, (0, 0))

            surface.blit(self.render_background('JaaBabe_Shop'), (0, 0))

            buy_sell = 0

            for event in self.tk_eventDispatch():
                self.menu_timer.get_event(event.type)

                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        quit_shop = True

                if event.type == self.tk_event_mouseup:
                    if event.button == 1:   # LMB
                        buy_sell = 1

                    elif event.button == 3: # RMB
                        buy_sell = 2

            mods = self.tk_get_mods()
            mod_event = 0
            
            # Buy/Sell in bulk
            if mods & self.tk_user_special['shift_l']: 
                mod_event = 1

            # Sell all
            elif mods & self.tk_user_special['ctrl_l']:
                mod_event = 2

            buy_only = buy_sell if buy_sell == 1 else 0
            mx, my = self.tk_mouse_pos()

            weapon = self.ms_render_weapons(surface, hover=(mx, my), click=buy_sell)
            
            self.ms_render_ammo(surface, hover=(mx, my), hl_wpn=weapon, click=buy_sell, click_mod=mod_event)

            self.ms_render_gadgets(surface, hover=(mx, my), click=buy_only)

            self.ms_renderHealthArmorCreditsMenu(surface, hover=(mx, my), click=buy_only)

            self.ms_renderExtra(surface)
            
            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))

            self.tk_display.flip() 

            # This is to keep the last draw surface drawn for outro effect(Visually more pleasing)
            if quit_shop: return surface


    def ms_validate_ammo_buy(self, mod, *args, **kw):
        """
            Validate buy ammo

            mod -> Keyboard mods:
                   0: Normal buy/sell
                   1: Bulk buy/sell (lshift)
                   2: Sell all      (lctrl)

            return -> None

        """
        ammo_key = kw['ammo_id']
        ammo_price = self.all_ammo_data[ammo_key][1]

        # Normal buy/sell (Single)
        if mod == 0:
            # Buy
            if kw['key'] == 1 and ammo_price <= self.i_playerStats['credits']: 
                self.i_playerAmmo[ammo_key] += 1
                self.i_playerStats['credits'] -= ammo_price
            
            # Sell (Gives half the price of the ammo)
            elif kw['key'] == 2 and self.i_playerAmmo[ammo_key] > 0:
                self.i_playerAmmo[ammo_key] -= 1
                self.i_playerStats['credits'] += int(ammo_price / 2)
        
        # Bulk buy/sell
        elif mod == 1:
            # Buy
            if kw['key'] == 1:
                # Use the remainder for negotiating few extra ammo when low on cash?
                q, r = divmod(self.i_playerStats['credits'], ammo_price)
                amount = self.__BULK_AMOUNT if q >= self.__BULK_AMOUNT else q
                
                self.i_playerAmmo[ammo_key] += amount
                self.i_playerStats['credits'] -= ammo_price * amount        

            # Sell (Maybe give more if selling in bulk?)
            elif kw['key'] == 2:
                q, r = divmod(self.i_playerAmmo[ammo_key], self.__BULK_AMOUNT)
                amount = self.__BULK_AMOUNT if q > 0 else r 

                self.i_playerAmmo[ammo_key] -= amount
                self.i_playerStats['credits'] += (ammo_price / 2) * amount
        
        # Sell all
        elif mod == 2 and kw['key'] == 2:
            self.i_playerStats['credits'] += (ammo_price / 2) * self.i_playerAmmo[ammo_key]
            self.i_playerAmmo[ammo_key] = 0


    def ms_validate_weapon_buy(self, weapon, dual_version, *args, **kw):
        """
            Validate weapon buying/selling

            weapon -> Weapon id
            dual_version -> Is the weapon dual version?

            return -> None

        """ 
        w_price = self.all_weapons[weapon]['w_price'] 
        w_cat = 'w_{}'.format(self.all_weapons[weapon]['w_class'])
        dual_weapon = '{}{}'.format(weapon, self.weapon_dual_tag) 
        check_for_dual = dual_weapon in self.all_weapons

        # Buy
        if kw['key'] == 1:
            weapon_choice = None
            # Check that the single weapon in in before buying second weapon
            if check_for_dual and weapon in self.i_playerStats[w_cat] and dual_weapon not in self.i_playerStats[w_cat]:
                weapon_choice = dual_weapon
            else:
                if weapon not in self.i_playerStats[w_cat]: 
                    weapon_choice = weapon
            
            if weapon_choice is not None and self.i_playerStats['credits'] >= w_price:
                self.i_playerStats[w_cat].append(weapon_choice)
                self.i_playerStats['credits'] -= w_price    

        # Sell
        elif kw['key'] == 2:
            weapon_choice = None
            if dual_weapon in self.i_playerStats[w_cat]:
                weapon_choice = dual_weapon
            
            else:
                if weapon in self.i_playerStats[w_cat]:
                    weapon_choice = weapon

            if weapon_choice is not None:
                self.i_playerStats[w_cat].remove(weapon_choice)
                self.i_playerStats['credits'] += int(w_price / 2)


    def ms_validate_gadget_buy(self, gadget, *args, **kw):
        """
            Validate gadget buying

            return -> None

        """
        g_type = self.gl_gadgets[gadget]['g_type']
        g_price_base = self.gl_gadgets[gadget]['g_price']

        # Calculate the the price for next level upgrade
        g_price_next = g_price_base + (g_price_base * self.__GADGET_PRICE_INC * self.i_playerStats[gadget]) 
        
        if g_type == 'single' and self.i_playerStats['credits'] >= g_price_base and \
        self.i_playerStats[gadget] != 1:
            self.i_playerStats[gadget] = 1
            self.i_playerStats['credits'] -= g_price_base

        elif g_type == 'level' and self.i_playerStats['credits'] >= g_price_next:
            self.i_playerStats[gadget] += 1
            self.i_playerStats['credits'] -= g_price_next

            # Suffix should be always in the inventory
            upgrade_tag = gadget.split('_')[1]

            # Level gadgets should always be [value, max]
            self.i_playerStats[upgrade_tag] = [v + self.__GADGET_LEVEL_INC for v in self.i_playerStats[upgrade_tag]] 

            
    def ms_validate_hparm_buy(self, hp_or_armor, *args, **kw):
        """
            Validate refilling armor and health

            hp_or_armor -> 'health' or 'armor'

            return -> None

        """
        multiplier = self.__HEALTH_REFILL if hp_or_armor == 'health' else self.__ARMOR_REFILL 
        
        # Get the total cost
        v_left = self.i_playerStats[hp_or_armor][1] - self.i_playerStats[hp_or_armor][0]
        v_left = v_left * multiplier

        # Credits available
        q, r = divmod(self.i_playerStats['credits'], v_left)
        if q > 0:
            self.i_playerStats[hp_or_armor][0] = self.i_playerStats[hp_or_armor][1]
            self.i_playerStats['credits'] -= v_left 
        else:
            self.i_playerStats[hp_or_armor][0] += int(r / multiplier)
            self.i_playerStats['credits'] -= r 

    
    def ms_render_item_stats(self, surface, _set, **kw):
        """
            Show data about the item being pointed at

            surface -> Active screen surface
            _set -> Which item set are we talking about

            return -> None

        """
        # Note: Move these to their own functions
        px, py = 16, kw['py']

        # Render and carry x the length of the surface width
        render_carry = lambda src, dest, px, py: dest.blit(src, (px, py)).width

        # Weapons
        if _set == self.__E_WEAPON:
            # Dual version borrows data from single version (Strip the dual tag)
            if kw['key'].endswith(self.weapon_dual_tag):
                kw['key'] = kw['key'].split(self.weapon_dual_tag)[0]

            weapon_price = self.all_weapons[kw['key']]['w_price'] 

            # Note: Convert all this to 'two_color_text' function
            surface.blit(self.ms_pre_text['w_id'], (px, py))
            px += self.ms_pre_text['w_id'].get_width()
            
            w_name = self.font_0.render('{} '.format(kw['key']), 1, (0xff, 0x0, 0x80)) 
            surface.blit(w_name, (px, py)); px += w_name.get_width() 

            for w in ('w_price', 'w_damage', 'w_range', 'w_firerate'):
                value = self.all_weapons[kw['key']][w]
                # Calculate the Rounds-per-minute
                if w == 'w_firerate': value = int(1.0 / value * 60.0)

                child = self.font_0.render('{} {} '.format(value, 'cr.' if w == 'w_price' else ''), 1, (0xff, 0x0, 0x80))

                px += render_carry(self.ms_pre_text[w], surface, px, py)
                px += render_carry(child, surface, px, py) 

            return weapon_price        

        # Ammo
        elif _set == self.__E_AMMO:
            ammo_price = self.all_ammo_data[kw['key']][1] 

            px += render_carry(self.ms_pre_text['w_id'], surface, px, py)
            
            # Id
            w_ammo = self.font_0.render('{} '.format(self.all_ammo_data[kw['key']][0]), 1, (0xff, 0x0, 0x80)) 
            px += render_carry(w_ammo, surface, px, py)

            # Price
            px += render_carry(self.ms_pre_text['w_price'], surface, px, py)
            ammo_price_str = self.font_0.render('{} cr.'.format(ammo_price), 1, (0xff, 0x0, 0x80))
            px += render_carry(ammo_price_str, surface, px, py)

            return ammo_price

        # Gadgets
        elif _set == self.__E_GADGET:
            gadget_price = self.gl_gadgets[kw['key']]['g_price']  

            px += render_carry(self.ms_pre_text['w_id'], surface, px, py)
            
            w_name = self.font_0.render('{} '.format(kw['key']), 1, (0xff, 0x0, 0x80)) 
            px += render_carry(w_name, surface, px, py)
            
            # Remove price removes the price tag, if player owns the gadget
            remove_price = self.gl_gadgets[kw['key']]['g_type'] == 'single' and self.i_playerStats[kw['key']]
            if not remove_price:
                px += render_carry(self.ms_pre_text['w_price'], surface, px, py) 
                # Upgrade the price based on level
                gadget_price = int(gadget_price + (gadget_price * self.__GADGET_PRICE_INC * self.i_playerStats[kw['key']]))

                g_price = self.font_0.render('{} cr.'.format(gadget_price), 1, (0xff, 0x0, 0x80))
                px += render_carry(g_price, surface, px, py)

            # Description
            g_desc = self.font_0.render(self.gl_gadgets[kw['key']]['g_desc'], 1, (0xff, 0x0, 0x80))
            px += render_carry(g_desc, surface, 16, py + self.ms_font_height)

            return gadget_price 


    def ms_render_weapons(self, surface, **kw):
        """
            Render weapons

            surface -> Active screen surface

            return -> Name of the weapon being highlighted

        """
        # Passed over to ammo rendering for highlighting the correct ammotype
        highlight_ammo = None
        
        # First 2 (text height) rows are reserved for weapons related text
        for enum, key in enumerate([x for x in self.ms_wIcons['weapon_keys'] if not x.endswith(self.weapon_dual_tag)]):
            # Check for dual version
            dual_weapon = '{}{}'.format(key, self.weapon_dual_tag)
            check_for_dual = dual_weapon in self.all_weapons
            own_dual_weapon = self.ms_pre_text['dual_n']

            w_cat = 'w_{}'.format(self.all_weapons[key]['w_class'])
            if key in self.i_playerStats[w_cat]:
                if check_for_dual and dual_weapon in self.i_playerStats[w_cat]: 
                    own_dual_weapon = self.ms_pre_text['dual_y']
                    key = dual_weapon 

                own_weapon = True
            
            else:
                own_weapon = False

            rsurf = self.ms_wIcons[key]
            rsurf.rs_updateRect(16 + (80 * self.menu_scale) * enum, 16 * self.menu_scale)

            # Own the weapon?
            #surface.blit(own_weapon, (rsurf.rs_getPos('left'), rsurf.rs_getPos('bottom')))
            if own_weapon:
                pos = rsurf.rs_getPos('center')
                surface.blit(self.ms_have_item, (pos[0] - self.ms_have_item.get_width() / 2, pos[1] - self.ms_have_item.get_height() / 2))

            surface.blit(*rsurf.rs_renderSurface(position=1))
            
            # Own the dual version too?
            if check_for_dual:
                surface.blit(own_dual_weapon, (rsurf.rs_getPos('right') - own_dual_weapon.get_width(), rsurf.rs_getPos('bottom')))
            
            if rsurf.rs_hover_over(kw['hover']):
                self.ms_highlight_option(*rsurf.rs_getPos('topleft'), icon_d=rsurf.rs_getSize(), surface=surface)
                weapon_price = self.ms_render_item_stats(surface, self.__E_WEAPON, py=rsurf.rs_getPos('bottom') + self.ms_font_height, key=key)
                
                highlight_ammo = key

                if kw['click']:
                    if kw['click'] == 1 and self.i_playerStats['credits'] < weapon_price:
                        self.ph_common_soundeffect(not_enough=True)
                    else: 
                        rsurf.rs_click(weapon=key.split(self.weapon_dual_tag)[0], dual_version=check_for_dual, key=kw['click'])

        return highlight_ammo


    def ms_render_ammo(self, surface, **kw):
        """
            Render ammo

            surface -> Active screen surface

            return -> None

        """
        if kw['hl_wpn'] is not None: 
            hl_ammo = self.all_weapons_data[kw['hl_wpn']][0]
        else:
            hl_ammo = None

        for enum, key in enumerate(self.ms_aIcons['ammo_keys']):
            rsurf = self.ms_aIcons[key]

            rsurf.rs_updateRect(16 + (80 * self.menu_scale) * enum, 160 * self.menu_scale)
            surface.blit(*rsurf.rs_renderSurface(position=1))

            ammo_count = self.i_playerAmmo[key]
            color_indication = (0xff if ammo_count else 0x80, 0x0, 0x80 if ammo_count else 0x0) 
            ammo_count = self.font_0.render('x{}'.format(int(ammo_count)), 1, color_indication)
            surface.blit(ammo_count, (rsurf.rs_getPos('left'), rsurf.rs_getPos('bottom')))

            if hl_ammo is not None and key == hl_ammo:
                self.ms_highlight_option(*rsurf.rs_getPos('topleft'), icon_d=rsurf.rs_getSize(), surface=surface)    

            if rsurf.rs_hover_over(kw['hover']): 
                self.ms_highlight_option(*rsurf.rs_getPos('topleft'), icon_d=rsurf.rs_getSize(), surface=surface)
                ammo_price = self.ms_render_item_stats(surface, self.__E_AMMO, py=rsurf.rs_getPos('bottom') + self.ms_font_height, key=key)

                if kw['click']:
                    if kw['click'] == 1 and self.i_playerStats['credits'] < ammo_price:
                        self.ph_common_soundeffect(not_enough=True)
                    else: 
                        rsurf.rs_click(mod=kw['click_mod'], key=kw['click'], ammo_id=key)

    
    def ms_render_gadgets(self, surface, **kw):
        """
            Render gadgets

            surface -> Active screen surface

            return -> None

        """
        for enum, key in enumerate(self.ms_sIcons['mod_keys']):
            rsurf = self.ms_sIcons[key]
            rsurf.rs_updateRect(16 + (80 * self.menu_scale) * enum, 304 * self.menu_scale)
            #surface.blit(*rsurf.rs_renderSurface(position=1)) 

            g_type = self.gl_gadgets[key]['g_type']
            if g_type == 'single':
                if self.i_playerStats[key]:
                    pos = rsurf.rs_getPos('center')
                    surface.blit(self.ms_have_item, (pos[0] - self.ms_have_item.get_width() / 2, pos[1] - self.ms_have_item.get_height() / 2))
            
            else:
                level = self.i_playerStats[key]
                color_indication = (0xff if level else 0x80, 0x0, 0x80 if level else 0x0) 
                g_level = self.font_0.render('lvl.{}'.format(self.i_playerStats[key]), 1, color_indication) 
                surface.blit(g_level, (rsurf.rs_getPos('left'), rsurf.rs_getPos('bottom')))

            surface.blit(*rsurf.rs_renderSurface(position=1))

            if rsurf.rs_hover_over(kw['hover']): 
                self.ms_highlight_option(*rsurf.rs_getPos('topleft'), icon_d=rsurf.rs_getSize(), surface=surface)
                gadget_price = self.ms_render_item_stats(surface, self.__E_GADGET, py=rsurf.rs_getPos('bottom') + self.ms_font_height, key=key)

                if kw['click']:
                    if self.i_playerStats['credits'] < gadget_price:
                        self.ph_common_soundeffect(not_enough=True)
                    else: 
                        rsurf.rs_click(gadget=key)


    def ms_renderHealthArmorCreditsMenu(self, surface, **kw):
        """
            Render everything associated with health and armor bars

            surface -> Active screen surface
            click -> Pass variable to indicate mouse click

            return -> None

        """

        surface.blit(*self.ms_armorHealthIcon.rs_renderSurface(position=1))
        
        # Health and armor
        for bar, stat, color in ((self.ms_healthBar, 'health', (0xff, 0x0, 0x40, 0x80)), 
                                 (self.ms_armorBar,  'armor',  (0x40, 0x0, 0xff, 0x80))):
            surface.blit(*bar.rs_renderSurface(position=1))         
            px, py = bar.rs_getPos('topleft')

            max_length = bar.rs_getSize()[0]

            length = self.tk_clamp(float(max_length) / self.i_playerStats[stat][1] * self.i_playerStats[stat][0], 0, max_length)

            self.tk_draw_gfx_rect(surface, (px, py - 2, length, bar.rs_getSize()[1] + 4), color)
            text = self.tk_renderText(self.font_0, "{} / {}".format(*self.i_playerStats[stat]), 
                                      1, (0xff, 0x0, 0x80), shadow=1)
            surface.blit(text, (bar.rs_getPos('right') - text.get_width() - 2, 
                                bar.rs_getPos('bottom') - text.get_height() / 2))

            if self.i_playerStats[stat][0] < self.i_playerStats[stat][1]:
                flash = 0x80 * abs(self.tk_sin(self.menu_timer.get_ticks())) 
                
                re_text = self.tk_renderText(self.font_0, 'Replenish!', 1, (0xff, 0x0, 0x40 + flash), shadow=1)
                surface.blit(re_text, (bar.rs_getPos('left') + 2, bar.rs_getPos('top') - re_text.get_height() / 2))

                x, y = bar.rs_getPos('midright')
                
                # Get the total cost to replish all health or armor
                v_left = self.i_playerStats[stat][1] - self.i_playerStats[stat][0] 
                v_left = v_left * (self.__HEALTH_REFILL if stat == 'health' else self.__ARMOR_REFILL) 

                re_text_cost = self.two_color_text(self.font_0, "To Max: {} cr.".format(int(v_left)), color_v=(0xff, 0x0, 0x40 + flash))
                surface.blit(re_text_cost, (x, y - re_text_cost.get_height() / 2)) 

                if bar.rs_hover_over(kw['hover']) and kw['click']:
                    if stat == 'armor' and self.i_playerStats['credits'] < self.__ARMOR_REFILL:
                        self.ph_common_soundeffect(not_enough=True)
                        return None    

                    elif stat == 'health' and  self.i_playerStats['credits'] < self.__HEALTH_REFILL:
                        self.ph_common_soundeffect(not_enough=True)
                        return None

                    bar.rs_click(hp_or_armor=stat)

    
    def ms_renderExtra(self, surface):
        """
            Render extra shop related stuff

            return -> None

        """
        # Note: Separate these in to their own functions
        surface.blit(*self.ms_creditsIcon.rs_renderSurface(position=1))
        credits = self.font_0.render('{:,} cr.'.format(int(self.i_playerStats['credits'])), 1, (0xff, 0x0, 0x80)) 

        surface.blit(credits, (self.ms_creditsIcon.rs_getPos('left') - credits.get_width() - 8,
                               self.ms_creditsIcon.rs_getPos('centery') - credits.get_height() / 2))
        
        # Help info
        row = 0     # Accumulater for text heights
        for h in sorted([key for key in self.ms_pre_text.iterkeys() if key.startswith('help')]):
            height =  self.ms_pre_text[h].get_height()  
            y = self.ms_armorHealthIcon.rs_getPos('top') - (height + row) 
            surface.blit(self.ms_pre_text[h], (16, y))
            row += height
    

    def ms_highlight_option(self, x, y, icon_d, surface):
        """
            Highlight icon

            x, y -> Position
            icon_d -> Icon dimensions
            surface -> Active screen surface

            return -> None

        """
        t = abs(self.tk_sin(self.menu_timer.get_ticks()))
        x1, y1 = x - 2 * t, y - 2 * t
        x2, y2 = (x + icon_d[0] - 1) + 2 * t, (y + icon_d[1] - 1) + 2 * t

        self.tk_draw_aalines(surface, (0xff, 0x0, 0x80), 0, ((x1, y1 + 16), (x1, y1), (x1 + 16, y1)), 1)
        self.tk_draw_aalines(surface, (0xff, 0x0, 0x80), 0, ((x2, y2 - 16), (x2, y2), (x2 - 16, y2)), 1)

    
    def ms_setupSpecialGadgets(self, bg):
        """
            Setup all special gadgets (Usually hardcoded stuff)

            bg -> Background for the gadget icons

            return -> None
        """
        # NOTE: Keep special gadgets name consistent with the inventory names
        # Also change this to be more robust
        self.ms_sIcons = {}

        csurf_64 = bg
        csurf_64_d = bg.get_size()

        # Laser sight goggles
        for key, value in self.gl_gadgets.iteritems():
            surf = self.tk_scaleSurface(value['g_tex'], self.menu_scale) 
            _s = bg.copy()
            _s.blit(surf, (csurf_64_d[0] / 2 - surf.get_width()  / 2, 
                           csurf_64_d[1] / 2 - surf.get_height() / 2)) 

            self.ms_sIcons[key] = RectSurface(_s, snd_hover_over=181, snd_click=184, func=self.ms_validate_gadget_buy)  

        self.ms_sIcons['mod_keys'] = sorted(self.ms_sIcons.keys())


    def ms_setupWeaponsAmmo(self, bg):
        """
            Setup weapon and ammo clickable surfaces

            bg -> Background for the weapon/ammo icons

            return -> None

        """
        self.ms_wIcons = {}
        self.ms_aIcons = {}
        
        csurf_64 = bg
        csurf_64_d = bg.get_size()
        
        # Weapons
        for key, value in self.all_weapons_data.iteritems():
            if not self.all_weapons[key]['w_buyable']: continue
            
            _s = csurf_64.copy()
            surf = self.tk_scaleSurface(value[1], self.menu_scale)

            ofsx, ofsy = (csurf_64_d[0] - surf.get_width()) / 2, (csurf_64_d[1] - surf.get_height()) / 2 
            _s.blit(surf, (ofsx, ofsy))
            self.ms_wIcons[key] = RectSurface(_s, snd_hover_over=181, snd_click=184, func=self.ms_validate_weapon_buy)

        # Ammo
        for key, value in self.all_ammo_data.iteritems():
            _s = csurf_64.copy()
            surf = self.tk_scaleSurface(value[3], self.menu_scale)

            ofsx, ofsy = (csurf_64_d[0] - surf.get_width()) / 2, (csurf_64_d[1] - surf.get_height()) / 2
            _s.blit(surf, (ofsx, ofsy))
            self.ms_aIcons[key] = RectSurface(_s, snd_hover_over=181, snd_click=185, func=self.ms_validate_ammo_buy)

        self.ms_wIcons['weapon_keys'] = sorted([key for key in self.ms_wIcons.keys()])
        self.ms_aIcons['ammo_keys'] = sorted(self.ms_aIcons.keys())



class MenuIntroOutro(PagesHelp):
    
    def __init__(self, function=None):
        self.function = function
    
    
    def __get__(self, obj, type=None):
        return partial(self, obj) 

    
    def __call__(self, *args, **kw):
        surface = self.function(*args, **kw)
        self.run(surface)
        return surface


    def run(self, surface):
        """
            Run the outro 

            surface -> Active screen surface, (Optional int to signal something)

            return -> Active screen surface

        """
        # Fades out the music nicely with the outro
        self.musicStopPlayback(ms=1400)    # Magic number based on how fast the outro moves

        signal = 0
        if isinstance(surface, tuple):
            surface, signal = surface

        static = surface.copy()

        fadeout_surface = self.tk_surface(surface.get_size(), self.tk_srcalpha)
        fadeout_factor = 0
        
        self.dt_tick()
        while 1:
            self.dt_tick()
            fadeout_surface.fill((0x0, 0x0, 0x0, int(fadeout_factor) & 0xff))

            if int(fadeout_factor) & 16: self.outro_effect(static, fadeout_factor)
            surface.blit(static, (0, 0))

            fadeout_factor += 128 * self.dt_getDelta()

            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        fadeout_factor = 0xff

            surface.blit(fadeout_surface, (0, 0))

            self.tk_display.set_caption(self.tk_name)
            self.tk_display.flip()

            if fadeout_factor >= 0xff:
                self.musicStopPlayback()    # Force shutdown (Player skipped the outro)
                if signal:
                    return surface, signal
                else: 
                    return surface

    
    def outro_effect(self, surface, factor):
        """
            Do some magic to the last captured surface

            surface -> Snapshot of the last surface
            factor -> effect factor

            return -> None
        """
        array = self.tk_surfarray.pixels3d(surface)
        sway = int(8 * self.tk_sin(int(factor + 1)))
        sway = 1 if sway == 0 else sway 
        array[::sway, ::sway, 1:] = 0x20



class MenuOptions(PagesHelp):
    
    def __init__(self):
        self.mo_font_1 = self.tk_font(self.ElementFonts[0], int(48 * self.menu_scale))
        self.mo_font_2 = self.tk_font(self.ElementFonts[1], int(32 * self.menu_scale))
        self.mo_font_3 = self.tk_font(self.ElementFonts[0], int(40 * self.menu_scale)) 
        
        self.mo_options = self.tk_ordereddict()

        self.mo_options[0] = RectSurface(self.tk_renderText(self.mo_font_1, 
                                         "Volume", True, (0xff, 0x0, 0x0), shadow=True), 
                                         snd_hover_over=180, snd_click=181, func=lambda: 0)
        
        self.mo_options[1] = RectSurface(self.tk_renderText(self.mo_font_1, 
                                         "Controls", True, (0xff, 0x0, 0x0), shadow=True), 
                                         snd_hover_over=180, snd_click=181, func=lambda: 1)
        
        self.mo_options[2] = RectSurface(self.tk_renderText(self.mo_font_1, 
                                         "Exit", True, (0xff, 0x0, 0x0), shadow=True), 
                                         snd_hover_over=180, snd_click=181, func=self.tk_quitgame)

        w = max([x.rs_getSize()[0] for x in self.mo_options.itervalues()])
        h = sum([x.rs_getSize()[1] for x in self.mo_options.itervalues()])
        
        # 2 backgrounds for options menu. One with all menu elements height and   (Game)
        #                                 one with minus the exit surface height  (Menu)
        self.mo_background = [self.tk_draw_rounded_rect(w + int(48 * self.menu_scale), 
                                                        h + int(48 * self.menu_scale), 8, (0xff, 0x0, 0x0), 0x60, False),
                              self.tk_draw_rounded_rect(w + int(48 * self.menu_scale), (h - self.mo_options[2].rs_getSize()[1]) + \
                                                        int(48 * self.menu_scale), 8, (0xff, 0x0, 0x0), 0x60, False)] 

        self.mo_functions = {-1: self.mo_root_settings,
                              0: self.mo_sound_settings,
                              1: self.mo_userkeys_settings}

        total_height = sum([h.rs_getSize()[1] + 8 for h in self.mo_options.itervalues()]) / 2
        
        row = 0
        for key, value in self.mo_options.iteritems():
            x = self.tk_res_half[0] - value.rs_getSize()[0] / 2 
            y = self.tk_res_half[1]
            y -= total_height 

            value.rs_updateRect(x, y + row)
            row += value.rs_getSize()[1] + 16         

        self.mo_display_func = -1    # Which menu to display (-1: Root, 0: Volume Control, 1: Controls)
        self.mo_last_select =  -1    # Keep the last selected option highlighted even if mouse is not hovering over it
        self.mo_gui_func = {0: self.mo_sound_settings,
                            1: self.mo_userkeys_settings}

        # ---- Sound variables 
        # Note: Move all this in to its own class
        self.mo_music_volume = {'radial': RadialSlider(64, (0xff, 0x0, 0x0), 96 * self.menu_scale, 1.0, self.def_values['audio_music_level'])}
        self.mo_music_volume['mask'] = RectSurface(self.tk_distortSurface(self.mo_music_volume['radial'].rs_mask, 1), 
                                                   snd_click=181, _id=0) 
        
        self.mo_music_volume['mask'].rs_updateRect(self.tk_res_half[0] - self.mo_music_volume['mask'].rs_getSize()[0] - 128 * self.menu_scale,
                                                   self.tk_res_half[1] - self.mo_music_volume['mask'].rs_getSize()[1] / 2)
        
        self.mo_music_volume['vol_id'] = self.tk_renderText(self.mo_font_1, "Music Volume", True, 
                                         self.mo_music_volume['radial'].rs_color, shadow=True)


        self.mo_effect_volume = {'radial': RadialSlider(64, (0xff, 0x0, 0x0), 96 * self.menu_scale, 1.0, self.def_values['audio_effect_level'])}
        self.mo_effect_volume['mask'] = RectSurface(self.tk_distortSurface(self.mo_effect_volume['radial'].rs_mask, 1), 
                                                    snd_click=181, _id=1)
        
        self.mo_effect_volume['mask'].rs_updateRect(self.tk_res_half[0] + 128 * self.menu_scale,
                                                    self.tk_res_half[1] - self.mo_effect_volume['mask'].rs_getSize()[1] / 2)

        self.mo_effect_volume['vol_id'] = self.tk_renderText(self.mo_font_1, "Effects Volume", True, 
                                          self.mo_music_volume['radial'].rs_color, shadow=True)

        # Contains current x, y delta and id of the slider being used
        self.mo_snd_delta_id = None

        # ---- Control variables
        self.mo_uk_prerendered = {}
        
        pre_max_w = 0   # Needed to build the background
        suf_max_w = 0   # -- || --
        full_h    = 0   # Sum of all keys height
        
        for key in self.tk_user.keys():
            pre = self.tk_renderText(self.mo_font_3, key.upper(), True, (0xff, 0x0, 0x0), shadow=True)
            pre = RectSurface(pre, snd_hover_over=180)
            w, h = pre.rs_getSize() 
            pre_max_w = w if w > pre_max_w else pre_max_w 
            
            suf = self.tk_renderText(self.mo_font_3, self.tk_key_name(self.tk_user[key]), True, (0xff, 0x0, 0x0), shadow=True)  
            suf = RectSurface(suf)

            self.mo_uk_prerendered[key] = [pre, suf]

            full_h += h

        #self.mo_uk_prerendered[-1] = self.mo_font_3.render("Assign key", True, (0xff, 0x0, 0x80))
        self.mo_uk_prerendered[-1] = self.tk_renderText(self.mo_font_3, "Assign key", True, (0xff, 0x0, 0x80), shadow=True)

        suf_max_w = self.mo_uk_prerendered[-1].get_width()

        self.mo_background_keys = self.tk_draw_rounded_rect(pre_max_w + suf_max_w + int(160 * self.menu_scale), 
                                                            full_h + int(32 * self.menu_scale), 
                                                            8, (0xff, 0x0, 0x0), 0x60, False)

        self.tk_draw_aaline(self.mo_background_keys, (0xff, 0x0, 0x0), 
                            (self.mo_background_keys.get_width() / 2, 16), 
                            (self.mo_background_keys.get_width() / 2, self.mo_background_keys.get_height() - 16), 1)
 
        self.mo_uk_layout = {'x': self.tk_res_half[0],
                             'y': self.tk_res_half[1] - (self.mo_uk_prerendered['esc'][0].rs_getSize()[1] * 
                                                         (len(self.mo_uk_prerendered)) - 1) / 2} 

        self.mo_uk_editme = ''    # Store the last selected key


    def run(self, surface, snapshot=False, enable_quit=True):
        """
            Run the options menu

            surface -> Active screen surface
            snapshot -> Take a snapshot of the surface for background(Used as pause background during game)
            enable_quit -> Allow quitting during game via menu

            return -> 'False' when quit

        """
        pause_bg = surface.copy() if snapshot else None
        
        if pause_bg is not None:
            # Decorate the options menu during gameplay
            pause_bg.fill((0x40, 0x0, 0x0, 0x80), special_flags=self.tk_blend_rgba_mult)
            pause_bg.blit(self.menu_background, (0, 0), special_flags=self.tk_blend_rgba_add)

        while 1:
            surface.fill(self.tk_bg_color)

            mx, my = self.tk_mouse_pos()

            if pause_bg is None:
                if not self.mo_display_func:
                    bg = self.render_background('JaaBabe_Options')
                else:
                    bg = self.render_background('JaaBabe_Main')
            else:
                bg = pause_bg 

            surface.blit(bg, (0, 0))   
            
            if self.mo_display_func == -1:
                background_index = 1 if pause_bg is None else 0
                surface.blit(self.mo_background[background_index], 
                            (self.tk_res_half[0] - self.mo_background[0].get_width()  / 2, 
                             self.tk_res_half[1] - self.mo_background[0].get_height() / 2))

            click_down = click_up = tick = 0
            
            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_mousedown:
                    if event.button == 1:
                        click_down = 1

                elif event.type == self.tk_event_mouseup:
                    if event.button == 1:
                        click_up = 1

                elif self.menu_timer.get_event(event.type): tick = 1 


                elif event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc'] and not self.mo_uk_editme:
                        # Quit the options menu entirely
                        if self.mo_display_func == -1:
                            return self.ph_common_soundeffect(return_type=False)

                        # Go back to root
                        else:
                            self.ph_common_soundeffect()
                            # Reset userkey change if exiting the menu
                            if self.mo_display_func == 1: 
                                self.mo_uk_editme = ''
                            
                            if self.mo_display_func == 0:
                                # Save audio settings when exiting the audio menu
                                self.tk_ParseDefaultConfigs(force_rewrite=1)

                            # Go back to root
                            self.mo_display_func = -1

                    self.__mo_validate_userkey(surface, event.key, stage=2)

            if pause_bg is None:
                self.interactive_background.ab_render(surface, tick)

            self.mo_functions[self.mo_display_func](surface, mx, my, click_up, 
                                                    hide_quit=enable_quit, 
                                                    click_down=click_down)

            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))

            self.tk_display.flip()


    def mo_root_settings(self, surface, mx, my, click, hide_quit=False, **kw):
        """
            Display the root settings

            surface -> Active screen surface
            mx, my -> Mouse position
            click -> Mouse click bool
            hide_quit -> Hide the quit option

            return -> None

        """
        for key, value in self.mo_options.iteritems():
            if not hide_quit:
                if key == 2: continue

            surf, pos = value.rs_renderSurface(position=1)
            x, y = pos.x, pos.y
             
            if value.rs_hover_over((mx, my)):
                if self.mo_last_select != key:
                    self.mo_last_select = key    
                    self.menu_timer.get_ticks.reset()  # Just to stop snapping of the elements being highlighted

            if key == self.mo_last_select:
                surf, x, y = self.ph_flash_effect(surf, (x, y))
                
                if click and value.rs_hover_over((mx, my)): 
                    self.mo_display_func = value.rs_click()
            
            surface.blit(surf, (x, y))
        
    
    def mo_sound_settings(self, surface, mx, my, click, **kw):
        """
            Edit music/effects volumes

            surface -> Active screen surface
            mx, my -> Mouse position
            click -> Mouse click bool

            return -> None

        """
        hold = self.tk_mouse_pressed()[0]
        if not hold: self.mo_snd_delta_id = None

        for enum, vol in enumerate((self.mo_music_volume, self.mo_effect_volume)):
            surface.blit(*vol['mask'].rs_renderSurface(position=1))

            value = vol['radial'].rs_render_slider(surface, vol['mask'].rs_getPos('topleft'))

            volume_value = self.mo_font_2.render(str(int(100 * value)) if value else 'OFF', True, vol['radial'].rs_color)
            surface.blit(volume_value, (vol['mask'].rs_getPos('centerx') - volume_value.get_width() / 2, 
                                        vol['mask'].rs_getPos('centery') - volume_value.get_height() / 2))

            message = vol['vol_id']
            surface.blit(message, (vol['mask'].rs_getPos('centerx') - message.get_width() / 2,
                                   vol['mask'].rs_getPos('bottom'))) 

            if kw['click_down'] and vol['mask'].rs_hover_over((mx, my)):
                self.mo_snd_delta_id = mx, my, vol['mask'].rs_id

            if self.mo_snd_delta_id is not None: 
                if vol['mask'].rs_id == self.mo_snd_delta_id[2]:
                    vol['radial'].rs_slide(mx, my, vol['mask'].rs_getPos('center'))
                    self.editVolume(enum, value, True, play_sound_cue=enum)  

    
    def mo_userkeys_settings(self, surface, mx, my, click, **kw):
        """
            Edit player controls

            surface -> Active screen surface
            mx, my -> Mouse position
            click -> Mouse click bool

            return -> None

        """ 
        surface.blit(self.mo_background_keys, (self.tk_res_half[0] - self.mo_background_keys.get_width()  / 2, 
                                               self.tk_res_half[1] - self.mo_background_keys.get_height() / 2 - 16 * self.menu_scale))
        r = 0
        # Keep the order consistent (Might wanna use orderedDict and manually set the order)
        # Currently ordered by the last char which puts esc at the top
        for key in sorted([x for x in self.mo_uk_prerendered.keys() if not isinstance(x, int)], key=lambda x: ord(x[-1])):

            pre_f, suf_f = self.mo_uk_prerendered[key] 

            pre_f.rs_updateRect(self.mo_uk_layout['x'] - pre_f.rs_getSize()[0] - 16, self.mo_uk_layout['y'] + r) 
            surface.blit(*pre_f.rs_renderSurface(position=1))

            suf_f.rs_updateRect(self.mo_uk_layout['x'] + 16, self.mo_uk_layout['y'] + r)
            surf, pos = suf_f.rs_renderSurface(position=1)
            if key == self.mo_uk_editme: 
                surf = self.mo_uk_prerendered[-1] 
            
            if pre_f.rs_hover_over((mx, my)): # or suf_f.rs_hover_over((mx, my)):
                indicate_selected = 16
                if click: self.__mo_validate_userkey(surface, key, stage=1)

            else:
                indicate_selected = 16 if key == self.mo_uk_editme else 0 

            surface.blit(surf, (pos[0] + indicate_selected * abs(self.tk_sin(self.menu_timer.get_ticks())), pos[1]))

            r += pre_f.rs_getSize()[1]


    def __mo_validate_userkey(self, surface, key, stage=0):
        """
            Validate the new userkey

            surface -> Active screen surface 
            key -> stage 1: Selected key being modified (Prepare)
                   stage 2: New key being applied to this keyslot (Validate and apply) 
            
            stage -> 1: Enable key edit
                     2: New key fetched from event queue 

            return -> None

        """
        # Prepare input change
        if stage == 1:
            self.mo_uk_editme = key
            self.tk_user[key] = ''  # Enable for edit 

        # Validate input
        elif stage == 2 and self.mo_uk_editme: 
            if key in self.tk_user.values(): 
                # Key already in-use
                return None

            # Valid key
            self.tk_user[self.mo_uk_editme] = key
            new = self.tk_renderText(self.mo_font_3, self.tk_key_name(key), True, (0xff, 0x0, 0x0), shadow=True)
            self.mo_uk_prerendered[self.mo_uk_editme][1].rs_updateSurface(new)

            def_key = 'key_{}'.format(self.mo_uk_editme)
            self.def_values[def_key] = key

            self.mo_uk_editme = ''

            self.tk_ParseDefaultConfigs(force_rewrite=1)


class MenuReport(PagesHelp, BookKeeping, Inventory):

    __rating_ranks = {'rank': '- Rank -',
                      20:  "Polygon",
                      40:  "Amateur",
                      60:  "Experienced",
                      80:  "Veteran",
                      100: "Agent 47"}

    # Base credits earned completing the level
    __level_bonus = 1500
   
    # Build all the report decorations during the first __call__
    __report_initialized = False


    def __init__(self, function=None):
        self.function = function


    def init_report_data(self): 
        """
            Init/Setup all data related for reporting player stats from the level playthrough

            return -> 'True' on initialization

        """
        self.font_0 = self.tk_font(self.ElementFonts[1], int(24 * self.menu_scale))
        self.font_1 = self.tk_font(self.ElementFonts[1], int(18 * self.menu_scale)) 
        self.font_2 = self.tk_font(self.ElementFonts[0], int(40 * self.menu_scale))
        
        background = self.tk_draw_rounded_rect(int(512 * self.menu_scale), 
                                               self.tk_resolution[1] - 32,
                                               8, (0xff, 0x0, 0x0), 0x60, False)
        # Decorations for the background
        self.tk_draw_aaline(background, (0xff, 0x0, 0x0), (16, 16), (16, background.get_height() - 16), 1)
        self.tk_draw_aaline(background, (0xff, 0x0, 0x0), (background.get_width() - 16, 16), 
                                                          (background.get_width() - 16, 
                                                           background.get_height() - 16), 1)

        self.background = RectSurface(background)
        self.background.rs_updateRect(self.tk_res_half[0] - self.background.rs_getSize()[0] / 2,
                                      self.tk_res_half[1] - self.background.rs_getSize()[1] / 2) 

        # Render all ranks to surfaces
        self.__rating_ranks.update({key: self.tk_renderText(self.font_0 if key == 'rank' else self.font_2, value, 
                                                            True, (0xff, 0x0, 0x0) if key == 'rank' else (0xff, 0x0, 0x80), shadow=1) 
                                    for key, value in self.__rating_ranks.iteritems()})

        # Per level data
        self.r_tags = self.tk_ordereddict()

        return True    


    def build_report(self):
        """
            Build a level report

            Current report consist of: (These are values held by the BookKeep)
                - Level name
                - Completion time
                - Kills / kills
                - Pickups / pickups
                - Date (Hmmm..)

            return -> None

        """
        self.r_tags.clear()

        key, name = self.getSetRecord('name')
        name = name.split('/')[-1]    # Disgard the folder name if there is one
        self.r_tags[key] = self.two_color_text(self.font_0, "Level Report: \"{}\"".format(name))

        key, time = self.getSetRecord('time')
        self.r_tags[key] = self.two_color_text(self.font_0, "Time: {}".format(self.tk_seconds_to_hms(time, to_string=True))) 

        key, kill = self.getSetRecord('kill')
        self.r_tags[key] = self.two_color_text(self.font_0, "Kills: {} / {}".format(*kill))

        key, pickups = self.getSetRecord('pcup')
        self.r_tags[key] = self.two_color_text(self.font_0, "Pickups: {} / {}".format(*pickups))

        key, credits = self.getSetRecord('credits') 
        credits += self.__level_bonus
        self.r_tags[key] = self.two_color_text(self.font_0, "Credits Earned: {}".format(credits))
        self.i_playerStats['credits'] += credits

        # Calculate the final score
        score_per = 100.0 / 3.0    # Give each category percentage (Currently 3 categories)

        # Estimated around 4 minutes per level
        time_estimate = 60 * 4
        time_score = (score_per / time_estimate) * max(0, (time_estimate - time))

        try:
            kill_score = (score_per / kill[1]) * kill[0]
        except ZeroDivisionError:
            # No kills, give the max score
            kill_score = score_per

        try:
            pickup_score = (score_per / pickups[1]) * pickups[0]
        except ZeroDivisionError:
            # No pickups, give the max score
            pickup_score = score_per

        score = time_score + kill_score + pickup_score
        score = min([i for i in self.__rating_ranks.iterkeys() if isinstance(i, int)], key=lambda i: abs(i - score))
        
        self.r_tags['final_score'] = score

        # (Left over from old idea)
        # Current day in DD/MM/YY format (As it should be) wink wink
        self.r_tags['date'] = self.tk_renderText(self.font_1, '-- {} --'.format(self.tk_strftime("%d/%m/%y")), 
                                                 True, (0xff, 0x0, 0x0), shadow=True)  

    
    def __get__(self, obj, type=None):
        return partial(self, obj)

    
    def __call__(self, *args, **kw):
        if not self.__report_initialized:
            self.__report_initialized = self.init_report_data()

        surface = self.function(*args, **kw)

        if isinstance(surface, tuple) and surface[1] == 1:
            return surface

        self.run(surface)
        return surface

    
    def run(self, surface):
        """
            Run the report menu

            return -> None

        """
        self.build_report()

        surface, level_count = surface
        
        self.playMusic(0, -1)
        while 1:
            #surface.fill(self.tk_bg_color)
            surface.blit(self.render_background('JaaBabe_Report'), (0, 0))

            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        return surface, level_count

                self.menu_timer.get_event(event.type)

            surface.blit(*self.background.rs_renderSurface(position=1))

            row = self.background.rs_getPos('top')
            for key, surf in self.r_tags.iteritems():
                if key in ('date', 'final_score', 'credits') : 
                    continue
                surface.blit(surf, (self.tk_res_half[0] - surf.get_width() / 2, row)) 
                row += surf.get_height()  

            x, y = self.background.rs_getPos('bottomleft')
            date = self.r_tags['date'] 
            surface.blit(date, (self.tk_res_half[0] - date.get_width() / 2, y - date.get_height()))

            credits = self.r_tags['credits']
            surface.blit(credits, (self.tk_res_half[0] - credits.get_width() / 2, y - date.get_height() * 2))

            # What rank did the player get
            rank = self.__rating_ranks[self.r_tags['final_score']]
            cx, cy = self.background.rs_getPos('center')
            x, y = (cx - rank.get_width() / 2, cy - rank.get_height() / 2)
            rank_f, xf, yf = self.ph_flash_effect(rank, (x, y))

            surface.blit(rank_f, (xf, yf))
            
            rank_tag = self.__rating_ranks['rank'] 
            surface.blit(rank_tag, (cx - rank_tag.get_width() / 2, y - rank.get_height()))

            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))
            self.tk_display.flip()


# ---------------------------------

#           Intro (Optional)
#              |
#             Menu - - - -
#              |          |
#       Episode Select  Options
#              |           
#    - - > Build level
#   |          |
#   |       *Outro
#   |          |
#   |      Play level  - - - - 
#   |          |              |
#   |          |           Options
#   |       *Outro
#   |       *Report
#   |        *Shop
#    - - - - < |
#              |
#         *Full report
#              |
#      Episode Select(Skip)
#              |
#             Menu

# ---------------------------------


class MenuManager(EpisodeParser):
    """
        Handles the setup how everything is organized

        'm_main' should be the first one to be call'd (Intro before if available)
        then 'm_episode' stacks top of m_main. 

        After that, all functions should call and exit
        to avoid recursive problems 
    """
    # 'MenuMain' should be the first function call'd

    def __init__(self):
        PagesHelp.ph_initData()
        
        # Note: Get rid of these ref hacks and replace with decorators
        self.all_menus = {'m_main':    MenuMain(),
                          'm_episode': MenuCampaign(),
                          'm_options': MenuOptions(),
                          'm_end':     MenuEnd()}

        self.all_menus['m_main'].menu_set_references(intro=MenuIntro(), 
                                                     options=self.all_menus['m_options'],
                                                     episode=self.all_menus['m_episode'])

        self.all_menus['m_episode'].campaign_set_references(episode_roll=self.episodeRoll)


    def mainRun(self, surface, world_build_function, game_loop_function):
        """
            Start the gameplay

            surface -> Active screen surface
            world_build_function -> Function to build the level and emit data about it
            game_loop_function   -> Gameplay loop (Plays the level)

            return -> None

        """
        self.episode_set_references(build=world_build_function,        # Build the level 
                                    run=game_loop_function,            # Play the level
                                    end=self.all_menus['m_end'],       # Credits
                                    reset=Inventory.setup_inventory)   # Reset player stats before the campaign starts
        self.all_menus['m_main'].run(surface)



if __name__ == '__main__':
    pass
