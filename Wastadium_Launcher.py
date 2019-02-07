import Tkinter as tk
import tkMessageBox as mp_error

import ttk as tk_adv
from os import path

from PIL import ImageTk, Image
from ConfigsModuleEditor import ed_centerWidget

from subprocess import Popen

from collections import OrderedDict, namedtuple

from ConfigsModule import DefaultConfigParser


VERSION = 1.0


ID_0 = """Game Resolution.

Note: You can apply custom resolution 
via the 'default.ini' (Not recommended).

These resolutions are chosen based on 
testing to provide good performance. 
(Game was build 1280x720 in mind)
"""

ID_1 = """Enable/Disable Fullscreen.

Note: blackbars might annoy you,
if the aspect ratio is wrong.
"""

ID_2 = """Enable/Disable Wall Shadows.

Note: This is the biggest framerate booster if you disable it 
(Tho you can see everything)
Note: If you want to build a map with 
lots of enemies, i recommend 
that you disable it.
"""

ID_3 = """Wall Shadows Quality.

HIGH: Very expensive RGBA values.
LOW:  Pure black darkness. Use this
      if the game lags in 'HIGH'
"""

ID_4 = """Enable/Disable Character Shadows.

Cast small ellipse shadow (Player only)
(Might enable in the future for enemies 
aswell.)
"""

ID_5 = """Enable/Disable Effects.

Effects include: bullet casings, wall hits, blood flying and what not.
"""

ID_6 = """Enable/Disable footstep decals?

Should player leave footprints when walking over stained floor?
"""

ID_7 = """Select Control Scheme

Controls how movement is handled
TANK: Up moves in the direction of player
AXIS: Up moves up regardless of direction

(Applies to all movement input)
"""

MAPPING = {'OFF':  0,
           'ON':   1,
           'TANK': 0,
           'AXIS': 1,
           'LOW':  0,
           'HIGH': 1}

option = namedtuple("option", ['name', 'option_id', 'options', 'help_id', 'sep'])
OPTIONS = OrderedDict()

OPTIONS[0] = option('Resolution:',     'resolution',            ('(1280, 720)', '(1024, 768)', '(800, 600)'), ID_0, False)
OPTIONS[1] = option('Fullscreen:',     'fullscreen',            ('ON', 'OFF'),    ID_1, True )
OPTIONS[2] = option('Shadows:',        'world_shadows',         ('ON', 'OFF'),    ID_2, False)
OPTIONS[3] = option('Shadow Quality',  'world_shadows_quality', ('HIGH', 'LOW'),  ID_3, True )
OPTIONS[4] = option('Light Shadows',   'world_char_shadows',    ('ON', 'OFF'),    ID_4, False)
OPTIONS[5] = option('Effects',         'world_effects',         ('ON', 'OFF'),    ID_5, False)
OPTIONS[6] = option('Footstep Decals', 'world_footsteps',       ('ON', 'OFF'),    ID_6, True)
OPTIONS[7] = option('Control Scheme',  'control_scheme',        ('AXIS', 'TANK'), ID_7, False)


class LabelOptionMenu(tk.Frame):

    grid = {'row': 0}

    # Label_tag_id: StringVar
    config_vars = {}

    def __init__(self, base, label_tag, label_tag_id, entry_values, help_id_update, help_msg, default_value=None):
        self.help_msg = help_msg

        self.label = tk.Label(base, text=label_tag, anchor=tk.W)
        self.label.grid(row=self.grid['row'], column=0, sticky=tk.W + tk.E)
        self.label.bind("<Enter>", lambda event: help_id_update(self.help_msg))

        self.config_vars[label_tag_id] = tk.StringVar()
        self.config_vars[label_tag_id].set(entry_values[0] if default_value is None else default_value) 

        self.option_menu = tk.OptionMenu(base, self.config_vars[label_tag_id], *entry_values)
        self.option_menu.config(width=8)
        self.option_menu.grid(row=self.grid['row'], column=1, sticky=tk.W + tk.E)
        self.option_menu.bind("<Enter>", lambda event: help_id_update(self.help_msg))

        self.grid['row'] += 2


    @classmethod
    def read_var_states(cls):
        """
            return -> Return states of all instance StringVars
        """
        for key, var in cls.config_vars.iteritems():
            v = var.get()
            v = MAPPING[v] if v in MAPPING else v

            yield key, v


