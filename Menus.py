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

from sys import argv as read_argv

from functools import partial


__all__ = ('MenuManager', )


class PagesHelp(uiElements, SoundMusic, GlobalGameData, DeltaTimer):

    
    @classmethod
    def ph_initData(cls):
        """
            Setup common data used by all the pages

            return -> None

        """
        # Provide global scale for all UI elements (Except in-game)
        cls.menu_scale = cls.tk_resolution_scale    # Possible add some correction here for the menu items?

        # Provide a same background for all the menus
        cls.menu_background = cls.__ph_createBackground(1)

        # Note: What the fuck was i thinging here? - Replace this menu_timer bullshit with get_ticks()
        # Provide common timer for every menu class
        cls.menu_base_event = cls.tk_uEvent 
        cls.menu_timer = MenuEventDispatch(get_event=lambda t=None: cls.menu_base_event if t is None \
                                                     else cls.menu_timer.get_ticks.m_add(.05) if t == cls.menu_base_event else 0,  
                                           get_ticks=cls.tk_counter(0)) 
        
        cls.interactive_background = ActiveBackGround()
        cls.scanline_effect = ScanLineGenerator(8, 4)   # Currently Mainmenu uses this effect

        # Start the common event timer
        cls.tk_time.set_timer(cls.menu_timer.get_event(), 10)

    
    @classmethod
    def ph_go_back_soundeffect(cls, snd_id=188, return_type=None):
        """
            Provide common exit sound effect for menues

            return -> None
        """
        cls.playSoundEffect(snd_id)
        return return_type

    
    @classmethod
    def ph_flash_effect(cls, surface, pos):
        """
            Wiggle surface around (Try it to see the effect)

            surface -> Which surface receives the effect

            return -> Affected surface, position

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
    def __ph_createBackground(cls, op=1):
        """
            Create a common background for all the menus
            Change this function to create you're own or 
            add support for loading custom image as background

            op -> 1: Stripe background
                  2: Faded background

            return -> Surface

        """
        if op & 1: 
            background = cls.tk_surface(cls.tk_resolution)

            # Access the pixel arrays of the surface for effects
            background_array = cls.tk_surfarray.pixels3d(background)

            # Added every second horizontal line as dark red for fitting the theme of the game 
            background_array[::3, ::2] = 0x40, 0x0, 0x0

        if op & 2:
            background = cls.tk_surface(cls.tk_resolution, cls.tk_srcalpha)
            background.fill((0x40, 0x0, 0x0, 0x80))

        return background



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

        # Font
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
            surface.fill(self.tk_bg_color)
            surface.blit(self.menu_background, (0, 0))

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
                        self.options[key][1](surface)       

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

        self.selection_bg = self.tk_draw_rounded_rect(int(256 * self.menu_scale), 
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
            surface.fill(self.tk_bg_color)
            surface.blit(self.menu_background, (0, 0))

            tick = click = 0
            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        return self.ph_go_back_soundeffect()

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
    

    def __init__(self, function=None):
        self.function = function


    def __get__(self, obj, type=None):
        return partial(self, obj)

    
    def __call__(self, *args, **kw):
        if not self.__shop_initialized:
            self.__shop_initialized = self.init_shop_data()    

        surface = self.function(*args, **kw)
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
        self.ms_pre_text = {'w_id': self.font_0.render('Id: ',               1, (0xff, 0x0, 0x0)), 
                            'w_price': self.font_0.render('| Price: ',       1, (0xff, 0x0, 0x0)),
                            'w_damage': self.font_0.render('| Damage: ',     1, (0xff, 0x0, 0x0)),
                            'w_range': self.font_0.render('| Range: ',       1, (0xff, 0x0, 0x0)),
                            'w_firerate': self.font_0.render('| Firerate: ', 1, (0xff, 0x0, 0x0)),
                            'dual_n': self.font_0.render('Dual',             1, (0x80, 0x0, 0x0)),
                            'dual_y': self.font_0.render('Dual',             1, (0xff, 0x0, 0x0)),
                            'owned_n': self.font_0.render('Owned',           1, (0x80, 0x0, 0x0)),
                            'owned_y': self.font_0.render('Owned',           1, (0xff, 0x0, 0x0)),
                            'help_1': self.font_0.render('LMB - Buy | RMB - sell', 1, (0xff, 0x0, 0x0))}

        # Provide much nicer background for the icons (32x32, 64x64)
        # Since my antialising method is slow, its betters to build one and pass that to everyone
        _64 = int(64 * self.menu_scale) 
        csurf_64 = self.tk_draw_rounded_rect(_64, _64, 8, (0xff, 0x0, 0x0), 0x60, True)
        
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

        bar_bg = self.tk_surface((128 * self.menu_scale, self.ms_armorHealthIcon.rs_getSize()[1] / 2 - (40 * self.menu_scale)), self.tk_srcalpha)
        bar_bg.fill((0xff, 0x0, 0x0, 0x80))
        
        self.ms_healthBar = RectSurface(bar_bg, snd_hover_over=181, snd_click=183)
        self.ms_healthBar.rs_updateRect(self.ms_armorHealthIcon.rs_getPos('right'),
                                        self.ms_armorHealthIcon.rs_getPos('top') + \
                                        self.ms_armorHealthIcon.rs_getSize()[1] / 4 - bar_bg.get_height() / 2)

        self.ms_armorBar = RectSurface(bar_bg, snd_hover_over=181, snd_click=182) 
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
        while 1:
            surface.fill(self.tk_bg_color)
            surface.blit(self.menu_background, (0, 0))

            click = 0

            for event in self.tk_eventDispatch():
                self.menu_timer.get_event(event.type)

                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        quit_shop = True

                if event.type == self.tk_event_mouseup:
                    if event.button == 1:
                        click = 1

            mx, my = self.tk_mouse_pos()

            weapon = self.ms_render_weapons(surface, hover=(mx, my), click=click)
            
            self.ms_render_ammo(surface, hover=(mx, my), click=click, hl_wpn=weapon)

            self.ms_render_gadgets(surface, hover=(mx, my), click=click)

            self.ms_renderHealthArmorCreditsMenu(surface, hover=(mx, my), click=click)
            
            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))

            self.tk_display.flip() 

            # This is to keep the last draw surface drawn for outro effect(Visually more pleasing)
            if quit_shop: return surface


    def ms_validate_buy(self):
        """
            TBD

            return -> None
        """
        pass

    
    def ms_render_weapons(self, surface, **kw):
        """
            Render weapons

            return -> Name of the weapon being highlighted

        """
        # Passed over to ammo rendering for highlighting the correct ammotype
        hl_weapon = None
        
        # First 2 (text height) rows are reserved for weapons related text
        for enum, key in enumerate(self.ms_wIcons['weapon_keys']):
            value = self.ms_wIcons[key]
            
            value.rs_updateRect(16 + (80 * self.menu_scale) * enum, 16 * self.menu_scale)
            surface.blit(*value.rs_renderSurface(position=1))

            if key + '-dual' in self.all_weapons: 
                dual_i = self.ms_pre_text['dual_n']
                surface.blit(dual_i, (value.rs_getPos('right') - dual_i.get_width(), value.rs_getPos('bottom')))
            
            if value.rs_hover_over(kw['hover']):
                self.ms_highlight_option(*value.rs_getPos('topleft'), icon_d=value.rs_getSize(), surface=surface)
                self.ms_render_item_stats(surface, 0, py=value.rs_getPos('bottom') + self.ms_font_height, key=key)
                hl_weapon = key

                if kw['click']: value.rs_click()

        return hl_weapon

    
    def ms_render_item_stats(self, surface, _set, **kw):
        """
            Show data about the item being pointed at

            surface -> Active screen surface
            _set -> Which item set are we talking about

            return -> None

        """
        px, py = 16, kw['py']

        # Render and carry x the length of the surface width
        render_carry = lambda src, dest, px, py: dest.blit(src, (px, py)).width

        # Weapons
        if _set == 0:
            surface.blit(self.ms_pre_text['w_id'], (px, py))
            px += self.ms_pre_text['w_id'].get_width()
            
            w_name = self.font_0.render('{} '.format(kw['key']), 1, (0xff, 0x0, 0x80)) 
            surface.blit(w_name, (px, py)); px += w_name.get_width() 

            for w in ('w_price', 'w_damage', 'w_range', 'w_firerate'):
                value = self.all_weapons[kw['key']][w]
                child = self.font_0.render('{} {} '.format(value, 'cr.' if w == 'w_price' else ''), 1, (0xff, 0x0, 0x80))

                px += render_carry(self.ms_pre_text[w], surface, px, py)
                px += render_carry(child, surface, px, py)         

        # Ammo
        elif _set== 1:
            px += render_carry(self.ms_pre_text['w_id'], surface, px, py)
            
            w_ammo = self.font_0.render('{} '.format(self.all_ammo_data[kw['key']][0]), 1, (0xff, 0x0, 0x80)) 
            px += render_carry(w_ammo, surface, px, py)

            px += render_carry(self.ms_pre_text['w_price'], surface, px, py)
            a_price = self.font_0.render('{} cr.'.format(self.all_ammo_data[kw['key']][1]), 1, (0xff, 0x0, 0x80))
            px += render_carry(a_price, surface, px, py)

        
        # Gadgets
        elif _set == 2:
            px += render_carry(self.ms_pre_text['w_id'], surface, px, py)

            w_name = self.font_0.render('{} '.format(kw['key']), 1, (0xff, 0x0, 0x80)) 
            px += render_carry(w_name, surface, px, py)

            px += render_carry(self.ms_pre_text['w_price'], surface, px, py)
            g_price = self.font_0.render('{} cr.'.format(self.gl_gadgets[kw['key']]['g_price']), 1, (0xff, 0x0, 0x80))
            px += render_carry(g_price, surface, px, py)

            g_desc = self.font_0.render(self.gl_gadgets[kw['key']]['g_desc'], 1, (0xff, 0x0, 0x80))
            px += render_carry(g_desc, surface, 16, py + self.ms_font_height) 



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
            value = self.ms_aIcons[key]

            value.rs_updateRect(16 + (80 * self.menu_scale) * enum, 160 * self.menu_scale)
            surface.blit(*value.rs_renderSurface(position=1))

            ammo_count = self.font_0.render('x{}'.format(self._i_max_ammo), 1, (0xff if self._i_max_ammo else 0x80, 0x0, 0x80))
            surface.blit(ammo_count, (value.rs_getPos('left'), value.rs_getPos('bottom')))

            if hl_ammo is not None and key == hl_ammo:
                self.ms_highlight_option(*value.rs_getPos('topleft'), icon_d=value.rs_getSize(), surface=surface)    

            if value.rs_hover_over(kw['hover']): 
                self.ms_highlight_option(*value.rs_getPos('topleft'), icon_d=value.rs_getSize(), surface=surface)
                self.ms_render_item_stats(surface, 1, py=value.rs_getPos('bottom') + self.ms_font_height, key=key)

                if kw['click']: value.rs_click()

    
    def ms_render_gadgets(self, surface, **kw):
        """
            Render gadgets

            surface -> Active screen surface

            return -> None

        """
        for enum, key in enumerate(self.ms_sIcons['mod_keys']):
            value = self.ms_sIcons[key]
            value.rs_updateRect(16 + (80 * self.menu_scale) * enum, 304 * self.menu_scale)
            surface.blit(*value.rs_renderSurface(position=1)) 

            owned_i = self.ms_pre_text['owned_n']
            surface.blit(owned_i, (value.rs_getPos('right') - owned_i.get_width(), value.rs_getPos('bottom'))) 

            if value.rs_hover_over(kw['hover']): 
                self.ms_highlight_option(*value.rs_getPos('topleft'), icon_d=value.rs_getSize(), surface=surface)
                self.ms_render_item_stats(surface, 2, py=value.rs_getPos('bottom') + self.ms_font_height, key=key)

                if kw['click']: value.rs_click()


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
                re_text = self.tk_renderText(self.font_0, 'Replenish!', 1, 
                                            (0xff, 0x0, 0x40 + 0x80 * abs(self.tk_sin(self.menu_timer.get_ticks()))), shadow=1)

                surface.blit(re_text, (bar.rs_getPos('left') + 2, bar.rs_getPos('top') - re_text.get_height() / 2))

                # Refill if needed
                if bar.rs_hover_over(kw['hover']):
                    if kw['click']: bar.rs_click()

        # Credits
        surface.blit(*self.ms_creditsIcon.rs_renderSurface(position=1))
        credits = self.font_0.render('{:,} cr.'.format(self.i_playerStats['credits']), 1, (0xff, 0x0, 0x80)) 

        surface.blit(credits, (self.ms_creditsIcon.rs_getPos('left') - credits.get_width() - 8,
                               self.ms_creditsIcon.rs_getPos('centery') - credits.get_height() / 2))
        
        # Help info
        surface.blit(self.ms_pre_text['help_1'], (16, self.ms_armorHealthIcon.rs_getPos('top') - \
                                                      self.ms_pre_text['help_1'].get_height()))
    

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

            self.ms_sIcons[key] = RectSurface(_s, snd_hover_over=181, snd_click=184)  

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
            self.ms_wIcons[key] = RectSurface(_s, snd_hover_over=181, snd_click=184)

        # Ammo
        for key, value in self.all_ammo_data.iteritems():
            _s = csurf_64.copy()
            surf = self.tk_scaleSurface(value[3], self.menu_scale)

            ofsx, ofsy = (csurf_64_d[0] - surf.get_width()) / 2, (csurf_64_d[1] - surf.get_height()) / 2
            _s.blit(surf, (ofsx, ofsy))
            self.ms_aIcons[key] = RectSurface(_s, snd_hover_over=181, snd_click=185)

        self.ms_wIcons['weapon_keys'] = sorted([key for key in self.ms_wIcons.keys() if len(key.split('-')) != 2])
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

            surface -> Active screen surface

            return -> Active screen surface

        """
        # Fades out the music nicely with the outro
        self.musicStopPlayback(ms=1400)    # Magic number based on how fast the outro moves

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
        self.mo_music_volume = {'radial': RadialSlider(64, (0xff, 0x0, 0x0), 96 * self.menu_scale, 1.0)}
        self.mo_music_volume['mask'] = RectSurface(self.tk_distortSurface(self.mo_music_volume['radial'].rs_mask, 1), 
                                                   snd_click=181, _id=0) 
        
        self.mo_music_volume['mask'].rs_updateRect(self.tk_res_half[0] - self.mo_music_volume['mask'].rs_getSize()[0] - 128 * self.menu_scale,
                                                   self.tk_res_half[1] - self.mo_music_volume['mask'].rs_getSize()[1] / 2)
        
        self.mo_music_volume['vol_id'] = self.tk_renderText(self.mo_font_1, "Music Volume", True, 
                                         self.mo_music_volume['radial'].rs_color, shadow=True)


        self.mo_effect_volume = {'radial': RadialSlider(64, (0xff, 0x0, 0x0), 96 * self.menu_scale, 1.0)}
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

            surface.blit(self.menu_background if pause_bg is None else pause_bg, (0, 0))   
            
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
                            return self.ph_go_back_soundeffect(return_type=False)

                        # Go back to root
                        else:
                            self.ph_go_back_soundeffect()
                            # Reset userkey change if exiting the menu
                            if self.mo_display_func == 1: 
                                self.mo_uk_editme = ''
                            
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
                    print self.mo_snd_delta_id[2]
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

            # Valid
            self.tk_user[self.mo_uk_editme] = key
            new = self.tk_renderText(self.mo_font_3, self.tk_key_name(key), True, (0xff, 0x0, 0x0), shadow=True)
            self.mo_uk_prerendered[self.mo_uk_editme][1].rs_updateSurface(new)
            self.mo_uk_editme = ''


