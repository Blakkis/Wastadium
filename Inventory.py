from Weapons import Weapons
from GadgetLoader import GadgetLoader


__all__ = ('Inventory',)


class Inventory(Weapons, GadgetLoader):

    # kghl4, tkar30, pp4-dual, uuz62, sh87, ahs12, pp4, uuz62-dual, fist, kkl2, skp5, hbullx1

    # Player inventory/status shared between Player, Shop and UI
    i_playerStats = {}

    # Player Ammunition type/count (MAX: 99999)
    i_playerAmmo  = {}

    # Max amout of ammo player can hold for each ammo type
    _i_max_ammo = 99999

    
    @classmethod
    def inv_changeWeapon(cls, key):
        """
            Rotate the weapon wheel classes and return the first one

            key -> Weapon wheel id

            return -> None

        """
        k = 'w_{}'.format(cls.tk_key_name(key))
        weapon_tag = cls.i_playerStats[k][0]
        cls.i_playerStats['weapon'] = weapon_tag

        # Rotate next weapon in wheel
        cls.i_playerStats[k].rotate(1)

        return weapon_tag

    
    @classmethod
    def inv_reset(cls, **kw):
        """
            Setup the basics of inventory

            return -> None

        """
        cls.i_playerStats['weapon'] = 'uuz62'
        cls.i_playerStats['health'] = [10, 100]
        cls.i_playerStats['armor']  = [10, 100]
        cls.i_playerStats['credits'] = 19284
        
        # Setup gadgets booleans
        for key in cls.gl_gadgets: 
            cls.i_playerStats[key] = 1

        for key, value in cls.all_ammo_data.iteritems():
            # Id = Count
            cls.i_playerAmmo[key] = cls._i_max_ammo

        # Setup weapon wheels
        for key, value in cls.all_weapons.iteritems():
            k = 'w_{}'.format(value['w_class'])
            
            # Each key slot has wheel on it
            if k not in cls.i_playerStats:
                cls.i_playerStats[k] = cls.tk_deque()
            
            cls.i_playerStats[k].append(key)

        #print cls.i_playerStats
     
