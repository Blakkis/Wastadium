import tkFileDialog as mp_file
import tkMessageBox as mp_error
import xml.etree.cElementTree as xmlParse
import zipfile

from pygame import image, surface, SRCALPHA
from shutil import make_archive, rmtree
from os import path, makedirs, rename, getcwd

from io import BytesIO
import pygame.image as pyimage
import sys

__all__ = 'MapParser', 


MAP_PACK_PREFERRED_EXT = 'zip'
MAP_FORMAT_EXT_FULL = "Wasted zip", "*.{}".format(MAP_PACK_PREFERRED_EXT)
MAP_PATH_BASE = 'maps'

# Format in which the layers are stored
MAP_SURFACE_EXT = 'png'

# Folder tags
MAP_DATA_EXT  = 'data.xml'
MAP_GROUND    = 'id_ground'
MAP_WALLS     = 'id_walls'
MAP_OBJECTS   = 'id_objects'

# Segment tags
MAP_COLLISION_XML = 'id_collisions'
MAP_ENEMY_XML     = 'id_enemies'
MAP_LIGHT_XML     = 'id_lights'
MAP_DECAL_XML     = 'id_decals'
MAP_WIRE_XML      = 'id_wires'
MAP_PICKUP_XML    = 'id_pickup'
MAP_CELL_XML      = 'id_cell_data'
MAP_GENERAL_XML   = 'id_general' 

# General data sub-tags

MAP_PSTARTEND_XML = 'id_p_start_end'
MAP_DIMENSION_XML = 'id_dimensions'


MAP_ALL_TAGS = (MAP_COLLISION_XML, MAP_ENEMY_XML, 
                MAP_LIGHT_XML,     MAP_DECAL_XML,
                MAP_WIRE_XML,      MAP_PICKUP_XML, 
                MAP_CELL_XML,      MAP_GENERAL_XML,
                MAP_PSTARTEND_XML, MAP_DIMENSION_XML)


# ----

class WastadiumEditorException(Exception):
    pass 


# Error names(+ codes if needed for parsing?)

MAP_PLAYER_MISSING   = "Player Missing! - 0x{}"    .format(0x1 << 1)
MAP_ASSERT_ERROR     = "Assert Error! - 0x{}"      .format(0x1 << 2)
MAP_CORRUPTION_ERROR = "Map File Corrupted! - 0x{}".format(0x1 << 3) 

XML_PARSING_ERROR =     "Error Parsing The XML File!"
XML_PARSING_SUB_ERROR = "Error Parsing The Following XML Section: {}!"

# ----


def dataParseCheck(func): 
    def wrapped(*args, **kw):
        # Gather and clean the data from the deep nests
        clean_data = []
        for c_block in kw['data']:
            for r_block in c_block:
                # Data is stored in dict or list on each world chunk
                if isinstance(r_block, dict):
                    for key, value in r_block.iteritems():
                        clean_data.append((key, value))
                
                else:
                    for value in r_block:
                        clean_data.append(value)
        
        kw['data'] = clean_data
        try:
            r = func(*args, **kw)
        # Should not happen. But just incase
        except Exception as e:
            mp_error.showerror(MAP_ASSERT_ERROR, e)
 
    return wrapped


