from ConfigsModule import GlobalGameData
from SoundModule import SoundMusic
from _3d_models import Model3D


__all__ = ('RectSurface', 'ScanLineGenerator', 'ActiveBackGround', 'RadialSlider')


# This should be replaced with pygame.sprite.Sprite
class RectSurface(SoundMusic):
    def __init__(self, surface, _id=None, snd_click=None, snd_hover_over=None, func=None):
        self._rs_id = _id
        self.rs_surface = surface
        self.rs_rect = self.rs_surface.get_rect()
        
        # Play this sound que when you click this
        self.rs_snd_click = snd_click           # Sound id
        
        # Play this sound que when you hover over this
        self.rs_snd_hover_over = snd_hover_over # Sound id
        self._rs_snd_hover_over_v = 0           # Control to play once

        # Execute this function when clicked
        self.rs_function = func

    def rs_updateSurface(self, surf):
        self.rs_surface = surf
        self.rs_rect = surf.get_rect()
    
    def rs_renderSurface(self, position=False): return (self.rs_surface, self.rs_rect) if position else self.rs_surface 
    
    
    def rs_updateRect(self, x, y): self.rs_rect.x = x; self.rs_rect.y = y

    
    def rs_hover_over(self, point):
        b = self.rs_rect.collidepoint(point) 
        
        if self.rs_snd_hover_over is not None: 
            if self._rs_snd_hover_over_v and b: self.playSoundEffect(self.rs_snd_hover_over)  
            self._rs_snd_hover_over_v = 0 if b else 1 

        return b

    
    def rs_click(self, *args, **kw):
        if self.rs_snd_click is not None:
            self.playSoundEffect(self.rs_snd_click)

        if self.rs_function is not None:
            return self.rs_function(*args, **kw)


    def rs_getSize(self): return self.rs_surface.get_size()

    def rs_getPos(self, pos): return getattr(self.rs_rect, pos)

    @property
    def rs_id(self): return self._rs_id



class RadialSlider(GlobalGameData):
    def __init__(self, steps, color, radius, map_value, default_value=1.0):
        # Note: Need to rework how the circle is builded to support all ranges of values
        # Currently 64 is your best bet
        self._rs_steps = steps    # 64 Currently works nicely  
        self._rs_ring_points = {}
        self._rs_mask = None
        self._rs_color = color
        self._rs_radius = radius
        self._rs_size = radius * 2 + 4

        # Slider values
        self._rs_value = {'map': map_value}

        # Create the slider mask and steps
        self._rs_create_radial(default_value)

    
    @property
    def rs_size(self): return self._rs_size
    
    @property
    def rs_mask(self): return self._rs_mask

    @property
    def rs_color(self): return self._rs_color
    
    def _rs_create_radial(self, default_value):
        """
            Create the radial slider

            return -> None

        """
        self._rs_mask = self.tk_surface((self._rs_size, self._rs_size), self.tk_srcalpha)
        copy = self._rs_mask.copy() 

        half_mask = self._rs_size / 2

        for enum, ring in enumerate((self._rs_radius, self._rs_radius / 2)):
            steps = []
            for r in xrange(45, 360 + self._rs_steps, 360 / self._rs_steps):
                r = r + 90
                if r > 360 + 45: continue

                r = self.tk_radians(r)
                x = half_mask + self.tk_cos(r) * ring
                y = half_mask + self.tk_sin(r) * ring
                steps.append((x, y))

            # Store points for creating the slider itself
            self._rs_ring_points[enum] = steps

        self._rs_ring_points[1].reverse()   # Reverse the inner-ring to form continues line

        self.tk_draw_lines(self._rs_mask, self._rs_color, 1, self._rs_ring_points[0] + self._rs_ring_points[1], 3)

        self._rs_mask = self.tk_blur_surface(self._rs_mask)    # Blur the mask a little bit(shitty one)
        
        # Value for controlling the slider input/output
        self._rs_value['max'] = len(self._rs_ring_points[0])                             # 
        self._rs_value['val'] = int(self.tk_ceil(self._rs_value['max']) * default_value) # 
        self._rs_value['mul'] = self._rs_value['map'] / self._rs_value['max']            # 
        self._rs_value['adi'] = float(270) / self._rs_value['max']                       # 
        self._rs_value['dva'] = default_value                                            #  

    
    def rs_slide(self, sx, sy, pos):
        """
            Handle the radial slider

            sx, sy -> Position of the handler relative to the slider center (Mouse position most likely)
            pos -> Position of the radial slider (For sx, sy)

            return -> None

        """
        angle = self.tk_degrees(self.tk_atan2(pos[0] - sx, sy - pos[1])) % 360
        angle = (max(45, angle) if angle < 180 else min(315, angle)) - 45

        self._rs_value['val'] = int(angle / self._rs_value['adi'])
        self._rs_value['dva'] = self._rs_value['mul'] * self._rs_value['val']

    
    def rs_render_slider(self, surface, pos=None):
        """
            Render the radial slider

            surface -> Active screen surface
            pos -> (x, y) position (Screen coordinates)

            return -> Current slider value mapped within-range

        """
        if pos is None: pos = (0, 0) 
        
        if self._rs_value['val'] > 1:
            self.tk_draw_polygon(surface, (0xff, 0x40, 0x0), 
                                 [(x + pos[0], y + pos[1]) for x, y in self._rs_ring_points[0][:self._rs_value['val']] + \
                                                                       self._rs_ring_points[1][-self._rs_value['val']:]])

        return self.tk_clamp(round(self._rs_value['dva'], 2), 0, self._rs_value['map']) 





