import tkFileDialog as mp_file
import tkMessageBox as mp_error
import xml.etree.cElementTree as xmlParse
import zipfile

from pygame import image, surface, SRCALPHA
from shutil import make_archive, rmtree
from os import path, makedirs, rename, getcwd, remove

from io import BytesIO
import pygame.image as pyimage

from Tokenizers import *
from Tokenizers import Ed_CellPoint, PackerParserToken, PackerParserCell
from ConfigsModuleEditor import MAX_VALID_CUBE_RANGE, GlobalGameDataEditor

from ast import literal_eval
from collections import OrderedDict
from math import sqrt
from glob import iglob

from traceback import print_exc as mp_getLastException


# Enable print based exceptions 
IDE_TRACEBACK = True


# Game might show errors via MessageBox which creates un-needed Tkinter window
def ROOT_ENABLE_HIDE():
    # Since messagebox requires Tk window, we are going to create
    # one, but hide it
    from Tkinter import Tk

    __GAME_TK_ROOT = Tk()
    __GAME_TK_ROOT.overrideredirect(True)
    __GAME_TK_ROOT.withdraw()

    return __GAME_TK_ROOT



__all__ = 'MapParser',


MAP_PACK_PREFERRED_EXT = 'zip'
MAP_FORMAT_EXT_FULL = "Wasted zip", "*.{}".format(MAP_PACK_PREFERRED_EXT)
MAP_PATH_BASE = 'maps'

# Format in which the layers are stored
MAP_SURFACE_EXT = 'png'

# File tags inside pack
MAP_DATA_EXT  = 'data.xml'      # Keep the name and suffix in same string!
MAP_GROUND    = 'id_ground'
MAP_OBJECTS   = 'id_objects'
MAP_WALLS     = 'id_walls'

# Checksum to validate pack content
MAP_FILES_CHECKSUM = hash((MAP_DATA_EXT,
                           '.'.join((MAP_GROUND,  MAP_SURFACE_EXT)),
                           '.'.join((MAP_OBJECTS, MAP_SURFACE_EXT)),
                           '.'.join((MAP_WALLS,   MAP_SURFACE_EXT)))) 


# Segment tags in XML
MAP_COLLISION_XML = 'id_collisions'
MAP_ENEMY_XML     = 'id_enemies'
MAP_LIGHT_XML     = 'id_lights'
MAP_DECAL_XML     = 'id_decals'
MAP_WIRE_XML      = 'id_wires'
MAP_PICKUP_XML    = 'id_pickup'
MAP_CELL_XML      = 'id_cell_data'
MAP_GENERAL_XML   = 'id_general' 

# General data sub-tags
MAP_PLR_BEGIN_XML = 'id_plr_begin'
MAP_PLR_END_XML   = 'id_plr_end'
MAP_DIMENSION_XML = 'id_dimensions'


MAP_ALL_TAGS = {}
for key in locals().keys():
    if key.startswith('MAP_') and key.endswith('_XML'):
        MAP_ALL_TAGS[key] = locals()[key]

#
# ---- Exceptions (Note: Move these in to their own module)

class WastadiumEditorException(Exception):
    pass 


def W_errorHandler(e, error_id=''):
    if IDE_TRACEBACK: mp_getLastException()
    else: mp_error.showerror(error_id, e)


# Note: Since users can edit the files, i tried to provide as much context for errors as possible
def W_errorToken(section_tag):
    """
        Use this decorator to mark setup/init functions
        to pinpoint which function is failing and why
    """
    def wrapper(func):
        def wrapped(*args, **kw):
            """
                Return 'None' on success (Exception if kw defines "editor_only" then return result)
                       'section_tag' on failure
            """
            try:
                result = func(*args, **kw)
            except Exception:
                return section_tag
            
            return result if 'editor_only' in kw else None
            
        return wrapped
    return wrapper    


# Error names(+ codes if needed for parsing?)

MAP_PLAYER_MISSING   = "Player Missing!"
MAP_ASSERT_ERROR     = "Assert Error!"
MAP_CORRUPTION_ERROR = "Map File Corrupted!"
INIT_ERROR           = "Init Error!" 

