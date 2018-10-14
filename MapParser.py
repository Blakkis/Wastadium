from shutil import make_archive, rmtree
from os import path, makedirs, rename, getcwd
import tkFileDialog as mp_file
from pygame import image, surface, SRCALPHA
import xml.etree.cElementTree as xmlParse

#>>> import xml.etree.cElementTree as ET
#>>> root = ET.Element("root")
#>>> doc = ET.SubElement(root, 'doc')
#>>> ET.SubElement(doc, "field1", name="blah").text = "some value1"
#>>> ET.SubElement(doc, "field2", name="asdfasd").text = "some vlaue2"
#>>> tree = ET.ElementTree(root)
#>>> tree.write("filename.xml") 


__all__ = 'MapParser', 


MAP_FORMAT_EXT_EXT = '.waw'
MAP_FORMAT_EXT_FULL = "WheresAllWaste", "*{}".format(MAP_FORMAT_EXT_EXT)
MAP_PATH_BASE = 'maps'
MAP_PACK_PREFERRED_EXT = 'zip'
MAP_DATA_EXT = 'data.xml'

MAP_SURFACE_EXT = '.png'

MAP_COLLISION_XML = 'id_collisions'
MAP_ENEMY_XML     = 'id_enemies'
MAP_LIGHT_XML     = 'id_lights'
MAP_DECAL_XML     = 'id_decals'

# ----

class WorldLoadException(Exception):
    pass



# ----

def dataParser(func): 
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
        r = func(*args, **kw)
    
    return wrapped
    

class MapParser(object):

    def __init__(self):
        pass

    @classmethod
    def mp_save(cls, data_fetcher):
        """
            TBD

            return -> None

        """
        mapname = cls.bf_mapname.get()

        filename = mp_file.asksaveasfilename(initialdir=MAP_PATH_BASE, filetypes=(MAP_FORMAT_EXT_FULL, ))
        if not filename: return None

        # Create directory for the map in the target base path
        map_path = path.join(getcwd(), MAP_PATH_BASE, filename)
        makedirs(map_path)

        # Build all the layers and save them
        #for index, name_id in ((0, 'l_ground'), (1, 'l_objects'), (2, 'l_walls')):
        #   cls.__parseWorld(data_fetcher('w_world', index), name_id, map_path) 

        root = xmlParse.Element('root')
        cls.__parseCollisions(root, data=data_fetcher('E_ID_COLLISION'), name=MAP_COLLISION_XML)

        cls.__parseEnemies(root, data=data_fetcher('E_ID_ENEMY'), name=MAP_ENEMY_XML)

        cls.__parseLights(root, data=data_fetcher('E_ID_LIGHT'), name=MAP_LIGHT_XML)

        cls.__parseDecals(root, data=data_fetcher('E_ID_DECAL'), name=MAP_DECAL_XML)

        final_tree = xmlParse.ElementTree(root)
        final_tree.write(path.join(map_path, MAP_DATA_EXT))

        # Save the collision tables
        #cls.__parseCollisions(map_path, data_fetcher('w_collision'), 'w')
        
        # Save the enemy positions and typle
        #cls.__parseEnemies(map_path, data_fetcher('w_enemy'), 'w')
        
        # Turn in to archive 
        #make_archive(filename, MAP_PACK_PREFERRED_EXT, map_path)
        #rmtree(map_path)   # Delete original mapfolder(now archived and copied)

        # Rename the extension to game specific format
        #tmp_path_base = path.join(getcwd(), MAP_PATH_BASE, '{}.{}'.format(filename, MAP_PACK_PREFERRED_EXT))
        #rename(tmp_path_base, ''.join(tmp_path_base.split('.')[:-1]) + MAP_FORMAT_EXT_EXT)

    
    @classmethod
    def __parseWorld(cls, data, name_id, final_path):
        """
            Clue all the subsurfaces together to form a full surface image
            for storing

            data -> Data used to form the layer
            name_id -> Name of layer on disk
            final_path -> Save path

            return -> None

        """
        base = surface.Surface(data[1], flags=SRCALPHA)

        # Blit all the subsurfaces to the full surface
        for column in data[0]:
            for x, y, surf in column:
                base.blit(surf, (x, y))

        image.save(base, path.join(final_path, name_id + MAP_SURFACE_EXT))


    @classmethod
    @dataParser
    def __parseCollisions(cls, xml_root, data, name=''):
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
        # Compress the data by shifting the position closer to cell index positions 
        parent.text = '.'.join([str(pos >> 5) for token, _ in data for pos in token])
    

    @classmethod
    @dataParser
    def __parseEnemies(cls, xml_root, data, name=''):
        """
            Parse enemy data to/from xml file

            xml_root -> xml root object
            data -> Data to be written
            name -> Field name on the xml

            return -> None

        """
        segment = xmlParse.SubElement(xml_root, name)

        # Save the enemies in sorted order
        for e in sorted(data, key=lambda x: x[1].id):
            enemy = e[1]
            parent = xmlParse.SubElement(segment, name, name=enemy.id)
            parent.text = '{}.{}'.format(enemy.x >> 5, enemy.y >> 5) 


    @classmethod
    @dataParser
    def __parseLights(cls, xml_root, data, name=''):
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

            # Radius is stored, although, not used
            parent.text = '{}.{}.{}.{}'.format(light.x >> 5, light.y >> 5, light.radius, hex_repr)


    @classmethod
    @dataParser
    def __parseDecals(cls, xml_root, data, name=''):
        """
            TBD

            return -> None

        """
        segment = xmlParse.SubElement(xml_root, name)
        # Remember rotate!
        for x in data:
            print x

            
    
    @classmethod
    def mp_load(cls, editor_loader=False):
        """
            TBD

            return -> None

        """
        pass
