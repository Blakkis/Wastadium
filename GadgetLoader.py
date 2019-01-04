from ConfigsModule import GlobalGameData
from MapParser import W_errorToken

__all__ = ('GadgetLoader', 'LaserSightModule')

# Note: 


class GadgetLoader(GlobalGameData):

    gl_gadgets = {}

    
    def __init__(self):
        pass

    
    @classmethod
    @W_errorToken("Error Initializing Gadgets!")
    def load_gadgets(cls):
        """
            TBD

            return -> None

        """
        # Source path for the gadget configs
        src_path_cfg = cls.tk_path.join('configs', 'gadgets')

        # Source path for the gadget textures
        ui_elem_path_tex = cls.tk_path.join('textures', 'uielements')

        for cfg in cls.tk_iglob(cls.tk_path.join(src_path_cfg, '*.cfg')):
            name = cls.tk_path.split(cfg)[-1].split('.')[0]
            tex_data = {'g_tex': None,
                        'g_price': 100,
                        'g_desc': '-'}
            
            for line in cls.tk_readFile(cfg, 'r'):
                if line[0] == 'g_tex': tex_data[line[0]] = cls.tk_image.load(cls.tk_path.join(ui_elem_path_tex, line[1])).convert_alpha()
                
                elif line[0] == 'g_price': tex_data[line[0]] = int(line[1]) 
                
                elif line[0] == 'g_desc': tex_data[line[0]] = line[1].replace('_', ' ') 

            cls.gl_gadgets[name] = tex_data


                
class LaserSightModule(GlobalGameData):
    """
        Cast a lasersight from player position
        with offsets to keep the laser in left eye

        Note: Only player should have this

    """
    def __init__(self, wall_check_function):
        # Color of the laser beam
        self.l_color = 0xff, 0x0, 0x0, 0x80

        # Provide for the cosine a constant increasing value
        self.l_sway = 0

        # NOTE: Need to change these to use the head base tracking (with these coming from rest of the frames)

        # Generate lasersight base offsets
        # Keep the lasersight front of the left eye when the head bobbles 
        # (Hmmm... bad idea for custom animations)
        self.l_offsets = {1: [2,  -16],     
                          2: [1,  -15],
                          3: [0,  -9 ],
                          4: [0,  -4 ],
                          5: [2,  -4 ],
                          6: [4,  -4 ],
                          7: [4,  -9 ],
                          8: [4,  -15]}
        for k in self.l_offsets.keys():
            v = self.l_offsets[k] 
            self.l_offsets[k].append(self.tk_atan2(v[0], v[1]))
            self.l_offsets[k].append(self.tk_hypot(v[0], v[1]))

        # Raycast function for checking walls within line-of-sight
        self.l_wall_check = wall_check_function 

  
    def cast_lasersight(self, surface, angle, dist, base, sway=False, firing=False, delta=0):
        """
            If player has bought the lasersight module
            cast a small laser beam

            surface -> Surface which receives the beam
            angle -> view angle (Radians)
            dist -> Max distance for the laser ray
            base -> base for the headtracking
            sway -> Sway the lasersight when moving (for added realism)
            firing -> Stable the aim when firing (Doesn't sway the lasersight)

            return -> None

        """
        # Only sway the lasersight when moving
        if sway and not firing: 
            angle += 0.04 * self.tk_cos(self.l_sway)
            self.l_sway = (self.l_sway + 16 * delta) % 32 

        # Get the lasersight offset
        ofs = base if not sway or firing else self.l_offsets[sway] 

        vecx = self.tk_sin(angle)
        vecy = self.tk_cos(angle)

        # Get all collisions intersecting the ray
        dist = self.l_wall_check(self.tk_res_half[0], 
                                 self.tk_res_half[1], 
                                 vecx, vecy, dist, 
                                 ret_first_dist=1)

        # Starting point
        sx = self.tk_res_half[0] + self.tk_sin(angle - ofs[2]) * ofs[3] 
        sy = self.tk_res_half[1] + self.tk_cos(angle - ofs[2]) * ofs[3]

        # Endpoint
        ex = self.tk_res_half[0] - vecx * dist 
        ey = self.tk_res_half[1] - vecy * dist  

        # Cast the visuals
        self.tk_draw_aaline(surface, self.l_color, (sx, sy), (ex, ey))
        self.tk_draw_circle(surface, self.l_color, (int(ex + 1), int(ey + 1)), 2)
        
