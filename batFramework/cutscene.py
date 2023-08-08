import batFramework as bf

class CutsceneBlock:...

class Cutscene:...

class CutsceneManager(metaclass=bf.Singleton):
    def __init__(self,manager) -> None:
        self.current_cutscene : Cutscene = None
        self.manager : bf.Manager = manager

    def get_flag(self,flag):
        return None

    def process_event(self,event):
        if self.current_cutscene:
            self.current_cutscene.process_event(event)
    def play(self,cutscene: Cutscene):
        if self.current_cutscene is None:
            self.current_cutscene = cutscene
            self.current_cutscene.play()
        self.manager.set_sharedVar("in_cutscene",True)

    def update(self,dt):
        if not self.current_cutscene is None :
            self.current_cutscene.update(dt)
            # print("cutscene manager update")
            if self.current_cutscene.has_ended():
                self.manager.set_sharedVar("in_cutscene",False)
                self.current_cutscene = None

class Cutscene:
    def __init__(self) -> None:
        self.cutscene_blocks : list[CutsceneBlock] = []
        self.block_index = 0
        self.ended = False
    def add_block(self,*blocks:list[CutsceneBlock]):
        for block in blocks:
            self.cutscene_blocks.append(block)

    def process_event(self,event):
        if not self.ended and self.block_index < len(self.cutscene_blocks):
            self.cutscene_blocks[self.block_index].process_event(event)
    def play(self):
        self.block_index = 0
        if self.cutscene_blocks:
            self.cutscene_blocks[self.block_index].start()
        else:
            self.ended

    def update(self,dt):
        if self.ended : return
        # print("cutscene update",self.cutscene_blocks[self.block_index])
        self.cutscene_blocks[self.block_index].update(dt)
        if self.cutscene_blocks[self.block_index].has_ended():
            self.block_index +=1
            if self.block_index == len(self.cutscene_blocks):
                self.ended = True
                return
            self.cutscene_blocks[self.block_index].start()

            # print("NEXT BLOCK")
    def has_ended(self):
        return self.ended

class CutsceneBlock: 
    def __init__(self) -> None:
        self.callback = None
        self.parent_cutscene : Cutscene = None
        self.get_flag = CutsceneManager().get_flag
        self.ended = False
        self.started = False

    def set_parent_cutscene(self,parent):
        self.parent_cutscene = parent

    def process_event(self,event):
        pass

    def update(self,dt):
        pass

    def start(self):
        self.started = True
        # print("Block start",self)

    def end(self):
        self.ended = True

    def has_ended(self):
        return self.ended
    

class ParallelBlock(CutsceneBlock):
    def __init__(self,*blocks) -> None:
        super().__init__()
        self.blocks :list[CutsceneBlock]=blocks
        
    def start(self):
        super().start()
        for block in self.blocks:
            block.start()
    
    def process_event(self, event):
        _ = [b.process_event(event) for b in self.blocks]
        
    
    def update(self, dt):
        _ = [b.update(dt) for b in self.blocks]
    
    def has_ended(self):
        all(b.has_ended() for b in self.blocks)

class SceneTransitionBlock(CutsceneBlock):
    def __init__(self,scene,transition,duration,**kwargs) -> None:
        super().__init__()
        self.target_scene = scene
        self.transition = transition
        self.duration = duration
        self.kwargs = kwargs
        self.timer = bf.Time().timer(duration=duration,callback=self.end)

    def start(self):
        super().start()
        CutsceneManager().manager.transition_to_scene(self.target_scene,self.transition,self.duration,**self.kwargs)
        self.timer.start()        



class PlayMusicBlock(CutsceneBlock):
    def __init__(self,music,path=None,wait_end=False,loop=True,fade=0) -> None:
        super().__init__()
        if path : bf.AudioManager().load_music(music,path)
        self.music = music
        self.wait_end = wait_end
        self.fade = fade
        self.loop = loop if not wait_end else False

    def start(self):
        super().start()
        bf.AudioManager().play_music(self.music,self.loop,self.fade)
        if not self.wait_end:self.end()

    def process_event(self, event):
        if event.type == bf.const.MUSIC_END_EVENT:
            # bf.AudioManager().stop_music()
            self.end()

class StopMusicBlock(CutsceneBlock):
    def __init__(self,fade_ms=0) -> None:
        super().__init__()
        self.fade_ms = fade_ms

    def start(self):
        super().start()
        if self.fade_ms:
            bf.AudioManager().fadeout_music(self.fade_ms)
        else:
            bf.AudioManager().stop_music()
            self.end()

    def process_event(self, event):
        if event.type == bf.const.MUSIC_END_EVENT:
            self.end()


class PlaySound(CutsceneBlock):
    def __init__(self,sound,path=None,wait_end=False) -> None:
        super().__init__()
        self.sound_file = bf.AudioManager().load_sound(sound,path)
        self.wait_end = wait_end
        self.sound = sound

    def start(self):
        super().start()
        bf.AudioManager().play_sound(self.sound)
        if self.wait_end:
            bf.Time().timer(duration=self.sound_file.get_length()*1000,callback=self.end)
        else:
            self.end()

