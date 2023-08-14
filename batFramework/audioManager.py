import batFramework as bf
import pygame

pygame.mixer.init()


class AudioManager(metaclass=bf.Singleton):
    def __init__(self):
        self.sounds: dict[str : dict[str, pygame.mixer.Sound, bool]] = {}
        self.musics: dict[str:str] = {}
        self.current_music = None
        self.music_volume = 1
        self.sound_volume = 1
        pygame.mixer_music.set_endevent(bf.const.MUSIC_END_EVENT)

    def free_sounds(self, force=False):
        if force:
            self.sounds = {}
            return
        to_remove = []
        for name, data in self.sounds.items():
            if not data["persistent"]:
                to_remove.append(name)

        _ = [self.sounds.pop(i) for i in to_remove]

    def set_sound_volume(self, volume: float):
        self.sound_volume = volume

    def set_music_volume(self, volume: float):
        self.music_volume = volume
        pygame.mixer_music.set_volume(volume)

    def has_sound(self, name):
        return name in self.sounds

    def load_sound(self, name, path, persistent=False) -> pygame.mixer.Sound:
        if name in self.sounds:
            return self.sounds[name]["sound"]
        path = bf.utils.get_path(path)
        self.sounds[name] = {
            "path": path,
            "sound": pygame.mixer.Sound(path),
            "persistent": persistent,
        }
        return self.sounds[name]["sound"]

    def play_sound(self, name, volume=1):
        self.sounds[name]["sound"].set_volume(volume * self.sound_volume)
        self.sounds[name]["sound"].play()

    def stop_sound(self, name):
        if name in self.sounds:
            self.sounds[name]["sound"].stop()

    def load_music(self, name, path):
        self.musics[name] = bf.utils.get_path(path)

    def play_music(self, name, loop=0, fade=500):
        if name in self.musics:
            pygame.mixer_music.load(self.musics[name])
            pygame.mixer_music.play(loop, fade_ms=fade)
            self.current_music = name
        else:
            print(f"Music '{name}' not found in AudioManager.")

    def stop_music(self):
        if not self.current_music:
            return
        pygame.mixer_music.stop()

    def fadeout_music(self, fade_ms: int):
        if not self.current_music:
            return
        pygame.mixer_music.fadeout(fade_ms)

    def pause_music(self):
        if not self.current_music:
            return
        pygame.mixer_music.pause()

    def resume_music(self):
        if not self.current_music:
            return
        pygame.mixer_music.unpause()
