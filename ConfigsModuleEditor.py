import pygame
import Tkinter as tk
import ttk
import tkMessageBox
import math
from PIL import Image as pil_image
from ImageTk import PhotoImage
from os import environ, path
from collections import deque
from compiler.ast import flatten
from copy import copy

from pprint import pprint as prn



__all__ = ('GlobalGameDataEditor', 'ed_killMe',     'ed_centerWidget', 
           'ed_LabelFrame',        'ed_TopLevel',   'ed_Checkbutton',
           'ed_LabelImagePreview', 'ed_LabelEntry', 'ed_Button',
           'ed_AutoWallSolver',    'ed_BitToggle')


class ed_BitToggle(object):
    """
        Provide capsulated toggle bit for inside lambdas
    """
    def __init__(self):
        self._bit = 0
    
    @property
    def bit(self): return self._v

    def bit_toggle(self): self._bit ^= 1

    def __nonzero__(self): return self._bit



class ed_AutoWallSolver(object):
    """
        Solve the Autowall matrix

    """
    # Number of edges : Correct segment
    # Note: This relies on the fact that all the wallset textures are created in the proper order
    __aw_axis_id = {0: 6,       # Free
                    1: 3,       # Cap 
                    2: (1, 2),  # Line/Corner 
                    3: 4,       # T 
                    4: 5}       # Cross 

    __aw_deque = deque

    @classmethod
    def __aw_segmentOrient(cls, center, grid, wsize):
        """
            Find the correct segment and orientation based on surrounding walls

            return -> orient, segment

        """
        x, y = center

        # Check the near segments for the wall
        # Make sure the segments are inside the map

        # Top, Bottom
        t = grid[y - 1][x] if -1 < y - 1 < wsize[1]     else None 
        b = grid[y + 1][x] if -1 < y + 1 < len(grid)    else None
        
        # Left, Right
        l = grid[y][x - 1] if -1 < x - 1 < wsize[0]     else None 
        r = grid[y][x + 1] if -1 < x + 1 < len(grid[0]) else None
        
        # Check the near cells if they contain a wall
        t = 1 if t is not None and sum(t[2]) else 0
        b = 1 if b is not None and sum(b[2]) else 0
        l = 1 if l is not None and sum(l[2]) else 0
        r = 1 if r is not None and sum(r[2]) else 0

        # Number of edges near
        seg = sum((t, b, l, r))
        
        # Cap needs top and bottom swapped
        o = cls.__aw_deque((t, l, b, r) if seg == 1 else (b, l, t, r))

        # if the segment id contains multiple segment use this to id the correct one
        special_index = None

        # Orientation for the segment
        ori = 0

        # No rotation needed (Free or cross)
        if seg in (0, 4): pass 

        # One wall near (Cap)
        elif seg == 1: 
            o.rotate(-1)
            ori = list(o).index(1)

        elif seg == 2:
            # Corner
            if o[1] + o[3] == 1:
                special_index = 0
                # Brute force the correct orientation
                for r in xrange(4):
                    if o[0] and o[3]:
                        ori = r; break
                    o.rotate(1) 
                
            # Line
            else:
                special_index = 1
                if o[0] and o[2]: ori = 1

        # T 
        elif seg == 3:
            # Brute force the correct orientation
            for r in xrange(4):
                if o[0] and o[3] and o[2]:
                    ori = r; break
                o.rotate(1)

        # Get the correct segment
        seg = cls.__aw_axis_id[seg]
        if isinstance(seg, tuple): seg = seg[special_index] 
        
        return ori, seg
            


    @classmethod
    def __aw_getGridCenter(cls, grid, center):
        """
            Get the center of the 5x5 grid

            grid -> 5x5 grid sample from the world around the mouse
            center -> mouse cell position

            return -> Index of the center (x, y)

        """
        for e1, y in enumerate(grid):
            for e2, x in enumerate(y):
                if center == tuple(x[:2]):    
                    return e2, e1

    
    @classmethod
    def aw_autoWallSolve(cls, grid, center, wsize, delete=False):
        """
            TBD

            grid -> 5x5 grid sample from the world around the mouse
            center -> mouse cell position
            wsize -> Worldsize (per cell)
            delete -> Delete the middle cell (Inverse of this function) 

            return -> TBD

        """
        # Final layout
        cell_layout = []

        c_grid = grid[:]

        i = cls.__aw_getGridCenter(grid, center)

        # Solve the center wall first
        cseg = (center[0], center[1], cls.__aw_segmentOrient(i, grid, wsize)) 
        c_grid[i[1]][i[0]] = cseg
        cell_layout.append(cseg)

        # Solve the surrounding segments
        for ofx, ofy in ((0, -1), (-1, 0), (0, 1), (1, 0)):
            bndx, bndy = center[0] + ofx, center[1] + ofy
            # Make sure the offsets are within map boundaries
            if -1 < bndx < wsize[0] and -1 < bndy < wsize[1]:
                gpos = i[0] + ofx, i[1] + ofy
                if sum(c_grid[gpos[1]][gpos[0]][2]) == 0: continue

                cseg = (bndx, bndy, cls.__aw_segmentOrient((gpos[0], gpos[1]), c_grid, wsize)) 

                c_grid[gpos[1]][gpos[0]] = cseg
                cell_layout.append(cseg)  


        return cell_layout


