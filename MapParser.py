from shutil import make_archive, rmtree
from os import path, makedirs, rename, getcwd
import tkFileDialog as mp_file
from pygame import image, surface, SRCALPHA


__all__ = 'MapParser', 


MAP_FORMAT_EXT_EXT = '.waw'
MAP_FORMAT_EXT_FULL = "WheresAllWaste", "*{}".format(MAP_FORMAT_EXT_EXT)
MAP_PATH_BASE = 'maps'
MAP_PACK_PREFERRED_EXT = 'zip'

MAP_SURFACE_EXT = '.png'
MAP_SURFACE_GROUND  = 'ground'		# Note: These should be fetched from the 'World' class
MAP_SURFACE_OBJECTS = 'objects'
MAP_SURFACE_WALLS   = 'walls'


class WorldLoadException(Exception):
    pass


class MapParser(object):

    
    def __init__(self):
        pass


    @classmethod
    def mp_save(cls, data_fetch):
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

        # Create all the
        for index, name_id in ((0, MAP_SURFACE_GROUND), 
        		  			   (1, MAP_SURFACE_OBJECTS), 
        		  			   (2, MAP_SURFACE_WALLS)):
        	cls.__createSurfaceLayer(data_fetch('w_world', index), name_id, map_path) 

        
        # Turn in to archive 
        #make_archive(filename, MAP_PACK_PREFERRED_EXT, map_path)
        #rmtree(map_path)	# Delete original mapfolder(now archived and copied)

        # Rename the extension to game specific format
        #tmp_path_base = path.join(getcwd(), MAP_PATH_BASE, '{}.{}'.format(filename, MAP_PACK_PREFERRED_EXT))
        #rename(tmp_path_base, ''.join(tmp_path_base.split('.')[:-1]) + MAP_FORMAT_EXT_EXT)

    
    @classmethod
    def __createSurfaceLayer(cls, data, name_id, image_path):
    	"""
    		Clue all the subsurfaces together to form a full surface image
    		for storing

    		data -> Data used to form the layer
    		name_id -> Name of layer on disk

    		return -> None

    	"""
    	base = surface.Surface(data[1], flags=SRCALPHA)

    	# Blit all the subsurfaces to the full surface
    	for column in data[0]:
    		for x, y, surf in column:
    			base.blit(surf, (x, y))

    	image.save(base, path.join(image_path, name_id + MAP_SURFACE_EXT))


    	 

    
    @classmethod
    def mp_load(cls):
        """
            TBD

            return -> None

        """
        pass
