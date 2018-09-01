from shutil import make_archive
from os import path
import tkFileDialog as mp_file


__all__ = 'MapParser', 


MAP_FORMAT_SUFFIX = "WastadiumMapData", '*.wmd'


class WorldLoadException(Exception):
    pass


class MapParser(object):

    
    def __init__(self):
        pass


    @classmethod
    def mp_save(cls, _iter):
        """
            TBD

            return -> None

        """
        mapname = cls.bf_mapname.get()

        filename = mp_file.asksaveasfilename(initialdir='maps', filetypes=(MAP_FORMAT_SUFFIX,))
        #if not filename: return None

        print _iter()

    
    @classmethod
    def mp_load(cls):
        """
            TBD

            return -> None

        """
        pass
