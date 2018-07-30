import Tkinter as tk
from ConfigsModuleEditor import GlobalGameDataEditor 


class EditorStatistics(tk.Frame, GlobalGameDataEditor):
	"""
		Provide realtime stats about the editor/world
	"""
	# Holds the Tkinter variables by id
	__es_stats = {}
					

	def __init__(self, base, row, column):
		super(EditorStatistics, self).__init__(base)

		self.grid(row=row, column=column, columnspan=3, sticky=self.ed_sticky_full)

		tk.Label(self, text='Editor & World Info').grid(row=0, column=0, padx=5, 
                                                        sticky=self.ed_sticky_w)

		for enum in xrange(0, len(self.__es_stats)):
			k, v = self.__es_stats[enum] 
			tk.Label(self, text=k).grid(row=enum + 1, column=0, ipadx=5, sticky=self.ed_sticky_w)
			tk.Label(self, textvariable=v).grid(row=enum + 1, column=1, sticky=self.ed_sticky_w)	

	
	@classmethod
	def es_initVariables(cls, reset=False):
		"""


			values -> List of tuples containing (Label Name, Tkinter 'int' variable)
			reset -> Reset all the Tkinter variables to 0

			return -> None

		"""
		if reset: 
			for r in cls.__es_stats.itervalues():
				rv = 0 
				if isinstance(r[1]._default, str): rv = ''
				
				r[1].set(rv) 
		else:
			# Stats on the statistics frame
			cls.__es_stats[0] = ('Framerate:',       cls.ed_int())
			cls.__es_stats[1] = ('Camera Position:', cls.ed_str()); cls.__es_stats[1][1].set('-') 
			cls.__es_stats[2] = ('Object Count:',    cls.ed_int())
			cls.__es_stats[3] = ('Decal Count:',     cls.ed_int())
			cls.__es_stats[4] = ('Wall Segments:',   cls.ed_int())
			cls.__es_stats[5] = ('Light Count:',     cls.ed_int())
			cls.__es_stats[6] = ('Enemy Count',      cls.ed_int())
			cls.__es_stats[7] = ('Pickup Count',     cls.ed_int())


	@classmethod
	def es_update_decorator(cls, _id, op=1):
		"""
			Decorator based updater

			Note: Functions using this decorator should return 1, -1 or None (Depends of the operation)
		"""
		def wrap(func):
			
			def wrapped(*args, **kw):
				v = func(*args, **kw)
				
				if v is None: return
				
				cls.es_update(_id, v, op=op)
			
			return wrapped
		
		return wrap

	
	@classmethod
	def es_update(cls, _id, value, op=0):
		"""
			Apply new values for the statistics

			_id -> Id of the variable
			value -> Value for the variable
			op -> Operation to perform
				  0: Assign
				  1: Add

			return -> None

		"""
		if op == 0: cls.__es_stats[_id][1].set(value)
		elif op == 1: cls.__es_stats[_id][1].set(cls.__es_stats[_id][1].get() + value) 

	
	@classmethod
	def es_createStatFrame(cls, base, row, column):
		"""
			Create statistics info frame

			base -> Tkinter root frame
			row, column -> grid row, column

			return -> Instance

		"""
		return cls(base, row, column)


	