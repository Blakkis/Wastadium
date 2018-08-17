from collections import namedtuple


__all__ = ('ID_Pickup', 'ID_Enemy', 'ID_Light')


# Note: Editor should adapt these aswell


class ID_Pickup(namedtuple('id_pickup', ['x', 'y', 'id', 'value'])):
	pass



class ID_Enemy(namedtuple('id_enemy', ['x', 'y', 'id'])):
	pass



class ID_Light(namedtuple('id_light', ['x', 'y', 'radius', 'color'])):
	pass