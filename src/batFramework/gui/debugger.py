from .label import Label
from typing import Self

class Debugger(Label):
	def __init__(self)->None:
		super().__init__("")
		self.static_data : dict 	= {}
		self.dynamic_data : dict 	= {}
		self.refresh_rate = 10
		self.refresh_counter = 0
		self.render_order = 99

	def to_string_id(self)->str:
		return "Debugger"
		
	def set_refresh_rate(self, value:int)-> Self:
		self.refresh_rate = value
		return self
		
	def add_data(self,key:str,data):
		self.static_data[key] = str(data)
		self.update_text()
		
	def add_dynamic_data(self,key:str,func)->None:
		self.dynamic_data[key] = func
		self.update_text()

	def set_parent_scene(self,scene)->None:
	    super().set_parent_scene(scene)
	    self.update_text()
        
	def update_text(self)->None:
		if not self.parent_scene:return	
		d = '\n'.join(key+':'+data if key!='' else data for key,data in self.static_data.items())
		d2 = '\n'.join(key+':'+str(data()) if key!='' else str(data()) for key,data in self.dynamic_data.items())
		self.set_text('\n'.join((d,d2)).strip())

	def update(self,dt:float)->None:
		if not self.parent_scene:return
		if self.parent_scene.get_sharedVar("is_debugging_func")() != 1:
			self.set_visible(False)
			return
		self.set_visible(True)
		self.refresh_counter = self.refresh_counter + (dt * 60) 
		if self.refresh_counter > self.refresh_rate:
			self.refresh_counter = 0
			self.update_text()
