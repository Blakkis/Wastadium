from collections import namedtuple


__all__ = ('Id_Pickup', 'Id_Enemy', 'Id_Light', 'Id_Entity_Values')


# Note: Editor should adapt these aswell


class Id_Pickup(namedtuple('id_pickup', ['x', 'y', 'id', 'content', 'value'])):
    pass

class Id_Enemy(namedtuple('id_enemy', ['x', 'y', 'id'])):
    pass

class Id_Light(namedtuple('id_light', ['x', 'y', 'radius', 'color'])):
    pass

class Id_Entity_Values(namedtuple('id_entity', ['id', 'content', 'value'])):
    pass
