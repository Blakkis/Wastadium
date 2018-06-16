class RectInsideQuadrilateral(object):
    """
        Check if rect is inside the quadrilateral
        by breaking it in to 2 triangles and using barycentric coordinates
        to find any of the rect points inside the triangles
        (https://en.wikipedia.org/wiki/Barycentric_coordinate_system)
                
        Note: The core idea was written by someone else
              i simple extended the idea to work with quadrilaterals

        
    """
    
    @classmethod
    def sign(cls, p1, p2, p3):
        """
            TBD

            return ->
        """
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])


    @classmethod
    def pointInTriangle(cls, p1, p2, p3, p4):
        """
            TBD

            p1 -> Point to check if inside the triangle

            Points are handled in clockwise order
            p2 -> Triangle point 
            p3 -> -||-
            p4 -> -||-

            return -> 'True' if point is inside the triangle points, 'False' otherwise
        """
        t1 = cls.sign(p1, p2, p3) < 0
        t2 = cls.sign(p1, p3, p4) < 0
        t3 = cls.sign(p1, p4, p2) < 0

        return t1 == t2 and t2 == t3


    @classmethod
    def rectInsideQuadrilateral(cls, quad_points, rect):
        """
            TBD

            quad_points -> list of 4 (x, y) points in clockwise order
            rect -> A rect to test if its inside the quadrilateral 
            
            return -> 'True' if inside 'False' otherwise
        """
        # The quad is broke in to 2 clockwise triangles
        tri1 = quad_points[0], quad_points[1], quad_points[3]
        tri2 = quad_points[3], quad_points[1], quad_points[2]

        return all((cls.pointInTriangle(p, *tri1) or cls.pointInTriangle(p, *tri2)) \
                    for p in (rect.topleft, rect.topright, rect.bottomleft, rect.bottomright))
                
