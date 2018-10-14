from collections import namedtuple


__all__ = ('Id_Pickup', 'Id_Enemy', 'Id_Light', 'Id_Entity_Values', 'Id_Decal', 'Id_Wire')


# Note: Adapt more of these to get rid of constant indexing


class Id_Pickup(namedtuple('id_pickup', ['x', 'y', 'id', 'content', 'value', 'debug_name'])):
    
    __slots__ = ()
    # Debug_name is reserved for editor only.
    def __new__(cls, x, y, id, content, value, debug_name=None):
    	return super(Id_Pickup, cls).__new__(cls, x, y, id, content, value, debug_name)


class Id_Enemy(namedtuple('id_enemy', ['x', 'y', 'id', 'debug_name'])):
    
    __slots__ = ()
    # Debug_name is reserved for editor only.
    def __new__(cls, x, y, id, debug_name=None):
    	return super(Id_Enemy, cls).__new__(cls, x, y, id, debug_name)


class Id_Light(namedtuple('id_light', ['x', 'y', 'radius', 'color'])):
    pass


class Id_Entity_Values(namedtuple('id_entity', ['id', 'content', 'value'])):
    pass


class Id_Decal(namedtuple('id_decal', ['tex', 'name', 'pos', 'w', 'h', 'orientation'])):
	pass


class Id_Wire(namedtuple('id_wire', ['p1', 'p2', 'color'])):
	pass