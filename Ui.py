from ConfigsModule import GlobalGameData
from TextureLoader import uiElements
from Weapons import Weapons
from EventManager import EventManager
from Inventory import Inventory
from VictoryCondition import VictoryCondition, BookKeeping


__all__ = 'uiOverlay', 'uiGameTimer' 

# NOTE: Replace the hardcoded shit with more robust system


class uiGameTimer(GlobalGameData, BookKeeping):

    # Note: Rename ui to hud
    hud_data = {'g_timer':      None,        # Game timer
                'g_timer_bg':   None,        # Decorative
                'g_timer_fg':   None,        # - || -
                'g_timer_text':[None, None], # Rendered timer surface
                'g_font':       None}        # Font used to render

    
    @classmethod
    def tick_timer(cls, reset=False):
        """
            Tick the timer and update the timer surface 

            return -> None

        """
        if not cls.i_playerStats['alive']:
            return None

        color = 0xff, 0x0, 0x0
        if reset: 
            cls.hud_data['g_timer'].reset()
        else:
            if not cls.task_record['complete']:
                cls.hud_data['g_timer'] += 1
            else:
                # Highlight the color
                color = 0xff, 0x0, 0x80

        seconds = cls.hud_data['g_timer']()
        time_out = cls.tk_seconds_to_hms(seconds, to_string=True)
        
        cls.hud_data['g_timer_text'][0] = cls.tk_renderText(cls.hud_data['g_font'], time_out, True, color, shadow=1)  

    
    @classmethod
    def render_timer(cls, surface):
        """
            Render the timer

            surface -> Active screen surface

            return -> None

        """
        surface.blit(*cls.hud_data['g_timer_bg'])
        
        # Get the position for aligning the objective msg under it
        blit, pos = cls.hud_data['g_timer_fg'] 
        surface.blit(blit, pos)
        
        surface.blit(*cls.hud_data['g_timer_text'])

        # Render objective under the timer
        if not cls.task_record['complete']:
            obj_tex = cls.victory_data['msg_objective'] 
            surface.blit(obj_tex, (cls.tk_res_half[0] - obj_tex.get_width() / 2, pos[1]))

    
    @classmethod
    def setup_timer(cls, font):
        """
            Setup/Initialize timer

            font -> font used to render the timer

            return -> None

        """
        cls.hud_data['g_font'] = font
        cls.hud_data['g_timer'] = cls.tk_counter(0)

        # Get size estimations for the timer
        ew, eh = font.size('99:99:99')

        # Background
        bg = cls.tk_gradient_rect(ew + 32, eh, (0xff, 0x0, 0x0), 0xaa, length=16)
        bg_pos = cls.tk_res_half[0] - bg.get_width() / 2, 0 
        cls.hud_data['g_timer_bg'] = bg, bg_pos

        # Decoration line
        fg = cls.tk_gradient_rect(ew + 64, 2, (0xff, 0x0, 0x0), 0xaa) 
        fg_pos = cls.tk_res_half[0] - fg.get_width() / 2, bg.get_height()   
        cls.hud_data['g_timer_fg'] = fg, fg_pos

        # Timer font surface
        cls.hud_data['g_timer_text'] = [None, None]
        cls.tick_timer() 
        cls.hud_data['g_timer_text'][1] = cls.tk_res_half[0] - cls.hud_data['g_timer_text'][0].get_width() / 2, 0 


    