class Packer(object):

    # Zip file path
    __filepath = None
    
    
    @classmethod
    def getValidFilePath(cls, filepath):
        """
            This needs to be called before decompressing the zipfile

            filepath -> Path to valid mapfile

            return -> '-1' if not valid else 'None'

        """
        if path.exists(filepath) and zipfile.is_zipfile(filepath):
            cls.__filepath = filepath
        else:
            return -1
    
    
    @classmethod
    def decompressAndParse(cls, editor_loader=False):
        """
            Decompress the mapfile. Validate and parse the contents

            return -> None

        """
        assert cls.__filepath is not None, "Get the path first!" 

        with zipfile.ZipFile(cls.__filepath) as zr:
            files = zr.namelist() 
            try:
                # Check these files exist inside the pack
                data = files.index(MAP_DATA_EXT)
                lr01 = files.index('{}.{}'.format(MAP_GROUND,  MAP_SURFACE_EXT))
                lr02 = files.index('{}.{}'.format(MAP_OBJECTS, MAP_SURFACE_EXT))
                lr03 = files.index('{}.{}'.format(MAP_WALLS,   MAP_SURFACE_EXT))

            except Exception as e:
                mp_error.showerror(MAP_CORRUPTION_ERROR, e)

            if editor_loader:
                return cls.parseXML(zr, files[data])

            else:
                # Load surfaces (Ground surface doesn't need alpha component)
                surfaces = {key: BytesIO(zr.read(files[layer])).convert() if key == lr01 else
                                 BytesIO(zr.read(files[layer])).convert_alpha() for key in (lr01, lr02, lr03)}
                return surfaces     
    
    
    @classmethod
    def compress(cls, filename, filepath):
        """
            TBD

            return -> None

        """
        make_archive(filename, MAP_PACK_PREFERRED_EXT, filepath)
        rmtree(filepath)   # Delete original mapfolder(now archived and copied)


    @classmethod
    def parseXML(cls, handler, xml_zip_file):
        """
            TBD

            return -> None

        """
        with handler.open(xml_zip_file) as pzip:
            try:
                xml_data = {}

                tree = xmlParse.parse(pzip)
                root = tree.getroot()

                # Check that all child are in
                if any([child.tag not in MAP_ALL_TAGS for child in root.getchildren()]):
                    raise WastadiumEditorException(XML_PARSING_ERROR)

                childrens = {child.tag: child for child in root.getchildren()}  
                for key, value in childrens.iteritems():
                    cls.__parseXML_helper(xml_data, key, value)    

            except (WastadiumEditorException, Exception) as e:
                mp_error.showerror(MAP_CORRUPTION_ERROR, e)
                xml_data.clear()

        return xml_data

    
    @classmethod
    def __parseXML_helper(cls, data_cache, ckey, cval):
        """
            TBD

            return -> None

        """
        # Sub-dict for all the data sections
        data_cache[ckey] = {}

        if ckey == MAP_GENERAL_XML:
            data_cache[ckey] = cls.parseGeneralData(data_fetcher=cval, operation='r')


    @classmethod
    def parseGeneralData(cls, xml_root=None, data_fetcher=None, name='', operation='w'):
        """
            Parse general map data
            -   SpawnPos/EndPos
            -   World size

            return -> None

        """
        assert operation in ('w', 'r')

        if operation == 'w':
            segment = xmlParse.SubElement(xml_root, name)

            # Player position
            data = data_fetcher('w_SpawnEnd', layers=False)
            parent_p = xmlParse.SubElement(segment, MAP_PSTARTEND_XML, name=data[0].id)
            parent_p.text = "{}.{}".format(data[0].x, data[0].y)

            # End goal (Optional!)
            if data[1] is not None:
                parent_e = parent_p = xmlParse.SubElement(segment, MAP_PSTARTEND_XML, name=data[1].id)
                parent_e.text = "{}.{}".format(data[1].x, data[1].y)

            # Map related data
            data = data_fetcher('w_Size', layers=False)[4:6] 
            parent_p = xmlParse.SubElement(segment, MAP_DIMENSION_XML)
            parent_p.text = "{}.{}".format(*data)

        elif operation == 'r':
            data = {}
            childs = {child.tag: child for child in data_fetcher.getchildren()} 
            if any([tag + '1' not in MAP_ALL_TAGS for tag in childs]):
                raise WastadiumEditorException(XML_PARSING_SUB_ERROR.format(data_fetcher.tag))
            