class Launcher_Options(tk.Frame, DefaultConfigParser):
    def __init__(self, *args, **kw):
        super(Launcher_Options, self).__init__(*args, **kw)
        self.config(padx=8, pady=8)

        self.tk_ParseDefaultConfigs()


        for key, value in OPTIONS.iteritems():
            try:
                index = self.def_values[value.option_id]
            except KeyError:
                pass
            else:
                if isinstance(index, tuple):
                    default = None
                else:
                    default = value.options[index ^ 1]

            LabelOptionMenu(self, value.name, value.option_id, value.options, 
                            self.help_box_update, value.help_id, default) 
            if value.sep:
                sep = tk_adv.Separator(self, orient='horizontal')
                sep.grid(sticky=tk.W + tk.E, columnspan=2, pady=8) 

        # This could be replaced with tk.Message (But Text handles wrapping better)
        self.help_box = tk.Text(self)
        self.help_box.config(bg='#FFFFFF', state='disabled', padx=4, pady=4,
                             background=self.cget('background'))
        self.help_box.grid(columnspan=2, sticky=tk.E + tk.W + tk.N + tk.S, pady=4) 

        self.help_box.bind("<Enter>", self.help_box_update)

        tk.Button(self, text='Save', command=self.save_config).grid(sticky=tk.W + tk.E) 
        
        columns, rows = self.grid_size()
        for col in xrange(columns):
            self.grid_columnconfigure(col, weight=1)

        self.grid_rowconfigure(15, weight=1)


    def save_config(self):
        """
            Save the configs

            return -> None

        """
        for key, value in LabelOptionMenu.read_var_states():
            assert key in self.def_values, "Following key: {} doesn't exist in default configs!".format(key)

            self.def_values[key] = value

        self.tk_ParseDefaultConfigs(force_rewrite=1)



    def help_box_update(self, msg='', *args, **kw): 
        """
            Update the message widget text

            msg -> string

            return -> None

        """
        self.help_box.config(state='normal')
        self.help_box.delete('1.0', 'end')
        self.help_box.insert(tk.END, '' if not isinstance(msg, basestring) else msg)
        self.help_box.config(state='disabled')


class Launcher_Main(tk.Frame, object):
    def __init__(self, *args, **kw):
        super(Launcher_Main, self).__init__(*args, **kw)
        self.config(pady=32)

        launch_game = tk.Button(self, text='Launch Wastadium', 
                                command=lambda: self.launch_selection(game_or_editor='game'))
        launch_game.config(height=2)
        launch_game.pack(fill='both', padx=64, pady=4)

        _sep = tk_adv.Separator(self, orient='horizontal')
        _sep.pack(fill='x', padx=16, pady=16)
        
        launch_editor = tk.Button(self, text='Launch Editor', 
                                  command=lambda: self.launch_selection('editor'))
        launch_editor.config(height=2)
        launch_editor.pack(fill='both', padx=64, pady=4)

        try:
            self.background = ImageTk.PhotoImage(Image.open(path.join('textures', 'background', 
                                                                      'launcher_background.png')))
        except (IOError, Exception) as e:
            print e
            self.background = None

        if self.background is not None:
            self.label = tk.Label(self, image=self.background)
            self.label.pack(side=tk.BOTTOM)
    
    
    def launch_selection(self, game_or_editor):
        """
            Run the game or editor .exe(s)

            game_or_editor -> 'game' or 'editor'

            return -> None
            
        """
        try:
            if game_or_editor == 'game':
                name = 'Wastadium.exe' 
                Popen([name, ''])

            elif game_or_editor == 'editor':
                name = 'MapEditor.exe' 
                Popen([name, ''])
        
        except Exception:
            mp_error.showerror("Where Did They Go?", "Unable to locate: \"{}\"".format(name))



class Launcher(tk.Tk, object):
    def __init__(self):
        super(Launcher, self).__init__()
        self.title("Wastadium - Launcher, v{}".format(VERSION))
        self.geometry('400x532')
        self.resizable(0, 0)
        self.config(padx=8, pady=8)

        self.l_notebook = tk_adv.Notebook(self)
        self.l_notebook.add(Launcher_Main(self.l_notebook), text='Game')
        self.l_notebook.add(Launcher_Options(self.l_notebook), text='Options')

        self.l_notebook.pack(expand=1, fill='both')

        ed_centerWidget(self)

    
    def begin_mainloop(self):
        self.mainloop()


if __name__ == '__main__':
    Launcher().begin_mainloop()
