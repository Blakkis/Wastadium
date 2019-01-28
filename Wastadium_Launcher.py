import Tkinter as tk
import ttk as tk_adv
from os import path

from PIL import ImageTk, Image
from ConfigsModuleEditor import ed_centerWidget

from subprocess import Popen

from collections import OrderedDict


ON = HIGH = 1
OFF = LOW = 0

ID_0 = """Note: You can apply custom resolution 
via the 'default.ini' (Not recommended).

These resolutions are chosen based on 
testing to provide good performance. 
(Game was build 1280x720 in mind)
"""

ID_1 = """Enable fullscreen.

Note: blackbars might annoy you,
if the aspect ratio is wrong.
"""

ID_2 = """Should walls cast shadows?

Note: This is the biggest framerate booster, if you disable it 
(Tho you can see everything)

Note: If you want to build a map with 
lots of enemies, i recommend 
that you disable it.
"""

ID_3 = """Quality of the wall shadows

HIGH: Very expensive RGBA values.
LOW:  Pure black darkness. Use this
      if the game lags in 'HIGH'
"""

ID_4 = """Should spotlights cast actor shadows?

Cast small ellipse shadow (Player only)
(Might enable in the future for enemies 
aswell.)
"""

ID_5 = """Enable/Disable effects?

Effects include: bullet casings, wall hits, blood flying and what not.
"""

ID_6 = """Enable/Disable footstep decals?

Should player leave footprints when walking over stained floor?
"""


OPTIONS = OrderedDict()
OPTIONS['Resolution:']     = ['1280x720', '1024x768', '800x600'], ID_0
OPTIONS['Fullscreen:']     = ['OFF',   'ON'], ID_1, 'sep' 
OPTIONS['Shadows:']        = ['ON',   'OFF'], ID_2
OPTIONS['Shadow Quality:'] = ['HIGH', 'LOW'], ID_3, 'sep' 
OPTIONS['Light Shadows:']  = ['ON',   'OFF'], ID_4
OPTIONS['Effects']         = ['ON',   'OFF'], ID_5
OPTIONS['Footstep Decals'] = ['ON',   'OFF'], ID_6, 'sep'


VERSION = 1.0


class LabelOptionMenu(tk.Frame):

    _grid = {'row':     0,
             'column': -1}

    def __init__(self, base, label_tag, entry_values, help_id_update, help_msg):
        self.help_msg = help_msg

        self.label = tk.Label(base, text=label_tag, anchor=tk.W)
        self.label.grid(row=self._grid['row'], column=0, sticky=tk.W + tk.E)
        self.label.bind("<Enter>", lambda event: help_id_update(self.help_msg))

        self.option = tk.StringVar()
        self.option.set(entry_values[0])
        self.option_menu = tk.OptionMenu(base, self.option, *entry_values)
        self.option_menu.config(width=8)
        self.option_menu.grid(row=self._grid['row'], column=1, sticky=tk.W + tk.E)
        self.option_menu.bind("<Enter>", lambda event: help_id_update(self.help_msg))

        self._grid['row'] += 2



class Launcher_Options(tk.Frame, object):
    def __init__(self, *args, **kw):
        super(Launcher_Options, self).__init__(*args, **kw)
        self.config(padx=8, pady=8)

        for key, value in OPTIONS.iteritems():
            sep = True if len(value) > 2 else False

            LabelOptionMenu(self, key, value[0], help_id_update=self.help_box_update, help_msg=value[1]) 
            if sep:
                sep = tk_adv.Separator(self, orient='horizontal')
                sep.grid(sticky=tk.W + tk.E, columnspan=2, pady=8) 

        # This could be replaced with tk.Message (But Text handles wrapping better)
        self.help_box = tk.Text(self)
        self.help_box.config(bg='#FFFFFF', state='disabled', padx=4, pady=4,
                             borderwidth=0, background=self.cget('background'))
        self.help_box.grid(columnspan=2, sticky=tk.E + tk.W + tk.N + tk.S, pady=4) 

        self.help_box.bind("<Enter>", self.help_box_update) 
        
        columns, rows = self.grid_size()
        for col in xrange(columns):
            self.grid_columnconfigure(col, weight=1)

        self.grid_rowconfigure(14, weight=1)

    def help_box_update(self, msg='', *args, **kw): 
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
            self.label.pack()
    
    
    def launch_selection(self, game_or_editor):
        """
            Run the game or editor .exe(s)

            game_or_editor -> 'game' or 'editor'

            return -> None
            
        """
        if game_or_editor == 'game':
            Popen(["python", "wastadium.py"])

        elif game_or_editor == 'editor':
            Popen(["python", "mapeditor.py"])



class Launcher(tk.Tk, object):
    def __init__(self):
        super(Launcher, self).__init__()
        self.title("Wastadium - Launcher, v{}".format(VERSION))
        self.geometry('400x512')
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