XML_PARSING_ERROR     = "Error Parsing The XML File!"
XML_PARSING_SUB_ERROR = "Error Parsing The Following XML Section: {}!"

# ----


def dataParseCheck(func): 
    def wrapped(*args, **kw):
        # Gather and clean the data from the deep nests (With another deep nest)
        if kw['operation'] == 'w':
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
            return r
        # Should not happen. But just incase
        except Exception as e:
            W_errorHandler(e, MAP_ASSERT_ERROR)
 
    return wrapped


class EpisodeParser(object):
    
    # All campaigns with atleast one valid map file
    all_valid_campaigns = {}

    __ref_functions = {}
    
    @classmethod
    def parseEpisodeFiles(cls):
        """
            Parse campaign files which contains the play order for the episode maps

            return -> None

        """
        for cfg in iglob(path.join(MAP_PATH_BASE, '*.cfg')):
            with open(cfg) as read:
                # Check that the file contains atleast one valid map
                # (Doesn't validate the content of the pack files) *Propably should do it here
                name = path.split(cfg)[-1].split('.')[0]
                cls.all_valid_campaigns[name] = list() 
                
                for line in read:
                    if not line.startswith('-'): continue
                    
                    map_name = line.split('-')[-1].rstrip()

                    # Allow both with extension suffix and without
                    if map_name.endswith(".{}".format(MAP_PACK_PREFERRED_EXT)):
                        pass
                    else:
                        map_name = '.'.join((map_name, MAP_PACK_PREFERRED_EXT))

                    # Run few checksums test on the maps
                    filepath = path.join(MAP_PATH_BASE, map_name) 
                    if not path.exists(filepath):
                        continue

                    # Check that the pack contains only the allowed tags inside it
                    with zipfile.ZipFile(filepath) as checksum_files:
                        if not hash(tuple(checksum_files.namelist())) == MAP_FILES_CHECKSUM:
                            continue

                    cls.all_valid_campaigns[name].append(map_name.split('.')[0])

    
    @classmethod
    def episodeRoll(cls, episode_name, surface):
        """
            Begin episode playback

            episode_name -> avaiable id in 'cls.all_valid_campaigns' 

            return -> None
        """     
        for level in cls.all_valid_campaigns[episode_name]:
            cls.__ref_functions['build'](level, surface)
            cls.__ref_functions['run']()

        return None

    
    @classmethod
    def episode_set_references(cls, **kw):
        cls.__ref_functions.update(**kw)    


