import Tkinter as tk
from ConfigsModuleEditor import GlobalGameDataEditor 

from PickUps import Pickups
from EnemiesModule import Enemies

__all__ = 'EntityPicker',


class EntityOptionMenuContent(Pickups, Enemies):
	"""
		Provide more minimalistic version of the pickups, enemies, ...

		Also pickups and Enemies relay on different configs
	"""

	@classmethod
	def entity_content_load(cls):
		"""
			Load handler for the entity contents

			return -> TBD

		"""
		token = {'id_enemy':   cls.build_all_enemies(editor_only=True),
		         'id_pickups': cls.load_pickups(editor_only=True)}

		return token



class EntityOptionMenu(tk.OptionMenu, GlobalGameDataEditor):
	def __init__(self, base, variable, labeltext, row, column):
		# Holds the full string id from the menu
		self.variable_id = variable

		# Hold the display version of the menu (Keep the width in control)
		self.variable_id_display = self.ed_str(); self.variable_id_display.set('-')

		super(EntityOptionMenu, self).__init__(base, self.variable_id_display, 'test1ttttttt', 'test2', 'test3', 
											   command=self.__opt_limit_width)
		self.config(font=('consolas', 10))    # Monotype font

		self.ep_label = tk.Label(base, text=labeltext)
		self.ep_label.grid(row=row, column=column, padx=5, sticky=self.ed_sticky_w)

		self.grid(row=row, column=column + 1, sticky=self.ed_sticky_vert, columnspan=3, padx=5)


	def epm_set(self, value): 
		"""
			Set the default value on the optionmenu widget

			value -> Set default to this value

			return -> None

		"""
		self.variable_id_display.set(value)


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



class EntityPicker(tk.Frame, GlobalGameDataEditor):

	entity_data = {'id': None,		# string id of the entity
				   'content': None,	# Content of the entity (or value)
				   'state': -1}		# State of the picker widget

	# Button id with associated function (Modify the content of the menutabs)
	# The int id are buttons indexes from the menubar
	entity_valid_id = {7: None,		# Enemies
					   8: None}		# Pickups


	def __init__(self, base, row, column):
		super(EntityPicker, self).__init__(base)
		self.grid_columnconfigure(1, weight=1)	# Let the Optionmenu fill the second column entirely

		self.grid(row=row, column=column, columnspan=3, sticky=self.ed_sticky_full)

		self.ep_labelinfo = tk.Label(self, text='Entity Settings')
		self.ep_labelinfo.grid(row=0, column=0, padx=5, sticky=self.ed_sticky_w)
		
		tokens = EntityOptionMenuContent.entity_content_load()
		self.entity_valid_id[7] = tokens['id_enemy'],   'ID_ENEMY' 
		self.entity_valid_id[8] = tokens['id_pickups'], 'ID_PICKUP'

		self.ep_entity_id = EntityOptionMenu(self, self.entity_data['id'], "Entity id:", 1, 0)
		self.ep_entity_content = EntityOptionMenu(self, self.entity_data['content'], "Content id:", 2, 0)

		self.ep_set_state()		# Default to hidden
		
		self.entity_data['state'].trace('w', self.__state_traceback)
		self.entity_data['id'].trace('w', self.__ep_entity_configure)		# MUISTA TAMA!

	
	def __state_traceback(self, *args):
		"""
			Work as a bridge between instance and class via trace

			return -> None

		"""
		v = self.entity_data['state'].get()
		self.ep_set_state('normal' if v != -1 else 'disabled')

	
	
	def ep_set_state(self, state='disabled'):
		"""
			Control the state of the entity picker widget (Instance)
			
			state -> 'normal', 'disabled'

			return -> None

		"""
		for child in self.winfo_children():
			if isinstance(child, EntityOptionMenu): 
				child.epm_set('-')

			child.config(state=state)
		
		value = self.entity_data['state'].get() 
		if value != -1: 
			self.ep_entity_id.epm_set(self.entity_valid_id[value][1])
			self.ep_entity_content.config(state='disabled')	

	
	def __ep_entity_configure(self, *args):
		"""
			TBD

			return -> None

		"""
		print args
			

	@classmethod
	def ep_controlState(cls, button_id):
		"""
			Provide a class method to control the state of the widgets

			button_id -> Id of the buttons (For controlling when to enable the widgets)

			return -> None

		"""
		# Enable
		if button_id in cls.entity_valid_id:
			if button_id == cls.entity_data['state'].get(): return None
			cls.entity_data['state'].set(button_id)
		
		# Disable
		else: 
			if cls.entity_data['state'].get() == -1: return None
			cls.entity_data['state'].set(-1)



	@classmethod
	def ep_createEntityFrame(cls, base, row, column):
		"""
			Create entity picker frame

			base -> Tkinter root frame
			row, column -> grid row, column

			return -> Instance

		"""
		cls.entity_data['id'] = cls.ed_str()
		cls.entity_data['content'] = cls.ed_str()
		cls.entity_data['state'] = cls.ed_int(); cls.entity_data['state'].set(-1) 

		return cls(base, row, column)
