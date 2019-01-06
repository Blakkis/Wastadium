import pygame
import Tkinter as tk

from ConfigsModuleEditor import *
from ConfigsModuleEditor import MAX_CUBE_SIZE
from TextureLoader import TextureLoader, uiElements
from TextureHandlerEditor import TextureSelectOverlay
from DecalModule import DecalGibsHandler
from LightEditor import Lights
from MapParser import MapParser, Packer, MAP_ALL_TAGS
from StatisticsEditor import EditorStatistics
from EntityPickerEditor import EntityPicker
from Timer import DeltaTimer
from Tokenizers import *
from Tokenizers import Ed_CellPoint


# NOTE
#   Getting Tkinter and Pygame to work together includes some small hacks
#   Such as controlling the execution of events
#   I've marked someone of hacks with comment '# -- Hack --'
#   Tokenizing the data is shit. Switch to something more understandable (namedtuple)
#   Make the code more understandable


class VisualResources(TextureLoader, uiElements, DecalGibsHandler, EditorStatistics, 
                      TextureSelectOverlay, Lights, MapParser, GlobalGameDataEditor):
    """
        Loads and init all external elements needed by the editor

    """
    # Clear texture(void)
    void_texture = None

    # Share data between all childrens
    data = {}

    
    @classmethod
    def initVisualsAndExtModules(cls):
        """
            Load and init all external

            return -> None

        """
        # Void(black) texture
        cls.void_texture = cls.ed_surface((32, 32)); cls.void_texture.fill((0x0, 0x0, 0x0))

        cls.load_elements()
        
        cls.load_textures(world_textures_only=True)
        
        cls.load_decalsGibs()

        cls.tso_createTextureSets()

        cls.data['ed_font'] = cls.ed_font(cls.ElementFonts[1], 12)

    
    @classmethod
    def fontRender(cls, s, shadow=True):
        """
            Global font renderer for the editor

            s -> String to be renderer
            shadow -> Apply shadow highlight to the font

            return -> None
        """
        if shadow:
            w, h = cls.data['ed_font'].size(s) 
            surf = cls.ed_surface((w, h), cls.ed_srcalpha)
            surf.blit(cls.data['ed_font'].render(s, True, (0x0,  0x0,  0x0)),  (-1, 1))
            surf.blit(cls.data['ed_font'].render(s, True, (0xff, 0xff, 0xff)), ( 0, 0))
            return surf
        
        else:
            return cls.data['ed_font'].render(s, True, (0xff, 0xff, 0xff))



