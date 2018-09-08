import Tkinter as tk
from ConfigsModuleEditor import GlobalGameDataEditor, ed_LabelEntry

from PickUps import Pickups
from EnemiesModule import Enemies
from Tokenizers import Id_Entity_Values


__all__ = ('EntityPicker',)


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

        super(EntityOptionMenu, self).__init__(base, self.variable_id_display, '', 
                                               command=self.__opt_limit_width)
        self.config(font=('consolas', 10))    # Monotype font

        self.ep_label = tk.Label(base, text=labeltext)
        self.ep_label.grid(row=row, column=column, padx=5, sticky=self.ed_sticky_w)

        self.grid(row=row, column=column + 1, sticky=self.ed_sticky_vert, columnspan=3, padx=5)


    def emp_configure_options(self, list_of_options, default=False):
        """
            TBD

            return -> None

        """
        self['menu'].delete(0, 'end')

        for s in list_of_options:
            self['menu'].add_command(label=s, command=lambda v=s: self.__opt_limit_width(v))

        self.config(state='normal')

        if default:
            self.__opt_limit_width(list_of_options[0])


    def epm_set(self, value='', reset=False): 
        """
            Set the default value on the optionmenu widget

            value -> Set the default value for this widget 

            return -> None

        """
        if reset:
            self.variable_id_display.set('-')
            self.config(state='disabled')
            self.variable_id.set('')
        
        else:
            self.variable_id_display.set(value) 



    def __opt_limit_width(self, value):
        """
            Parse the value before displaying it
            to keep the width from going all over GUI

            value -> Optionmenu value about to be selected

            return -> None

        """
        if not isinstance(value, str): value = str(value)
        self.variable_id.set(value)
        
        # 10 is currently good max value
        if len(value) > 10: value = "{}..".format(value[:8])
        self.variable_id_display.set(value)



class EntityPicker(tk.Frame, GlobalGameDataEditor):

    entity_data = {'c_id': None,        # string id of the entity
                   'c_content': None,   # Content of the entity 
                   'c_value': None,     # Content value
                   'state': -1}         # State of the picker widget

    # Button id with associated function (Modify the content of the menutabs)
    # The int id are buttons indexes from the menubar
    entity_valid_id = {7: None,     # Enemies
                       8: None}     # Pickups


    def __init__(self, base, row, column):
        super(EntityPicker, self).__init__(base)
        self.grid_columnconfigure(1, weight=1)  # Let the Optionmenu fill the second column entirely

        self.grid(row=row, column=column, columnspan=3, sticky=self.ed_sticky_full)

        self.ep_labelinfo = tk.Label(self, text='Entity Settings')
        self.ep_labelinfo.grid(row=0, column=0, padx=5, sticky=self.ed_sticky_w)
        
        tokens = EntityOptionMenuContent.entity_content_load()
        _tokenizer = self.ed_namedtuple('Token', 'content id func')

        self.entity_valid_id[7] = _tokenizer(tokens['id_enemy'],   'ID_ENEMY', self.__ep_entity_enemy)
        self.entity_valid_id[8] = _tokenizer(tokens['id_pickups'], 'ID_PICKUP', self.__ep_entity_pickup)

        self.ep_entity_id = EntityOptionMenu(self, self.entity_data['c_id'], "Entity Id:", 1, 0)
        self.ep_entity_content = EntityOptionMenu(self, self.entity_data['c_content'], "Content Id:", 2, 0)
        self.ep_entity_value = EntityOptionMenu(self, self.entity_data['c_value'], "Content Value:", 3, 0)

        self.ep_set_state()     # Default to hidden
        
        self.entity_data['state'].trace('w', self.__state_traceback)
        self.entity_data['c_id'].trace('w', lambda *args: self.entity_valid_id[self.entity_data['state'].\
                                                          get()].func(key=self.entity_data['state'].get()))

    
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
            self.ep_entity_id.epm_set(self.entity_valid_id[value].id)
            self.ep_entity_content.epm_set(reset=1) 
            self.ep_entity_value.epm_set(reset=1)

            self.entity_valid_id[value].func(populate=True, key=value)
        

    def __ep_entity_enemy(self, populate=False, key=-1):
        """
            populate -> Pre-populate the entity id to remove the 'ID_ENEMY'
            key -> 

            return -> None

        """
        if populate:
            self.ep_entity_id.emp_configure_options(sorted(self.entity_valid_id[key].content))
        
        else:
            # This is just to pass the apply check
            c_val = 1,
            self.ep_entity_value.emp_configure_options(c_val, default=1) 


    def __ep_entity_pickup(self, populate=False, key=-1):
        """
            Edit the optionmenu widget contents 

            populate -> Pre-populate the entity id to remove the 'ID_PICKUP'
            key -> 

            return -> None

        """
        if populate:
            self.ep_entity_id.emp_configure_options(sorted(self.entity_valid_id[key].content.keys()))
        
        else:
            enable_id_state = 0

            _id = self.entity_data['c_id'].get()

            if self.entity_valid_id[key].content[_id]['p_pickup_type'] == 't_ammo':
                c_ids = sorted(self.entity_valid_id[key].content[_id]['p_pickup_ammo'].keys())
                enable_id_state = 1

            elif self.entity_valid_id[key].content[_id]['p_pickup_type'] == 't_weapon':
                c_ids = sorted(self.entity_valid_id[key].content[_id]['p_pickup_weapons'])
                enable_id_state = 1 

            # Content is option for some pickups
            if enable_id_state:
                self.ep_entity_content.emp_configure_options(c_ids, default=1)
            else:
                self.ep_entity_content.epm_set(reset=True)
        
            # Value is mandatory
            c_val = sorted(self.entity_valid_id[key].content[_id]['p_pickup_content'])
            self.ep_entity_value.emp_configure_options(c_val, default=1)    

    
    @classmethod
    def ep_getPacket(cls):
        """
            Get the states of the widgets variables in a tuple

            return -> Tuple of data or None (If the entries are empty)

        """
        _id = cls.entity_data['c_id'].get()
        content = cls.entity_data['c_content'].get()
        value = cls.entity_data['c_value'].get() 
        
        if _id and (content or value):
            return Id_Entity_Values(_id, content, value)
        else:
            return None

        return cls.entity_data[key].get()


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
        cls.entity_data['c_id'] = cls.ed_str()
        cls.entity_data['c_content'] = cls.ed_str()
        cls.entity_data['c_value'] = cls.ed_str() 

        cls.entity_data['state'] = cls.ed_int(); cls.entity_data['state'].set(-1) 

        return cls(base, row, column)
