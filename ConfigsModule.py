#from __future__ import division    # Uncomment this to enable true division across everything that imports this module (Tho something will break)   

import pygame
import pygame.gfxdraw
from pygame.locals import *
import math
import itertools
import random
import multiprocessing
import collections
import os
from Timer import *
from time import strftime
from sys import exit as exit_system
from numpy import copyto, roll, zeros, dot
from numpy import sum as _sum
#from numpy.linalg import norm
from ast import literal_eval
from glob import iglob
from copy import deepcopy


__all__ = ('GlobalGameData', 'TkCounter', 'TkWorldDataShared')


# Note: Replace this shit
class TkCounter(object):
    """
        Small counter 

        Note: Add logging and caching stuff

        instance.reset() -> Resets the counter to init value
        .instance() -> Returns current value
        
    """
    def __init__(self, v): self.__init = v; self.__c = v

    def __iadd__(self, v): self.__c += v; return self

    def __repr__(self): return repr(self.__c)

    def __call__(self): return self.__c

    def m_add(self, v): self.__c += v; return 1

    def reset(self): self.__c = self.__init


class TkWorldDataShared(object):
    
    # Common data shared between classes
    w_share = {'WorldPosition':      (0, 0),    # Up-to-date world position
               'WorldPositionDelta': (0, 0),    # Delta between last and current world position        
               'ShadowOffset':       (0, 0)}    # Used with shadow casting

    @classmethod
    def getWorldIndex(cls):
        """
            Convert the World position to Cell indexes

            return -> World index
        """
        x, y = cls.w_share['WorldPosition']
        x, y = int(-x) + 16 >> 5, int(-y) + 16 >> 5

        return x, y


class TkRect(pygame.Rect):
    """
        Extend the Rect class with the hashing so it can be used as key with dictonaries and sets

    """
    def __hash__(self):
        return hash(tuple(self))
    
    def __repr__(self):
        # Just to make it easier to read. Comment this out, if you need the original rect repr
        return repr('{},{}'.format(self.x, self.y))


class DefaultConfigParser(object):

    __slots__ = ()
    
    __DEFAULT_CONFIG = "default.ini"

    # Read/Write default values
    def_values = collections.OrderedDict([
                    ('max_fps',             60),
                    ('resolution',  (1280, 720)),
                    ('fullscreen',            0),
                    ('control_scheme',        0),
                    ('world_shadows',         1),
                    ('world_char_shadows',    1),
                    ('world_shadows_quality', 1),
                    ('world_footsteps',       1),
                    ('world_effects',         1),
                    ('key_up',              K_w),
                    ('key_right',           K_d),
                    ('key_down',            K_s),
                    ('key_left',            K_a),
                    ('key_esc',        K_ESCAPE),
                    ('key_slot1',           K_1),
                    ('key_slot2',           K_2),
                    ('key_slot3',           K_3),
                    ('key_slot4',           K_4),
                    ('key_slot5',           K_5),
                    ('key_slot6',           K_6),
                    ('ai_rotation_speed',     4),
                    ('ai_hear_range',        64),
                    ('ai_alarm_state',      1.5),
                    ('ai_idle_hunt',        2.5),
                    ('phy_max_objects',      32),
                    ('phy_linear_damp',  0.0002),
                    ('phy_force_max',        16),
                    ('phy_force_min',         8),
                    ('audio_max_channels',  256),
                    ('audio_buffer_size',   512),
                    ('audio_frequency',   22050),
                    ('audio_mono_or_stereo',  2),
                    ('audio_music_level',   1.0),
                    ('audio_effect_level',  1.0)]) 

    @classmethod
    def tk_readFile(cls, _file, mode='r', comment='#', keyValue_delimiter='='):
        """
            Open and handle file reading/writing
            Skips lines with comment sign and empty lines
            Handles key/value separation

            _file -> Filename
            mode -> In which mode the file is being worked on
            comment -> Skips lines beginning with this comment char
            keyValue_delimiter -> char which acts as splitter to separate key/value 

            return -> Generator over lines

        """
        with open(_file, mode) as rcfg:
            for read in rcfg:
                # Line starts with comment, skip
                if read.startswith(comment): continue
                
                line = read.strip()
                # Line is empty, skip
                if not line: continue
                
                # Remove all whitespace in the line and separate the key/value
                line = line.replace(' ', '').split(keyValue_delimiter)

                yield line

    
    @classmethod
    def tk_ParseDefaultConfigs(cls, force_rewrite=False):
        """
            Parse configs for the game specific settings

            return -> None
        """
        # Check if file exists. If not rebuild it
        if not os.path.isfile(cls.__DEFAULT_CONFIG) or force_rewrite:
            with open(cls.__DEFAULT_CONFIG, 'w') as w:
                for key, value in cls.def_values.iteritems():
                    w.write("{}={}\n".format(key, value))
        
        # Read and parse
        else:
            with open(cls.__DEFAULT_CONFIG, 'r') as r:
                for line in cls.tk_readFile(cls.__DEFAULT_CONFIG):
                    key, value = line
                    if key in cls.def_values:
                        cls.def_values[key] = literal_eval(value)



