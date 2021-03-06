from ConfigsModule import GlobalGameData, TkWorldDataShared
from PreProcessor import PreProcessor

from pygame import RLEACCEL

# Note: Rather than casting shadow from each wall
# one could pre-calculate all the horizontal and vertical wall slices
# and cast bigger shadow from them

# Obviously, there's alot more room for improvement on this module

__all__ = 'Shadows', 'CharacterShadows'


class Shadows(GlobalGameData, TkWorldDataShared):

    # Shadow table size
    shadow_map_size = 0, 0

    # Shadow world size
    shadow_world_size = 0, 0

    # 2D map of each cell
    shadow_map = []

    def __init__(self):
        self.s_shadow_surf = self.tk_surface(self.tk_resolution)
        if self.tk_shadow_quality: 
            self.s_shadow_surf.set_colorkey(self.tk_shadow_mask_color)

        self.s_buildShadowDirMap()
    
    
    def s_buildShadowDirMap(self):
        """
            TBD
        """
        self.s_shadow_dir_map = []

        # Every cell has one line to work as guides for the shadow quadrilateral
        # Line meaning align the line clockwise diagonally to cast the shadows
        
        # Finetune these to workout the line inside the wall segment (Doesn't peek out from the wall)
        # These are offsets from topleft of the wall 
        axis_dir = {0:   [0,  31, 31, 31],      # Top
                    90:  [31, 32, 31, 0 ],      # Left
                    180: [32, 1,  0,  1 ],      # Down
                    270: [1,  0,  1,  32]}      # Right

        non_axis_dir = {45:  [0,  32, 32, 0 ],  # TopLeft
                        315: [0,  0,  32, 32],  # TopRight
                        135: [32, 32, 0,  0 ],  # DownLeft
                        225: [32, 0,  0,  32]}  # DownRight

        # Find the 2d array mid point
        x_mid_value = range(sum(self.tk_shadow_minmax_x)) 
        x_mid_value = x_mid_value[len(x_mid_value) / 2]

        y_mid_value = range(sum(self.tk_shadow_minmax_y)) 
        y_mid_value = y_mid_value[len(y_mid_value) / 2]

        y_range_slide = self.tk_chain(xrange(1, y_mid_value + 1), 
                                      xrange(y_mid_value + 1, 0, -1))

        for e1, y in enumerate(xrange(sum(self.tk_shadow_minmax_y))):
            y_range_value = y_range_slide.next()
            
            x_range_slide = self.tk_chain(xrange(1, x_mid_value + 1), 
                                          xrange(x_mid_value + 1, 0, -1))
            row = []
            
            for e2, x in enumerate(xrange(sum(self.tk_shadow_minmax_x))):
                x_range_value = x_range_slide.next() 

                # Get Angle to each cell from the middle for shadow cast line
                _dir = int(self.tk_degrees(self.tk_atan2(x_mid_value - e2, y_mid_value - e1) % (self.tk_pi * 2)))

                if e1 == y_mid_value and e2 == x_mid_value:
                    # Ignore mid value 
                    d = [0, 0, 0, 0]

                elif _dir in axis_dir:
                    # Axis aligned direction
                    d = axis_dir[_dir][:] 

                else:
                    # Find the closest non-axis angle
                    non_axis = min(non_axis_dir.keys(), key=lambda x: abs(x - _dir))
                    d = non_axis_dir[non_axis][:] 
                
                d.append(min(y_range_value, x_range_value))
                
                # Fixes peeking by lowering the extra angle per wall
                # as the distance increases
                dist = self.tk_hypot(x_mid_value - e2, y_mid_value - e1)
                d.append(max(0, 0.16 - 0.01 * dist))
                
                row.append(tuple(d))
            
            self.s_shadow_dir_map.append(tuple(row))
        
        self.s_shadow_dir_map = tuple(self.s_shadow_dir_map)
        
     
    def s_loadSurfaceMap(self, surface):
        """
            Load the ground layer as shadow mask

            surfaces -> All macro surfaces

            return -> None

        """
        fade_surface = self.tk_surface(surface.get_size(), self.tk_srcalpha)
        fade_surface.fill(self.tk_shadow_color)

        self.s_fade_surf = surface.copy()
        self.s_fade_surf.blit(fade_surface, (0, 0)) 


    def s_loadCellWalls(self, cellwalls):
        """
            Load world map and convert all cells to 2d binary map (Walls=1 else 0) 

            cellwalls -> 2d world map

            return -> None
            
        """
        final = []
        # Per-cell size
        self.shadow_map_size = len(cellwalls[0]), len(cellwalls)
        
        # Per-sector size 
        self.shadow_world_size = self.shadow_map_size[0] * 32, self.shadow_map_size[1] * 32  
        
        # Cells with collisions are marked with 1 else 0
        for y in xrange(self.shadow_map_size[1]):
            row = []
            for x in xrange(self.shadow_map_size[0]):
                row.append(1 if cellwalls[y][x].w_collision else 0)
            final.append(tuple(row))

        self.shadow_map[:] = final

    # Note: Remove this   
    exec(PreProcessor.parseCode("""
def s_applyShadows(self, surface):

    x, y = self.w_share["WorldPosition"]
    ofsx = x - self.w_share['ShadowOffset'][0]
    ofsy = y - self.w_share['ShadowOffset'][1]

    #-ifdef/tk_shadow_quality
    self.s_shadow_surf.blit(surface, (0, 0))
    self.s_shadow_surf.lock()
    #-endif

    rounded_x, rounded_y = int(x), int(y)
    
    ori_x, ori_y = (self.tk_res_half[0] + rounded_x,
                    self.tk_res_half[1] + rounded_y)
    
    # Get index of which cell the player is standing on
    near_x, near_y = -int(x - 16) >> 5, -int(y - 16) >> 5
    
    min_y, max_y = self.tk_shadow_minmax_y
    min_x, max_x = self.tk_shadow_minmax_x

    # Shadows are calculated clockwise
    for e1, ry in enumerate(xrange(near_y - min_y, near_y + max_y)):
        if ry < 1 or ry > self.shadow_map_size[1]-2:
            # Most outer rows do not cast shadows (Walls between playable area and the void) 
            continue
        for e2, rx in enumerate(xrange(near_x - min_x, near_x + max_x)):
            if rx < 1 or rx > self.shadow_map_size[0]-2:
                # Most outer columns do not cast shadows
                continue
            # Check if the cell can cast shadows
            if self.shadow_map[ry][rx]:
                # Get the line endpoints
                pc = self.s_shadow_dir_map[e1][e2]
                
                # Position of the object(TopLeft)
                sox = (ori_x + 32 * rx - 17) - ofsx
                soy = (ori_y + 32 * ry - 17) - ofsy  

                # How far the shadow is casted from the wall/object
                length = 80 * pc[4]
                
                ep1 = sox + pc[0], soy + pc[1]      # Endpoint 1
                # Calculate the angle to endpoints of the cubes
                angle_1 = self.tk_atan2(ori_x - (ep1[0] + x), ori_y - (ep1[1] + y)) + pc[5]
                end_p_1 = (ep1[0] - self.tk_sin(angle_1) * length,
                           ep1[1] - self.tk_cos(angle_1) * length)
                
                ep2 = sox + pc[2], soy + pc[3]      # Endpoint 2
                angle_2 = self.tk_atan2(ori_x - (ep2[0] + x), ori_y - (ep2[1] + y)) - pc[5]
                end_p_2 = (ep2[0] - self.tk_sin(angle_2) * length,
                           ep2[1] - self.tk_cos(angle_2) * length)
                
                # Cast a shadow polygon from the line and color it for colorkeying
                self.tk_draw_polygon({surface}, self.tk_shadow_mask_color,
                                    (ep1, end_p_1, end_p_2, ep2))

    #-ifdef/tk_shadow_quality 
    self.s_shadow_surf.unlock()

    mapPos = -x, -y 

    # The shadow map is the chosen layer 'shadowed' and stored in memory.
    # This section cuts a correct size of that map and displays it
    
    # If the topleft map corner is in view, clamp it from going below 0
    topLeft = max(0, mapPos[0] - self.tk_res_half[0] + 16), max(0, mapPos[1] - self.tk_res_half[1] + 16)

    bottomRight = (min(self.shadow_world_size[0] - topLeft[0], self.tk_res_half[0] + mapPos[0] + 16), 
                   min(self.shadow_world_size[1] - topLeft[1], self.tk_res_half[1] + mapPos[1] + 16)) 

    # Area which will be cut from the shadow map
    area = (topLeft[0] + (ofsx if topLeft[0] else 0), 
            topLeft[1] + (ofsy if topLeft[1] else 0), 
            bottomRight[0] - (ofsx if topLeft[0] else -1 - ofsx), 
            bottomRight[1] - (ofsy if topLeft[1] else -1 - ofsy))

    # The topleft anchor point should always be at topleft corner of the screen
    # But when the topleft of the map is in view, it should anchor to that one
    dest = (self.tk_res_half[0] + x - 16 + topLeft[0] - (ofsx if not topLeft[0] else 1), 
            self.tk_res_half[1] + y - 16 + topLeft[1] - (ofsy if not topLeft[1] else 1))  
    
    # Blit the shadowed part of the ground

    surface.blit(self.s_fade_surf, dest, area=area)  
    
    # Blit the visible area
    surface.blit(self.s_shadow_surf, (0, 0))
    #-endif

    """.format(surface='self.s_shadow_surf' if GlobalGameData.tk_shadow_quality else 'surface'),
    tk_shadow_quality=GlobalGameData.tk_shadow_quality))



