from Weapons import Weapons


__all__ = ('Inventory', )


class Inventory(Weapons):

	# kghl4, tkar30, pp4-dual, uuz62, sh87, ahs12, pp4, uuz62-dual, fist, kkl2, skp5

	# Player inventory/status shared between Player, Shop and UI
	i_playerStats = {}

	# Player Ammunition type/count (MAX: 99999)
	i_playerAmmo  = {}

	
	@classmethod
	def inv_Reset(cls, **kw):
		"""
			Setup the basics of inventory

			return -> None

		"""
		cls.i_playerStats['weapon'] = 'sh87'
		cls.i_playerStats['health'] = [10, 100]
		cls.i_playerStats['armor']  = [10, 100]
		cls.i_playerStats['credits'] = 19284
		cls.i_playerStats['mod_laser'] = 0

		for key, value in cls.all_ammo_data.iteritems():
			# Id = Count
			cls.i_playerAmmo[key] = 99999
 	 