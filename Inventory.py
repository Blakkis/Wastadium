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
	def inv_Reset(cls, **kw):
		"""
			Setup the basics of inventory

			return -> None

		"""
		cls.i_playerStats['weapon'] = 'hbullx1'
		cls.i_playerStats['health'] = [10, 100]
		cls.i_playerStats['armor']  = [10, 100]
		cls.i_playerStats['credits'] = 19284
		
		# Setup gadgets booleans
		for key in cls.gl_gadgets: cls.i_playerStats[key] = 1

		for key, value in cls.all_ammo_data.iteritems():
			# Id = Count
			cls.i_playerAmmo[key] = cls._i_max_ammo
 	 