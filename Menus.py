from TextureLoader import uiElements
from ConfigsModule import GlobalGameData
from EventManager import EventManager
from SoundModule import SoundMusic
from Inventory import Inventory
from MenuUtils import * 
from _3d_models import Model3D


__all__ = ('MenuManager')


class PagesHelp(uiElements, SoundMusic, GlobalGameData):

    @classmethod
    def ph_initData(cls):
        """
            Setup common data used by all the pages

            return -> None

        """
        # Provide global scale for all UI elements (Except in-game)
        cls.menu_scale = cls.tk_resolution_scale    # Possible add some correction here for the menu items?

        # Provide a same background for all the menus
        cls.menu_background = cls.__ph_createBackground()

        # Provide constant timer for menu effects (uEvent 24 (index 0))
        cls.menu_timer = [cls.tk_uEvent, cls.tk_counter(0)]
        cls.menu_timer_add = lambda cls: cls.menu_timer[1].m_add(.05) 

        cls.tk_time.set_timer(cls.menu_timer[0], 10)



    @classmethod
    def __ph_createBackground(cls):
        """
            Create a common background for all the menus
            Change this function to create you're own or 
            add support for loading custom image as background

            return -> Surface

        """
        background = cls.tk_surface(cls.tk_resolution)

        # Access the pixel arrays of the surface for effects
        background_array = cls.tk_surfarray.pixels3d(background)

        # Added every second horizontal line as dark red for fitting the theme of the game 
        background_array[::3, ::2] = 0x40, 0x0, 0x0

        return background