class World(VisualResources, MapParser, Packer):

    w_Pos = [0, 0]          # World position
    
    # World additional read/write data dict
    w_Data = {'mouseIndex': (0, 0)}
    
    # 2d array containing all single cells(32 x 32)
    w_Cells_Single = []

    # Copy read-only values from the MapParser
    locals()['w_enum'] = MapParser.w_enum
    locals().update(**MAP_ALL_TAGS)

    # Holds all textures layers in separated list/dictionaries
    w_Cells_Layers = {key: [] for key in w_enum.itervalues()}

    # Order in which the layers are rendered
    w_Blit_Order = None
  
    # World size (x, y: Chunk)(x, y: Raw)(x, y: Single Cells)
    w_Size = 0, 0, 0, 0, 0, 0

    # Spawn place for the player (And optional goal)
    w_SpawnEnd = [None, None]

    # Holds which layers to display and the display function for it
    w_Display_Layer = {key: [1, None] for key in w_enum.itervalues()}
    w_Display_Layer[-1] = [0, None]     # Display sectors (Special)

    def __init__(self, x, y, low_id):
        self.cell_pos = 32 * x, 32 * y
        # Texture, Orientation(0-3), *(wall segment id)
        self.cell_lowTex =  low_id, 0
        self._cell_midTex = None,   0, 0
        self._cell_objTex = None,   0
        
        # Objects might occupy multiple cells. Keep a link between the cells
        # pointing to the topleft cell as origin point
        self._cell_link = None

    
    def get_set_CellToken(self, token=None):
        """
            Get/Set a token of cell variable states

            return -> Dict

        """
        if token is None:
            return {'low': self.cell_lowTex, 'mid': self._cell_midTex, 
                    'obj': self._cell_objTex, 'link': self._cell_link}
        else:
            pass

    
    def _get_mid(self): return self._cell_midTex

    def _set_mid(self, value):
        """
            Wall placement controls collision applying
            
            value -> ('tex' or 'None', orient, id)

            return -> None 
        """
        cx, cy = (self.cell_pos[0] >> 5) >> 3, (self.cell_pos[1] >> 5) >> 3 

        if value[0] is None:
            assert self.cell_pos in self.w_Cells_Layers[self.E_ID_COLLISION][cy][cx], \
            "Trying to delete collision from empty cell" 
            del self.w_Cells_Layers[self.E_ID_COLLISION][cy][cx][self.cell_pos]

        else:
            # Check if the wall has collision enabled
            if self.mid_textures[value[0]]['tex_collision']:
                self.w_Cells_Layers[self.E_ID_COLLISION][cy][cx][self.cell_pos] = 1   

        self._cell_midTex = value

    cell_midTex = property(_get_mid, _set_mid)


    def _get_obj(self): return self._cell_objTex

    def _set_obj(self, value): self._cell_objTex = value

    cell_objTex = property(_get_obj, _set_obj)


    def _get_link(self): return self._cell_link

    def _set_link(self, value): self._cell_link = value

    cell_link = property(_get_link, _set_link)

    
    @classmethod
    def w_getWorldData(cls, data_segment='', layers=True):
        """
            Data handler for saving 

            data_segment -> World attribute
            layers -> if 'False' get any attribute inside World class

            return -> None

        """
        if layers:
            return cls.w_Cells_Layers[data_segment]
        else:
            return getattr(cls, data_segment) 


    @classmethod
    def w_moveWorld(cls, x=0, y=0, reset=False):
        """
            Move the world

            x, y -> move direction
            reset -> Reset position to origin

            return -> None

        """
        if reset: cls.w_Pos = [0, 0]
        else: cls.w_Pos[0] += x; cls.w_Pos[1] += y

        cls.es_update('id_camera', '({}, {})'.format(-round(cls.w_Pos[0], 1), -round(cls.w_Pos[1], 1)), 0) 


    @classmethod
    def w_toggleLayers(cls, layer_id):
        """
            Toggle visibility of the layer

            return -> None
            
        """
        cls.w_Display_Layer[layer_id][0] ^= 1


    @classmethod
    def w_createMap(cls, width=0, height=0, floor_id='debug_floor', wall_set_id='concrete_wall_01', load_from_disk=False):
        """
            Worldbuild

            width, height -> Map Dimensions
            floor_id -> str id for the default floor texture
            wall_set_id -> str id for the default wallset textures
            load_from_disk -> Load and parse map from the disk

            return -> None

        """
        disk_data = load_from_disk
        
        if load_from_disk:
            cls.mp_load(editor_loader=load_from_disk)
            disk_data = cls.decompressAndParse(editor_loader=load_from_disk)
            
            if disk_data is None:
                return
            
            width, height = disk_data[cls.MAP_GENERAL_XML][cls.MAP_DIMENSION_XML]   

        # ---- Reset/Basic setup
        cls.es_initVariables(reset=True)

        cls.w_moveWorld(reset=True)

        cls.w_SpawnEnd = disk_data[cls.MAP_GENERAL_XML][cls.MAP_PLR_BEGIN_XML] if disk_data else [None, None]

        # Reset entity containers (Ignore the first 3: Ground, Object, Wall)
        for reset_enum in sorted(cls.w_Cells_Layers.keys())[3:]:
            _type = dict if reset_enum in (cls.E_ID_COLLISION, cls.E_ID_LIGHT, 
                                           cls.E_ID_ENEMY,     cls.E_ID_PICKUP) else list
            cls.w_Cells_Layers[reset_enum] = [[_type() for x in xrange(0, width,  cls.ed_chunk_size)] 
                                                       for y in xrange(0, height, cls.ed_chunk_size)]

        # ----
        if disk_data: 
            cls.__w_diskPopulate(disk_data)

        # Store the world size in multiple formats (Desc more!)
        cls.w_Size = (width / cls.ed_chunk_size, height / cls.ed_chunk_size, 
                      width * 32, height * 32,  
                      width, height)    
        
        chunk = 32 * cls.ed_chunk_size 

        if disk_data:
            disk_data[cls.MAP_CELL_XML]

        cls.w_Cells_Single[:] = []

        for buildstep in (cls.E_ID_GROUND, cls.E_ID_OBJECT, cls.E_ID_WALL):
            full_world = cls.ed_surface((32 * width, 32 * height), pygame.SRCALPHA)
            
            if buildstep == cls.E_ID_GROUND:    
                for y, column in enumerate(disk_data[cls.MAP_CELL_XML]) if disk_data else enumerate(xrange(height)):
                    r = []
                    for x, row in enumerate(column) if disk_data else enumerate(xrange(width)):
                        f_id = row.low[0] if disk_data else floor_id 
                        full_world.blit(cls.low_textures[f_id]['tex_main'], (x * 32, y * 32))
                        r.append(World(x, y, f_id))
                    cls.w_Cells_Single.append(r)

            
            elif disk_data and buildstep == cls.E_ID_OBJECT:   
                obj_cnt = 0
                for y, column in enumerate(disk_data[cls.MAP_CELL_XML]):
                    for x, row in enumerate(column):
                        tex, orient = row.obj
                        link = row.link

                        if link is not None:
                            cls.w_Cells_Single[y][x].cell_link = link
                        
                        if tex is not None:
                            cls.w_Cells_Single[y][x].cell_objTex = tex, orient

                            sector, pos = link[1][0]

                            px = cls.ed_chunk_size_raw * sector[0] + pos[0]
                            py = cls.ed_chunk_size_raw * sector[1] + pos[1] 
                            full_world.blit(cls.ed_transform.rotate(cls.obj_textures[tex]['tex_main'], orient * 90), (px, py))
                            obj_cnt += 1

                cls.es_update('id_object_cnt', obj_cnt)
            
            
            elif buildstep == cls.E_ID_WALL: 
                if disk_data:
                    for y, column in enumerate(disk_data[cls.MAP_CELL_XML]):
                        for x, row in enumerate(column):
                            tex, orient, _id = row.mid
                            if tex is not None:
                                cls.w_Cells_Single[y][x].cell_midTex = tex, orient, _id 
                                tex = cls.ed_transform.rotate(cls.mid_textures[row.mid[0]][row.mid[2]], row.mid[1] * 90) 
                                full_world.blit(tex, (x * 32, y * 32))  


                else:     
                    for wall_cnt, wall in enumerate(cls.__w_wallBuilder(width, height), start=1):
                        _id, orient, x, y = wall
                        cls.w_Cells_Single[y][x].cell_midTex = wall_set_id, orient / 90, _id
                        full_world.blit(cls.ed_transform.rotate(cls.mid_textures[wall_set_id][_id], orient), (32 * x, 32 * y))

                    cls.es_update('id_wall_cnt', wall_cnt)
            
            # Chop the world into chunks
            cls.w_Cells_Layers[buildstep] = [[(chunk * x, chunk * y, full_world.subsurface(chunk * x, 
                                                                                           chunk * y, 
                                                                                           chunk, chunk)) 
                                            for x in xrange(cls.w_Size[0])]
                                            for y in xrange(cls.w_Size[1])]

    @classmethod
    def __w_diskPopulate(cls, data):
        """
            Populate the world map with disk data

            data -> xml data dict

            return -> None

        """
        # Get macro cell position and world position 
        cell_pos = lambda x, y: ((x >> 3, y >> 3, ((x << 5) + 16, (y << 5) + 16)))

        # Enemies
        for e in data[cls.MAP_ENEMY_XML]:
            cx, cy, pos = cell_pos(e.x, e.y) 

            # Replace needed due to editor having access to font rendering 
            e = e._replace(x=e.x, y=e.y, id=e.id, debug_name=cls.fontRender(e.id))

            cls.w_Cells_Layers[cls.E_ID_ENEMY][cy][cx][pos] = e
        
        cls.es_update('id_enemy_cnt', len(data[cls.MAP_ENEMY_XML]))

        # Lights
        for l in data[cls.MAP_LIGHT_XML]:
            cx, cy, pos = cell_pos(l.x, l.y) 
            cls.w_Cells_Layers[cls.E_ID_LIGHT][cy][cx][pos] = l

        cls.es_update('id_light_cnt', len(data[cls.MAP_LIGHT_XML]))

        # Decals
        for d in data[cls.MAP_DECAL_XML]:
            cx, cy = (d.pos[0] >> 5) >> 3, (d.pos[1] >> 5) >> 3
            tex = cls.ed_transform.rotate(cls.dh_all_decals[d.name], d.orient)
            w, h = tex.get_size()

            # Replace needed due to editor having access to textures only
            d = d._replace(tex=tex, name=d.name, pos=d.pos, w=w, h=h, orient=d.orient)

            cls.w_Cells_Layers[cls.E_ID_DECAL][cy][cx].append(d)

        cls.es_update('id_decal_cnt', len(data[cls.MAP_LIGHT_XML]))

        # Wires
        for w in data[cls.MAP_WIRE_XML]:
            cx1, cy1 = (w.p1[0] - 1 >> 5) >> 3, (w.p1[1] - 1 >> 5) >> 3
            cx2, cy2 = (w.p2[0] - 1 >> 5) >> 3, (w.p2[1] - 1 >> 5) >> 3
 
            cls.w_Cells_Layers[cls.E_ID_WIRE][cy1][cx1].append(w)
            cls.w_Cells_Layers[cls.E_ID_WIRE][cy2][cx2].append(w)

        cls.es_update('id_wire_cnt', len(data[cls.MAP_WIRE_XML]))

        # Pickups
        for p in data[cls.MAP_PICKUP_XML]:
            cx, cy, pos = cell_pos(p.x, p.y)
            p = p._replace(x=p.x, y=p.y, id=p.id, content=p.content, value=p.value, 
                           debug_name=cls.fontRender("{} : {}".format(p.content if p.content else p.id, p.value)))
            cls.w_Cells_Layers[cls.E_ID_PICKUP][cy][cx][pos] = p

        cls.es_update('id_pickup_cnt', len(data[cls.MAP_PICKUP_XML]))




    @classmethod
    def __w_wallBuilder(cls, w, h):
        """
            Create a generators over the walls of the newmap

            Go along the edges of the 2d array in clockwise

            w/h -> 2d array width/height

            return -> Generator over map edges in clockwise returning (texture_id, orientation, x, y)

        """
        # Note: Need to add scaling of walls from center of the map
        
        # The 4 int's are: (texture id, orientation, x, y) 
        
        # Start from Topleft -> right
        yield 1, 0, 0, 0    
        for x in xrange(1, w - 1): yield 2, 0, x, 0

        # From Topright -> down
        yield 1, 270, w - 1, 0  
        for y in xrange(1, h - 1): yield 2, 90,  w - 1, y

        # Bottomright -> left
        yield 1, 180, w - 1, h - 1 
        for x in xrange(w - 2, 0, -1): yield 2, 180, x, h - 1

        # Bottomleft -> up
        yield 1, 90, 0, h - 1 
        for y in xrange(h - 2, 0, -1): yield 2, 270, 0, y   



    @classmethod
    def w_renderWorld(cls, surface, active_tool):
        """
            Render the world

            layer -> Which layer to render
            surface -> To which surface to draw on
            active_tool -> Active tool id

            return -> None

        """
        dx, dy = -int(cls.w_Pos[0]) >> 8, -int(cls.w_Pos[1]) >> 8    # Spatial pos

        disp_extra = {-1: set(),     # Chunk sectors
                       cls.E_ID_DECAL:     set(),
                       cls.E_ID_COLLISION: set(),
                       cls.E_ID_LIGHT:     set(),
                       cls.E_ID_ENEMY:     set(),
                       cls.E_ID_PICKUP:    set(),
                       cls.E_ID_WIRE:      set()}
        
        #cls.w_render_decals(surface, active_tool, 3)

        for layer in cls.w_Blit_Order:
            
            if not cls.w_Display_Layer[layer][0]:
                continue 
            
            for y in xrange(dy - 2, dy + 3):
                if y < 0 or y > cls.w_Size[1] - 1: 
                    continue
                for x in xrange(dx - 2, dx + 3):
                    if x < 0 or x > cls.w_Size[0] - 1: 
                        continue
                    
                    if callable(cls.w_Display_Layer[layer][1]):
                        # Returns id and extra display content or None
                        token = cls.w_Display_Layer[layer][1](x, y, surface, active_tool)
                        if token is not None and token[0] in disp_extra:
                            disp_extra[token[0]].update(token[1])    

                    # Rest are world surfaces
                    else:
                        px, py, tex = cls.w_Cells_Layers[layer][y][x]
                        px, py = cls.w_homePosition(px, py) 
                        surface.blit(tex, (px, py))
                        if cls.w_Display_Layer[-1][0]:
                            disp_extra[-1].add((int(px), int(py), cls.ed_chunk_size_raw, cls.ed_chunk_size_raw))  

        
        # Render extra display info about the current active entities (Based on the current active tool)
        for k, v in disp_extra.iteritems():
            if k == -1: continue
            if v: cls.w_Display_Layer[k][1](surface=surface, list_of_strs=v)         

        # Display the chunk sectors
        if disp_extra[-1]:
            for sector in disp_extra[-1]: cls.ed_draw_rect(surface, (0xff, 0xff, 0x0), sector, 1)

        # Keep spawn/end point rendering last on the render stack
        for flag in cls.w_SpawnEnd:
            if flag is None: continue
            pos = cls.w_homePosition(flag.x * 32, flag.y * 32) 

            surface.blit(cls.ElementTextures[43 if flag.id == 'id_spawn' else 44], pos)

    

    @classmethod
    def w_render_decals(cls, x=0, y=0, surface=None, tool_id=-1, list_of_strs=None):
        """
            Render decals

            x, y -> Render position
            surface -> Surface which to render on
            tool_id -> Current active tool id
            layer_id -> Which render layer this is
            list_of_strs -> Data rendered last on renderstack

            return -> None

        """
        if list_of_strs is not None:
            for decal in list_of_strs:
                cls.__w_ShowDecalOrigin(surface, (decal,))  

        else:  
            extra_info = set()

            for decals in cls.w_Cells_Layers[cls.E_ID_DECAL][y][x]:
                posx, posy = cls.w_homePosition(*decals.pos) 
                surface.blit(decals.tex, (posx, posy))
                # Add origin markers for the decals to be more visible
                if tool_id == cls.E_ID_DECAL:
                    origin = (int(posx) + decals.w / 2, 
                              int(posy) + decals.h / 2)
                    extra_info.add(origin) 

            return tool_id, extra_info


    @classmethod
    def w_render_collisions(cls, x=0, y=0, surface=None, tool_id=-1, list_of_strs=None):
        """
            -- || --

            return -> None

        """
        if list_of_strs is not None:
            for collision in list_of_strs:
                cls.__w_ShowCollisionOrigin(surface, *collision)  
            
        else:   
            # Skip rendering any collision unless the tool is active (Move this out from this function
            #                                                         to save a function call)
            if not tool_id == cls.E_ID_COLLISION:
                return None

            extra_info = set()

            for key in cls.w_Cells_Layers[cls.E_ID_COLLISION][y][x].iterkeys():
                posx, posy = cls.w_homePosition(*key, _round=1)
                extra_info.add((posx, posy))

            return tool_id, extra_info


    @classmethod
    def w_render_lights(cls, x=0, y=0, surface=None, tool_id=-1, list_of_strs=None):
        """
            -- || --

            return -> None

        """
        if list_of_strs is not None:
            for light in list_of_strs:
                cls.ed_draw_aacircle(surface, *light) 
            
        else: 
            extra_info = set()

            for light in cls.w_Cells_Layers[cls.E_ID_LIGHT][y][x].itervalues():
                posx, posy = cls.w_homePosition((light.x << 5) + 16, (light.y << 5) + 16, _round=1)
                # Render light radius when the light tool is active
                if tool_id == cls.E_ID_LIGHT:
                    extra_info.add((posx, posy, light.radius, light.color))

                # Display the light icon
                surface.blit(cls.ElementTextures[40], (posx - 16, posy - 16)) 

            return tool_id, extra_info

    @classmethod
    def w_render_enemies(cls, x=0, y=0, surface=None, tool_id=-1, list_of_strs=None):
        """
            -- || --

            return -> None

        """
        if list_of_strs is not None:
            for enemy in cls.w_renderEntityNameBackground(surface, list_of_strs):
                surface.blit(*enemy)
            
        else: 
            extra_info = set()

            for enemy in cls.w_Cells_Layers[cls.E_ID_ENEMY][y][x].itervalues():
                posx, posy = cls.w_homePosition((enemy.x << 5) + 16, (enemy.y << 5) + 16, _round=1)
                if tool_id == cls.E_ID_ENEMY:
                    extra_info.add((enemy.debug_name, (posx, posy)))    

                surface.blit(cls.ElementTextures[42], (posx - 16, posy - 16)) 

            return tool_id, extra_info  


    @classmethod
    def w_render_pickups(cls, x=0, y=0, surface=None, tool_id=-1, list_of_strs=None):
        """
            -- || --

            return -> None

        """
        if list_of_strs is not None:
            for pickup in cls.w_renderEntityNameBackground(surface, list_of_strs):
                surface.blit(*pickup)  
        
        else:
            extra_info = set()

            for pickup in cls.w_Cells_Layers[cls.E_ID_PICKUP][y][x].itervalues():
                posx, posy = cls.w_homePosition((pickup.x << 5) + 16, (pickup.y << 5) + 16, _round=1)
                if tool_id == cls.E_ID_PICKUP:
                    extra_info.add((pickup.debug_name, (posx, posy))) 

                surface.blit(cls.ElementTextures[41], (posx - 16, posy - 16))

            return tool_id, extra_info


    @classmethod
    def w_render_wires(cls, x=0, y=0, surface=None, tool_id=-1, list_of_strs=None):
        """
            -- || --

            return -> None

        """
        if list_of_strs is not None:
            for wire in list_of_strs:
                cls.__w_ShowDecalOrigin(surface, [wire[x:2+x] for x in xrange(0, len(wire), 2)])    
            
        else:
            # Renders the line twice from both ends
            extra_info = set()

            for wire in cls.w_Cells_Layers[cls.E_ID_WIRE][y][x]:
                pos1 = cls.w_homePosition(*wire.p1, _round=1)
                pos2 = cls.w_homePosition(*wire.p2, _round=1)
                w = pos1 + pos2
                
                cls.ed_draw_line(surface, wire.color, pos1, pos2)
                
                if tool_id == cls.E_ID_WIRE: 
                    extra_info.add(w)  

            return tool_id, extra_info


    @classmethod
    def w_setupWorldState(cls):
        """
            Setup world render functions/variables

            return -> None

        """
        # Convert from dict to class variables
        #for key, value in cls.w_enum.iteritems():
        #    setattr(World, key, value)

        # Setup order in which the layers are rendered in
        cls.w_Blit_Order = (cls.E_ID_GROUND, cls.E_ID_DECAL,  cls.E_ID_OBJECT,
                            cls.E_ID_WIRE,   cls.E_ID_WALL,   cls.E_ID_LIGHT,
                            cls.E_ID_ENEMY,  cls.E_ID_PICKUP, cls.E_ID_COLLISION)  

        # Setup the rendering functions
        cls.w_Display_Layer[cls.E_ID_DECAL][1]     = cls.w_render_decals
        cls.w_Display_Layer[cls.E_ID_COLLISION][1] = cls.w_render_collisions
        cls.w_Display_Layer[cls.E_ID_LIGHT][1]     = cls.w_render_lights
        cls.w_Display_Layer[cls.E_ID_ENEMY][1]     = cls.w_render_enemies
        cls.w_Display_Layer[cls.E_ID_PICKUP][1]    = cls.w_render_pickups
        cls.w_Display_Layer[cls.E_ID_WIRE][1]      = cls.w_render_wires


    @classmethod
    def w_renderEntityNameBackground(cls, surface, list_of_strs):
        """
            Render entity names with the last one (Nearest to mouseindex) getting black background

            surface -> Active screen surface
            list_of_strs -> List of font rendered strings

            return -> None

        """
        mx, my = cls.w_Data['mouseIndex']
        mx, my = cls.w_homePosition((mx << 5) + 16, (my << 5) + 16, _round=1)
        last = len(list_of_strs)
        
        # Sort the strings based on distance to mouse index (so the last one gets black background)
        for enum, text in enumerate(sorted(list_of_strs, 
                                           key=lambda p: cls.ed_hypot(mx - p[1][0], 
                                                                      my - p[1][1]), reverse=1), start=1):
            w, h = text[0].get_size()
            x = text[1][0] - w / 2
            y = text[1][1] - (h + 16)
            if enum == last:
                # Last one gets a black background to make it more visible 
                # (Which is the pickup nearest mouse index)
                cls.ed_draw_rect(surface, (0x0, 0x0, 0x0), (x - 2, y + 4, w + 4, h - 6)) 
            
            yield text[0], (x, y)
    

    @classmethod
    def w_renderWorldCell(cls, surface, tool_id):
        """
            Render cell associated stuff such as enemies, lights, collisions etc...

            surface -> To which surface to draw on
            tool_id -> Active tool id 

            return -> None

        """
        dx, dy = -int(cls.w_Pos[0]) >> 5, -int(cls.w_Pos[1]) >> 5    # Spatial pos

        for y in xrange(dy - cls.ed_frags_per_col, dy + cls.ed_frags_per_col + 1):
            if y < 0 or y > cls.w_Size[5] - 1: 
                continue
            for x in xrange(dx - cls.ed_frags_per_row, dx + cls.ed_frags_per_row + 1):
                if x < 0 or x > cls.w_Size[4] - 1: 
                    continue
                
                cPos = cls.w_Cells_Single[y][x].cell_pos

                fx = int(cPos[0] + cls.ed_resolution[0] / 2 + cls.w_Pos[0]) + 16
                fy = int(cPos[1] + cls.ed_resolution[1] / 2 + cls.w_Pos[1]) + 16
                
                if cls.w_Cells_Single[y][x].cell_light is not None:
                    radius, color = cls.w_Cells_Single[y][x].cell_light 
                    cls.ed_draw_circle(surface, color, (fx, fy), radius, 1)

                if cls.w_Cells_Single[y][x].cell_collision:
                    pass

                if cls.w_Cells_Single[y][x].cell_enemy is not None:
                    pass            

    
    @classmethod
    def __w_ShowDecalOrigin(cls, surface, points):
        """
            Draw small origin indicator for entities

            surface -> ActiveScreen
            x, y -> Pos

            return -> None

        """
        for x, y in points:
            cls.ed_draw_line(surface, (0xff, 0x0, 0x0), (x, y + 1), (x + 16, y + 1), 1)
            cls.ed_draw_line(surface, (0x0, 0xff, 0x0), (x - 1, y), (x - 1, y - 16), 1)

    
    @classmethod
    def __w_ShowCollisionOrigin(cls, surface, x, y):
        """
            Draw a collision marker(X) for cells with collision enabled

            surface -> ActiveScreen
            x, y -> Pos

            return -> None

        """
        cls.ed_draw_line(surface, (0xff, 0x0, 0x0), (x + 4, y +  4), (x + 28, y + 28), 2)
        cls.ed_draw_line(surface, (0xff, 0x0, 0x0), (x + 4, y + 28), (x + 28, y +  4), 2)


    @classmethod
    def w_homePosition(cls, x, y, invert=False, _round=False):
        """
            Maintain proper home position at the center of the screen

            x, y -> Screen coordinates in which the resolution and world position gets added/subtracted to/from
            invert -> Same as above but inverted

            return -> Offset

        """
        if invert: pos = x - (cls.ed_resolution[0] / 2 + cls.w_Pos[0]), y - (cls.ed_resolution[1] / 2 + cls.w_Pos[1]) 
        else: pos = x + (cls.ed_resolution[0] / 2 + cls.w_Pos[0]), y + (cls.ed_resolution[1] / 2 + cls.w_Pos[1])
        if _round: pos = int(pos[0]), int(pos[1])

        return pos