class ScanLineGenerator(GlobalGameData):
    """
        Create 'Scanline effect' which distorts the surface content by shifting pixels left/right per-scanline

    """
    def __init__(self, num_of_lines, speed):
        
        # Number of scanlines
        self.slg_num_of_scanlines = num_of_lines

        # Speed (ms)
        self.slg_speed = speed

        # Shifting direction/amount
        self.slg_shift_dir = self.tk_deque((32, -32))

        # Keep track of the scanline
        self.slg_scanline_cycle = self.tk_cycle(xrange(self.tk_resolution[1] + self.slg_num_of_scanlines))
        self.slg_scanline_value = 0


    def slg_update(self):
        """
            Update the scanline position

            return -> None

        """
        self.slg_scanline_value = self.slg_scanline_cycle.next() 


    def slg_scanlineEffect(self, surface):
        """
            Create the scanline effect

            surface -> Surface which receives the effect

            return -> None

        """
        sh = surface.get_height()

        scanline_array = self.tk_surfarray.pixels2d(surface) 

        for sl in xrange(self.slg_num_of_scanlines):
            line = self.slg_scanline_value - sl 
            if not -1 < line < sh: continue

            # Shift the pixels left or right by x amount
            self.tk_np_copyto(scanline_array[:, line], self.tk_np_roll(scanline_array[:, line], self.slg_shift_dir[0]))
            self.slg_shift_dir.rotate(1) 

        if self.tk_randrange(0, 100) > 50:
            self.tk_np_copyto(scanline_array[::4, ::4], self.tk_np_roll(scanline_array[::4, ::4], 4))


class ActiveBackGround(GlobalGameData):
    # Display a background with 3d objects (Currently locked to bulletcasings only)
    def __init__(self):
        self.ab_num_of_casings = 12

        self.ab_columns_width = self.tk_resolution[0] / self.ab_num_of_casings
        # Column, [Model, Speed, column_x]
        self.ab_columns = {key: [Model3D.m_create_BulletCasing(), .2, \
        self.tk_randrange(0, self.ab_columns_width)] for key in xrange(self.ab_num_of_casings)}

        for key in self.ab_columns.iterkeys():
            self._ab_resetColumn(key)


    def _ab_resetColumn(self, column_id=None):
        """
            Reset column

            column_id -> Key of the column (int)

            return -> None

        """ 
        self.ab_columns[column_id][0].m_reset()     # Reset model vertices
        # Move the model top of the screen
        self.ab_columns[column_id][0].m_translate(ty=-self.ab_columns[column_id][0].get_radius, absolute=1)

        self.ab_columns[column_id][1] = self.tk_uniform(1.0, 2.5)    # Speed
        self.ab_columns[column_id][2] = self.tk_randrange(0, self.ab_columns_width)     # x position in column         

        # Init with random rotation, position
        self.ab_columns[column_id][0].m_rotate_x(self.tk_randrange(0, 359))
        self.ab_columns[column_id][0].m_rotate_y(self.tk_randrange(0, 359))
        self.ab_columns[column_id][0].m_rotate_z(self.tk_randrange(0, 359))
        self.ab_columns[column_id][0].m_translate(self.ab_columns_width * column_id + self.ab_columns[column_id][2]) 


    def ab_render(self, surface, tick):
        """
            Render active background

            surface -> Active screen
            tick -> Tickrate for the elements

            return -> None

        """
        mx, my = self.tk_mouse_pos()

        for key, value in self.ab_columns.iteritems():
            # Get distance to each model
            dist = self.tk_hypot(value[0].get_x - mx, value[0].get_y - my)
            dist = min(1, (1 / dist) * 64)
            
            if tick:
                value[0].m_rotate_x(2.5 * dist)
                value[0].m_rotate_y(2.5 * dist)
                value[0].m_rotate_z(3.5 * dist)

                value[0].m_translate(ty=value[1])
            
            boundary = value[0].m_render(surface, color=(0x40 + (0x60 * dist), 0x0, 0x0))
            if value[0].get_y - boundary > self.tk_resolution[1]:
                self._ab_resetColumn(key)    