def ed_killMe(func):
    """
        Every function that calls 'Toplevel' should use this 
        so only one instance can be alive at any given moment
        insert the following code in top of the function:

        func -> Function to decorate

        return -> Innerfunc

    """
    def innerFunc(*args, **kw):
        _id = func(*args, **kw)
        
        try:
            if ed_killMe.instance_id.winfo_exists:
                ed_killMe.instance_id.destroy()
        except AttributeError:
            # First boot so the instance_id does not exist yet 
            pass
        
        ed_killMe.instance_id = _id
        
        return _id
    
    return innerFunc


def ed_centerWidget(widget):
    """
        After the widget has been created
        use this function to center it on screen

        widget -> widget to be centered on screen

        return -> None

    """
    widget.update_idletasks()
    scr_w, scr_h = widget.winfo_screenwidth(), widget.winfo_screenheight()
    wig_w, wig_h = widget.winfo_width(),       widget.winfo_height()
    pos = scr_w / 2 - wig_w / 2, scr_h / 2 - wig_h / 2  

    widget.geometry('{}x{}+{}+{}'.format(wig_w, wig_h, *pos))


# Note: Mostly used Tkinter widgets are subclassed to hide the options and settings from cluttering the maincode
# Note: Since ill be using pretty much similar styled widgets across the editor, this fits well.
# Note: All the arguments these takes are Tkinter basic arguments with slightly different name 

class ed_Checkbutton(tk.Checkbutton):
    """
        Extended Tk.Checkbutton

    """
    def __init__(self, base, text, variable, row=0, column=0, **kw):
        tk.Checkbutton.__init__(self, base, text=text, variable=variable)
        self.grid(row=row, column=column, padx=5, sticky=tk.W)



class ed_Button(tk.Button):
    """
        Extended tk.Button

        All the buttons in the editor are tool buttons, which only 1 is allowed to be on at any given moment
        This class controls the behavior

    """
    # Make a set of buttons with only one being allowed to be 'on' at any given moment
    ed_button_all = []

    # Unique id for every button
    ed_button_id = 0

    # Keep the ON button hint active
    ed_hint_last = '-'
    
    def __init__(self, base, image, row=0, column=0, **kw):
        tk.Button.__init__(self, base, command=self.ed_toggle)
        self.config(image=image)
        self.ed_img = image     # Keep a reference
        
        self.ed_hint = kw['tool_h_t']
        self.ed_hint_l = kw['tool_h_l']

        self.bind('<Enter>', lambda event: self.ed_hint_l.set(self.ed_hint))
        self.bind('<Leave>', lambda event: self.ed_hint_l.set(self.ed_hint_last))

        self.grid(row=row, column=column, sticky=tk.W)
        
        self.ed_id = ed_Button.ed_button_id
        ed_Button.ed_button_id += 1

        # Store for toggling
        self.ed_button_all.append([self, 0])
        
    
    def ed_toggle(self, event=None, hotkey=False):
        """
            TBD
        """ 
        self.ed_button_all[self.ed_id][1] ^= 1
        self.config(relief=tk.SUNKEN if self.ed_button_all[self.ed_id][1] else tk.RAISED)

        # Reset the other buttons
        for enum, reset in enumerate(self.ed_button_all):
            if enum != self.ed_id: reset[0].config(relief=tk.RAISED); reset[1] = 0 

        self.ed_setHintState(self.ed_id, hotkey)
    
    
    @classmethod
    def ed_setHintState(cls, key_index, hotkey=False):
        """
            Change the toolbar hint message to reflect the current selected tool

            return -> None

        """
        if any([x[1] for x in cls.ed_button_all]):
            cls.ed_hint_last = cls.ed_button_all[key_index][0].ed_hint 
        else:
            cls.ed_hint_last = '-'

        # Update the hint label manually
        if hotkey: cls.ed_button_all[key_index][0].ed_hint_l.set(cls.ed_hint_last)  


    @classmethod
    def ed_setButtonState(cls, key_index):
        """
            The SDL window has the keyboard focus all the time
            So normal Tkinter binding wont work

            We're going to use this function to toggle the states of the buttons via
            SDL loop 

            key_index -> Index of the Button from the 'ed_button_all' and call its 'ed_toggle'  

            return -> None
        """
        cls.ed_button_all[key_index][0].ed_toggle(hotkey=True)
    
    
    @classmethod
    def ed_getButtonStates(cls, num_of_buttons=False):
        """
            Get the states of all the buttons

            num_of_buttons -> Return number of toolbar buttons

            return -> list of all button states (0 - 1)

        """
        if num_of_buttons: return len(cls.ed_button_all)
        try:
            return [b[1] for b in cls.ed_button_all].index(1)
        except ValueError:
            return -1 