class TkinterResources(VisualResources):

    
    def __init__(self):
        pass

    
    @classmethod
    def bf_initVariables(cls):
        """
            Create Tkinter variables inside class space for sharing

            return -> None

        """
        cls.es_initVariables()  # Statistic stats

        # Map                              # Default values
        cls.bf_mapname     = cls.ed_str(); cls.bf_mapname.set('None') 
        cls.bf_mapwidth    = cls.ed_int(); cls.bf_mapwidth.set(32) 
        cls.bf_mapheight   = cls.ed_int(); cls.bf_mapheight.set(32) 
        cls.bf_mapbase_tex = cls.ed_str()
        cls.bf_mapwall_tex = cls.ed_str()

        # Display
        cls.bf_disp_chunk  = cls.ed_bool()
        cls.bf_disp_gnd    = cls.ed_bool()
        cls.bf_disp_dec    = cls.ed_bool()
        cls.bf_disp_objs   = cls.ed_bool()
        cls.bf_disp_wall   = cls.ed_bool()
        cls.bf_disp_wire   = cls.ed_bool()
        cls.bf_disp_light  = cls.ed_bool()
        cls.bf_disp_enemy  = cls.ed_bool()
        cls.bf_disp_pickup = cls.ed_bool()
        cls.bf_snap_dec    = cls.ed_bool()
        cls.bf_autowalls   = cls.ed_bool()

        # General
        cls.bf_disablePygameEvents = cls.ed_bool()      # -- Hack -- Disable pygame event handling when creating
                                                        #            new Tkinter windows

    
    @ed_killMe
    def bf_newMap(self, root=None):
        """
            Create New Map

            Provide all the context and options for creating/customizating the new map

            return -> None  

        """
        self.bf_disablePygameEvents.set(True)
        
        # Note: The code is structured in the same way as the gui is displaying it
        nm_frame = ed_TopLevel('Map Details', w_takefocus=True)
        nm_frame.attributes('-topmost', 'true')
        nm_frame.grab_set()
        nm_frame.transient(root)

        # Hijack the X quit protocol
        nm_frame.protocol('WM_DELETE_WINDOW', lambda: (self.bf_disablePygameEvents.set(False), 
                                                       nm_frame.destroy(), self.bf_mapname.set('None')))
        
        nm_geo_frame = ed_LabelFrame(nm_frame, 'Map Basics', False)
        nm_geo_frame.grid(row=0, column=0, sticky=self.ed_sticky_full)

        ed_LabelEntry(nm_geo_frame, 'MapName:',  self.bf_mapname,   row=0)
        
        ed_LabelEntry(nm_geo_frame, 'Width:',    self.bf_mapwidth,  row=1)
        tk.Label(nm_geo_frame, text='Mult of 8!').grid(row=1, column=2, padx=5)
        
        ed_LabelEntry(nm_geo_frame, 'Height:',   self.bf_mapheight, row=2)
        tk.Label(nm_geo_frame, text='Mult of 8!').grid(row=2, column=2, padx=5)

        self.ed_separator(nm_geo_frame, orient='horizontal').grid(row=3, columnspan=3, pady=5, padx=5,
                                                                  sticky=self.ed_sticky_vert)
        # Note: Combine the LabelImagePreview & OptionMenu
        
        # Default Ground Texture
        default_tex = self.low_textures.keys()[0]
        nm_preview_1 = ed_LabelImagePreview(nm_geo_frame, 'GroundTexture', default_tex, self.bf_mapbase_tex,  
                                            self.ed_pygameToTkinter(self.low_textures[default_tex]['tex_main']), 4, 0) 

        nm_option_menu_1 = tk.OptionMenu(nm_geo_frame, self.bf_mapbase_tex, *self.low_textures.keys(), 
                                         command=lambda v1: nm_preview_1.setImage(self.ed_pygameToTkinter(\
                                                                                  self.low_textures[v1]['tex_main'])))
        nm_option_menu_1.grid(row=5, column=1, sticky=self.ed_sticky_vert, 
                              columnspan=2, pady=5)

        
        # Default Wall Set
        default_tex = self.mid_textures.keys()[0]
        nm_preview_2 = ed_LabelImagePreview(nm_geo_frame, 'WallSet', default_tex, self.bf_mapwall_tex,  
                                            self.ed_pygameToTkinter(self.mid_textures[default_tex][0]), 6, 0) 

        nm_option_menu_2 = tk.OptionMenu(nm_geo_frame, self.bf_mapwall_tex, *self.mid_textures.keys(), 
                                         command=lambda v1: nm_preview_2.setImage(self.ed_pygameToTkinter(\
                                                                                  self.mid_textures[v1][0])))
        nm_option_menu_2.grid(row=7, column=1, sticky=self.ed_sticky_vert, 
                              columnspan=2, pady=5)

        
        nm_button = tk.Button(nm_frame, text='Create', command=lambda: self.__bf_beforeNewMap(nm_frame))
        nm_button.grid(sticky=self.ed_sticky_vert, padx=5, pady=5)

        # Put the toplevel center of the screen
        ed_centerWidget(nm_frame)
        
        # Set the root wait for toplevel quit
        root.wait_window(nm_frame)
        
        return nm_frame

    
    def __bf_beforeNewMap(self, toplevel_id):
        """
            Before newmap can be created, the input has to be checked and/or corrected

            toplevel_id -> Widget which receives focus if error has occured

            return -> None

        """
        error = False
        try:
            name = self.bf_mapname.get()
            width = self.bf_mapwidth.get() 
            height = self.bf_mapheight.get()

            # Check everything to satisfy minimum details
            if not name:
                self.ed_msg_box.showerror("Empty Name", "Please specify name for the map!")
                error = True

            # Make sure the map width/height are multiples of 8
            elif ((width  % self.ed_chunk_size or width  == 0) or 
                  (height % self.ed_chunk_size or height == 0)):
                self.ed_msg_box.showerror("Incorrect Map Dimensions", 
                                          "Map dimensions are incorrect. They need to be multiple of 8!")
                error = True

            # Map max dimensions are 64 x 64
            elif width > MAX_CUBE_SIZE or height > MAX_CUBE_SIZE:
                self.ed_msg_box.showerror("Incorrect Map Dimensions",
                                          "Map max width/height are 64 x 64!")
                error = True

        except ValueError, Exception:
            # Entries with 'IntVar' expects Integers so we need to prepare for strings on them
            self.ed_msg_box.showerror("Incorrect Values", "Some of the entries has incorrect values!")
            error = True    

        if error: toplevel_id.focus(); return None

        # Succeed! Pass everything for worldbuilder
        toplevel_id.destroy()
        
        self.bf_disablePygameEvents.set(False)

        World.w_createMap(abs(self.bf_mapwidth.get()), abs(self.bf_mapheight.get()), 
                          self.bf_mapbase_tex.get(),   self.bf_mapwall_tex.get())