class MenuIntro(PagesHelp, EventManager):
    """
        Display the Dev Intro (Which ALWAYS should be skippable!)
 

    """
    def __init__(self):
        self.intro_time = 3000  # ms
        self.intro_exit = 1

        # Gear surface
        self.dsurf = self.__mi_generateGear()

        # Fader surface
        self.fade = self.tk_surface(self.tk_resolution, self.tk_srcalpha) 

        # Font
        self.font = self.tk_font(self.ElementFonts[0], int(128 * self.menu_scale))
 
        w, h = self.font.size(self.tk_dev_name)
        self.fsurf = self.tk_surface((w, h))
        self.fsurf.blit(self.font.render(self.tk_dev_name, 1, (0xff, 0x0, 0x0)), (0, 0))

        # Quitting the intro either via quit key or timer
        EventManager.__init__(self)
        self.Event_newEvent(self.intro_time, self.__mi_clearExit)

    
    def run(self, surface):
        """
            Run the Intro

            return -> None

        """
        while self.intro_exit:
            surface.fill(self.tk_bg_color)
            
            for event in self.tk_eventDispatch():
                if event.type == self.tk_event_keydown:
                    if event.key == self.tk_user['esc']:
                        self.intro_exit = 0

                self.Event_handleEvents(event.type) 

            # Find the center position for the gear and text
            dsurf_pos = (self.tk_res_half[0] - ((self.dsurf.get_width()  / 2 + self.fsurf.get_width())  / 2),
                         self.tk_res_half[1] - ((self.dsurf.get_height() / 2 + self.fsurf.get_height()) / 2))
            
            surface.blit(self.dsurf, dsurf_pos)

            surface.blit(self.fsurf, (dsurf_pos[0] + self.dsurf.get_width()  / 2,
                                      dsurf_pos[1] + self.dsurf.get_height() / 2 - self.fsurf.get_height()))


            self.tk_display.flip()


    def __mi_clearExit(self):
        """
            Exit intro once the intro timer has been reached

            return -> None

        """
        # Note: Possible clean the intro stuff when quitting it?

        self.intro_exit = 0

    
    def __mi_generateGear(self):
        """
            Generate the gear (Why not?)

            return -> Surface with the gear image on it

        """
        # Obviously it would easier just to create the image and load that

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

        # Generate the outer ring
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
    # Notes about the menu
    # There's room for 2 lines of text under different categories of items (Weapons, ammo, gadgets)


    def __init__(self):
        self.font_96 = self.tk_font(self.ElementFonts[0], int(96 * self.menu_scale))
        self.font_48 = self.tk_font(self.ElementFonts[0], int(48 * self.menu_scale))
        self.font_16 = self.tk_font(self.ElementFonts[1], int(16 * self.menu_scale))

        
        self.gfont = self.font_96.render(self.tk_name, 1, (0xff, 0x0, 0x0))
        self.gfont_pos = (self.tk_res_half[0] - self.gfont.get_width()  / 2,
                          self.tk_res_half[1] - self.gfont.get_height() / 2)


        self.gfont_bg = self.font_96.render(self.tk_name, 1, (0xaa, 0x0, 0x0)) 
        self.gfont_bg_pos = (self.tk_res_half[0] - self.gfont_bg.get_width()  / 2,
                             self.tk_res_half[1] - self.gfont_bg.get_height() / 2)  
        
        self.version_id = self.font_16.render('ver: ' + self.tk_version, 1, (0xff, 0x0, 0x0)) 

        self.scanline = ScanLineGenerator(8, 4)

        self.options_selected = -1  # Keep the last selected option highlighted even if mouse is not hovering on it
        
        self.options = self.tk_ordereddict()
        self.options[0] = (RectSurface(self.font_48.render("New Game", 1, (0xff, 0x0, 0x0)), snd_hover_over=180),  
                           lambda: None)
        
        self.options[1] = (RectSurface(self.font_48.render("Options", 1, (0xff, 0x0, 0x0)), snd_hover_over=180),   
                           lambda: None)
        
        self.options[2] = (RectSurface(self.font_48.render("Exit Game", 1, (0xff, 0x0, 0x0)), snd_hover_over=180), 
                           lambda: self.tk_quitgame())

        # Get the total height of all the options
        self.options_height = (sum([h[0].rs_getSize()[1] for h in self.options.itervalues()]) + self.gfont.get_height()) / 2

        self.mm_active_bg = ActiveBackGround()
        
        # Update scanline y position
        EventManager.__init__(self)
        self.Event_newEvent(self.scanline.slg_speed, self.scanline.slg_update)

        self.clock = self.tk_time.Clock()
    
    
    def run(self, surface):
        """
            Mainmenu

            surface -> Surface on which to display the contents

            return -> None

        """
        while 1:
            self.clock.tick(8192)
            surface.fill(self.tk_bg_color)
            surface.blit(self.menu_background, (0, 0))

            click = 0; tick = 0

            for event in self.tk_eventDispatch():
                self.Event_handleEvents(event.type)

                if event.type == self.menu_timer[0]: self.menu_timer_add(); tick = 1

                if event.type == self.tk_event_mouseup: click = 1

            self.mm_active_bg.ab_render(surface, tick)

            # Give some random wiggle for certain ui elements
            if tick: twitch = 4 if self.tk_randrange(0, 100) > 95 else 0
            else: twitch = 0 

            surface.blit(self.gfont_bg, (self.gfont_bg_pos[0] + twitch,
                                         self.gfont_bg_pos[1] - (self.options_height + twitch)))
 

            surface.blit(self.gfont, (self.gfont_pos[0] - twitch,
                                      self.gfont_pos[1] - (self.options_height - twitch)))
            
            mx, my = self.tk_mouse_pos()
            
            for k, v in self.options.iteritems():
                v = v[0].rs_renderSurface()
                px = self.tk_res_half[0] - v.get_width()  / 2 
                py =  self.gfont_pos[1] + self.gfont.get_height()
                
                # Spacing between logo and options 
                py += 64 * self.menu_scale - self.options_height
                
                # Spacing between options text 
                py += (v.get_height() + 16 * self.menu_scale) * k  
                
                self.options[k][0].rs_updateRect(px, py)

                if self.options[k][0].rs_hover_over((mx, my)):
                    if self.options_selected != k:
                           
                        self.options_selected = k    
                        
                        self.menu_timer[1].reset()

                    #if self.tk_mouse_pressed()[0]:
                    #    self.options[k][1]()

                if k == self.options_selected:
                    # Highlight the selected option
                    vx, vy = v.get_size()
                    
                    # Wiggle the selected option around
                    v = self.tk_rotozoom(v, 8 * self.tk_sin(self.menu_timer[1]()), 
                                         1.0 + (0.2 * abs(self.tk_sin(self.menu_timer[1]()))))
                    
                    vx = v.get_width()  - vx
                    vy = v.get_height() - vy
                    px -= vx / 2; py -= vy / 2

                surface.blit(v, (px, py))


            # -- Set everything above this function to be affected by the scanline --
            self.scanline.slg_scanlineEffect(surface)

            surface.blit(self.version_id, (8, self.tk_resolution[1] - (self.version_id.get_height() + 4)))

            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))

            self.tk_display.set_caption('{}, FPS: {}'.format(self.tk_name, round(self.clock.get_fps(), 2)))
                
            self.tk_display.flip()  



class MenuCampaign(PagesHelp):
    def __init__(self):
        pass

    def run(self, surface):
        while 1:
            pass 


