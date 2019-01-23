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


class Id_Decal(namedtuple('id_decal', ['tex', 'name', 'pos', 'w', 'h', 'orient'])):
	pass


class Id_Wire(namedtuple('id_wire', ['p1', 'p2', 'color'])):
	pass


class Id_Entity_Values(namedtuple('id_entity', ['id', 'content', 'value'])):
    pass


# ---- (These should be moved on their' own modules)

class Ed_Processing(namedtuple('ed_processing', ['window', 'update', 'finish'])):
	pass

class Ed_CellPoint(namedtuple('ed_cellpoint', ['x', 'y', 'id'])):
	pass


class PackerParserToken(namedtuple('PackerParserToken', ['parse', 'id'])):
	pass


class PackerParserCell(namedtuple('PackerParserCell', ['low', 'mid', 'obj', 'link'])):
	pass


class MenuEventDispatch(namedtuple('MenuEventDispatch', ['get_event', 'get_ticks'])):
	pass


class EnemyDeathSeq(namedtuple('enemydeathseq', ['angle_deg', 'g_profile', 'd_frame', 'e_weapon'])):
	pass