class BaseFrame(tk.Tk, TkinterResources):
    """
        Base of the Tkinter
        
    """
    def __init__(self, *args, **kw):
        tk.Tk.__init__(self, *args, **kw)
        self.resizable(0, 0)
        
        TkinterResources.bf_initVariables()
                              
        self.title("None - MapEditor"); 
        #   Update the title when newmap is being created via variable tracing
        self.bf_mapname.trace('w', lambda *args: self.title('{} - MapEditor'.format(self.bf_mapname.get())))
        
        #self.resizable(False, False)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.menuBar = tk.Menu(self)
        self.config(padx=5, pady=5, menu=self.menuBar)

        self.menuMap = tk.Menu(self.menuBar, tearoff=0)
        self.menuMap.add_command(label='New',     command=lambda: self.bf_newMap(self))
        self.menuMap.add_command(label='Open...', command=lambda: World.w_createMap(load_from_disk=True))
        self.menuMap.add_command(label='Save...', command=lambda: self.mp_save(World.w_getWorldData))
        self.menuMap.add_separator()
        self.menuMap.add_command(label='Exit',    command=lambda: self.destroy())
        
        self.menuBar.add_cascade(label='Map', menu=self.menuMap)

        self.menuBar.add_command(label='Settings', command=lambda: None, state='disabled')
     
# ------

class ToolFrame(ed_LabelFrame, TkinterResources):
    """
        Create a custom LabelFrame which contains all the tools buttons and options

    """
    def __init__(self, base):
        ed_LabelFrame.__init__(self, base, 'Tools')
        self.grid(row=0, column=0, sticky=self.ed_sticky_full)

        tk.Label(self, text='World Show/Hide')\
        .grid(row=0, column=0, padx=5, sticky=self.ed_sticky_w)

        ed_Checkbutton(self, "Hide Ground",  self.bf_disp_gnd,    1, 0)
        ed_Checkbutton(self, "Hide Objects", self.bf_disp_objs,   1, 1)
        ed_Checkbutton(self, "Hide Walls",   self.bf_disp_wall,   2, 0)
        ed_Checkbutton(self, "Hide Wires",   self.bf_disp_wire,   2, 1)
        ed_Checkbutton(self, "Hide Lights",  self.bf_disp_light,  3, 0)
        ed_Checkbutton(self, "Hide Enemies", self.bf_disp_enemy,  3, 1)
        ed_Checkbutton(self, "Hide Pickups", self.bf_disp_pickup, 4, 0)
        
        self.ed_separator(self, orient='horizontal')\
        .grid(row=5, columnspan=3, pady=15, padx=5, sticky=self.ed_sticky_vert)

        tk.Label(self, text='Decal Settings').grid(row=6, column=0, padx=5, 
                                                   sticky=self.ed_sticky_w)
        
        ed_Checkbutton(self, 'Hide Decals', self.bf_disp_dec, 7, 0)
        ed_Checkbutton(self, 'Snap Decals', self.bf_snap_dec, 7, 1)

        self.ed_separator(self, orient='horizontal')\
        .grid(row=8, columnspan=3, pady=15, padx=5, sticky=self.ed_sticky_vert)

        tk.Label(self, text='Misc Settings')\
        .grid(row=9, column=0, padx=5, sticky=self.ed_sticky_w)
        
        ed_Checkbutton(self, 'AutoWalling', self.bf_autowalls, 10, 0)
        ed_Checkbutton(self, 'Show Sectors', self.bf_disp_chunk, 11, 0)

        self.ed_separator(self, orient='horizontal')\
        .grid(row=12, columnspan=3, pady=15, padx=5, sticky=self.ed_sticky_vert)

        tk.Label(self, text='Light & Wire Color')\
        .grid(row=13, column=0, padx=5, sticky=self.ed_sticky_w)
        
        Lights.l_createColorFrame(self, row=14, column=0)

        self.ed_separator(self, orient='horizontal')\
        .grid(row=15, columnspan=3, pady=15, padx=5, sticky=self.ed_sticky_vert)

        EditorStatistics.es_createStatFrame(self, row=16, column=0)

        self.ed_separator(self, orient='horizontal')\
        .grid(row=17, columnspan=3, pady=15, padx=5, sticky=self.ed_sticky_vert)

        EntityPicker.ep_createEntityFrame(self, row=18, column=0)

        self.ed_separator(self, orient='horizontal')\
        .grid(row=19, columnspan=3, pady=15, padx=5, sticky=self.ed_sticky_vert)

# -------