class MenuShop(PagesHelp, Inventory, EventManager):
    
    def __init__(self):
        self.ms_font_16 = self.tk_font(self.ElementFonts[1], int(16 * self.menu_scale))
        
        # Pre-rendered texts (Color/Text doesn't change)
        self.ms_pre_text = {'price': self.ms_font_16.render('Price: ', 1, (0xff, 0x0, 0x0)),
                            'dual_n': self.ms_font_16.render('Dual', 1, (0x80, 0x0, 0x0)),
                            'dual_y': self.ms_font_16.render('Dual', 1, (0xff, 0x0, 0x0))}

        # Provide much nicer background for the icons (32x32, 64x64)
        _64 = int(64 * self.menu_scale) 
        csurf_64 = self.tk_draw_rounded_rect(_64, _64, 8, (0xff, 0x0, 0x0), 0x60, True)
        
        _32 = int(32 * self.menu_scale) 
        csurf_32 = self.tk_draw_rounded_rect(_32, _32, 8, (0xff, 0x0, 0x0), 0x60, True) 

        self.ms_setupWeaponsAmmo(csurf_64)

        self.ms_setupSpecialGadgets(csurf_64)

        self.ms_setup_credits(csurf_32)
        
        self.ms_setup_healthArmor()


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
            TBD

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
        while 1:
            surface.fill(self.tk_bg_color)
            surface.blit(self.menu_background, (0, 0))

            click = 0

            for event in self.tk_eventDispatch():
                if event.type == self.menu_timer[0]: self.menu_timer_add() 

                if event.type == self.tk_event_mouseup: click = 1


            mx, my = self.tk_mouse_pos()

            self.ms_render_weapons(surface, hover=(mx, my), click=click)
            
            self.ms_render_ammo(surface, hover=(mx, my), click=click)

            self.ms_render_gadgets(surface, hover=(mx, my), click=click)

            self.ms_renderHealthArmorCreditsMenu(surface, hover=(mx, my), click=click)
            
            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))

            self.tk_display.flip() 


    def ms_validate_buy(self):
        """
            TBD

            return -> None
        """

    
    def ms_render_weapons(self, surface, **kw):
        """
            Render weapons

            return -> None

        """
        # First 2 (text height) rows are reserved for weapons related text
        for enum, key in enumerate(self.ms_wIcons['weapon_keys']):
            value = self.ms_wIcons[key]
            
            value.rs_updateRect(16 + (80 * self.menu_scale) * enum, 16 * self.menu_scale)
            surface.blit(*value.rs_renderSurface(position=1))

            if key + '-dual' in self.all_weapons: 
                dual = self.ms_pre_text['dual_n']
                surface.blit(dual, (value.rs_getPos('right') - dual.get_width(), value.rs_getPos('bottom')))
            
            if value.rs_hover_over(kw['hover']):
                self.ms_highlight_option(*value.rs_getPos('topleft'), icon_d=value.rs_getSize(), surface=surface)
                
                surface.blit(self.ms_pre_text['price'], (16, value.rs_getPos('bottom')))
                price = self.ms_font_16.render('{} cr.'.format(self.all_weapons[key]['w_price']), 1, (0xff, 0x0, 0x80))
                surface.blit(price, (16 + self.ms_pre_text['price'].get_width(), value.rs_getPos('bottom')))

                if kw['click']: value.rs_click()


    def ms_render_ammo(self, surface, **kw):
        """
            Render ammo

            return -> None

        """
        for enum, key in enumerate(self.ms_aIcons['ammo_keys']):
            value = self.ms_aIcons[key]

            value.rs_updateRect(16 + (80 * self.menu_scale) * enum, 160 * self.menu_scale)
            surface.blit(*value.rs_renderSurface(position=1))

            if value.rs_hover_over(kw['hover']): 
                self.ms_highlight_option(*value.rs_getPos('topleft'), icon_d=value.rs_getSize(), surface=surface)

                if kw['click']: value.rs_click()

    
    def ms_render_gadgets(self, surface, **kw):
        """
            Render gadgets

            return -> None

        """
        for enum, key in enumerate(self.ms_sIcons['mod_keys']):
            value = self.ms_sIcons[key]
            value.rs_updateRect(16 + 80 * enum, 304 * self.menu_scale)
            surface.blit(*value.rs_renderSurface(position=1)) 

            if value.rs_hover_over(kw['hover']): 
                self.ms_highlight_option(*value.rs_getPos('topleft'), icon_d=value.rs_getSize(), surface=surface)

                if kw['click']: value.rs_click()


    def ms_renderHealthArmorCreditsMenu(self, surface, **kw):
        """
            Render everything associated with health and armor bars

            surface -> Surface which to draw on
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
            text = self.tk_renderText(self.ms_font_16, "{} / {}".format(*self.i_playerStats[stat]), 
                                      1, (0xff, 0x0, 0x80), shadow=1)
            surface.blit(text, (bar.rs_getPos('right') - text.get_width() - 2, 
                                bar.rs_getPos('bottom') - text.get_height() / 2))

            if self.i_playerStats[stat][0] < self.i_playerStats[stat][1]:
                re_text = self.tk_renderText(self.ms_font_16, 'Replenish!', 1, 
                                            (0xff, 0x0, 0x40 + 0x80 * abs(self.tk_sin(self.menu_timer[1]()))), shadow=1)

                surface.blit(re_text, (bar.rs_getPos('left') + 2, bar.rs_getPos('top') - re_text.get_height() / 2))

                # Refill if needed
                if bar.rs_hover_over(kw['hover']):
                    if kw['click']: bar.rs_click()

        # Credits
        surface.blit(*self.ms_creditsIcon.rs_renderSurface(position=1))
        credits = self.ms_font_16.render('{:,} cr.'.format(self.i_playerStats['credits']), 1, (0xff, 0x0, 0x80)) 

        surface.blit(credits, (self.ms_creditsIcon.rs_getPos('left') - credits.get_width() - 8,
                               self.ms_creditsIcon.rs_getPos('centery') - credits.get_height() / 2))
    
    
    def ms_highlight_option(self, x, y, icon_d, surface):
        """
            Highlight icon

            x, y -> Position
            icon_d -> Icon dimensions
            surface -> Surface which to draw on to

            return -> None

        """
        t = abs(self.tk_sin(self.menu_timer[1]()))
        x1, y1 = x - 2 * t, y - 2 * t
        x2, y2 = (x + icon_d[0] - 1) + 2 * t, (y + icon_d[1] - 1) + 2 * t

        self.tk_draw_aalines(surface, (0xff, 0x0, 0x80), 0, ((x1, y1 + 16), (x1, y1), (x1 + 16, y1)), 1)
        self.tk_draw_aalines(surface, (0xff, 0x0, 0x80), 0, ((x2, y2 - 16), (x2, y2), (x2 - 16, y2)), 1)

        #self.tk_draw_circle(surface, (0xff, 0xff, 0xff), tl, 2)
        #self.tk_draw_circle(surface, (0xff, 0xff, 0xff), br, 2)

    
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
        goggles = self.tk_scaleSurface(self.ElementTextures[2], self.menu_scale) 
        _s = bg.copy()
        _s.blit(goggles, (csurf_64_d[0] / 2 - goggles.get_width() / 2, 
                          csurf_64_d[1] / 2 - goggles.get_height() / 2))

        self.ms_sIcons['mod_laser'] = RectSurface(_s, snd_hover_over=181, snd_click=184) 

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
    def __init__(self):
        pass

    def run(self, surface):
        while 1:
            surface.fill(self.tk_bg_color)

            for event in self.tk_eventDispatch():
                pass

            self.tk_display.flip() 


class MenuOptions(PagesHelp):
    def __init__(self):
        self.mo_font = self.tk_font(self.ElementFonts[1], int(24 * self.menu_scale))
        self.mo_gui_id = -1

        self.mo_gui_func = {0: self.mo_sound_settings,
                            1: self.mo_userkeys_settings}


    def run(self, surface):

        while 1:
            surface.fill(self.tk_bg_color)

            for event in self.tk_eventDispatch():
                
                if event.type == self.tk_event_mouseup:
                    print 'Yeah?'


            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))

            self.tk_display.flip()

    
    def mo_sound_settings(self, surface):
        """
            Edit music/effects volumes

            return -> None

        """
        pass

    
    def mo_userkeys_settings(self, surface):
        """
            TBD

            return -> None

        """
        pass


class MenuReport(PagesHelp):
    def __init__(self):
        self.mr_rating_ranks = {20: "Drive-By",
                                40: "",
                                60: "Firearm Instructor",
                                80: "",
                                100: "47, Is That You?"}


    def run(self, surface):
        while 1:
            surface.fill(self.tk_bg_color)

            for event in self.tk_eventDispatch():
                pass

            surface.blit(*self.tk_drawCursor(self.ElementCursors[1]))

            self.tk_display.flip()


class MenuManager(object):
    # 'MenuMain' should be the first function call'd

    def __init__(self):
        PagesHelp.ph_initData()
        
        self.all_menus = {0: MenuIntro(),
                          1: MenuMain(),
                          2: MenuCampaign(),
                          3: MenuShop(),
                          4: MenuIntroOutro(),
                          5: MenuOptions(),
                          6: MenuReport()}



if __name__ == '__main__':
    pass 
