import Tkinter as tk
import ttk as tk_adv


VERSION = 1.0

class LabelEntry(object):
	pass


class Launcher_Options(tk.Frame, object):
    def __init__(self, *args, **kw):
        super(Launcher_Options, self).__init__(*args, **kw)



class Launcher_Main(tk.Frame, object):
    def __init__(self, *args, **kw):
        super(Launcher_Main, self).__init__(*args, **kw)
        self.config(pady=32)

        launch_game = tk.Button(self, text='Launch Wastedium', command=lambda: None)
        launch_game.config(height=2)
        launch_game.pack(fill='both', padx=64, pady=4)

        _sep = tk_adv.Separator(self, orient='horizontal')
        _sep.pack(fill='x', padx=16, pady=16)
        
        launch_editor = tk.Button(self, text='Launch Editor', command=lambda: None)
        launch_editor.config(height=2)
        launch_editor.pack(fill='both', padx=64, pady=4)
    
    
    def launch_selection(self):
        pass    



class Launcher(tk.Tk, object):
    def __init__(self):
        super(Launcher, self).__init__()
        self.title("Wastedium - Launcher, v{}".format(VERSION))
        self.geometry('400x512')
        self.resizable(0, 0)
        self.config(padx=8, pady=8)

        self.l_notebook = tk_adv.Notebook(self)
        self.l_notebook.add(Launcher_Main(self.l_notebook), text='Game')
        self.l_notebook.add(Launcher_Options(self.l_notebook), text='Options')

        self.l_notebook.pack(expand=1, fill='both')

    
    def begin_mainloop(self):
        self.mainloop()


if __name__ == '__main__':
    Launcher().begin_mainloop()