class PygameFrameToolBar(ed_LabelFrame, TkinterResources):

    # Message explaining what the buttons does
    h_helpstrings = {}

    
    def __init__(self, base, **kw):
        
        ed_LabelFrame.__init__(self, base)

        self.ft_tool_hint_str = self.ed_str(); self.ft_tool_hint_str.set('-')
        self.ft_tool_hint = tk.Label(self, textvariable=self.ft_tool_hint_str)
        self.ft_tool_hint.grid(row=0, column=1, columnspan=16, sticky=self.ed_sticky_w)

        # Floors
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[20]), 1, 1,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Paint Floor")   
        
        # Objects
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[21]), 1, 2,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Place Objects")  
        
        # Walls
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[22]), 1, 3,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Place Walls")
        
        # Decals
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[23]), 1, 4,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Apply Decals")

        self.ed_separator(self, orient='vertical').grid(row=1, column=5, padx=10, 
                                                        sticky=self.ed_sticky_hori) 
        
        # Collisions
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[24]), 1, 6,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Edit World Collisions") 
        
        # Lights
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[25]), 1, 7,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Place Lights")

        # Wire
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[26]), 1, 8,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Place Wires")    

        # Enemies
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[27]), 1, 9,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Place Enemies")

        # Pickups
        ed_Button(self, self.ed_pygameToTkinter(self.ElementTextures[28]), 1, 10,
                  tool_h_l=self.ft_tool_hint_str, tool_h_t="Place Pickups")

        self.h_initHelpStrings()


    @classmethod
    def h_initHelpStrings(cls):
        """
            Provide help messages for the buttons explaining what they do

            return -> None

        """
        # NOTE: Move these to the buttons themself
        helpstrFont = cls.ed_font(cls.ElementFonts[1], 12)

        # Small function for converting text strings to surface strings
        h_createStrings = lambda strs: [helpstrFont.render(s, 1, (0xff, 0xff, 0xff)) for s in strs] 

        # Convert user keys to string representation
        str_key = {name : cls.ed_key.name(rep).upper() for name, rep in cls.ed_keys.iteritems()}

        cls.h_helpstrings[-1] = h_createStrings(("Hold '{}' to place ('LMB' - Spawnpoint, 'RMB' - Optional Endpoint)".format('L_CTRL'),))

        # Ground
        cls.h_helpstrings[0] = h_createStrings(("'LMB' - Apply",
                                                "'RMB' - FloodFill",
                                                "Press '{}', to open '{}' selection window".format(str_key['action_1'], 'ground textures'),
                                                "'{}', to rotate 90\xb0".format(str_key['action_rot'])))

        # Objects
        cls.h_helpstrings[1] = h_createStrings(("'LMB' - Apply / 'RMB' - Delete",
                                                "Press '{}', to open '{}' selection window".format(str_key['action_1'], 'object textures'), 
                                                "'{}', to rotate 90\xb0".format(str_key['action_rot'])))

        # Walls
        cls.h_helpstrings[2] = h_createStrings(("'LMB' - Apply / 'RMB' - Delete",
                                                "Press '{}', to open '{}' selection window".format(str_key['action_1'], 'walls textures'), 
                                                "'{}', to rotate 90\xb0 (Manual mode)".format(str_key['action_rot']),
                                                "'{}' / '{}', shift between segments (left/right) (Manual mode)".format(str_key['action_2'], 
                                                                                                                        str_key['action_3'])))

        # Decals
        cls.h_helpstrings[3] = h_createStrings(("'LMB' - Apply / 'RMB' - Delete",
                                                "Press '{}', to open '{}' selection window".format(str_key['action_1'], 'decals textures'), 
                                                "'{}', to rotate 45\xb0".format(str_key['action_rot'])))

        # Collisions
        cls.h_helpstrings[4] = h_createStrings(("'LMB' - Apply / 'RMB' - Delete",))

        
        # Lights
        cls.h_helpstrings[5] = h_createStrings(("'LMB' - Apply / 'RMB' - Delete",
                                                "Use the Tools menu to change the color of the light"))

        # Wire
        cls.h_helpstrings[6] = h_createStrings(("'LMB' - Apply / 'RMB' - Delete",
                                                "Use the Tools menu to change the color of the wire"))

        # Enemy
        cls.h_helpstrings[7] = h_createStrings(("'LMB' - Apply / 'RMB' - Delete",))

        # Pickup
        cls.h_helpstrings[8] = h_createStrings(("'LMB' - Apply / 'RMB' - Delete",))

    
    @classmethod
    def h_render(cls, surface, _id):
        """
            Render the help string based on the toolbar button selected (id)

            return -> None

        """ 
        vert = 0
        for r in cls.h_helpstrings[_id]:
            surface.blit(r, (4, vert))
            vert += r.get_height() - 4 
        