class uiOverlay(uiElements, EventManager, Inventory, uiGameTimer, VictoryCondition):

    # Flash the healthbar when health is equal or lower
    __healthCriticalThreshhold = 30
    
    def __init__(self):            
        # NOTE: Most of these hardcoded stuff is for the textures which do not scale with resolution (in-game)
        
        self.font_0 = self.tk_font(self.ElementFonts[0], 20)
        self.font_1 = self.tk_font(self.ElementFonts[0], 24)
        self.font_2 = self.tk_font(self.ElementFonts[0], 40)

        self.setup_timer(self.font_0)
        
        # Decorations ----

        # Weapon 
        self.olWeaponElem = self.tk_draw_rounded_rect(64 + 8, 64 + 8, 10, (0xcc, 0x0, 0x0), 0x90, 
                                                      ipad=8, anchor_pos=(4, self.tk_resolution[1] - 84))
        
        # Ammo 
        self.olAmmoElem = self.tk_draw_rounded_rect(128 + 8, 32 + 8, 10, (0xcc, 0x0, 0x0), 0x90,
                                                    ipad=8, anchor_pos=(4, self.tk_resolution[1] - 136))

        self.tk_draw_aaline(self.olAmmoElem[0], (0xff, 0x0, 0x0), (48, 8), (48, 39))    # Separation of icon and ammo count
        self.AmmoBar = self.tk_surface((80, 28), self.tk_srcalpha)
        self.AmmoBar.fill((0x80, 0x0, 0x0, 0xaa))
        
        # Health and armor bg
        self.olHpArmsElem = self.tk_draw_rounded_rect(144 + 8, 64 + 8, 10, (0xcc, 0x0, 0x0), 0x90,
                                                      ipad=8, anchor_pos=(88, self.tk_resolution[1] - 84))
        
        # Decoration for the health and armor slot (Endcaps)
        self.tk_draw_aaline(self.olHpArmsElem[0], (0xff, 0x0, 0x0), (44,  11), (44,  38))   # Health endcaps
        self.tk_draw_aaline(self.olHpArmsElem[0], (0xff, 0x0, 0x0), (146, 11), (146, 38))

        self.tk_draw_aaline(self.olHpArmsElem[0], (0xff, 0x0, 0x0), (44,  43), (44,  70))   # Armor endcaps
        self.tk_draw_aaline(self.olHpArmsElem[0], (0xff, 0x0, 0x0), (146, 43), (146, 70))

        # Health 
        self.healthBar = self.tk_surface((96, 28), self.tk_srcalpha)
        self.heartBeatCycle = self.tk_cycle(self.__heartBeatGenerator())
        # Generate the sin table for the heartbeat effect generator
        self.heartBeatTable = [self.tk_sin(self.tk_radians(x)) for x in xrange(0, 360, 10)]

        self.healthBarCriticalCycle = self.tk_cycle(self.tk_chain(xrange(0, 128, 4), xrange(128, 0, -4)))
        self.healthBarCritical = self.tk_surface((96, 28), self.tk_srcalpha)
        self.healthBarCritical.fill((0x80, 0x0, 0x0, 0xaa))

        # Armor 
        self.armorBar = self.tk_surface((96, 28), self.tk_srcalpha)
        self.armorBar.fill((0x80, 0x0, 0x0, 0xaa))

        #self.playerDeath = self.font_2.render("You Are Dead", True, (0xff, 0x0, ))
        self.playerDeath = self.tk_renderText(self.font_2, "You Are Dead", True, (0xff, 0x0, 0x0), shadow=1)

        # Weapon slots available
        base_surf = self.tk_draw_rounded_rect(32, 32, 4, (0xcc, 0x0, 0x0), 0x90)
        bw, bh = base_surf.get_size()
        bw /= 2; bh /= 2

        self.avai_wpn_slots = {}
        for key in xrange(1, len(self.tk_slots_available) + 1):
            # Weapon in the wheel
            base_copy = base_surf.copy()
            key_slot = self.tk_renderText(self.font_0, str(key), True, (0xff, 0x0, 0x80), shadow=1)
            base_copy.blit(key_slot, (bw - key_slot.get_width() / 2, bh - key_slot.get_height() / 2))
            self.avai_wpn_slots[key] = base_copy

            # No weapon in the wheel
            base_copy = base_surf.copy()
            key_slot = self.tk_renderText(self.font_0, str(key), True, (0x80, 0x0, 0x0), shadow=1)
            base_copy.blit(key_slot, (bw - key_slot.get_width() / 2, bh - key_slot.get_height() / 2))
            self.avai_wpn_slots[-key] = base_copy

        # Ui Events
        EventManager.__init__(self)
        self.Event_newEvent(1000, self.tick_timer)
        self.Event_newEvent(2, self.__flashGenerator)


    def __heartBeatGenerator(self):
        """
            Create an 'Heartbeat' between delays

            return -> Generator

        """
        # Full 360 heartbeat
        if self.i_playerStats['alive']:
            for beat in self.heartBeatTable:
                yield beat    
        
        # Rest time between heartbeats (Read player's health)
        for rest in xrange(min(72, max(8, self.i_playerStats['health'][0]))):
            yield 0

        yield None  # Do an action between the beat and at start of rest
    

    def __flashGenerator(self):
        """
            Update overlays visual effects

            return -> None

        """
        beat = self.heartBeatCycle.next()
        if beat is None:
            # Restart the cycle 
            self.heartBeatCycle = self.tk_cycle(self.__heartBeatGenerator())
            return beat
        
        # Convert the sine wave to triangle wave
        beat = int(self.tk_asin(beat) * 6)
        
        # Health is critical, flash the healthbar : Redo this
        if self.i_playerStats['health'][0] <= self.__healthCriticalThreshhold:
            critical = self.healthBarCriticalCycle.next()
            self.healthBarCritical.fill((0xaa, 0x0, critical, critical))
        else:
            self.healthBarCritical.fill((0xaa, 0x0, 0x0, 0x0))

        self.tk_draw_circle(self.healthBar, (0xff, 0x0, 0x0), (93, 14 + beat), 2)
        self.healthBar.scroll(-1, 0)


    def drawOverlay(self, surface, **kw):
        """
            Draw the overlay during gameplay

            surface -> Surface to draw the overlay on

            return -> None

        """
        if self.task_record['complete'] and self.level_report['time'] is None:
            self.getSetRecord('time', self.hud_data['g_timer']())
            self.tick_timer()

        self.render_timer(surface)     

        # Weapon
        surface.blit(*self.olWeaponElem[:2])
        surface.blit(self.all_weapons_data[self.i_playerStats['weapon']][1], self.olWeaponElem[2])

        # Health/Armor bars
        bar_bg, bar_bg_pos = self.olHpArmsElem[:2] 
        surface.blit(bar_bg, bar_bg_pos)
        
        pos = self.olHpArmsElem[2]
        surface.blit(self.ElementTextures[0], pos)                          
        surface.blit(self.healthBarCritical, (pos[0] + 40, pos[1] + 3))     
        surface.blit(self.healthBar,         (pos[0] + 40, pos[1] + 3))    
        
        armor_pos = pos[0] + 40, pos[1] + 35
        surface.blit(self.armorBar, armor_pos) 
        armor_bar_length = self.armorBar.get_width() 
        armor_left = (self.i_playerStats['armor'][1] / armor_bar_length) * self.i_playerStats['armor'][0]
        armor_bar = (armor_pos[0], armor_pos[1],
                     min(armor_bar_length, armor_left),
                     self.armorBar.get_height()) 
        
        self.tk_draw_gfx_rect(surface, armor_bar, (0x10, 0x10, 0xaa, 0x80))
        
        # Health text (Separated from the blit to get the size of the string, so it can be anchored by the right side)
        text_surf = self.tk_renderText(self.font_0, str(int(self.i_playerStats['health'][0])), 
                    1, (0xff, 0x0, 0x0), shadow=1) 
        surface.blit(text_surf, (pos[0] + 134 - text_surf.get_width(), pos[1] + 16))
        
        # Armor text
        text_surf = self.tk_renderText(self.font_0, str(int(self.i_playerStats['armor'][0])), 
                    1, (0xff, 0x0, 0x0), shadow=1)
        surface.blit(text_surf, (pos[0] + 134 - text_surf.get_width(), pos[1] + 48))  

        # Weapons with infinite ammo, do not need the ammo gui element
        ammo_id = self.all_weapons_data[self.i_playerStats['weapon']][0]
        if ammo_id != -1: self.drawOverlayAmmo(surface, ammo_id)

        # Draw available weapon slots
        base_y = self.tk_resolution[1] - 2 
        base_x = bar_bg_pos[0] + bar_bg.get_width() - 6 
        base_x_def = bar_bg_pos[0] + bar_bg.get_width() - 6 

        for key in xrange(1, len(self.tk_slots_available) + 1):
            wpn_wheel = 'w_{}'.format(key)

            surf = self.avai_wpn_slots[key if len(self.i_playerStats[wpn_wheel]) > 0 else -key] 
            surface.blit(surf, (base_x, base_y - surf.get_height()))
            
            base_x += surf.get_width() + 2
            if key == 3: 
                base_y -= surf.get_height() + 2
                base_x = base_x_def 
             
        surface.blit(*self.tk_drawCursor(self.ElementCursors[0]))

        if not self.i_playerStats['alive']:
            surface.blit(self.playerDeath, (self.tk_res_half[0] - self.playerDeath.get_width()  / 2, 
                                            self.tk_res_half[1] - self.playerDeath.get_height() / 2 - 32))

        hud_token = {'victory': self.check_if_victory_achieved(surface, quick_exit_key=kw['escape']) \
                                if self.i_playerStats['alive'] else None,
                     'death':   self.i_playerStats['alive']}

        return hud_token

    
    def drawOverlayAmmo(self, surface, ammo_id):
        """
            Render ammo icon/count if needed

            ammo element doesn't get rendered if ammo_id is -1 (Infinite ammo)

            return -> None
        """
        # Ammo text
        surface.blit(*self.olAmmoElem[:2])
        pos = self.olAmmoElem[2] 
        surface.blit(self.all_ammo_data[ammo_id][2], pos)       # Ammo Icon
        surface.blit(self.AmmoBar, (pos[0] + 48, pos[1] + 2))   # Ammo Count bg

        # Ammo count text (Limit the bullet count rendering to 99999)
        ammo_count_surf = self.tk_renderText(self.font_1, str(min(int(self.i_playerAmmo[ammo_id]), 99999)), 
                                             1, (0xff, 0x0, 0x0), shadow=1) 
        
        surface.blit(ammo_count_surf, ((pos[0] + 48) + self.AmmoBar.get_width() / 2 - ammo_count_surf.get_width() / 2, 
                                        pos[1] + 2))    


if __name__ == '__main__':
    pass