class ed_LabelFrame(tk.LabelFrame):
    """
        Extended tk.LabelFrame

    """
    def __init__(self, base, w_title='', w_free=False, **kw):
        tk.LabelFrame.__init__(self, base, text=w_title)
        self.config(padx=2, pady=2)

        #if w_free:
        #   self.grid_rowconfigure(0, weight=1)
        #   self.grid_columnconfigure(0, weight=1)



class ed_TopLevel(tk.Toplevel):
    """
        Extended tk.TopLevel

        Release all freespace inside the Toplevel automatically 
        which allows widgets to take every space in the row/column

        Takes focus on init

    """
    # Note: The _KillMe decorator functionality could be implemented inside this class
    def __init__(self, w_title='', w_geometry='', w_takefocus=False, resizable=False, w_free=True, **kw):
        tk.Toplevel.__init__(self)
        if w_title: self.title(w_title)
        if w_geometry: self.geometry(w_geometry)
        if w_takefocus: self.focus_set()
        
        self.resizable(resizable, resizable)
        self.config(padx=5, pady=5)

        if w_free: self.grid_rowconfigure(0, weight=1); self.grid_columnconfigure(0, weight=1)
            


class ed_LabelEntry(tk.Entry):
    """
        TBD
    """
    def __init__(self, base, w_title='', variable=None, row=0, column=0, **kw):
        # Add the label leftside of the entry
        label = tk.Label(base, text=w_title)
        label.grid(row=row, column=column, sticky=tk.E)
        label.config(padx=5, pady=5)
        
        tk.Entry.__init__(self, base, textvariable=variable, width=16)
        self.grid(row=row, column=column + 1, sticky=tk.W, padx=5)
        self.config(justify=tk.CENTER, relief=tk.GROOVE)
        self.bind("<FocusIn>", self._resetEntry)
        self.bind("<FocusOut>", self._checkEntry)

        self.default_v = variable._default
        #self._resetEntry()

    
    def _resetEntry(self, event, eq_check=False):
        """
            TBD
        """
        if eq_check:
            pass
        else:
            self.delete(0, tk.END)


    def _checkEntry(self, event):
        """
            Clear the Entry field when clicked

            return -> None

        """
        if self.get():
            pass
        else:
            self.insert(0, self.default_v)


class ed_LabelImagePreview(object):
    def __init__(self, base, w_title='', w_default_id=None, variable=None, w_default_img=None, row=0, column=0, **kw):
        variable.set(w_default_id)  # Default value for the Tkinter variable

        # Description label
        self.ed_label = tk.Label(base, text=w_title)
        self.ed_label.grid(row=row, column=column, sticky=tk.E + tk.W)

        # Image label
        self.ed_img_label = tk.Label(base, image=w_default_img)
        self.ed_img_label.tex = w_default_img   # Keep reference!
        self.ed_img_label.grid(row=row + 1, column=0)

    
    def setImage(self, image):
        """
            Update image preview

            return -> None

        """
        self.ed_img_label.config(image=image)
        self.ed_img_label.tex = image