class CharacterShadows(GlobalGameData):

    cs_data = {'world': None,
               'end_points': None,
               'falloff_mult': None,
               'index_points': None}

    # Number of polygons on the shadow ellipse
    __shadow_poly_limit = 12 


    @classmethod
    def cs_shadow_cast(cls, surface, px, py, pAngle=None):
        """
            Cast dynamic character shadows from world lights

            surface -> Active screen surface
            px, py -> World coordinates
            pAngle -> Angle of the character casting the shadow  

            return -> None

        """
        # Final polygon points
        points = []
        
        ix, iy = int(px) >> 8, int(py) >> 8
        try:
            # Get all lights near the character
            for x, y in cls.cs_data['index_points'][(ix, iy)]:
                for l in cls.cs_data['world'][y][x].itervalues():
                    # Calculate distance to the light
                    dist = max(10, cls.tk_hypot(px - l.x, py - l.y)) 
                    if dist < l.radius >> 1:
                        dist = min(64, dist)
                        angle = cls.tk_atan2(py - l.y, px - l.x) 
                        
                        tx = cls.tk_cos(angle)
                        ty = cls.tk_sin(angle)

                        for cos, sin in cls.cs_data['end_points']:
                            #w = max(6, abs(12 * cls.tk_cos(pAngle))) 
                            #h = max(6, abs(12 * cls.tk_sin(pAngle)))

                            lx = int((cls.tk_res_half[0] + dist * cos * tx - 10 * sin * ty) + tx * (dist - 10)) 
                            ly = int((cls.tk_res_half[1] + 10 * sin * tx + dist * cos * ty) + ty * (dist - 10)) 
                            points.append((lx, ly))

                        cls.tk_draw_gfx_polygon(surface, points, (0x20, 0x20, 0x20, 255 - dist * cls.cs_data['falloff_mult']))
                        points = []
        
        # Out of bounds from the map
        except KeyError: 
            return 


    
    @classmethod
    def cs_load_lights(cls, lights, world_size):
        """
            Build lights hashmap for dynamic shadows

            lights -> List of lights entities
            world_size -> Size of the world

            return -> None

        """
        cls.cs_data['world'] = [[{} for x in xrange(world_size[0])] for y in xrange(world_size[1])]

        for light in lights:
            key = light.x, light.y
            index = light.x >> 8, light.y >> 8
            cls.cs_data['world'][index[1]][index[0]][key] = light

        cls.cs_data['index_points'] = {}
        
        for wy in xrange(world_size[1]):
            for wx in xrange(world_size[0]):
                points = []
                for y in xrange(wy - 1, wy + 2):
                    if not -1 < y < world_size[1]:
                        continue
                    
                    for x in xrange(wx - 1, wx + 2):
                        if not -1 < x < world_size[0]:
                            continue 

                        points.append((x, y))
            
                cls.cs_data['index_points'][(wx, wy)] = points


    @classmethod
    def cs_setup_character_shadows(cls):
        """
            Setup(and possible load stuff in the future) for character shadow mapping

            return -> None

        """
        # Create the polygon points in ellipse shadow
        cls.cs_data['end_points'] = [cls.tk_radians(p) for p in xrange(0, 360, 360 / cls.__shadow_poly_limit)]
        cls.cs_data['end_points'] = tuple([(cls.tk_cos(r), cls.tk_sin(r)) for r in cls.cs_data['end_points']])

        # Shadow attenuation (Distance from the light)
        cls.cs_data['falloff_mult'] = 255 / float(128) * 2

        # Build static character shadow surface
        cls.cs_data['char_static_shadow'] = None


