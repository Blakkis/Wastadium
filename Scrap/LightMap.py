from ConfigsModule import GlobalGameData


#from ctypes import CDLL, c_int
#from RectInsideQuadrilateral import RectInsideQuadrilateral as tk_checkRect


# NOTE: Optimize shadowing by creating somekind of occlusion culling technique
# NOTE: Doing this whole operation in reverse might yield better fps
# NOTE: Remove the offsets during shadowing since there is no 2 layer shadowing 
#       Additional note: Right and bottom side of the shadowmap is off by 1 pixel
#       But they get hidden inside the gradient effect
# NOTE: Merge the 2 classes

class LightMapExtension(GlobalGameData):
    """
        TBD
    """
    # world size is the width and height of the 2d cell array multiplied by 32 
    ext_worldSize = 0, 0
    
    def __init__(self):
        self.ext_fullMapSurface = None
        self.ext_shadowForeGround = self.tk_surface((32 * self.tk_macro_cell_size,
                                                     32 * self.tk_macro_cell_size), self.tk_srcalpha)
        self.ext_shadowForeGround.fill(self.tk_shadow_color)

        # self.ext_half_x = xrange(1, self.tk_shadow_minmax_x[0])
        # self.ext_half_y = xrange(1, self.tk_shadow_minmax_y[0])
        # self.ext_mid_x = 0
        # self.ext_mid_y = 0

        # # Occlusion culling tables
        # # x, y, key
        # self.ext_occkeys = ((2, 2,  0), (16, 2,  1), (30, 2,  2),
        #                     (2, 16, 3), (16, 16, 4), (30, 16, 5),
        #                     (2, 30, 6), (16, 30, 7), (30, 30, 8))

        # # Pre-cached tables
        # self.ext_occtables = {}

    
    def ext_buildOccTables(self, w, h):
        """
            TBD

            return -> None

        """
        raise DeprecationWarning
        
        check_function = CDLL('cExtensions\libCextensions.so') 
        cArray = c_int * 8

        rect_tables = [[self.tk_rect(32 * row, 32 * column, 32, 32) for row in xrange(w)] \
                                                                    for column in xrange(h)]

        # Get the mid block from which the shadows are casted from
        mid_block = rect_tables[self.ext_mid_y][self.ext_mid_x]

        # Convert the rects to C arrays for checking
        for ey, conY in enumerate(rect_tables[:]):
            for ex, i in enumerate(conY):
                rect_tables[ey][ex] = cArray(i.topleft[0],    i.topleft[1],    i.topright[0],    i.topright[1],
                                             i.bottomleft[0], i.bottomleft[1], i.bottomright[0], i.bottomright[1])     


        # Create the empty 2D arrays ready for data
        for _ in xrange(len(self.ext_occkeys)): self.ext_occtables[_] = [tuple(set() for row in xrange(w)) for column in xrange(h)]

        num = 0
        for mid in self.ext_occkeys:
            # From which the shadow is casted from referenced to the wall
            cast_point = mid_block.x + mid[0], mid_block.y + mid[1]
            for ey, column in enumerate(self.shadow_dir_map):    
                for ex, row in enumerate(column):
                    # Skip the mid block (Player is standing on it)
                    if ey == self.ext_mid_y and ex == self.ext_mid_x:
                        continue 
                    
                    length = 128 * row[4]
                    
                    # Wall topleft position
                    wtl = ex * 32, ey * 32
                    
                    # X, Y; Angle from mid block to wall key points
                    wtl_1 = wtl[0] + row[0], wtl[1] + row[1]; angle_1 = self.tk_atan2(wtl_1[0] + cast_point[0], wtl_1[1] + cast_point[1])               
                    wtl_2 = wtl[0] + row[2], wtl[1] + row[3]; angle_2 = self.tk_atan2(wtl_2[0] + cast_point[0], wtl_2[1] + cast_point[1])                  
                    
                    # Convert the Quadrilateral to C Array for checking (Clockwise x, y points)
                    Quad = cArray(wtl_1[0], wtl_1[1], 
                                  int(self.tk_sin(angle_1 - 0.2) * length),
                                  int(self.tk_cos(angle_1 - 0.2) * length),
                                  int(self.tk_sin(angle_2 + 0.2) * length),
                                  int(self.tk_cos(angle_2 + 0.2) * length),
                                  wtl_2[0], wtl_2[1])
                    
                    key = mid[2]
                    # Now lets check which walls are inside the shadow quadrilateral casted by the wall
                    for index_y in xrange(h):
                        for index_x in xrange(w):
                            if check_function.rectInsideQuadrilateral(Quad, rect_tables[index_y][index_x]):
                                self.ext_occtables[key][ey][ex].add((index_y, index_x))   

        #print float(asizeof.asizeof(self.ext_occtables)) / float(1024 ** 2), 'mb'
                    
    
    def ext_findClosestPair(self, x, y):
        """
            Find the closest x, y point from list against the target x, y

            x, y -> target point

            return -> closest x, y point

        """
        raise DeprecationWarning
        return min(self.ext_occkeys, key=lambda pair: self.tk_hypot(x - pair[0], y - pair[1]))
    

    
    def ext_loadSurfaceMap(self, surfaces):
        """
            TBD
        """
        surf_size = 32 * self.tk_macro_cell_size 
        self.ext_fullMapSurface = self.tk_surface((surf_size * len(surfaces[0]),
                                                   surf_size * len(surfaces)))
        
        #print (self.ext_fullMapSurface.get_bytesize() * (self.ext_fullMapSurface.get_width() * \
        #       self.ext_fullMapSurface.get_height())) / 1024 ** 2, 'mb'  
        
        for ey, y in enumerate(surfaces):
            for ex, x in enumerate(y):
                surf = x[1].copy()
                surf.blit(self.ext_shadowForeGround, (0, 0))
                self.ext_fullMapSurface.blit(surf, (surf_size * ex, surf_size * ey))


    def __ext_spiralGenerator(self, topleft, downright, xiter, yiter, donex, doney):
        """
            Spiral outward from center of 2D array clockwise

            topleft -> the current maxsize of the expanding iter box on topleft 
            downright -> the current maxsize of the expanding iter box on downright  
            xiter -> Number of blocks to go through horizontally
            yiter -> number of blocks to go through in vertically
            donex -> Horizontal limit of the 2D array has been reached, use this as signal
            doney -> vertical limit of the 2D array has been reached, use this as signal

            return -> Yield of the current relative pos from map's topleft and absolute coordinates on the shadow direction map

        """
        raise DeprecationWarning
        half_rx = xiter >> 1
        half_ry = yiter >> 1

        # Expands from the mid in:  top row      (left  -> right)
        #                           down row     (right -> left)
        #                           right column (top   -> down)
        #                           left column  (down  -> top) 
        
        if doney != self.tk_shadow_minmax_y[0]: 
            for x1 in xrange(xiter):
                yield (topleft[0] + x1, topleft[1], 
                       self.ext_mid_x - half_rx + x1, 
                       self.ext_mid_y - half_ry)

            for x2 in xrange(xiter):
                yield (downright[0] - x2, downright[1], 
                       self.ext_mid_x + half_rx - x2, 
                       self.ext_mid_y + half_ry)

        # NOTE: If the screen height is greater than width (Which should never be done)
        #       Then extend the y1, y2 loops with exhaust protection
        for y1 in xrange(yiter):
            yield (downright[0], topleft[1] + y1, 
                   self.ext_mid_x + half_rx, 
                   self.ext_mid_y - half_ry + y1)

        for y2 in xrange(yiter):
            yield (topleft[0], downright[1] - y2, 
                   self.ext_mid_x - half_rx, 
                   self.ext_mid_y + half_ry - y2)
          


    def ext_SqExpandGenerator(self, cx, cy):
        """
            Start building expanding square from center coordinates (cx, cy)
            which is then fed to the spiral generator to generate the coordinates in clockwise order
        """
        raise DeprecationWarning
        gen_x, gen_y = iter(self.ext_half_x), iter(self.ext_half_y)
        x_exhaust = 0; y_exhaust = 0
        
        while (x_exhaust != self.tk_shadow_minmax_x[0] or y_exhaust != self.tk_shadow_minmax_y[0]):
            x_exhaust = next(gen_x, self.tk_shadow_minmax_x[0])
            y_exhaust = next(gen_y, self.tk_shadow_minmax_y[0])

            topleft   = cx - x_exhaust, cy - y_exhaust
            downright = cx + x_exhaust, cy + y_exhaust

            x_iter = abs(topleft[0] - downright[0])
            y_iter = abs(topleft[1] - downright[1])

            for s in self.__ext_spiralGenerator(topleft, downright, x_iter, y_iter, x_exhaust, y_exhaust):
                #print "{0: <2}, {1: <2}".format(*s[2:])
                yield s        