class Packer(object):

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

    # Zipfile path
    __filepath = None

    # Store cleaned data here for others to use if needed
    p_dataStorage = {} 

    # All parser functions
    p_parserFunctions = OrderedDict()
    
    
    @classmethod
    def getValidFilePath(cls, filepath):
        """
            This needs to be called before decompressing the zipfile

            filepath -> Path to valid mapfile

            return -> '-1' if not valid else 'None'

        """
        if path.exists(filepath) and zipfile.is_zipfile(filepath):
            cls.__filepath = filepath
            return True
        else:
            return -1
    
    
    @classmethod
    def decompressAndParse(cls, editor_loader=False):
        """
            Decompress the mapfile
            Validate and parse the contents

            editor_loader -> If 'True' load and parse everything in the mapfile
                             game itself needs only small portion of the data
                             if 'False' returns dict with surface: Layer images, data: XML data 

            return -> XML data if editor, else surfaces and xml data

        """
        if cls.__filepath is None:
            return None
        #assert cls.__filepath is not None, "Get the path first!" 

        with zipfile.ZipFile(cls.__filepath) as zr:
            files = zr.namelist() 
            try:
                # Check these files exist inside the pack (This is for editor. Game checks these files twice, fix it?)
                data = files.index(MAP_DATA_EXT)
                lr01 = files.index('{}.{}'.format(MAP_GROUND,  MAP_SURFACE_EXT))
                lr02 = files.index('{}.{}'.format(MAP_OBJECTS, MAP_SURFACE_EXT))
                lr03 = files.index('{}.{}'.format(MAP_WALLS,   MAP_SURFACE_EXT))

            except Exception as e:
                W_errorHandler(e, MAP_CORRUPTION_ERROR)

            if editor_loader:
                return cls.parseXML(zr, files[data])

            else:
                # These needs to be converted to surfaces outside the function
                # Since pygame.image relies on display being initialized
                surfaces = {files[key].split('.')[0]: BytesIO(zr.read(files[key])) for key in (lr01, lr02, lr03)}

                return {MAP_GROUND: surfaces, 
                        MAP_DATA_EXT.split('.')[0]: cls.parseXML(zr, files[data], editor_loader=False)}
    
    
    @classmethod
    def compress(cls, filename, filepath):
        """
            Pack the files in to archive

            filename -> Name of the output archive
            filepath -> Path to store the output archive

            return -> None

        """
        make_archive(filename, MAP_PACK_PREFERRED_EXT, filepath)
        rmtree(filepath)   # Delete original mapfolder(now archived and copied)

        # Add file renaming here if needed


    @classmethod
    def parseXML(cls, handler, xml_zip_file, editor_loader=True):
        """
            Validate and parse the xml file locating in the map archive

            handler -> zip handler
            xml_zip_file -> Archive filepath
            editor_loader -> if 'True' parse everything
                             else parse minimal amount needed for the game 

            return -> Parsed data for building the map

        """
        with handler.open(xml_zip_file) as pzip:
            try:
                xml_data = {}

                tree = xmlParse.parse(pzip)
                root = tree.getroot()

                # Check that all child are in
                if any([child.tag not in MAP_ALL_TAGS.values() for child in root.getchildren()]):
                    raise WastadiumEditorException(XML_PARSING_ERROR)

                childrens = {child.tag: child for child in root.getchildren()}  
                
                for key, value in childrens.iteritems():
                    if key not in cls.p_parserFunctions: 
                        continue

                    if not editor_loader:
                        # Game doesn't need all data
                        if key in (MAP_DECAL_XML): continue
                    
                    if key == MAP_GENERAL_XML:
                        xml_data[key] = cls.p_parserFunctions[key].parse(data_fetcher=value, operation='r')
                    else:    
                        xml_data[key] = cls.p_parserFunctions[key].parse(data=value, operation='r')

                xml_data[MAP_CELL_XML] = cls.parseWorldData(data=childrens[MAP_CELL_XML], operation='r', 
                                                            editor_loader=editor_loader)    

            except (WastadiumEditorException, Exception) as e:
                W_errorHandler(e, XML_PARSING_ERROR)
                xml_data.clear()

        return xml_data


    @classmethod
    def parseGeneralData(cls, xml_root=None, data_fetcher=None, name='', operation='w'):
        """
            Parse general map data
            -   SpawnPos/EndPos
            -   World size

            xml_root ->
            data_fetcher -> 
            name ->
            operation -> 'r', 'w'

            return -> None

        """
        assert operation in ('w', 'r')

        if operation == 'w':
            segment = xmlParse.SubElement(xml_root, name)

            # Player position (x, y, id)
            data = data_fetcher('w_SpawnEnd', layers=False)
            parent_p = xmlParse.SubElement(segment, MAP_PLR_BEGIN_XML, name=data[0].id)
            parent_p.text = "{}.{}".format(data[0].x, data[0].y)

            # End goal (Optional!)
            if data[1] is not None:
                parent_e = parent_p = xmlParse.SubElement(segment, MAP_PLR_END_XML, name=data[1].id)
                parent_e.text = "{}.{}".format(data[1].x, data[1].y)

            # Map related data (x, y)
            data = data_fetcher('w_Size', layers=False)[4:6] 
            parent_p = xmlParse.SubElement(segment, MAP_DIMENSION_XML)
            parent_p.text = "{}.{}".format(*data)

        else:
            r_data = {}
            childs = {child.tag: child for child in data_fetcher.getchildren()} 
            
            if any([tag not in MAP_ALL_TAGS.values() for tag in childs]):
                raise WastadiumEditorException(XML_PARSING_SUB_ERROR.format(data_fetcher.tag))
            
            r_data[MAP_PLR_BEGIN_XML] = [Ed_CellPoint(*[int(p) for p in childs[MAP_PLR_BEGIN_XML].text.split('.')], 
                                                      id=childs[MAP_PLR_BEGIN_XML].attrib['name']), 
                                         Ed_CellPoint(*[int(p) for p in childs[MAP_PLR_END_XML].text.split('.')],
                                                      id=childs[MAP_PLR_END_XML].attrib['name']) if MAP_PLR_END_XML in childs else None]
            
            r_data[MAP_DIMENSION_XML] = literal_eval('{},{}'.format(*childs[MAP_DIMENSION_XML].text.split('.')))

            return r_data
    
        
    @classmethod
    @dataParseCheck
    def parseCollisions(cls, xml_root=None, data=None, name='', operation='w'):
        """
            Parse collision data to/from xml file

            Collision data is in (pos): 1 (1 for now, but might be something in the future)

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml
            operation -> 'r', 'w'

            return -> None
        
        """
        # Collision data is single array of x, y pairs 
        # Compress the data by shifting the position closer to cell index positions 
        # (Should fix this in editor too) 

        assert operation in ('w', 'r')

        if operation == 'w':
            segment = xmlParse.SubElement(xml_root, name)
            parent = xmlParse.SubElement(segment, name)
            parent.text = '.'.join([str(pos >> 5) for token, _ in data for pos in token])

        else: 
            r_data = {}
            
            points = [int(p) for p in data[0].text.split('.')]
            for l in xrange(0, len(points), 2):
                r_data[tuple(points[l : l + 2])] = 1

            return r_data


    @classmethod
    @dataParseCheck
    def parseEnemies(cls, xml_root=None, data=None, name='', operation='w'):
        """
            Parse enemy data to/from xml file

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml
            operation -> 'r', 'w'

            return -> None

        """
        assert operation in ('w', 'r')

        if operation == 'w':
            segment = xmlParse.SubElement(xml_root, name)

            for e in sorted(data, key=lambda x: x[1].id):
                enemy = e[1]
                parent = xmlParse.SubElement(segment, name, name=enemy.id)

                parent.text = '{}.{}'.format(enemy.x, enemy.y)
        else:
            r_data = []
            
            for e in data.getchildren():
                name = e.attrib['name']
                x, y = [int(p) for p in e.text.split('.')]
                r_data.append(Id_Enemy(x=x, y=y, id=name, debug_name=None))

            return r_data

    
    @classmethod
    @dataParseCheck
    def parseLights(cls, xml_root=None, data=None, name='', operation='w'):
        """
            Parse light data to/from xml file

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml
            operation -> 'r', 'w'

            return -> None

        """
        assert operation in ('w', 'r')

        if operation == 'w':
            segment = xmlParse.SubElement(xml_root, name)

            for enum, l in enumerate(data):
                light = l[1]
                parent = xmlParse.SubElement(segment, name, name='light_{}'.format(enum))
                # Convert rgb tripled to hex
                r, g, b = light.color
                hex_repr = '{0:#0{1}x}'.format(((r << 16) ^ g << 8) ^ b, 8)    # Keep leading zeroes

                # x, y, radius(Kept for future use), hex color
                parent.text = '{}.{}.{}.{}'.format(light.x, light.y, light.radius, hex_repr)
        else:
            r_data = []
            
            for l in data.getchildren():
                x, y, r, c = [int(x, 0) for x in l.text.split('.')]
                r_data.append(Id_Light(x=x, y=y, radius=r, 
                                       color=((c >> 16) & 0xff, 
                                              (c >>  8) & 0xff, 
                                              (c & 0xff))))    

            return r_data


    @classmethod
    @dataParseCheck
    def parseDecals(cls, xml_root=None, data=None, name='', operation='w'):
        """
            Parse decals

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml
            operation -> 'r', 'w'

            return -> None

        """
        assert operation in ('w', 'r')

        if operation == 'w':
            segment = xmlParse.SubElement(xml_root, name)
            
            for decal in sorted(data, key=lambda x: x.name):
                parent = xmlParse.SubElement(segment, name, name=decal.name)

                # x, y, orientation
                parent.text = '{}.{}.{orient}'.format(*decal.pos, orient=decal.orient)

            # Store the decals for the world parser
            cls.p_dataStorage[cls.E_ID_DECAL] = data
        
        else:
            r_data = []

            for d in data.getchildren():
                name = d.attrib['name'] 
                x, y, orient = [int(p) for p in d.text.split('.')]
                r_data.append(Id_Decal(tex=None,    # Editor fills this
                                       name=name,
                                       pos=(x, y),
                                       w=None,      # - || -
                                       h=None,      # - || -
                                       orient=orient))

            return r_data


    @classmethod
    @dataParseCheck
    def parseWires(cls, xml_root=None, data=None, name='', operation='w'):
        """
            Parse wire segments

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml
            operation -> 'r', 'w'

            return -> None

        """
        assert operation in ('w', 'r')

        if operation == 'w':
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
        else:
            r_data = []

            for w in data.getchildren():
                x1, y1, x2, y2, color = [int(x, 0) for x in w.text.split('.')]

                r = (color >> 16) & 0xff
                g = (color >> 8) & 0xff
                b =  color & 0xff

                r_data.append(Id_Wire(p1=(x1, y1), p2=(x2, y2), color=(r, g, b)))

            return r_data


    @classmethod
    @dataParseCheck
    def parsePickups(cls, xml_root=None, data=None, name='', operation='w'):
        """
            Parse pickups

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml
            operation -> 'r', 'w'

            return -> None

        """
        assert operation in ('w', 'r')

        if operation == 'w':
            segment = xmlParse.SubElement(xml_root, name)

            for pup in sorted(data, key=lambda x: x[1].id):
                pup = pup[1]
                parent = xmlParse.SubElement(segment, name, name=pup.id)
                # x, y, content, value
                parent.text = '{}.{}.{}.{}'.format(pup.x, pup.y, pup.content, pup.value)

        else:
            r_data = []

            for p in data.getchildren():
                name = p.attrib['name']
                x, y, content, value = [int(x) if x.isdigit() else str(x) for x in p.text.split('.')]
                r_data.append(Id_Pickup(x=x, y=y, id=name,
                                        content=content, value=value))

            return r_data


    @classmethod
    def parseWorldData(cls, xml_root=None, data=None, name='', operation='w', editor_loader=True):
        """
            Parse cell data

            xml_root ->
            data ->
            name -> 
            operation -> 'r', 'w'

            return -> None

        """
        assert operation in ('w', 'r')

        if operation == 'w':
            segment = xmlParse.SubElement(xml_root, name)

            # Store ground data
            for y, row in enumerate(data):
                for x, cell in enumerate(row):
                    parent = xmlParse.SubElement(segment, name, name='c_{}.{}'.format(x, y))

                    obj = cell.get_set_CellToken()['obj'][0] 
                    if obj is not None: print obj

                    parent.text = "{low}.{mid}.{obj}.{link}".format(**cell.get_set_CellToken())

        else:
            # Check that the number of cells is within valid map ranges
            valid_cube = len(data.getchildren())
            if valid_cube not in MAX_VALID_CUBE_RANGE:
                raise WastadiumEditorException(XML_PARSING_ERROR)

            row_length = int(sqrt(valid_cube)) - 1
            final_matrix = []

            row = []
            for child in data.getchildren():
                pos = child.attrib['name'].split('_')[1]
                x, y = [int(c) for c in pos.split('.')]
                low, mid, obj, link = [literal_eval(c) for c in child.text.split('.')]
                
                if editor_loader:
                    row.append(PackerParserCell(low=low, mid=mid, obj=obj, link=link))
                
                else:
                    obj_token = None
                    if obj[0] is not None:
                        # Get macro cell and position relative to that cell
                        macro, pos = link[-2][-1]

                        # Game uses special collision for objects which is created at runtime
                        # Supply the coordinates for every objects (TopLeft and BottomRight)
                        cx = (macro[0] * GlobalGameDataEditor.ed_chunk_size_raw + pos[0]) >> 5
                        cy = (macro[1] * GlobalGameDataEditor.ed_chunk_size_raw + pos[1]) >> 5
                        obj_token = ((cx, cy), link[-1])

                    row.append(PackerParserCell(low=low[0], mid=mid[0], obj=obj_token, link=None))
                
                if x == row_length:
                    final_matrix.append(row)
                    row = []

            return final_matrix
    
    
    @classmethod
    def bindParsers(cls):
        """
            Bind/Bundle all the parser functions with their' associated XML id's

            return -> None

        """
        cls.p_parserFunctions[MAP_GENERAL_XML] = \
            PackerParserToken(parse=cls.parseGeneralData, id=None)
        
        cls.p_parserFunctions[MAP_COLLISION_XML] = \
            PackerParserToken(parse=cls.parseCollisions, id=cls.E_ID_COLLISION)

        cls.p_parserFunctions[MAP_ENEMY_XML] = \
            PackerParserToken(parse=cls.parseEnemies, id=cls.E_ID_ENEMY)
        
        cls.p_parserFunctions[MAP_LIGHT_XML] = \
            PackerParserToken(parse=cls.parseLights, id=cls.E_ID_LIGHT)

        cls.p_parserFunctions[MAP_DECAL_XML] = \
            PackerParserToken(parse=cls.parseDecals, id=cls.E_ID_DECAL)
        
        cls.p_parserFunctions[MAP_WIRE_XML] = \
            PackerParserToken(parse=cls.parseWires, id=cls.E_ID_WIRE)
        
        cls.p_parserFunctions[MAP_PICKUP_XML] = \
            PackerParserToken(parse=cls.parsePickups, id=cls.E_ID_PICKUP)


