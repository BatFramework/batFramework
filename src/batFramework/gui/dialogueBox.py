from .label import Label 
import batFramework as bf
from typing import Self
class DialogueBox(Label):
    def __init__(self)->None:
        self.cursor_position :float = 0.0
        self.text_speed :float = 20.0
        self.message_queue : list[str]= [] 
        self.is_over : bool = True
        super().__init__("")

        self.set_autoresize(False)
        self.set_alignment(bf.Alignment.LEFT)

    def set_text_speed(self,speed:float)->Self:
        self.text_speed = speed
        return self

    def cut_text_to_width(self,text:str)->list[str]:
        if text == '' or self.get_content_width() < 1 or not self._font_object : return ['']
        
        for index in range(len(text)):
            
            width = self._font_object.size(text[:index])[0]
            if width > self.get_content_width():
                cut_point_start = index-1
                cut_point_end = index-1
                last_space = text.rfind(' ',0,cut_point_start)
                if last_space != -1 : # space was found !:
                    cut_point_start = last_space
                    cut_point_end = last_space+1
                    
                res = [text[:cut_point_start].strip()]
                res.extend(self.cut_text_to_width(text[cut_point_end:].strip()))  
                return res 
        return [text]  
        
    def say(self,message:str):
        message = '\n'.join(self.cut_text_to_width(message))
        self.message_queue.append(message)

        self.is_over = False

    def is_queue_empty(self)->bool:
        return not self.message_queue

    def is_current_message_over(self)->bool:
        return self.is_over

    def clear_queue(self)->None:
        self.message_queue.clear()
        self.next_message()

    def next_message(self)->None:
        if self.message_queue:
            self.message_queue.pop(0)
        self.cursor_position = 0
        self.set_text("")

    def do_update(self,dt):
        if not self.message_queue : return
        if not self.is_over and self.cursor_position == len(self.message_queue[0]):
            self.is_over = True 
        else:
            self.cursor_position = min(
                self.cursor_position +  self.text_speed * dt,
                len(self.message_queue[0])
            )
            self.set_text(self.message_queue[0][:int(self.cursor_position)])
            