class PygameFrame(TkinterResources, World, DeltaTimer):
    """
        Create a custom 'Frame' which contains the SDL window and pygame related stuff

    """
    # It's somewhat hard to get Tkinter and Pygame to work together properly
    # There are small hacks here and there to force them to work, but it also 
    # introduces possible errors that can crash the program

    # Need to investigate and learn more about the events especially

    def __init__(self, base):
        # The pygame SDL window takes the whole frame, so this class needs 2 frames
        pygameBaseFrame = tk.LabelFrame(base, text='EditorView')
        pygameBaseFrame.config(padx=5, pady=5)
        pygameBaseFrame.grid(row=0, column=1, sticky=self.ed_sticky_full)

        # Frame taken by the Pygame 
        pygameSDLFrame = tk.Frame(pygameBaseFrame, width=self.ed_resolution[0],
                                                   height=self.ed_resolution[1])

        pygameSDLFrame.config(cursor='None')
        pygameSDLFrame.grid(row=1, column=0, sticky=self.ed_sticky_full)

        
        self.ed_environ['SDL_WINDOWID'] = str(pygameSDLFrame.winfo_id())
        self.ed_environ['SDL_VIDEODRIVER'] = self.ed_sdl_driver

        self.ed_init_everything()
        self.screen = pygame.display.set_mode(self.ed_resolution, pygame.NOFRAME)

        self.initVisualsAndExtModules()     

        self.pygameBaseToolBar = PygameFrameToolBar(pygameBaseFrame)
        self.pygameBaseToolBar.grid(row=0, column=0, pady=2, sticky=self.ed_sticky_vert) 

        self.ed_mouse.set_visible(0)        # Pygame default cursor is messed up with the SDL window. Disable it

        # Add traces to the layers
        self.bf_disp_gnd.trace('w',   lambda *args: self.w_toggleLayers(self.E_ID_GROUND))
        self.bf_disp_objs.trace('w',  lambda *args: self.w_toggleLayers(self.E_ID_OBJECT))
        self.bf_disp_wall.trace('w',  lambda *args: self.w_toggleLayers(self.E_ID_WALL))
        self.bf_disp_wire.trace('w',  lambda *args: self.w_toggleLayers(self.E_ID_WIRE))
        self.bf_disp_dec.trace('w',   lambda *args: self.w_toggleLayers(self.E_ID_DECAL))
        self.bf_disp_light.trace('w', lambda *args: self.w_toggleLayers(self.E_ID_LIGHT))
        self.bf_disp_enemy.trace('w', lambda *args: self.w_toggleLayers(self.E_ID_ENEMY))
        self.bf_disp_chunk.trace('w', lambda *args: self.w_toggleLayers(-1))

        
        # More traces to extra display/settings
        self.extra_options = {'auto_wall' : ed_BitToggle(),
                              'snap_dec'  : ed_BitToggle(),
                              'event_stop': ed_BitToggle()}

        self.bf_snap_dec.trace(           'w', lambda *args: self.extra_options['snap_dec'].bit_toggle())
        self.bf_autowalls.trace(          'w', lambda *args: self.extra_options['auto_wall'].bit_toggle())
        self.bf_disablePygameEvents.trace('w', lambda *args: self.extra_options['event_stop'].bit_toggle())

        self.w_setupWorldState()

        # Clear all events queued when the SDL window has no focus to clear 
        self.clear_event_stack = 1      # -- Hack --

        # Control painting/deleting by applying the actions once per cell
        self.pf_old_index = [0, 0]

        # Functions for texture/object applying 
        self.build_functions = {self.E_ID_GROUND:    self.__pf_applyGround,
                                self.E_ID_OBJECT:    self.__pf_applyObject,
                                self.E_ID_WALL:      self.__pf_applyWallset,
                                self.E_ID_DECAL:     self.__pf_applyDecals,
                                self.E_ID_COLLISION: self.__pf_editCollisions,
                                self.E_ID_LIGHT:     self.__pf_applyLights,
                                self.E_ID_ENEMY:     self.__pf_applyEnemies,
                                self.E_ID_PICKUP:    self.__pf_applyPickups,
                                self.E_ID_WIRE:      self.__pf_applyWires}

        # Reserved F keys for the toolbar (If you need more than F12, extend via using bitwise mods + f keys?)
        self.tso_reserved_keys = set([pygame.K_F1 + f for f in xrange(ed_Button.ed_getButtonStates(True))])
        
        # Index of which toolbar button is active (-1 for None is active)
        self.toolbar_action = -1


    def pf_RunPygameLogic(self):
        """
            pygame loop

            return -> None

        """
        mouse_focus = self.ed_mouse.get_focused()
        mx, my = self.ed_mouse.get_pos()

        if self.clear_event_stack and mouse_focus and not self.extra_options['event_stop']:
            # -- Hack --
            pygame.event.clear(); self.clear_event_stack = 0

        # Get the toolbar action we need
        self.toolbar_action = ed_Button.ed_getButtonStates()

        EntityPicker.ep_controlState(self.toolbar_action)
        
        # Render the world
        if not self.tso_textureSelectMode: self.w_renderWorld(self.screen, self.toolbar_action)

        # Note: There might be an error in Tkinter or Pygame that
        #       can fatally crash the Python if you handle Pygame events at the sametime
        #       when you're tinkering with the Tkinter stuff. 
        #       While doing so, this error can occur: 
        #           "Fatal Python error: PyEval_RestoreThread: NULL tstate"
        #           Fix here is to block events being processed when mouse cursor 
        #           Has exited the SDL frame

        mouse_btn_id = 0

        if mouse_focus and not self.extra_options['event_stop']:
            # -- Hack --
            # Only handle events if the sdl window has focus
            pygame.event.pump()
            for event in pygame.event.get():
                if event.type == pygame.KEYUP:
                    if event.key in self.tso_reserved_keys:
                        # Offset the event key to start from 0
                        ed_Button.ed_setButtonState(event.key - pygame.K_F1)

                    # Keys associated with texturing (All)
                    elif self.tso_setMode != -1:
                        # Texture: All 
                        if event.key == self.ed_keys['action_1']:
                            self.tso_toggleTextureSelection(self.screen)

                        # Rotate texture
                        elif event.key == self.ed_keys['action_rot']:
                            self.tso_updateDataTexture(1, self.tso_setMode)

                        # Functions/keys associated with walls
                        elif self.tso_setMode == 2: 
                            if event.key == self.ed_keys['action_2']:
                                self.tso_updateDataTexture(2, self.tso_setMode, d='l')

                            elif event.key == self.ed_keys['action_3']:
                                self.tso_updateDataTexture(2, self.tso_setMode, d='r')

                
                # Mousewheel capturing
                if event.type == pygame.MOUSEBUTTONUP:
                    # Texture window scrolling
                    if self.tso_textureSelectMode: 
                        if event.button == self.ed_scroll_wheeldown:
                            self.tso_updateScrollLevel(1);
                        
                        elif event.button == self.ed_scroll_wheelup: 
                            self.tso_updateScrollLevel(-1)

                    # Light size
                    #elif self.toolbar_action == 5:
                    #    if event.button == 5:   self.l_changeSize(-32)
                    #    elif event.button == 4: self.l_changeSize(32) 

                    # Store which button was pressed
                    mouse_btn_id = event.button


        else:
            # Get ready to flush event queue once focus has been restored to SDL window
            # -- Hack --
            self.clear_event_stack = 1

    
        keys = self.ed_key.get_pressed()
        mods = self.ed_key.get_mods()    # For special operations (Bitwise)
        
        speed = (self.ed_scroll_speed * (2 if mods & self.ed_keys['shift_l'] else 1)) * self.dt_getDelta()
        if keys[self.ed_keys['up']]:
            if self.tso_textureSelectMode: pass
            else: self.w_moveWorld(y=speed) 

        elif keys[self.ed_keys['down']]:
            if self.tso_textureSelectMode: pass
            else: self.w_moveWorld(y=-speed) 
        
        if keys[self.ed_keys['right']]:
            if self.tso_textureSelectMode: pass
            else: self.w_moveWorld(x=-speed) 
        
        elif keys[self.ed_keys['left']]:
            if self.tso_textureSelectMode: pass
            else: self.w_moveWorld(x=speed) 

        # Apply Objects/Textures
        if mouse_focus and not self.tso_textureSelectMode:
            index = self.pf_mouseSpatialPos(mx, my) 
            
            if self.toolbar_action != -1: 
                self.pf_decorateWorld(index, self.screen, self.toolbar_action, mouse_btn_id) 
            else:
                # Control setting spawn/end point
                self.__pf_setSpawnEnd(index, self.screen, mods, mouse_btn_id)    

        # Render the texture/object selection frames when needed
        self.tso_toolBarHandler(self.screen, self.toolbar_action, mouse_btn_id)

        self.pygameBaseToolBar.h_render(self.screen, self.toolbar_action)

        if mouse_focus: self.screen.blit(self.ElementCursors[1][0], (mx, my))

        pygame.display.flip()
        
        self.screen.fill(self.ed_bg_color)

        self.es_update('id_framerate', round(self.dt_fps(), 1))

    
    def pf_chunkSpatialPos(self, wx, wy, cxs, cys):
        """
            Get the position inside chunks

            wx, wy -> World position (x, y)
            cxs, cys -> Chunk position (x, y)

            return -> Position (x, y) from chunk topleft

        """
        return (32 * wx - self.ed_chunk_size_raw * cxs,
                32 * wy - self.ed_chunk_size_raw * cys) 

    
    def pf_chunkClearArea(self, layer, chunk_index, rect, clean_color=(0x0, 0x0, 0x0, 0x0)):
        """
            Clean the specified chunk area with clear alpha color

            layer -> Which world layer the clean will be applied to
            chunk_index -> World chunk (x, y)
            rect -> Cleaning area (x, y, w, h)
            clean_color -> Color used repaint the area 

            return -> None

        """
        self.ed_draw_rect(self.w_Cells_Layers[layer][chunk_index[1]][chunk_index[0]][-1], 
                          clean_color, rect)
        #
    
    
    def pf_mouseSpatialPos(self, mousex, mousey, shift_l=5):
        """
            Get cell spatial position from mouse position and highlight it

            mousex/mousey -> Mouse position
            shift_l -> divider

            return -> World index (x, y)

        """ 
        wx, wy = self.w_homePosition(mousex, mousey, invert=1)
        
        if -1 < wx < self.w_Size[2] and -1 < wy < self.w_Size[3]:
            snap = int(wx) >> shift_l, int(wy) >> shift_l
            x = self.ed_resolution[0] / 2 + self.w_Pos[0] + 32 * snap[0]
            y = self.ed_resolution[1] / 2 + self.w_Pos[1] + 32 * snap[1]   
            
            return snap, x, y
        else: 
            return -1           

    
    def pf_decorateWorld(self, index, surface, func, mouse_btn_id):
        """
            Main handler for the world edit functions

            index -> Cell index 
            surface -> Screen surface
            func ->
            mouse_btn_id -> Id of mouse button key

            return -> None

        """
        # Cell location, from topleft -> x, y
        index, x, y = index if index != -1 else (-1, -1, -1)
        if index == -1: return None 
        
        # continuously pressing down 
        if func in (self.E_ID_GROUND, self.E_ID_WALL):    # Which actions can use this functionality
            key = self.ed_mouse.get_pressed()
            
            # Stop from continually applying to same cell
            if self.pf_old_index != index and (key[0] or key[2]):
                self.pf_old_index = index
                _apply = 1
            else:
                _apply = 0

            action = (key[0] or (2 if key[2] else 0)) if _apply else 0
        
        else:
            # Needs click once per cell
            action = 1 if mouse_btn_id == 1 else 2 if mouse_btn_id == 3 else 0    

        self.w_Data['mouseIndex'] = index
        self.build_functions[func](index, int(x), int(y), self.screen, action, func)


    def __pf_setSpawnEnd(self, index, surface, kmods, mouse_btn_id):
        """
            Set player Spawn/(End <- Optional) point

            index -> world index
            kmods -> keyboard mods
            mouse_bnt_id -> mouse button key id

            return -> None

        """
        index, x, y = index if index != -1 else (-1, -1, -1)
        if index == -1: 
            return None

        if kmods & self.ed_keys['ctrl_l']:
            # Convert mouse button id's 1 & 3 to 0 & 1
            action = 0 if mouse_btn_id == 1 else 1 if mouse_btn_id == 3 else -1

            self.ed_draw_rect(surface, (0xff, 0xff, 0x0), (x, y, 32, 32), 1)

            if action in (0, 1):
                # Block from applying the flags to same position
                inv_action = action ^ 1
                if self.w_SpawnEnd[inv_action] is not None:
                    if index[0] == self.w_SpawnEnd[inv_action].x and \
                       index[1] == self.w_SpawnEnd[inv_action].y:
                        return None 

                post_type = 'id_spawn' if action == 0 else 'id_finish' 
                self.w_SpawnEnd[action] = Ed_CellPoint(*index, id=post_type)
    
    
    def __pf_applyGround(self, index, x, y, surface=None, action_key=0, set_id=0):
        """
            Paint ground

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id ->  Id used to what category is this part of

            return -> None

        """

        tex_data = self.tso_dataTextures[set_id]
        if not tex_data['name']: return None
        
        cx, cy = index[0] >> 3, index[1] >> 3

        self.ed_draw_rect(surface, (0xff, 0xff, 0x0), (x, y, 32, 32), 1)

        tex = self.tso_tex_modes[tex_data['set']][tex_data['name']]['tex_main']
        rot = self.ed_transform.rotate(tex, tex_data['rot']) 

        surface.blit(self.ed_fadeImage(rot, 0x80, 1), (x, y))
        
        if action_key == 1:
            # Store the texture id & angle
            self.w_Cells_Single[index[1]][index[0]].cell_lowTex = (tex_data['name'], tex_data['rot'] / 90)

            self.w_Cells_Layers[self.E_ID_GROUND][cy][cx][-1]\
            .blit(rot, self.pf_chunkSpatialPos(index[0], index[1], cx, cy))

        elif action_key == 2:
            self.__pf_floodFill(index, rot, tex_data['name'], tex_data['rot'] / 90)
    
    
    @EditorStatistics.es_update_decorator(_id='id_object_cnt')
    def __pf_applyObject(self, index, x, y, surface=None, action_key=0, set_id=0):
        """
            Apply objects to the world

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id ->  Id used to what category is this part of

            return -> None

        """
        # NOTE: Would have worked better just to blit these objects from a list

        tex_data = self.tso_dataTextures[set_id]
        if not tex_data['name']: return None

        # Get the selected texture
        tex = self.tso_tex_modes[tex_data['set']][tex_data['name']]['tex_main']  
        angle = self.tso_dataTextures[set_id]['rot']    # Get the stored rotation 
        
        rot = self.ed_transform.rotate(tex, angle)  
        
        sx, sy = rot.get_size()
        cx, cy = sx >> 5, sy >> 5    # Cells needed by the object

        if not self.__pf_checkPlacement(index, (cx, cy)):
            placement = 0; pcolor = 0xff, 0x0, 0x80
        
        else:
            placement = 1; pcolor = 0xff, 0xff, 0x0     
            
            # Display a fade version of the selected object
            surface.blit(self.ed_fadeImage(rot, 0x80), (x, y))

        # Display small direction arrow from the middle of the texture
        self.__pf_displayDirection(surface, x + sx / 2, y + sy / 2, angle)
        
        # Rect around the object for giving info if the object can be applied
        # Yellow: Available, DeepPink: Unavailable  
        self.ed_draw_rect(surface, pcolor, (x, y, sx, sy), 1)

        # Every check has passed. Apply the object
        # Since all the main cells are grouped up in chunks. We need to figure out
        # which cells the object wants to occupy
        
        # Apply
        if action_key == 1 and placement:
            chunks_blitted = []    # Mark the chunks which has received the object texture already

            n = 3 
            # Locate all the chunks indexes the object might occupy
            topleft  =  index[0] >> n,            index[1] >> n
            topright = (index[0] + cx - 1) >> n,  index[1] >> n
            botleft  =  index[0] >> n,           (index[1] + cy - 1) >> n  
            botright = (index[0] + cx - 1) >> n, (index[1] + cy - 1) >> n 

            base_index = self.pf_chunkSpatialPos(index[0], index[1], topleft[0], topleft[1])
            
            self.w_Cells_Layers[self.E_ID_OBJECT][topleft[1]][topleft[0]][-1].blit(rot, base_index)
            
            chunks_blitted.append((topleft, base_index))  

            # Multi chunk blit
            for c in (topright, botleft, botright):
                if any([c == _c[0] for _c in chunks_blitted]): continue

                base_index = self.pf_chunkSpatialPos(index[0], index[1], c[0], c[1])
                
                self.w_Cells_Layers[self.E_ID_OBJECT][c[1]][c[0]][-1].blit(rot, base_index)

                chunks_blitted.append((c, base_index))

            # All indexes occupied by the object
            stored_indexes = [(index[0] + _x, index[1] + _y) for _x in xrange(cx) for _y in xrange(cy)]

            # Only the topleft most index stored the (set, texture id) & angle
            self.w_Cells_Single[index[1]][index[0]].cell_objTex = (tex_data['name'], tex_data['rot'] / 90)

            # The rest of the cells gets the link data between the cells occupied by the object 
            for i in stored_indexes:
                self.w_Cells_Single[i[1]][i[0]].cell_link = (stored_indexes, chunks_blitted, (cx, cy))

            return 1
        
        # Delete
        elif action_key == 2 and self.w_Cells_Single[index[1]][index[0]].cell_link is not None:
            obj_data = self.w_Cells_Single[index[1]][index[0]].cell_link[:]    # Copy

            # Delete links
            for _del in obj_data[0]: self.w_Cells_Single[_del[1]][_del[0]].cell_link = None

            # Index 0 on the link list contains data about the obj
            index_0_data = obj_data[0][0]          # Reset it also
            self.w_Cells_Single[index_0_data[1]][index_0_data[0]].cell_objTex = None, 0 

            paint_area = 32 * obj_data[2][0], 32 * obj_data[2][1]
            
            # Repaint the areas taken by the object
            for paint in obj_data[1]:
                chunk, blit_pos = paint[0:2]
                self.pf_chunkClearArea(1, chunk, (blit_pos[0], blit_pos[1], paint_area[0], paint_area[1]))

            return -1
    

    @EditorStatistics.es_update_decorator(_id='id_wall_cnt')
    def __pf_applyWallset(self, index, x, y, surface=None, action_key=0, set_id=0):
        """
            Apply walls in manual or auto mode 

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id ->  Id used to what category is this part of

            return -> None

        """
        tex_data = self.tso_dataTextures[set_id]
        if not tex_data['name']: return None

        cx, cy = index[0] >> 3, index[1] >> 3

        base_index = self.pf_chunkSpatialPos(index[0], index[1], cx, cy)
        
        if self.extra_options['auto_wall']:
            self.ed_draw_rect(surface, (0xff, 0xff, 0x0), (x, y, 32, 32), 1)
        
        else:
            tex = self.tso_tex_modes[tex_data['set']][tex_data['name']][tex_data['windex'][0]]
            rot = self.ed_transform.rotate(tex, tex_data['rot']) 
            
            surface.blit(self.ed_fadeImage(rot, 0xaa, 1), (x, y))

        if action_key == 1:
            no_update = 1 if self.w_Cells_Single[index[1]][index[0]].cell_midTex[0] is not None else 0   
            
            # Auto
            if self.extra_options['auto_wall']:
                # Gathex 5x5 cell sample around the target cell
                _5x5_cells = []
                for ny in xrange(index[1] - 2, index[1] + 3):
                    row = []
                    if not -1 < ny < self.w_Size[5]: continue
                    
                    for nx in xrange(index[0] - 2, index[0] + 3):
                        if not -1 < nx < self.w_Size[4]: continue
                        
                        row.append((nx, ny, self.w_Cells_Single[ny][nx].cell_midTex[1:]))
                    
                    _5x5_cells.append(row)

                for p in ed_AutoWallSolver.aw_autoWallSolve(_5x5_cells, index, self.w_Size[4:]):
                    cx, cy = p[0] >> 3, p[1] >> 3

                    seg_index = self.pf_chunkSpatialPos(p[0], p[1], cx, cy)

                    self.pf_chunkClearArea(2, (cx, cy), (seg_index[0], seg_index[1], 32, 32))

                    _rot, seg = p[2]   

                    self.w_Cells_Single[p[1]][p[0]].cell_midTex = (tex_data['name'], 
                                                                   _rot, 
                                                                   seg)

                    tex = self.tso_tex_modes[tex_data['set']][tex_data['name']][seg]
                    rot = self.ed_transform.rotate(tex, _rot * 90)     
                    self.w_Cells_Layers[self.E_ID_WALL][cy][cx][-1].blit(rot, seg_index) 
            
            # Manual
            else:
                self.w_Cells_Single[index[1]][index[0]].cell_midTex = (tex_data['name'], 
                                                                       tex_data['rot'] / 90, 
                                                                       tex_data['windex'][0])

                self.pf_chunkClearArea(2, (cx, cy), (base_index[0], base_index[1], 32, 32))
                self.w_Cells_Layers[self.E_ID_WALL][cy][cx][-1].blit(rot, base_index) 

            return 1 - no_update 

        # Delete
        if action_key == 2 and self.w_Cells_Single[index[1]][index[0]].cell_midTex[0] is not None:

            if self.extra_options['auto_wall']:
                print 'Yeah?'
            
            else:
                self.w_Cells_Single[index[1]][index[0]].cell_midTex = (None, 0, 0)
                self.pf_chunkClearArea(2, (cx, cy), (base_index[0], base_index[1], 32, 32))

            return -1

        
    @EditorStatistics.es_update_decorator(_id='id_decal_cnt')
    def __pf_applyDecals(self, index, x, y, surface=None, action_key=0, set_id=0):
        """
            Paint decals

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id ->  Id used to what category is this part of

            return -> None

        """
        tex_data = self.tso_dataTextures[set_id]
        if not tex_data['name']: return None

        tex = self.tso_tex_modes[tex_data['set']][tex_data['name']] 
        angle = self.tso_dataTextures[set_id]['rot']     
        
        rot = self.ed_transform.rotate(tex, angle)

        rot_w, rot_h = rot.get_size()

        cx, cy = index[0] >> 3, index[1] >> 3

        ofsx_1, ofsy_1 = 0, 0
        ofsx_2, ofsy_2 = 0, 0

        if self.extra_options['snap_dec']:
            pos = x, y
            ofsx_2, ofsy_2 = 16, 16
        else:
            mx, my = self.ed_mouse.get_pos()
            pos = (x + (mx - x), y + (my - y))
            ofsx_1, ofsy_1 = 16, 16

        fade_pos = (pos[0] - rot_w / 2 + ofsx_2, 
                    pos[1] - rot_h / 2 + ofsy_2) 

        # Display a fade version of the selected object
        surface.blit(self.ed_fadeImage(rot, 0x80), fade_pos)

        self.ed_draw_rect(surface, (0xff, 0xff, 0x0), (pos[0] - ofsx_1, 
                                                       pos[1] - ofsy_1, 32, 32), 1)
        
        self.__pf_displayDirection(surface, pos[0] + ofsx_2, pos[1] + ofsy_2, angle)
        
        if action_key == 1:
            # Get the decal position on the map reference to world topleft
            decal_pos = ((pos[0] - (self.w_Pos[0] + self.ed_resolution[0] / 2)) - ofsx_1, 
                         (pos[1] - (self.w_Pos[1] + self.ed_resolution[1] / 2)) - ofsy_1)

            # Texture rotation alters the texture dimensions, offset corrections are needed
            xoff = rot_w % tex.get_width()  / 2 
            yoff = rot_h % tex.get_height() / 2

            # Since everything is based on the 32x32 texture placer, 
            # Some offset correction is needed for every other power of 2 textures
            offs_corr = ((fade_pos[0] - pos[0] + ofsx_1) + xoff, 
                         (fade_pos[1] - pos[1] + ofsy_1) + yoff)
            
            pos = int(decal_pos[0] - xoff + offs_corr[0]), int(decal_pos[1] - yoff + offs_corr[1]) 

            self.w_Cells_Layers[self.E_ID_DECAL][cy][cx].append(Id_Decal(tex=rot, 
                                                                         name=tex_data['name'], 
                                                                         pos=pos, 
                                                                         w=rot_w, 
                                                                         h=rot_h,
                                                                         orient=angle))

            return 1

        elif action_key == 2:
            mx, my = self.w_homePosition(*pos, invert=1)
            del_id = None
            
            for enum, d in enumerate(self.w_Cells_Layers[self.E_ID_DECAL][cy][cx]):
                rx, ry = d.w / 2, d.h / 2
                dist = self.ed_hypot(mx - (d.pos[0] + rx), my - (d.pos[1] + ry))
                if dist < self.ed_hypot(rx, ry):
                    del_id = enum
                    break    

            if del_id is not None:
                self.w_Cells_Layers[self.E_ID_DECAL][cy][cx].pop(del_id)
                return -1

    
    def __pf_editCollisions(self, index, x, y, surface=None, action_key=0, set_id=0):
        """
            Edit world collisions

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id ->  Id used to what category is this part of

            return -> None

        """
        cx, cy = index[0] >> 3, index[1] >> 3
        self.ed_draw_rect(surface, (0xff, 0xff, 0x0), (x, y, 32, 32), 1)

        index_mult = index[0] * 32, index[1] * 32

        if action_key == 1:
            self.w_Cells_Layers[self.E_ID_COLLISION][cy][cx][index_mult] = 1

        elif action_key == 2:
            if index_mult in self.w_Cells_Layers[self.E_ID_COLLISION][cy][cx]:
                del self.w_Cells_Layers[self.E_ID_COLLISION][cy][cx][index_mult]  



    @EditorStatistics.es_update_decorator(_id='id_light_cnt')
    def __pf_applyLights(self, index, x, y, surface=None, action_key=0, set_id=0):
        """
            Apply lights

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id ->  Id used to what category is this part of

            return -> None

        """ 
        cx, cy = index[0] >> 3, index[1] >> 3

        if self.w_Cells_Single[index[1]][index[0]].cell_midTex[0] is None:
            pcolor = 0xff, 0xff, 0x0    # Valid placement 
            
            # Light radius indicator
            self.ed_draw_circle(surface, (0xff, 0xff, 0x0), (int(x + 16), int(y + 16)), self.l_current_size, 1)

            # Smaller light to give better look at the color
            self.ed_draw_circle(surface, self.l_current_color[0], (int(x + 16), int(y + 16)), 8)

            # Works as position and key
            pos = (index[0] * 32 + 16, index[1] * 32 + 16)  

            if action_key == 1:
                no_update = 1 if pos in self.w_Cells_Layers[self.E_ID_LIGHT][cy][cx] else 0  

                self.w_Cells_Layers[self.E_ID_LIGHT][cy][cx][pos] = Id_Light(*index, 
                                                                             color=self.l_current_color[0],
                                                                             radius=self.l_current_size)

                return 1 - no_update

            elif action_key == 2 and pos in self.w_Cells_Layers[self.E_ID_LIGHT][cy][cx]:
                del self.w_Cells_Layers[self.E_ID_LIGHT][cy][cx][pos] 
                return -1

        else:
            pcolor = 0xff, 0x0, 0x80    # Invalid placement 
        
        self.ed_draw_rect(surface, pcolor, (x, y, 32, 32), 1)


    @EditorStatistics.es_update_decorator(_id='id_pickup_cnt')
    def __pf_applyPickups(self, index, x, y, surface=None, action_key=0, set_id=0):
        """
            Apply pickups 

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id ->  Id used to what category is this part of

            return -> None

        """
        cx, cy = index[0] >> 3, index[1] >> 3

        if self.w_Cells_Single[index[1]][index[0]].cell_midTex[0] is None:
            pcolor = 0xff, 0xff, 0x0

            pos = (index[0] * 32 + 16, index[1] * 32 + 16) 

            if action_key == 1:
                token = EntityPicker.ep_getPacket()
                if token is None: return 0

                no_update = 1 if pos in self.w_Cells_Layers[self.E_ID_PICKUP][cy][cx] else 0

                id_name = self.fontRender("{} : {}".format(token.content if token.content else token.id, token.value))

                self.w_Cells_Layers[self.E_ID_PICKUP][cy][cx][pos] = Id_Pickup(*index, 
                                                                               id=token.id, 
                                                                               content=token.content, 
                                                                               value=token.value,
                                                                               debug_name=id_name)

                return 1 - no_update

            elif action_key == 2 and pos in self.w_Cells_Layers[self.E_ID_PICKUP][cy][cx]:
                del self.w_Cells_Layers[self.E_ID_PICKUP][cy][cx][pos] 
                return -1

        else:
            pcolor = 0xff, 0x0, 0x80

        self.ed_draw_rect(surface, pcolor, (x, y, 32, 32), 1)

    
    @EditorStatistics.es_update_decorator(_id='id_enemy_cnt')
    def __pf_applyEnemies(self, index, x, y, surface=None, action_key=0, set_id=0):
        """
            Place enemies

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id -> Id used to what category is this part of

            return -> None

        """
        cx, cy = index[0] >> 3, index[1] >> 3

        if self.w_Cells_Single[index[1]][index[0]].cell_midTex[0] is None:
            pcolor = 0xff, 0xff, 0x0 

            pos = index[0] * 32 + 16, index[1] * 32 + 16 

            if action_key == 1:
                token = EntityPicker.ep_getPacket()
                if token is None: return 0

                no_update = 1 if pos in self.w_Cells_Layers[self.E_ID_ENEMY][cy][cx] else 0

                self.w_Cells_Layers[self.E_ID_ENEMY][cy][cx][pos] = Id_Enemy(x=pos[0] >> 5, 
                                                                             y=pos[1] >> 5, 
                                                                             id=token.id,
                                                                             debug_name=self.fontRender(token.id))

                return 1 - no_update

            elif action_key == 2 and pos in self.w_Cells_Layers[self.E_ID_ENEMY][cy][cx]:
                del self.w_Cells_Layers[self.E_ID_ENEMY][cy][cx][pos] 
                return -1

        else:
            pcolor = 0xff, 0x0, 0x80    

        self.ed_draw_rect(surface, pcolor, (x, y, 32, 32), 1)
    

    @EditorStatistics.es_update_decorator(_id='id_wire_cnt')
    @ed_WireTool
    def __pf_applyWires(self, index, x, y, surface=None, action_key=0, set_id=0, **kw):
        """
            Place wire endpoints

            index -> World cell index
            x, y -> Cell index position relative to screen topleft
            surface -> Screen surface
            action_key -> Paint or delete
            set_id -> Id used to what category is this part of

            return -> None

        """
        point_1 = kw['point']['p1']

        cx, cy = index[0] >> 3, index[1] >> 3 

        mx, my = self.ed_mouse.get_pos() 
        mx = x + 8 * (((mx - x) - 1) / 8)
        my = y + 8 * (((my - y) - 1) / 8)

        px, py = self.w_homePosition(mx + 8, my + 8, invert=1)
        px, py = int(self.ed_ceil(px)), int(self.ed_ceil(py))

        # Display a guide wire
        if point_1:
            point_1_r = self.w_homePosition(*point_1)
            self.ed_draw_aaline(surface, (0x0, 0x0, 0x0), point_1_r, (mx + 8, my + 8), 1)

        if action_key == 1:
            # Apply the first endpoint
            if not point_1: 
                kw['point']['p1'] = px, py
                kw['point']['p1_index'] = cx, cy
            
            # Finish the wire
            else:
                # Discard length 0 wires
                if (px, py) == point_1: 
                    pass
                
                # Success wire paint
                else:
                    # Both endcaps(So it can be rendered from both ends)
                    x1, y1 = kw['point']['p1_index']
                    wire_ = Id_Wire(p1=point_1, p2=(px, py), color=self.l_current_color[0])

                    self.w_Cells_Layers[self.E_ID_WIRE][y1][x1].append(wire_)
                    self.w_Cells_Layers[self.E_ID_WIRE][cy][cx].append(wire_)

                    kw['point']['p1'] = 0

                    return 1


        elif action_key == 2:
            if point_1:
                # Undo
                kw['point']['p1'] = 0 

            else:
                pop_this = None
                for enum, dwire in enumerate(self.w_Cells_Layers[self.E_ID_WIRE][cy][cx]):
                    # Check which endpoint the mouse is clicking
                    if (px, py) in (dwire.p1, dwire.p2):
                        pop_this = dwire
                        break  

                if pop_this is not None:
                    # Find and delete both endpoints
                    for x, y in (pop_this.p1, pop_this.p2):
                        # Note: This might cause problems (pushing back the index division by 1)
                        cx, cy = max(0, x - 1 >> 8), max(0, y - 1 >> 8)
                        index = self.w_Cells_Layers[self.E_ID_WIRE][cy][cx].index(pop_this)
                        self.w_Cells_Layers[self.E_ID_WIRE][cy][cx].pop(index)

                    return -1  

        self.ed_draw_rect(surface, (0xff, 0xff, 0x0), (mx, my, 16, 16), 1)

    
    def __pf_floodFill(self, index, surface, surface_str, surface_rot):
        """
            Perform a floodfill on ground by finding and replacing all target ground
            textures with the selected texture

            index -> start cell location
            texture -> Texture source

            return -> None

        """  
        neighbor_nodes = ((-1, 0), (0, -1), (1, 0), (0, 1)) 

        visited = set()

        n_visit = set(); n_visit.add(index)

        base_surface_str = self.w_Cells_Single[index[1]][index[0]].cell_lowTex[0] 

        while n_visit:
            for n in self.ed_copy(n_visit):

                cx, cy = n[0] >> 3, n[1] >> 3
                
                self.w_Cells_Single[n[1]][n[0]].cell_lowTex = (surface_str, surface_rot)
                self.w_Cells_Layers[self.E_ID_GROUND][cy][cx][-1].blit(surface, self.pf_chunkSpatialPos(n[0], n[1], cx, cy))

                visited.add(n)

                # Visit the next cells
                for nod in neighbor_nodes:
                    node = n[0] + nod[0], n[1] + nod[1] 
                    if self.__pf_floodFillCellCheck(node, base_surface_str) and node not in visited:
                        n_visit.add(node)   

                n_visit.discard(n)  

    
    def __pf_floodFillCellCheck(self, index, surface_str):
        """
            Check the neighbor cell that it contains the same texture
            that parent has and that there is no wall on the cell

            surface -> Base surface id

            return -> Bool

        """
        # Within map borders
        if not -1 < index[0] < self.w_Size[4]: return False     # x
        if not -1 < index[1] < self.w_Size[5]: return False     # y

        # Check if there is wall on the cell
        if self.w_Cells_Single[index[1]][index[0]].cell_midTex[0] is not None: return False

        # Neighbor cell contains the same surface_str as the init cell
        if self.w_Cells_Single[index[1]][index[0]].cell_lowTex[0] != surface_str: return False

        return True
        

    def __pf_checkPlacement(self, index, size):
        """
            Check cells for the object that they are available/inside the map

            index -> Base cell index (x, y) 
            size -> size of the object (w, h)

            return -> Bool
            
        """
        #bx, by = index

        # Since object painting starts from topleft, the right and bottom needs to be
        # check'd only for crossing the border
        for y in xrange(size[1]):
            if index[1] + y > self.w_Size[5] - 1: return False  
            
            for x in xrange(size[0]):
                if index[0] + x > self.w_Size[4] - 1: return False
                
                # Check the cells are free
                if self.w_Cells_Single[index[1] + y][index[0] + x].cell_link is not None:
                    return False
        
        return True

    
    def __pf_displayDirection(self, surface, ox, oy, angle):
        """
            Show a small indication arrow for the direction of the texture/object

            surface -> Surface to draw on
            ox, oy -> Origin of the arrow
            angle -> The direction the object/texture is facing in degrees

            return -> None

        """
        arrow_angle = self.ed_pi / 4
        theta = self.ed_radians(angle)

        ox, oy = self.ed_floor(ox), self.ed_floor(oy)  

        endpx = int(ox + self.ed_sin(theta) * 28)
        endpy = int(oy + self.ed_cos(theta) * 28)
        
        # Draw the 'Vertical' line
        self.ed_draw_aaline(surface, (0xff, 0xff, 0x0), (ox, oy), (endpx, endpy), 1)    

        # Draw the arrow head 
        self.ed_draw_aaline(surface, (0xff, 0xff, 0x0), (endpx, endpy), 
                            (endpx - self.ed_sin(theta - arrow_angle) * 8, 
                             endpy - self.ed_cos(theta - arrow_angle) * 8), 1)

        self.ed_draw_aaline(surface, (0xff, 0xff, 0x0), (endpx, endpy), 
                            (endpx - self.ed_sin(theta + arrow_angle) * 8, 
                             endpy - self.ed_cos(theta + arrow_angle) * 8), 1)
        

class Main(GlobalGameDataEditor, DeltaTimer):
    def __init__(self):
        self.base = BaseFrame()
        self.toolWindow = ToolFrame(self.base)
        self.pygameWindow = PygameFrame(self.base)

        # Center the editor on the screen
        ed_centerWidget(self.base)  
    

    def mainloop(self):
        """
            Editor loop

            return -> None

        """
        self.dt_tick()
        while 1:
            self.dt_tick(256)
            
            try:
                self.base.update()
                self.pygameWindow.pf_RunPygameLogic()
            except tk.TclError, Exception:
                # This is just to suppress the Exceptions when the window is closed
                break

if __name__ == '__main__':
    Main().mainloop()