class MapParser(Packer):

    Packer.bindParsers()
    
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
        try:
            # Create directory for the map in the target base path
            map_path = path.join(getcwd(), MAP_PATH_BASE, filename)
            makedirs(map_path)

            root = xmlParse.Element('root')

            for key, parser in cls.p_parserFunctions.iteritems():
                if key == MAP_GENERAL_XML:
                    parser.parse(root, name=key, data_fetcher=data_fetcher)
                else:
                    parser.parse(root, data=data_fetcher(parser.id), name=key, operation='w')

            cls.parseWorldData(root, data=data_fetcher('w_Cells_Single', layers=False), name=MAP_CELL_XML)

            # Build all the layers and save them
            width_height = data_fetcher('w_Size', layers=False)[2:4]
            for l_id, name_id in ((cls.E_ID_GROUND, MAP_GROUND), (cls.E_ID_OBJECT, MAP_OBJECTS), (cls.E_ID_WALL, MAP_WALLS)):
                cls.parseWorldSurfaces(data_fetcher(l_id), name_id, map_path, width_height, l_id) 

            # Build the final xml output
            final_tree = xmlParse.ElementTree(root)
            final_tree.write(path.join(map_path, MAP_DATA_EXT))
            
            # Pack everything
            cls.compress(filename, map_path)
        
        except (WastadiumEditorException, Exception) as e:
            W_errorHandler(e)
            
            # Error occured during saving. Delete the Folder/File
            try:
                if path.exists(map_path): rmtree(map_path)  
            except Exception:
                bad_file = '{}.{}'.format(map_path, MAP_PACK_PREFERRED_EXT) 
                if path.exists(bad_file): remove(bad_file) 

    
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
            if cls.E_ID_DECAL in cls.p_dataStorage:  
                for r_decal in cls.p_dataStorage[cls.E_ID_DECAL]:
                    base.blit(r_decal.tex, r_decal.pos)

        image.save(base, path.join(final_path, '{}.{}'.format(name_id, MAP_SURFACE_EXT)))

    
    @classmethod
    def mp_load(cls, filename='', editor_loader=False):
        """
            Load and parse map files

            editor_loader -> Set to 'True' when called by the map editor

            return -> None

        """ 
        # Note: This editor section should be moved to decompressAndParse function
        #       Only useful during debugging on its on __main__
        if editor_loader:
            valid = cls.getValidFilePath(mp_file.askopenfilename(initialdir=MAP_PATH_BASE, 
                                                                 filetypes=(MAP_FORMAT_EXT_FULL, )))
            if valid == -1:
                return None
            #cls.decompressAndParse(editor_loader=1)

        else:
            cls.getValidFilePath(path.join(MAP_PATH_BASE, '{}.{}'.format(filename, MAP_PACK_PREFERRED_EXT)))
            return cls.decompressAndParse()   


if __name__ == '__main__':
    pass
    #MapParser.mp_load(editor_loader=True)
    #EpisodeParser.parseEpisodeFiles()
