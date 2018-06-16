import Tkinter as tk

from ConfigsModuleEditor import GlobalGameDataEditor 
from tkColorChooser import askcolor


# NOTE: Wire tool uses this class too (Need to clarify it more)  



class Lights(tk.Frame, GlobalGameDataEditor):

	l_rgb_color = None		# StringVar
	l_hex_color = None		# -- || --
	
	l_current_color = None	# Stored output of the askcolor()
	l_current_size  = 32	# Min: 32 Max: 128

	# Threshold between black & white foreground text on the button
	__l_threshold = 64

	
	def __init__(self, base, row, column):
		super(Lights, self).__init__(base)
		
		self.grid(row=row, column=column, columnspan=2, sticky=self.ed_sticky_full)

		self.l_button = tk.Button(self, text='Pick Color', command=lambda: self.l_pickColor(self.l_button), width=8)
		self.l_button.config(activebackground='#FFFFFF', background='#FFFFFF')	# Init color : white
		self.l_button.grid(rowspan=2, padx=5, pady=5, sticky=self.ed_sticky_full, ipadx=5)

		tk.Label(self, text='RGB:').grid(row=0, column=1); 
		self.l_rgb = tk.Label(self, textvariable=self.l_rgb_color, font=('consolas', 10))
		self.l_rgb.grid(row=0, column=2, sticky=self.ed_sticky_w, pady=2)

		tk.Label(self, text='HEX:').grid(row=1, column=1) 
		self.l_hex = tk.Label(self, textvariable=self.l_hex_color, font=('consolas', 11))
		self.l_hex.grid(row=1, column=2, sticky=self.ed_sticky_w, pady=2)
	

	@classmethod
	def l_changeSize(cls, level):
		"""
			Change the size of the light area

			level -> inc/dec amount

			return -> None

		"""
		cls.l_current_size += level
		cls.l_current_size = max(32, min(128, cls.l_current_size))

	
	@classmethod
	def __l_colorFormatter(cls, v, _type='RGB'):
		"""
			Format the askcolor() output value

			v -> askcolor() return value (Tuple, str)
			_type -> RGB, 'HEX'

			return -> None

		"""
		if _type == 'RGB':
			# Keep the spacing between the tuple values same
			return '({})'.format(','.join(['{:>3}'.format(s) for s in v]))

		elif _type == 'HEX':
			# Convert the triplet to Hex
			return '#' + ''.join([format(s, '#04X')[2:] for s in v])


	@classmethod
	def l_pickColor(cls, b_config, value_only=False):
		"""
			Pick a color from the ColorChoose widget
			and store the rgb & hex inside the class

			value_only -> return the askcolor() output without internally setting it

			return -> None

		"""
		color = askcolor()
		if color[0] is None: return None 

		if value_only: return color

		# Edit the StringVars and store the raw color output
		cls.l_rgb_color.set(cls.__l_colorFormatter(color[0], 'RGB'))
		cls.l_hex_color.set(color[1].upper())

		# Update the button background colors
		b_config.config(background=color[1], activebackground=color[1])

		# Switch between black & white to make sure the foreground text can be seen
		b_config.config(foreground='white' if sum(color[0]) / 3 < cls.__l_threshold else 'black')	

		cls.l_current_color = color


	@classmethod
	def l_createColorFrame(cls, base, row, column):
		"""
			Create the light selection frame and the childrens for it

			base -> Parent
			row, column -> Grid location (x, y)

			return -> None

		"""
		# Initial value for the lights (White)
		def_value = 0xff, 0xff, 0xff
		def_rgb = cls.__l_colorFormatter(def_value, 'RGB') 
		def_hex = cls.__l_colorFormatter(def_value, 'HEX') 

		cls.l_rgb_color = cls.ed_str(); cls.l_rgb_color.set(def_rgb) 
		cls.l_hex_color = cls.ed_str(); cls.l_hex_color.set(def_hex)

		cls.l_current_color = def_value, def_hex 

		return cls(base, row, column)


