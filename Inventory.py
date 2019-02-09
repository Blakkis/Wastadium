from Weapons import Weapons
from GadgetLoader import GadgetLoader


__all__ = ('Inventory',)


class Inventory(Weapons, GadgetLoader):

    # kghl4, tkar30, pp4-dual, uuz62, sh87, ahs12, pp4, uuz62-dual, fist, kkl2, skp5, hbullx1

    # Player inventory/status shared between Player, Shop and UI
    i_playerStats = {}

    # Player Ammunition type/count (MAX: 99999)
    i_playerAmmo  = {}

    # Default weapon for the player (Using anything else than 'fist' might break the game)
    __default_weapon = 'fist'

    
    @classmethod
    def set_def_active_wpn(cls): cls.i_playerStats['weapon'] = cls.__default_weapon
    

    @classmethod
    def inv_changeWeapon(cls, key):
        """
            Rotate the weapon wheel classes and return the first one

            key -> Weapon wheel id

            return -> Weapon name from the weapon wheel (Or 'None' if empty)

        """
        wheel = 'w_{}'.format(cls.tk_key_name(key))
        # Empty weapon wheel, return None
        if len(cls.i_playerStats[wheel]) == 0:
            return None

        weapon_tag = cls.i_playerStats[wheel][0]
        cls.i_playerStats['weapon'] = weapon_tag

        # Rotate next weapon in wheel
        cls.i_playerStats[wheel].rotate(1)

        return weapon_tag
    
    
    @classmethod
    def setup_inventory(cls, **kw):
        """
            Setup the basics of inventory

            return -> None

        """
        cls.i_playerStats['weapon']  = cls.__default_weapon 
        cls.i_playerStats['health']  = [100, 100]
        cls.i_playerStats['armor']   = [100, 100]    
        cls.i_playerStats['credits'] = 0
        cls.i_playerStats['alive']   = True
        
        # Setup gadgets booleans
        for key in cls.gl_gadgets: 
            cls.i_playerStats[key] = 0

        # Ammo
        for key, value in cls.all_ammo_data.iteritems():
            # Id = Count
            cls.i_playerAmmo[key] = 0

        # Setup weapon wheels
        for key, value in cls.all_weapons.iteritems():
            wheel = 'w_{}'.format(value['w_class'])
            
            # Each key slot has wheel on it
            if wheel not in cls.i_playerStats:
                cls.i_playerStats[wheel] = cls.tk_deque()
            else:
                cls.i_playerStats[wheel].clear()
            
            # Give player the default weapon
            if key == cls.__default_weapon:
                cls.i_playerStats[wheel].append(key)
     