class MapParser(Packer):
    
    w_enum = {'E_ID_GROUND'   : 0x0,    
              'E_ID_OBJECT'   : 0x1,    
              'E_ID_WALL'     : 0x2,    
              'E_ID_DECAL'    : 0x3,    
              'E_ID_COLLISION': 0x4,    
              'E_ID_LIGHT'    : 0x5,    
              'E_ID_WIRE'     : 0x6,
              'E_ID_ENEMY'    : 0x7,
              'E_ID_PICKUP'   : 0x8}

    locals().update(w_enum)

    # Store cleaned data here for others to use if needed
    __DataStorage = {}

    
    @classmethod
    def mp_save(cls, data_fetcher):
        """
            Save map

            data_fetched -> Data fetch function from the world class

            return -> None

        """
        # Check that the player spawn point has been set
        w_spawn_end = data_fetcher('w_SpawnEnd', layers=False)
        if w_spawn_end[0] is None:
            mp_error.showerror(MAP_PLAYER_MISSING, "Player Spawn-point missing!")
            return None

        w_mapname = cls.bf_mapname.get()    # If we decide to change mapname during saving
                                            # Update it as the default name

        filename = mp_file.asksaveasfilename(initialdir=MAP_PATH_BASE,
                                             initialfile=w_mapname,
                                             filetypes=(MAP_FORMAT_EXT_FULL, ))
        if not filename: 
            return None

        # Create directory for the map in the target base path
        map_path = path.join(getcwd(), MAP_PATH_BASE, filename)
        makedirs(map_path)

        root = xmlParse.Element('root')

        cls.parseGeneralData(root, name=MAP_GENERAL_XML, data_fetcher=data_fetcher)

        cls.parseCollisions(root, data=data_fetcher(cls.E_ID_COLLISION), name=MAP_COLLISION_XML)

        cls.parseEnemies(root, data=data_fetcher(cls.E_ID_ENEMY), name=MAP_ENEMY_XML)

        cls.parseLights(root, data=data_fetcher(cls.E_ID_LIGHT), name=MAP_LIGHT_XML)

        cls.parseDecals(root, data=data_fetcher(cls.E_ID_DECAL), name=MAP_DECAL_XML)

        cls.parseWires(root, data=data_fetcher(cls.E_ID_WIRE), name=MAP_WIRE_XML)

        cls.parsePickups(root, data=data_fetcher(cls.E_ID_PICKUP), name=MAP_PICKUP_XML)

        cls.parseWorldData(root, data=data_fetcher('w_Cells_Single', layers=False), name=MAP_CELL_XML)

        # Build all the layers and save them
        width_height = data_fetcher('w_Size', layers=False)[2:4]
        for l_id, name_id in ((cls.E_ID_GROUND, MAP_GROUND), (cls.E_ID_OBJECT, MAP_OBJECTS), (cls.E_ID_WALL, MAP_WALLS)):
            cls.parseWorldSurfaces(data_fetcher(l_id), name_id, map_path, width_height, l_id) 

        # Build the final xml output
        final_tree = xmlParse.ElementTree(root)
        final_tree.write(path.join(map_path, MAP_DATA_EXT))

        cls.compress(filename, map_path)

    
    @classmethod
    def parseWorldSurfaces(cls, data, name_id, final_path, final_size, layer_index=-1):
        """
            Clue all the subsurfaces together to form a full surface image
            for storing

            data -> Data used to form the layer
            name_id -> Name of layer on disk
            final_path -> Save path
            final_size -> Final size of the surface images

            return -> None

        """ 
        base = surface.Surface(final_size, flags=SRCALPHA)

        # Blit all the subsurfaces to the full surface
        for column in data:
            for x, y, surf in column:
                base.blit(surf, (x, y))

        if layer_index == cls.E_ID_GROUND:
            if cls.E_ID_DECAL in cls.__DataStorage:  
                for r_decal in cls.__DataStorage[cls.E_ID_DECAL]:
                    base.blit(r_decal.tex, r_decal.pos)

        image.save(base, path.join(final_path, '{}.{}'.format(name_id, MAP_SURFACE_EXT)))

    
    @classmethod
    def parseWorldData(cls, xml_root, data, name=''):
        """
            TBD

            return -> None

        """
        segment = xmlParse.SubElement(xml_root, name)

        # Store ground data
        for y, row in enumerate(data):
            for x, cell in enumerate(row):
                parent = xmlParse.SubElement(segment, name, name='c_{}.{}'.format(x, y))
                parent.text = "{low}.{mid}.{obj}.{link}".format(**cell.get_set_CellToken())

    
    @classmethod
    @dataParseCheck
    def parseCollisions(cls, xml_root, data, name=''):
        """
            Parse collision data to/from xml file

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml

            return -> None
        
        """
        segment = xmlParse.SubElement(xml_root, name)
        parent = xmlParse.SubElement(segment, name)
        # Collision data is single array of x, y pairs 
        # Compress the data by shifting the position closer to cell index positions (Should fix this in editor too) 
        parent.text = '.'.join([str(pos >> 5) for token, _ in data for pos in token])
    

    @classmethod
    @dataParseCheck
    def parseEnemies(cls, xml_root, data, name=''):
        """
            Parse enemy data to/from xml file

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml

            return -> None

        """
        segment = xmlParse.SubElement(xml_root, name)

        for e in sorted(data, key=lambda x: x[1].id):
            enemy = e[1]
            parent = xmlParse.SubElement(segment, name, name=enemy.id)

            parent.text = '{}.{}'.format(enemy.x >> 5, enemy.y >> 5) 


    @classmethod
    @dataParseCheck
    def parseLights(cls, xml_root, data, name=''):
        """
            Parse light data to/from xml file

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml

            return -> None

        """ 
        segment = xmlParse.SubElement(xml_root, name)

        for enum, l in enumerate(data):
            light = l[1]
            parent = xmlParse.SubElement(segment, name, name='light_{}'.format(enum))
            # Convert rgb tripled to hex
            r, g, b = light.color
            hex_repr = '{0:#0{1}x}'.format(((r << 16) ^ g << 8) ^ b, 8)    # Keep leading zeroes

            # x, y, radius(Kept for future use), hex color
            parent.text = '{}.{}.{}.{}'.format(light.x >> 5, light.y >> 5, light.radius, hex_repr)


    @classmethod
    @dataParseCheck
    def parseDecals(cls, xml_root, data, name=''):
        """
            Parse decals

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml

            return -> None

        """
        segment = xmlParse.SubElement(xml_root, name)
        
        for decal in sorted(data, key=lambda x: x.name):
            parent = xmlParse.SubElement(segment, name, name=decal.name)

            # x, y, orientation
            parent.text = '{}.{}.{orient}'.format(*decal.pos, orient=decal.orient)

        # Store the decals for the world parser
        cls.__DataStorage[cls.E_ID_DECAL] = data


    @classmethod
    @dataParseCheck
    def parseWires(cls, xml_root, data, name=''):
        """
            Parse wire segments

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml

            return -> None

        """
        segment = xmlParse.SubElement(xml_root, name)

        done_inc = 0
        done = set()
        for wire in data:
            fw = wire.p1 + wire.p2
            if fw in done: 
                continue
            
            done.add(fw)
            parent = xmlParse.SubElement(segment, name, name='wire_{}'.format(done_inc))

            # Convert rgb tripled to hex
            r, g, b = wire.color
            hex_repr = '{0:#0{1}x}'.format(((r << 16) ^ g << 8) ^ b, 8) 

            # x, y, x, y, hex color
            parent.text = '{}.{}.{}.{}.{hex_repr}'.format(*fw, hex_repr=hex_repr)
            done_inc += 1


    @classmethod
    @dataParseCheck
    def parsePickups(cls, xml_root, data, name=''):
        """
            Parse pickups

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml

            return -> None

        """
        segment = xmlParse.SubElement(xml_root, name)

        for pup in sorted(data, key=lambda x: x[1].id):
            pup = pup[1]
            parent = xmlParse.SubElement(segment, name, name=pup.id)
            # x, y, content, value
            parent.text = '{}.{}.{}.{}'.format(pup.x, pup.y, pup.content, pup.value)
            
    
    @classmethod
    def mp_load(cls, editor_loader=False):
        """
            Load and parse map files

            editor_loader -> Set to 'True' when called by the map editor

            return -> None

        """ 
        if editor_loader:
            valid = cls.getValidFilePath(mp_file.askopenfilename(initialdir=MAP_PATH_BASE, 
                                                                 filetypes=(MAP_FORMAT_EXT_FULL, )))
            if valid == -1:
                return None

            #cls.decompressAndParse(editor_loader=1)

        else:
            pass


if __name__ == '__main__':
    MapParser.mp_load(editor_loader=True)