class GlobalGameDataEditor(object):
    """
        Editor options

    """
    # Game and Editor Data should be combined 

    # Special
    ed_name = 'MapEditor'
    ed_resolution = 1024, 768   # PygameFrame resolution   
    ed_fps = 8192
    ed_bg_color = 0x50, 0x50, 0x50
    ed_sdl_driver = 'windib'    # SDL driver see: https://www.libsdl.org/release/SDL-1.2.15/docs/html/sdlenvvars.html
    ed_chunk_size = 8           # Dont change this
    ed_chunk_size_raw = ed_chunk_size * 32
    
    # Row, column chunks per frame
    ed_chunk_per_row = ed_resolution[0] / ed_chunk_size_raw
    ed_chunk_per_col = ed_resolution[1] / ed_chunk_size_raw
    
    # row, column fragments per frame
    ed_frags_per_row = ed_resolution[0] / 32 / 2 
    ed_frags_per_col = ed_resolution[1] / 32 / 2

    # Pygame
    ed_init_everything = pygame.init 
    ed_mouse = pygame.mouse
    ed_image = pygame.image
    ed_surface = pygame.Surface
    ed_transform = pygame.transform
    ed_key = pygame.key
    ed_draw_rect = pygame.draw.rect
    ed_draw_line = pygame.draw.line
    ed_draw_circle = pygame.draw.circle
    ed_draw_aaline = pygame.draw.aaline
    ed_rect = pygame.Rect
    ed_srcalpha = pygame.SRCALPHA
    ed_font = pygame.font.Font
    ed_surfarray = pygame.surfarray

    # General 
    ed_pil_image = pil_image
    ed_photo_image = PhotoImage
    ed_msg_box = tkMessageBox
    ed_environ = environ
    ed_path = path
    ed_cos = math.cos
    ed_sin = math.sin
    ed_radians = math.radians
    ed_pi = math.pi
    ed_deque = deque 
    ed_flatten = staticmethod(flatten)
    ed_copy = staticmethod(copy) 

    # Tkinter
    ed_separator = ttk.Separator
    
    ed_sticky_n = tk.W
    ed_sticky_e = tk.E
    ed_sticky_s = tk.S
    ed_sticky_w = tk.W 
    ed_sticky_vert = tk.W + tk.E
    ed_sticky_hori = tk.N + tk.S
    ed_sticky_full = tk.W + tk.E + tk.N + tk.S

    ed_bool = tk.BooleanVar
    ed_str  = tk.StringVar
    ed_int  = tk.IntVar

    # User
    ed_keys = {'up': pygame.K_w, 'down':pygame.K_s, 'left':pygame.K_a, 'right':pygame.K_d, 
               'shift_l':1, 'action_1': pygame.K_1, 'action_2': pygame.K_2, 'action_3': pygame.K_3, 
               'action_rot': pygame.K_r}
    ed_scroll_speed = 1.0


    @classmethod
    def ed_fadeImage(cls, surface, opaque, convert=False):
        """
            Set surface opaque

            surface -> Surface on which to operate on
            opaque -> 0 -> 255

            return -> surface

        """
        # Note: Possible cache the results via texture name?
        #       if performace becomes issue
        if convert:
            alpha_image = surface.copy().convert_alpha()
        else:
            alpha_image = surface.copy()

        alpha_array = cls.ed_surfarray.pixels_alpha(alpha_image)
        # Apply opaque to every pixel whose alpha is greater than 0
        alpha_array[alpha_array > 0] = opaque

        return alpha_image


    @classmethod
    def ed_pygameToTkinter(cls, surface):
        """
            Convert pygame surface to Tkinter compatible format

            return -> Image

        """
        # Note: This should be moved inside the 'ed_LabelImagePreview' class
        
        # Convert Pygame surfaces to images suitable for Tkinter
         
        pygame_str = cls.ed_image.tostring(surface, 'RGB')
        size = surface.get_size()
        
        pil_str = cls.ed_pil_image.fromstring('RGB', size, pygame_str)
        img = cls.ed_photo_image(pil_str)
        
        return img

    
    @classmethod
    def ed_scaleImage(cls, surface, tsize):
        """
            Scale image while maintaining proper ratio

            surface -> Surface to which to operate on
            tsize -> Target surface size

            return -> Scaled surface

        """
        w, h = surface.get_size()
        
        if w < tsize[0] and h < tsize[1]: return surface
        
        # Ratio will be 1 if equal
        elif w == h: return cls.ed_transform.scale(surface, tsize)
        
        # Scale with ratio
        else:
            if w < h:
                ratio = float(w) / float(h)
                return cls.ed_transform.scale(surface, (int(tsize[0] * ratio), int(tsize[1])))
            else:
                ratio = float(h) / float(w)
                return cls.ed_transform.scale(surface, (int(tsize[0]), int(tsize[1] * ratio)))   