class MenuReport(PagesHelp):

    __rating_ranks = {20:  "Polygon Reviewer",
                      40:  "Amateur",
                      60:  "Experienced",
                      80:  "Veteran",
                      100: "Sicario"}
   
    # Build all the report decorations during the first __call__
    __report_initialized = False


    def __init__(self, function=None):
        self.function = function


    def init_report_data(self): 
        """
            Init/Setup all data related for reporting player stats from the level playthrough

            return -> None

        """
        self.font_0 = self.tk_font(self.ElementFonts[1], int(20 * self.menu_scale)) 
        
        background = self.tk_draw_rounded_rect(int(512 * self.menu_scale), 
                                               self.tk_resolution[1] - 32,
                                               8, (0xff, 0x0, 0x0), 0x60, False)

        self.background = RectSurface(background)
        self.background.rs_updateRect(self.tk_res_half[0] - self.background.rs_getSize()[0] / 2,
                                      self.tk_res_half[1] - self.background.rs_getSize()[1] / 2) 

        self.r_tag = self.tk_renderText(self.font_0, "Level Report", True, 
                                        (0xff, 0x0, 0x0), shadow=True, flags=1)

        self.r_tag_time = self.tk_strftime("%d/%m/%y")

        # Per level(Final report includes more data)
        self.r_tags = {'name': "Level Report: {}",
                       'time': "Time: {}",
                       'data': "Data: {}",
                       'kill': "Kills: {}",
                       'pkup': "Pickups: {}"}

        return True    


    def build_report(self):
        """
            Build the actual report in simplified police report

            return -> None

        """
        # Get the current date
        self.r_tag_time = self.tk_strftime("%d/%m/%y")
        self.r_tag_time = self.tk_renderText(self.font_0, self.r_tag_time, True, 
                                            (0xff, 0x0, 0x0), shadow=True, flags=1)


    
    def __get__(self, obj, type=None):
        return partial(self, obj)

    
    def __call__(self, *args, **kw):
        if not self.__report_initialized:
            self.__report_initialized = self.init_report_data()

        surface = self.function(*args, **kw)
        self.run(surface)
        return surface

    
    def run(self, surface):
        """
            Run the report menu

            return -> None

        """
        self.build_report()
        
        while 1:
            surface.fill(self.tk_bg_color)
            surface.blit(self.menu_background, (0, 0))

            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_keyup:
                    if event.key == self.tk_user['esc']:
                        return surface

            surface.blit(*self.background.rs_renderSurface(position=1))

            # Get the topleft position of the background
            bg_topleft = self.background.rs_getPos('topleft')

            # Report tag shall work as anchor
            #r_tag_pos = (bg_topleft[0] + 16 * self.menu_scale, bg_topleft[1] + 4 * self.menu_scale) 
            #surface.blit(self.r_tag, r_tag_pos)
            

            #surface.blit(self.r_tag_time, (r_tag_pos[0], r_tag_pos[1] + self.r_tag.get_height()))

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
        
        # Note: Get rid of these. And replace with decorator based
        self.all_menus = {'m_main':    MenuMain(),
                          'm_episode': MenuCampaign(),
                          'm_options': MenuOptions()}

        self.all_menus['m_main'].menu_set_references(intro=None if '-nosplash' in read_argv else MenuIntro(), 
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
        self.episode_set_references(build=world_build_function, run=game_loop_function)
        self.all_menus['m_main'].run(surface)



if __name__ == '__main__':
    pass 
