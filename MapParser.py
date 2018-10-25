import tkFileDialog as mp_file
import tkMessageBox as mp_error
import xml.etree.cElementTree as xmlParse

from pygame import image, surface, SRCALPHA
from shutil import make_archive, rmtree
from os import path, makedirs, rename, getcwd


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

# Format in which the layers are stored
MAP_SURFACE_EXT = '.png'

# layer tags
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


# ----

class WastadiumEditorException(Exception):
    pass



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
            mp_error.showerror("", e)
 
    return wrapped
    

class MapParser(object):
    
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
        mapname = cls.bf_mapname.get()

        filename = mp_file.asksaveasfilename(initialdir=MAP_PATH_BASE,
                                             initialfile=mapname,
                                             filetypes=(MAP_FORMAT_EXT_FULL, ))
        if not filename: 
            return None


        # Create directory for the map in the target base path
        map_path = path.join(getcwd(), MAP_PATH_BASE, filename)
        makedirs(map_path)

        root = xmlParse.Element('root')
        cls.__parseCollisions(root, data=data_fetcher(cls.E_ID_COLLISION), name=MAP_COLLISION_XML)

        cls.__parseEnemies(root, data=data_fetcher(cls.E_ID_ENEMY), name=MAP_ENEMY_XML)

        cls.__parseLights(root, data=data_fetcher(cls.E_ID_LIGHT), name=MAP_LIGHT_XML)

        cls.__parseDecals(root, data=data_fetcher(cls.E_ID_DECAL), name=MAP_DECAL_XML)

        cls.__parseWires(root, data=data_fetcher(cls.E_ID_WIRE), name=MAP_WIRE_XML)

        cls.__parsePickups(root, data=data_fetcher(cls.E_ID_PICKUP), name=MAP_PICKUP_XML)

        # Build all the layers and save them
        ws = data_fetcher('w_Size', layers=False)[2:4]
        for l_id, name_id in ((cls.E_ID_GROUND, MAP_GROUND), (cls.E_ID_OBJECT, MAP_OBJECTS), (cls.E_ID_WALL, MAP_WALLS)):
            cls.__parseWorld(data_fetcher(l_id), name_id, map_path, ws, l_id) 

        final_tree = xmlParse.ElementTree(root)
        final_tree.write(path.join(map_path, MAP_DATA_EXT))

        # Turn in to archive 
        make_archive(filename, MAP_PACK_PREFERRED_EXT, map_path)
        rmtree(map_path)   # Delete original mapfolder(now archived and copied)

        # Rename the extension to game specific format
        tmp_path_base = path.join(getcwd(), MAP_PATH_BASE, '{}.{}'.format(filename, MAP_PACK_PREFERRED_EXT))
        rename(tmp_path_base, ''.join(tmp_path_base.split('.')[:-1]) + MAP_FORMAT_EXT_EXT)

    
    @classmethod
    def __parseWorld(cls, data, name_id, final_path, final_size, layer_index=-1):
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

        image.save(base, path.join(final_path, name_id + MAP_SURFACE_EXT))


    @classmethod
    @dataParseCheck
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
    @dataParseCheck
    def __parseEnemies(cls, xml_root, data, name=''):
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

            # x, y
            parent.text = '{}.{}'.format(enemy.x >> 5, enemy.y >> 5) 


    @classmethod
    @dataParseCheck
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

            # x, y, radius(Kept for future use), hex color
            parent.text = '{}.{}.{}.{}'.format(light.x >> 5, light.y >> 5, light.radius, hex_repr)


    @classmethod
    @dataParseCheck
    def __parseDecals(cls, xml_root, data, name=''):
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
    def __parseWires(cls, xml_root, data, name=''):
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
    def __parsePickups(cls, xml_root, data, name=''):
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
            TBD

            return -> None

        """
        filename = mp_file.askopenfilename(initialdir=MAP_PATH_BASE, filetypes=(MAP_FORMAT_EXT_FULL, ))
        print filename


if __name__ == '__main__':
    pass
    #MapParser.mp_load()
