import batFramework as bf
from .widget import Widget
import pygame
class Image(Widget):
	def __init__(self,data:pygame.Surface|str,size:None|tuple[int,int]=None,convert_alpha=True):
		super().__init__(False)
		self.surface = None
		if isinstance(data,str):
			path = bf.utils.get_path(data)
			self.original_surface=pygame.image.load(path)
		elif isinstance(data,pygame.Surface):
			self.original_surface = data
			
		if convert_alpha:	self.original_surface = self.original_surface.convert_alpha()
		if not size : size = self.original_surface.get_size()
		self.set_size(*size)


	def build(self)->None:
		if not self.surface or self.surface.get_size() != self.get_size_int():
			self.surface = pygame.transform.scale(self.original_surface,self.get_size_int())
			
            
