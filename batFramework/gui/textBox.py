import batFramework as bf
import pygame
from math import sin
from .container import Container



class TextBox(Container):
    def __init__(self,uid=None):
        super().__init__(uid)
        # self.set_alignment(bf.Alignment.LEFT)
        # self.set_direction(bf.Direction.HORIZONTAL)
        # self.set_layout(bf.Layout.FIT)
        self.messages = []
        self.message_length = None
        self.progression = 0
        self.click_rate,self.click_counter = 2,0
        self.label = bf.Label("").set_alignment(bf.Alignment.LEFT).put_to(self)
        self.text_speed = 20
        self.end_callback = None
    def set_speed(self,speed = 0):
        self.text_speed = max(0,min(speed,100))

    def get_bounding_box(self):
        yield from super().get_bounding_box()
        yield from self.label.get_bounding_box()

    def resize(self, new_width, new_height):
        self.label.set_wraplength(new_width-self._padding[0]*2)
        return super().resize(new_width, new_height)

    def queue_message(self,message:str,end_callback=None):
        self.end_callback = end_callback
        #check message length + cut if necessary
        cut = None
        self.label.set_text(message)
        if self.label.rect.h> self.rect.h - self._padding[1]*2:
            font = bf.utils.FONTS[self.label._text_size] 
            new_lines =  [0]
            line_size = font.get_linesize()
            max_new_lines = (self.rect.h - self._padding[1]*2) // (line_size)
            while len(new_lines) < max_new_lines:
                force_break = False
                next_space = new_lines[-1]
                while font.size(message[new_lines[-1]:next_space].strip())[0] < self.label.rect.w - self.label._padding[0]*2:
                    tmp = message.find(' ',next_space+1)
                    tmp2 = message.find('\n',next_space+1)
                    if tmp2 <0 and tmp< 0 :
                        force_break = True
                        break 
                    if tmp < 0 : tmp = 1_000_000
                    if tmp2 < 0 : tmp2 = 1_000_000
                    next_space = min(tmp,tmp2)
                new_lines.append(next_space)
                if force_break : break
            message,cut = message[:new_lines[-2]].strip(),message[new_lines[-2]:].strip()
            # print("message : ",message,"cut :",cut)
        self.messages.append(message)


        #IF this is the first message
        if len(self.messages)==1:
            self.progression = 0
            self.message_length = len(self.messages[0])
            # self.set_visible(True)
        if cut : self.queue_message(cut,end_callback)


    def next_message(self):
        if self.progression != self.message_length: return
        self.messages.pop(0)
        self.progression = 0
        self.click_counter =0
        self.message_length = len(self.messages[0]) if self.messages else None

        if self.message_length is None:
            print("next message : callback !",self.end_callback)
            if self.end_callback : self.end_callback()
            return




    def update(self, dt: float):
        if  not self.messages : return
        new_progression = min(self.progression + (dt*self.text_speed),self.message_length)


        if int(new_progression) != int(self.progression):
            if self.click_counter % self.click_rate == 0:
                bf.AudioManager().play_sound("text_click",0.5)
            self.click_counter += 1
        self.progression = new_progression
        
        self.label.set_text(self.messages[0][:int(self.progression)])


    def draw(self, camera):
        i = super().draw(camera)
        if self.progression == self.message_length:
            p2 = self.rect.move(-4 - (2*sin(pygame.time.get_ticks()*.01)),-10).bottomright
            p1 = (p2[0]-4,p2[1]-4)
            p0 = (p2[0]-4,p2[1]+4)
            if len(self.messages) == 1:
                pygame.draw.polygon(camera.surface,bf.color.SHADE_GB,bf.move_points((3,0),p0,p1,p2))
            pygame.draw.polygon(camera.surface,bf.color.LIGHT_GB,[p0,p1,p2])
        return i