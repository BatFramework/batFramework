import batFramework as bf
import pygame
from .frame import Frame

class Label(Frame):
    def __init__(self,text:str,width:float|None=None,height:float|None=None) -> None:   
        self._autoresize = True
        self._text = ""
        self._antialias : bool = True
        self._padding : tuple[int,int] = (10,10)
        self._text_size = bf.const.DEFAULT_TEXT_SIZE
        self._text_color : tuple[int,int,int]|str = "black"
        self._font_name = None
        self._font_object = None
        self._text_rect = None
        self._text_surface : pygame.Surface | None= None 
        
        super().__init__(100,100)
        self.set_font(force=True)
        self.set_text(text)

    def get_bounding_box(self):
        yield from super().get_bounding_box()
        if self._text_rect : yield self._text_rect.move(*self.rect.topleft)

    def set_font(self,font_name:str=None,force:bool = False)-> "Label":
        if font_name == self._font_name and not force: return self
        self._font_name = font_name
        self._font_object = bf.utils.get_font(self._font_name,self._text_size)
        self.build()
        return self

    def set_text_size(self,text_size:int) -> "Label":
        text_size = round(text_size/2) * 2
        if text_size == self._text_size : return self
        self._text_size = text_size
        self._font_object = bf.utils.get_font(self._font_name,self._text_size)
        self.build()

        return self

    def get_text_size(self)-> int:
        return self._text_size

    def set_padding(self,value:tuple[int,int])-> "Label":
        if self._padding != value : return self
        self._padding = value
        self.build()
        return self

    def set_text(self,text:str) -> "Label":
        if text == self._text : return self
        self._text = text
        self.build()
        return self
    
    def _build_text(self)-> None:
        if self._font_object is None: return
        # render(text, antialias, color, bgcolor=None, wraplength=0) -> Surface
        self._text_surface = self._font_object.render(
            self._text,
            self._antialias,
            self._text_color,
            self._color
        )
        self._text_rect = self._text_surface.get_frect(
            center = self.rect.move(-self.rect.left,-self.rect.top).center
        )
        self.surface.blit(self._text_surface,self._text_rect)
        
        # return
        if self._autoresize:
            if self.rect.size != self._text_rect.inflate(*self._padding).size :
                self.rect.size = self._text_rect.inflate(*self._padding).size
                self.build()

            # modify rect so it is the same size as text_rect, but still same center as before.
    def build(self)->None:
        super().build()
        self._build_text()