class LightMap(LightMapExtension):
    """
        Handle the casting of shadows on the map to limit visibility of the player view
        
    """
    # lightmap size is the width and height of the 2d cell array
    light_map_size = 0, 0
    
    # Lightmap based as spatial hashmap with player position being key
    light_map = []

    def __init__(self):
        LightMapExtension.__init__(self)
        
        # Surface which holds the surface in shadow
        #self.shadow_surface = self.tk_surface(self.tk_resolution)
        
        # Surface which holds all visible area
        self.vis_surface = self.tk_surface(self.tk_resolution)
        if self.tk_shadow_quality: 
            self.vis_surface.set_colorkey(self.tk_shadow_mask_color)


        # # Mask color overlay (Which is the shadow layer that gets applied top of the surface)
        # if self.tk_shadow_quality: 
        #     self.overlay = self.tk_surface(self.tk_resolution, self.tk_srcalpha)
        # else:
        #     # Low version without alpha values 
        #     self.overlay = self.tk_surface(self.tk_resolution)  

        # self.overlay.fill(self.tk_shadow_color)

        # Additional angle for the edge lines
        self.add_angle = 0.1
        
        # Used to sync the visible and shadow maps  
        self.offset_fix = 0, 0
        
        # Find the 2d array mid point
        x_mid_value = range(sum(self.tk_shadow_minmax_x)); x_mid_value = x_mid_value[len(x_mid_value) / 2]
        y_mid_value = range(sum(self.tk_shadow_minmax_y)); y_mid_value = y_mid_value[len(y_mid_value) / 2]
        
        self.ext_mid_x, self.ext_mid_y = x_mid_value, y_mid_value
         
        y_range_slide = self.tk_chain(xrange(1, y_mid_value + 1), xrange(y_mid_value + 1, 0, -1))
        
        self.shadow_dir_map = []
        
        for e1, y in enumerate(xrange(sum(self.tk_shadow_minmax_y))):
            y_range_value = y_range_slide.next()
            # Create a x up/down counter 
            x_range_slide = self.tk_chain(xrange(1, x_mid_value + 1), xrange(x_mid_value + 1, 0, -1))
            row = []
            for e2, x in enumerate(xrange(sum(self.tk_shadow_minmax_x))):
                x_range_value = x_range_slide.next() 
                d = []
                # Next step is to build the shadow cast line  
                
                # Note: The points are clockwise endpoints from the topleft of the object

                # Lists are: x, y, x, y points 
                if e1 == y_mid_value and \
                   e2 == x_mid_value:      d = [0,  0,  0,  0 ]#'Middle'
                elif e2 < x_mid_value:
                    if  e1 == y_mid_value: d = [31, 32, 31, 0 ]#'Left'                     
                    elif e1 < y_mid_value: d = [0,  32, 32, 0 ]#'TopLeft'                                          
                    else:                  d = [32, 32, 0,  0 ]#'DownLeft'               
                elif e2 == x_mid_value:
                    if e1 < y_mid_value:   d = [0,  31, 32, 31]#'Top'                                          
                    else:                  d = [32, 1,  0,  1 ]#'Down'
                else:                       
                    if e1 == y_mid_value:  d = [1,  0,  1,  32]#'Right'
                    elif e1 < y_mid_value: d = [0,  0,  32, 32]#'TopRight'                     
                    else:                  d = [32, 0,  0,  32]#'DownRight'
                
                # Possible optimize idea..
                # Calculate inverted Manhattan-distance to each block to reduce the size of all the polygons draws
                #m = max(1, (x_mid_value + y_mid_value) - (abs(x - x_mid_value) + abs(y - y_mid_value)))

                # Get the length for the shadow for how far they can cast themself
                d.append(min(y_range_value, x_range_value)) 
                row.append(tuple(d))
            
            self.shadow_dir_map.append(tuple(row))
        
        self.shadow_dir_map = tuple(self.shadow_dir_map)

        #self.ext_buildOccTables(len(self.shadow_dir_map[0]), len(self.shadow_dir_map))


    
    def create_delta_offsets(self, x, y, surface=None):
        """
            Create delta offsets between shadow and visible layers (with player movement in the middle)

            x, y -> Store old world position before player movement is updated 
            
            surface -> Surface which receives the shadow mask (Not is use anymore)

            return -> None
            
        """
        # Note: This function is old reminiscent style how the visible/shadow was calculated
        #       and should be removed completly from the codebase

        self.offset_fix = x, y
        
        #if self.tk_shadow_quality:
            # Store the current surface
            #self.shadow_surface.blit(surface, (0, 0))
        
            # Paint the shadow surface over the original surface 
            # (Note: tk_shadow_blendkey can be used as special_flags, to create more color richer effect but slightly slower)
            #self.shadow_surface.blit(self.overlay, (0, 0))      


    def render_light_and_shadow(self, x, y, surface):
        """
            Render shadows outward from the origin (x, y) by finding all the blocks and cast shadows from them

            x -> Origin x
            y -> Origin y
            surface -> Surface which to draw on

            return -> None
            
        """

        # Calculate the difference between the shadow layer and visible layer
        offs_fix_x, offs_fix_y = x - self.offset_fix[0],  y - self.offset_fix[1]

        # Get the latest surface on the bench
        self.vis_surface.blit(surface, (0, 0))

        # Lock up, since we are going to make quite a few draw calls
        self.vis_surface.lock()

        rounded_x, rounded_y = int(x), int(y)
        
        ori_x, ori_y = (self.tk_res_half[0] + rounded_x,
                        self.tk_res_half[1] + rounded_y)

        # Get the position inside single 32x32 cell
        # raw_x, raw_y = abs(rounded_x - 16), abs(rounded_y - 16)
        
        # Get index of which cell the player is standing on
        near_x, near_y = -int(x - 16) >> 5, -int(y - 16) >> 5

        # # Pointpoint the cell position with the index pos
        # raw_x -= near_x * 32; raw_y -= near_y * 32

        # # Get the nearest occlusion cache dict key
        # key = self.ext_findClosestPair(raw_x, raw_y)[2]
        
        # # These blocks are under the shadow, so they dont have to cast shadows
        # no_cast = set()
 
        # for rx, ry, xi, yi in self.ext_SqExpandGenerator(near_x, near_y):
        #     if (ry < 1 or ry > self.light_map_size[1] - 2) or \
        #        (rx < 1 or rx > self.light_map_size[0] - 2):
        #         continue
        #     # Does the cell contain a wall and its not on the no_cast set?
        #     if self.light_map[ry][rx] and (yi, xi) not in no_cast:
        #         no_cast.update(self.ext_occtables[key][yi][xi])
        #         # Get the line endpoints
        #         pc = self.shadow_dir_map[yi][xi]

        #         # Position of the object(TopLeft)
        #         sox = (ori_x + 32 * rx - 17) - offs_fix_x
        #         soy = (ori_y + 32 * ry - 17) - offs_fix_y  

        #         # Add contact shadows for the walls(Tho looks more like toon shading edge effect)
        #         #self.tk_draw_rect(self.vis_surface, self.tk_shadow_mask_color,
        #         #                  (sox - 1, soy - 1, 34, 34))

        #         # How far the shadow is casted from the wall/object
        #         length = 80 * pc[4]
                
        #         ep1 = sox + pc[0], soy + pc[1]      # Endpoint 1

        #         # Calculate the angle to endpoints of the cubes
        #         angle_1 = self.tk_atan2(ori_x - (ep1[0] + x), ori_y - (ep1[1] + y)) + self.add_angle
        #         end_p_1 = (ep1[0] - self.tk_sin(angle_1) * length,
        #                    ep1[1] - self.tk_cos(angle_1) * length)
                
        #         ep2 = sox + pc[2], soy + pc[3]      # Endpoint 2
        #         angle_2 = self.tk_atan2(ori_x - (ep2[0] + x), ori_y - (ep2[1] + y)) - self.add_angle
        #         end_p_2 = (ep2[0] - self.tk_sin(angle_2) * length,
        #                    ep2[1] - self.tk_cos(angle_2) * length)
                
        #         # Cast a shadow polygon from the line and color it for colorkeying
        #         self.tk_draw_polygon(self.vis_surface, self.tk_shadow_mask_color,
        #                             (ep1, end_p_1, end_p_2, ep2)) 
        
        min_y, max_y = self.tk_shadow_minmax_y
        min_x, max_x = self.tk_shadow_minmax_x

        # Shadows are calculated clockwise
        for e1, ry in enumerate(xrange(near_y - min_y, near_y + max_y)):
            if ry < 1 or ry > self.light_map_size[1]-2:
                # Top/row most do not cast shadows
                continue
            for e2, rx in enumerate(xrange(near_x - min_x, near_x + max_x)):
                if rx < 1 or rx > self.light_map_size[0]-2:
                    # Left/right most columns do not cast shadows
                    continue
                # Check if the cell contains occlusion
                if self.light_map[ry][rx]:
                    # Get the line endpoints
                    pc = self.shadow_dir_map[e1][e2]
                    
                    # Position of the object(TopLeft)
                    sox = (ori_x + 32 * rx - 17) - offs_fix_x
                    soy = (ori_y + 32 * ry - 17) - offs_fix_y  

                    # Add contact shadows for the walls(Tho looks more like toon shading edge effect)
                    #self.tk_draw_rect(self.vis_surface, self.tk_shadow_mask_color,
                    #                  (sox - 1, soy - 1, 34, 34))

                    # How far the shadow is casted from the wall/object
                    length = 80 * pc[4]
                    
                    ep1 = sox + pc[0], soy + pc[1]      # Endpoint 1
                    # Calculate the angle to endpoints of the cubes
                    angle_1 = self.tk_atan2(ori_x - (ep1[0] + x), ori_y - (ep1[1] + y)) + self.add_angle
                    end_p_1 = (ep1[0] - self.tk_sin(angle_1) * length,
                               ep1[1] - self.tk_cos(angle_1) * length)
                    
                    ep2 = sox + pc[2], soy + pc[3]      # Endpoint 2
                    angle_2 = self.tk_atan2(ori_x - (ep2[0] + x), ori_y - (ep2[1] + y)) - self.add_angle
                    end_p_2 = (ep2[0] - self.tk_sin(angle_2) * length,
                               ep2[1] - self.tk_cos(angle_2) * length)
                    
                    # Cast a shadow polygon from the line and color it for colorkeying
                    self.tk_draw_polygon(self.vis_surface, self.tk_shadow_mask_color,
                                        (ep1, end_p_1, end_p_2, ep2))

            
        # Unlock, all draw calls has been done
        self.vis_surface.unlock()
        
        # Finally blit the shadow and visible surfaces (Old)
        #if self.tk_shadow_quality: surface.blit(self.shadow_surface, (0, 0))

        if self.tk_shadow_quality:
            mapPos = -x, -y     # Convert the worldpos (which by default is negative) to positive

            # The shadow map is the chosen layer 'shadowed' and stored in memory.
            # This section cuts a correct size of that map and displays it
            
            # If the topleft map corner is in view, clamp it from going below 0
            topLeft = max(0, mapPos[0] - self.tk_res_half[0] + 16), max(0, mapPos[1] - self.tk_res_half[1] + 16)

            bottomRight = (min(self.ext_worldSize[0] - topLeft[0], self.tk_res_half[0] + mapPos[0] + 16), 
                           min(self.ext_worldSize[1] - topLeft[1], self.tk_res_half[1] + mapPos[1] + 16)) 

            # Area which will be cut from the shadow map
            area = (topLeft[0] + (offs_fix_x if topLeft[0] else 0), 
                    topLeft[1] + (offs_fix_y if topLeft[1] else 0), 
                    bottomRight[0] - (offs_fix_x if topLeft[0] else -1 - offs_fix_x), 
                    bottomRight[1] - (offs_fix_y if topLeft[1] else -1 - offs_fix_y))

            # The topleft anchor point should always be at topleft corner of the screen
            # But when the topleft of the map is in view, it should anchor to that one
            dest = (self.tk_res_half[0] + x - 16 + topLeft[0] - (offs_fix_x if not topLeft[0] else 1), 
                    self.tk_res_half[1] + y - 16 + topLeft[1] - (offs_fix_y if not topLeft[1] else 1))  
            
            # Blit the shadowed part of the ground
            surface.blit(self.ext_fullMapSurface, dest, area=area)
        
        # Blit the visible area
        surface.blit(self.vis_surface, (0, 0)) 


    @classmethod
    def load_lightmap(cls, lightmap):
        """
            Load and convert the 2d world array to with each cell converted to 1(Occlusion), 0(No occlusion)

            lightmap -> 2d array of the world layer 
            
            return -> None
            
        """
        final_lightmap = []

        # Store the size of the world map
        cls.light_map_size = len(lightmap[0]), len(lightmap)
        cls.ext_worldSize = cls.light_map_size[0] * 32, cls.light_map_size[1] * 32  
        
        # Cells with collisions are marked with 1 else 0
        for y in xrange(cls.light_map_size[1]):
            row = []
            for x in xrange(cls.light_map_size[0]):
                row.append(1 if lightmap[y][x].collision else 0)
            final_lightmap.append(tuple(row))

        cls.light_map[:] = final_lightmap

        

if __name__ == '__main__':
    pass
