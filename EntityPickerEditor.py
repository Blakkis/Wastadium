import Tkinter as tk
from ConfigsModuleEditor import GlobalGameDataEditor 

from PickUps import Pickups

__all__ = 'EntityPicker',


class EntityOptionMenu(tk.OptionMenu, GlobalGameDataEditor):
	def __init__(self, base, variable, labeltext, row, column):
		# Holds the full string id from the menu
		self.variable_id = variable

		# Hold the display version of the menu (Keep the width in control)
		self.variable_id_display = self.ed_str(); self.variable_id_display.set('-')

		super(EntityOptionMenu, self).__init__(base, self.variable_id_display, 'test1ttttttt', 'test2', 'test3', command=self.__opt_limit_width)
		self.config(font=('consolas', 10))    # Monotype font

		self.ep_label = tk.Label(base, text=labeltext)
		self.ep_label.grid(row=row, column=column, padx=5, sticky=self.ed_sticky_w)

		self.grid(row=row, column=column + 1, sticky=self.ed_sticky_vert, columnspan=3, pady=5, padx=5)

		self.set_state()

	
	def __opt_limit_width(self, value):
		"""
			Parse the value before displaying it
			to keep the width from going all over GUI

			value -> Optionmenu value about to be selected

			return -> None

		"""
		self.variable_id.set(value)
		
		# 10 is currently good max value
		if len(value) > 10: value = "{}..".format(value[:8])
		self.variable_id_display.set(value)


	def set_state(self, state='disabled'):
		"""
			TBD

			return -> None

		"""
		pass


class EntityPicker(tk.Frame, GlobalGameDataEditor):

	ep_values = {'id': None,
				 'content': None}

	def __init__(self, base, row, column):
		super(EntityPicker, self).__init__(base)
		self.grid_columnconfigure(1, weight=1)	# Let the Optionmenu fill the second column entirely

		self.grid(row=row, column=column, columnspan=3, sticky=self.ed_sticky_full)

		self.ep_labelinfo = tk.Label(self, text='Entity Settings')
		self.ep_labelinfo.grid(row=0, column=0, padx=5, sticky=self.ed_sticky_w)
		
		self.ep_entity_id = EntityOptionMenu(self, self.ep_values['id'], "Entity id:", 1, 0)
		self.ep_entity_content = EntityOptionMenu(self, self.ep_values['content'], "Content id:", 2, 0)

		self.ep_set_state()


	def ep_set_state(self, state='disabled'):
		"""
			TBD

			return -> None

		"""
		[child.config(state=state) for child in self.winfo_children()]


	@classmethod
	def ep_createEntityFrame(cls, base, row, column):
		"""
			Create entity picker frame

			base -> Tkinter root frame
			row, column -> grid row, column

			return -> Instance

		"""
		cls.ep_values['id'] = cls.ed_str()
		cls.ep_values['content'] = cls.ed_str()

		return cls(base, row, column)