class GlobalGameData(DefaultConfigParser):
    """
        Provide the basegame option variables and most used functions 
    """
    __slots__ = ()

    DefaultConfigParser.tk_ParseDefaultConfigs()
    # Should capitalize more and separate the enums to different section


    # Special 
    tk_name     = 'Wastadium'
    tk_dev_name = 'JaaTeam'
    tk_version  = '1.0'
    tk_fullscreen = pygame.FULLSCREEN if DefaultConfigParser.def_values['fullscreen'] else 0 
    tk_fps        = DefaultConfigParser.def_values['max_fps']
    tk_resolution = DefaultConfigParser.def_values['resolution']
    tk_resolution_scale = max(float(tk_resolution[0]) / float(1280), 
                              float(tk_resolution[1]) / float(720))
    tk_res_half = tk_resolution[0] / 2, tk_resolution[1] / 2
    tk_bg_color = 0x0, 0x0, 0x0
    tk_macro_cell_size = 8    # Dont change this.
    tk_entity_sector_s = 2    # Dont change this.
    
    # Map effect 
    tk_static_shadow_color = 0x14, 0x14, 0x14, 0x80
    tk_ambient_color_tone  = 0xcc, 0xcc, 0xcc
    tk_blend_rgba_mult = pygame.BLEND_RGBA_MULT
    tk_blend_rgba_add  = pygame.BLEND_RGBA_ADD
    tk_blend_rgba_sub  = pygame.BLEND_RGBA_MAX

    # Weapon and casing related
    tk_bullet_trail_color = 0xff, 0xff, 0x0, 0xff
    tk_casing_rleaccel = pygame.RLEACCEL

    # Option 
    #tk_no_effect_layer  = 0     # Partially used. Explain where/why
    tk_no_shadow_layer  = not DefaultConfigParser.def_values['world_shadows']
    tk_no_footsteps     = not DefaultConfigParser.def_values['world_footsteps']
    tk_no_effects       = not DefaultConfigParser.def_values['world_effects']
    tk_no_char_shadows  = not DefaultConfigParser.def_values['world_char_shadows']
    
    # 0: Axis, 1: Tank
    tk_control_scheme = DefaultConfigParser.def_values['control_scheme'] 
    
    # 1: High quality (Experimental and Slow) 
    # Actually, the entire shadow casting is shit(Needs massive overhaul)
    tk_shadow_quality = DefaultConfigParser.def_values['world_shadows_quality']     
    
    # Lightmap 
    tk_shadow_color      = 0x0, 0x0, 0x0, 0xaa
    tk_shadow_mask_color = 0x0, 0x0, 0x0, 0xaa

    res_x = int(math.ceil(float(float(tk_resolution[0] / 2) / 32)))
    res_x |= ~res_x & 1     # Check and make sure x is odd     
    tk_shadow_minmax_x = res_x - 1, res_x
    
    res_y = int(math.ceil(float(float(tk_resolution[1] / 2) / 32)))
    res_y |= ~res_y & 1     # Check and make sure y is odd    
    tk_shadow_minmax_y = res_y - 1, res_y  

    del res_x, res_y   
    
    # General
    tk_ceil      = math.ceil
    tk_floor     = math.floor  
    tk_atan2     = math.atan2
    tk_pi        = math.pi
    tk_pi2       = math.pi * 2
    tk_sin       = math.sin
    tk_cos       = math.cos
    tk_sqrt      = math.sqrt
    tk_exp       = math.exp
    tk_hypot     = math.hypot
    tk_radians   = math.radians
    tk_degrees   = math.degrees
    tk_asin      = math.asin    
    tk_acos      = math.acos     
    tk_cycle     = itertools.cycle
    tk_chain     = itertools.chain
    tk_izip_long = itertools.izip_longest
    tk_choice    = random.choice
    tk_randrange = random.randrange
    tk_uniform   = random.uniform
    tk_sample    = random.sample
    tk_shuffle   = random.shuffle
    
    #tk_event_trigger = EventTrigger
    #tk_countdown_trigger = EventTriggerCountDown
    #tk_event_trigger_cons = EventTriggerConstant
    
    tk_trigger_hold  = MsHoldTrigger
    tk_trigger_const = MsDelayTrigger
    tk_trigger_down  = MsCountdownTrigger
    
    tk_strftime     = strftime
    tk_path         = os.path
    tk_environ      = os.environ
    tk_deque        = collections.deque
    tk_namedtuple   = staticmethod(collections.namedtuple)
    tk_ordereddict  = collections.OrderedDict
    tk_np_roll      = staticmethod(roll)     
    tk_np_copyto    = copyto
    tk_np_sum       = staticmethod(_sum) 
    tk_np_dot       = dot
    tk_quit_system  = exit_system
    tk_counter      = TkCounter
    tk_literal_eval = staticmethod(literal_eval)
    tk_iglob        =  staticmethod(iglob)
    tk_deepcopy     = deepcopy

    
    # Pygame
    tk_init               = pygame.init
    tk_display            = pygame.display 
    tk_time               = pygame.time
    tk_mouse_pos          = pygame.mouse.get_pos
    tk_mouse_vis          = pygame.mouse.set_visible
    tk_mouse_pressed      = pygame.mouse.get_pressed
    tk_mouse_focus        = pygame.mouse.get_focused
    tk_rotozoom           = pygame.transform.rotozoom
    tk_rotate             = pygame.transform.rotate
    tk_flip               = pygame.transform.flip
    tk_smoothscale        = pygame.transform.smoothscale
    tk_key_pressed        = pygame.key.get_pressed
    tk_key_name           = pygame.key.name
    tk_get_mods           = pygame.key.get_mods 
    tk_set_mods           = pygame.key.set_mods
    tk_draw_line          = pygame.draw.line
    tk_draw_lines         = pygame.draw.lines
    tk_draw_aaline        = pygame.draw.aaline
    tk_draw_aalines       = pygame.draw.aalines
    tk_draw_circle        = pygame.draw.circle
    tk_draw_polygon       = pygame.draw.polygon
    tk_draw_arc           = pygame.draw.arc
    tk_draw_rect          = pygame.draw.rect
    tk_draw_gfx_polygon   = pygame.gfxdraw.filled_polygon 
    tk_draw_gfx_line      = pygame.gfxdraw.line
    tk_draw_gfx_circle    = pygame.gfxdraw.filled_circle
    tk_draw_gfx_rect      = pygame.gfxdraw.box
    tk_draw_gfx_aacircle  = pygame.gfxdraw.aacircle
    tk_draw_gfx_aapolygon = pygame.gfxdraw.aapolygon
    tk_quit               = pygame.quit
    tk_surface            = pygame.Surface
    tk_rect               = TkRect
    tk_srcalpha           = pygame.SRCALPHA
    tk_surfarray          = pygame.surfarray
    tk_image              = pygame.image
    tk_font               = pygame.font.Font


    # Expand more slots for 1 - 9 keys (Don't go over bound)
    tk_slots_available = [key_v for key_v in \
    DefaultConfigParser.def_values.iterkeys() if key_v.startswith('key_slot')]

    # Player (Allow for customization) 
    tk_user = {'up':    DefaultConfigParser.def_values['key_up'], 
               'left':  DefaultConfigParser.def_values['key_left'], 
               'down':  DefaultConfigParser.def_values['key_down'], 
               'right': DefaultConfigParser.def_values['key_right'], 
               'esc':   DefaultConfigParser.def_values['key_esc']}

    tk_user.update({key.split('_')[-1]: DefaultConfigParser.def_values[key] for key in tk_slots_available})
    tk_slots_available = sorted([k for k in tk_user.iterkeys() if k.startswith('slot')])

    # Fixed keys (Maybe put these for edit too?)
    tk_user_special = {'shift_l': KMOD_LSHIFT, 'ctrl_l': KMOD_LCTRL}

    # Event
    tk_event_pump      = pygame.event.pump
    tk_event           = pygame.event
    tk_event_quit      = QUIT
    tk_event_keydown   = KEYDOWN
    tk_event_keyup     = KEYUP
    tk_event_mouseup   = MOUSEBUTTONUP
    tk_event_mousedown = MOUSEBUTTONDOWN
    tk_uEvent          = pygame.USEREVENT
    tk_uEventMax       = pygame.NUMEVENTS

    # Audio 
    tk_mixer              = pygame.mixer
    tk_mixer_music        = pygame.mixer.music
    tk_audio_max_channels = DefaultConfigParser.def_values['audio_max_channels']
    tk_audio_buffersize   = DefaultConfigParser.def_values['audio_buffer_size']
    tk_audio_frequency    = DefaultConfigParser.def_values['audio_frequency']
    tk_audio_channel      = DefaultConfigParser.def_values['audio_mono_or_stereo']

    # AI related
    tk_enemy_turn_speed    = DefaultConfigParser.def_values['ai_rotation_speed']
    tk_enemy_hearing_dist  = DefaultConfigParser.def_values['ai_hear_range']
    tk_enemy_alarm_state   = DefaultConfigParser.def_values['ai_alarm_state']
    tk_enemy_waypoint_get  = DefaultConfigParser.def_values['ai_idle_hunt']
    tk_enemy_safe_distance = tk_hypot(32, 32)   # Waypoint radius to stop at

    # Gib Physics
    tk_gib_max_gibs    = DefaultConfigParser.def_values['phy_max_objects']
    tk_gib_linear_damp = DefaultConfigParser.def_values['phy_linear_damp']
    tk_gib_force_max   = DefaultConfigParser.def_values['phy_force_max']
    tk_gib_force_min   = DefaultConfigParser.def_values['phy_force_min']


    @classmethod
    def tk_scaleSurface(cls, surface, scale):
        """
            Scale surface by float

            surface -> Surface to be operated on
            scale -> float 

            return -> Surface

        """
        w, h = surface.get_size()
        return cls.tk_smoothscale(surface, (int(w * scale), int(h * scale)))

    
    @classmethod
    def tk_boundaryCheck(cls, x, y, limit):
        """
            Check if x, y are within boundaries

            x, y -> values
            limit -> Check within these limits(Upper boundary)(0 is lower by default)

            return -> Bool
        """
        return -1 < x < limit[0] and -1 < y < limit[1]

    
    @classmethod
    def tk_clamp(cls, v, vmin, vmax):
        """
            Clamp v between vmin, vmax

            v -> Value
            vmin, vman -> Min, max values

            return -> Clamped value
        """
        return max(vmin, min(vmax, v))


    @classmethod
    def tk_distortSurface(cls, surface, dist_effect_ids):
        """
            Distort target surface with effects

            surface -> Target surface
            dist_effect_id -> (int) Which effect to apply (Chain multiple effects via bitwise) 

            return -> None

        """
        surf = cls.tk_surfarray.pixels2d(surface)

        if dist_effect_ids & 1:
            cls.tk_np_copyto(surf[::2, ::2], cls.tk_np_roll(surf[::2, ::2], 6))

        if dist_effect_ids & 2:
            pass 

        return surface   


    @classmethod
    def tk_seconds_to_hms(cls, seconds, to_string=False):
        """
            Translate seconds to hours, minutes, seconds

            seconds -> seconds

            return -> (hours, minutes, seconds)
        """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if to_string:
            return "{:02d}:{:02d}:{:02d}".format(h, m, s)
        else:
            return h, m, s


    @classmethod
    def tk_quitgame(cls):
        """
            Quits the Pygame/System

            return -> None

        """
        # Add "Are you sure you want to quit" here?
        cls.tk_quit(); cls.tk_quit_system()


    @classmethod
    def tk_eventDispatch(cls):
        """
            Return events from the event queue

            handles quit event automatically

            return -> Generator over events

        """
        cls.tk_event_pump()
        for event in cls.tk_event.get():
            if event.type == cls.tk_event_quit:
                cls.tk_quitgame()
            else:
                yield event 


    @classmethod
    def tk_drawCursor(cls, cursor):
        """
            Draw cursor

            cursor -> (surface, offsetx, offsety)

            return -> surface, (x, y)
            
        """
        mx, my = cls.tk_mouse_pos()
        return cursor[0], (mx - cursor[1], my - cursor[2])


    @classmethod
    def tk_drawOriginCross(cls, surface, pos, line_color=(0xff, 0xff, 0x0), circle_color=(0xff, 0x0, 0x0)):
        """
            Draw small origin cross

            surface -> surface which to draw on
            pos -> Position on the surface

            return -> None

        """
        cls.tk_draw_circle(surface, circle_color, (int(pos[0]), int(pos[1])), 8)
        cls.tk_draw_line(surface, line_color, (pos[0], pos[1] - 8), (pos[0], pos[1] + 8), 1)
        cls.tk_draw_line(surface, line_color, (pos[0] - 8, pos[1]), (pos[0] + 8, pos[1]), 1)


    @classmethod
    def tk_PolarToCartesian(cls, org_x, org_y, angle, dist):
        """
            Polar to cartesian

            org_x, org_y -> x, y of the origin the offset is rotating around
            angle -> in Radians 
            dist -> Polar hypot

            return -> Corrected offset x, y

        """
        # Note: Use this function more often. There's too many converts 
        
        # Turn angle + offset angle to x, y point around the origin 
        new_x = org_x - cls.tk_sin(angle) * dist 
        new_y = org_y - cls.tk_cos(angle) * dist
        return new_x, new_y

    
    @classmethod
    def tk_rotateImage(cls, image, angle, rect, fast_rot=0):
        """
            Takes image and rotates it by the angle
            while maintaining proper center

            image -> Image about to be rotated
            angle -> Angle in degrees
            rect -> rect of the image to be used as boundaries for the image
            fast_rot -> Use faster but uglier rotate

            (Rotation is quite expensive to call in realtime)

            return -> Image rotated by angle

        """
        if fast_rot: rot_image = cls.tk_rotate(image, angle)
        else: rot_image = cls.tk_rotozoom(image, angle, 1.0)
        
        rect.center = rot_image.get_rect().center
        return rot_image.subsurface(rect).copy()

    
    @classmethod
    def tk_renderText(cls, font, text, anti_alias, color, flags=0, shadow=False, shadow_color=(0x0, 0x0, 0x0)):
        """
            Convert str to surface text which can be draw for display

            font -> From which font object the text is rendered from
            text -> Text converted to surface with the text on it
            flags -> Control how the text is formatted
                     1: Underline
                     2: bold
                     4: italic
                     # Can be grouped up via bitwise |

            return -> Surface with the text on it

        """
        # Copied from pygame doc !
        # ---
        # The render can emulate bold or italic features, 
        # but it is better to load from a font with actual italic or bold glyphs. 
        # The rendered text can be regular strings or unicode.
        # ---
        
        # I included them just in-case via bitwise flags
        # These really need enum style flag names
        if flags != 0:
            font.set_underline(flags & 1)
            font.set_bold(flags & 2)
            font.set_italic(flags & 4)

        if shadow:
            surf = cls.tk_surface(font.size(text), cls.tk_srcalpha)
            surf.blit(font.render(text, anti_alias, shadow_color), (-2, 2))
            surf.blit(font.render(text, anti_alias, color), (0, 0))
            return surf
        else: 
            return font.render(text, anti_alias, color)

    
    @classmethod
    def tk_draw_rounded_rect(cls, w, h, r, color, alpha, anti_aliasing=True, ipad=0, anchor_pos=None):
        """
            Draw rect with rounded edges

            w -> width
            h -> height
            r -> radius of the corners
            color -> color of the rect 
            alpha -> alpha level of the rect 0 -> 255
            anti_aliasing -> Add antialiasing to the r_rect NOTE: Keep the dimensions small! It's un-optimized

            return -> Surface

        """
        # Final output surface
        surf = cls.tk_surface((w + ipad + r, h + ipad + r), cls.tk_srcalpha)

        # Draw 4 circles in each corner to create the rounded edges
        [cls.tk_draw_circle(surf, color, (x, y), r) \
         for x, y in ((r, r), (w, r), (r, h), (w, h))]

        # Draw 2 rects connecting the 4 corner circles
        cls.tk_draw_rect(surf, color, (r, 0, w - r, h + r))
        cls.tk_draw_rect(surf, color, (0, r, w + r, h - r))

        surf = cls.tk_set_surface_alpha(surf, alpha)

        if anti_aliasing: surf = cls.tk_blur_surface(surf, alpha)

        if anchor_pos is not None:
            padded_anchor = anchor_pos[0] + ipad, anchor_pos[1] + ipad
            return surf, anchor_pos, padded_anchor
        else:
            return surf


    @classmethod
    def tk_set_surface_alpha(cls, surface, alpha):
        """
            Set the alpha level of the surface

            surface -> target surface
            alpha -> 0 - 255

            return -> Surface with the alpha changes

        """
        surf = surface.copy()
        
        alpha_surf = cls.tk_surfarray.pixels_alpha(surf)
        alpha_surf[alpha_surf > 0] = alpha

        return surf

    
    @classmethod
    def tk_blur_surface(cls, surface, alpha=0):
        """
            Apply blur to surface

            surface -> Surface to be blurred
            alpha -> Alpha level of the surface

            return -> Surface

        """  
        # Note: Optimize this (Replace with: https://www.pygame.org/docs/tut/SurfarrayIntro.html soften)
        
        alpha_surf = cls.tk_surfarray.pixels_alpha(surface) 
        w, h = surface.get_size()  

        padded = zeros((w + 2, h + 2), dtype=int)
        padded[1:-1, 1:-1] = alpha_surf     # Add the original array to the middle of the padded array

        no_op = alpha * 9
        
        for py in xrange(h):
            for px in xrange(w):
                # Get a sample using 3x3 kernel
                sample = padded[px:3 + px, py:3 + py]
                
                # Only go through pixels which kernel middle alpha value is more than 0
                if not sample[1][1]: continue 
                
                # Calculate the median alpha value from surrounding alpha values
                mean = cls.tk_np_sum(sample)

                # All values are the same within kernel, continue
                if mean == no_op: continue

                alpha_surf[px][py] = mean / 9 if mean else 0 

        return surface

    # Helper function to make gradient rect look a bit nicer
    @classmethod
    def tk_tri_corners(cls, w, h, l, color):
        """
            Add triangle to the corners

            w, h -> Size of the surface which gets the corners
            l -> Length of the triangles (Not hypot)
            color -> Color of the triangles (support alpha too)

            return -> Alpha surface with the triangles

        """
        surf = cls.tk_surface((w, h), cls.tk_srcalpha)

        cls.tk_draw_gfx_polygon(surf, ((0, 0), (l, 0), (0, l)), color)
        cls.tk_draw_gfx_polygon(surf, ((w - 1, 0), (w - 1, l), ((w - 1) - l, 0)), color)
        cls.tk_draw_gfx_polygon(surf, ((0, h - 1), (0, (h - 1) - l), (l, (h - 1))), color)
        cls.tk_draw_gfx_polygon(surf, ((w - 1, h - 1), ((w - 1) - l, (h - 1)), ((w - 1), (h - 1) - l)), color)

        return surf

    
    @classmethod
    def tk_gradient_rect(cls, w, h, color, alpha, invert=False, both_sides=False, length=8, cut_corners=False):
        """
            Draw gradient rect with left and right side faded out

            w,h -> Width, Height
            color -> Color of the surface
            alpha -> Max alpha of the surface
            invert -> invert the grading
            both_sides -> Do gradient on both x, y
            length -> Length of the gradient

            return -> Surface

        """
        surf = cls.tk_surface((w, h), cls.tk_srcalpha)
        surf.fill(color)

        alpha_surf = cls.tk_surfarray.pixels_alpha(surf)
        alpha_surf[:] = 0 if invert else alpha

        l = 255 / length
        if invert:
            rng = xrange(alpha, 0, -l)
        else:
            rng = xrange(0, alpha, l)
    
        for enum, a in enumerate(rng):
            alpha = cls.tk_clamp(a, 0x0, 0xff) 
            alpha_surf[-enum] = alpha
            alpha_surf[enum]  = alpha

        if both_sides:
            del alpha_surf
            surf.blit(cls.tk_rotate(surf.copy(), 90), (0, 0))   

        if cut_corners:
            surf.blit(cls.tk_tri_corners(w, h, 4, (0x0, 0x0, 0x0, 0xee)), (0, 0))

        return surf 


if __name__ == '__main__':
    pass
