import batFramework as bf
import pygame




class AudioManager(metaclass=bf.Singleton):
    def __init__(self) -> None:
        self.sounds: dict = {}
        self.musics: dict = {}
        self.current_music: str | None = None
        self.music_volume: float = 1
        self.sound_volume: float = 1
        pygame.mixer.music.set_endevent(bf.const.MUSIC_END_EVENT)

    def free_sounds(self, force: bool = False):
        if force:
            self.sounds = {}
            return
        self.sounds: dict = {
            key: value for key, value in self.sounds.items() if value["persistent"]
        }

    def free_music(self):
        if self.current_music:
            pygame.mixer.music.unload(self.current_music)

    def set_sound_volume(self, volume: float):
        self.sound_volume = volume

    def set_music_volume(self, volume: float):
        self.music_volume = volume
        pygame.mixer.music.set_volume(volume)

    def get_music_volume(self) -> float:
        return self.music_volume

    def get_sound_volume(self) -> float:
        return self.sound_volume

    def has_sound(self, name: str):
        return name in self.sounds

    def load_sound(self, name, path, persistent=False) -> pygame.mixer.Sound:
        """
        if persistent==True the sound won't be unloaded when sounds are freed (unless force is used)
        """
        if name in self.sounds:
            return self.sounds[name]["sound"]
        path = bf.ResourceManager().get_path(path)
        self.sounds[name] = {
            "path": path,
            "sound": pygame.mixer.Sound(path),
            "persistent": persistent,
        }
        return self.sounds[name]["sound"]

    def load_sounds(self, sound_data: tuple[str, str, bool]) -> None:
        for data in sound_data:
            self.load_sound(*data)
        return

    def play_sound(self, name, volume=1) -> bool:
        """
        Play the sound file with the given name.
        returns True if the sound was played

        """
        try:
            self.sounds[name]["sound"].set_volume(volume * self.sound_volume)
            self.sounds[name]["sound"].play()
            return True
        except KeyError:
            print(f"Sound '{name}' not loaded in AudioManager.")
            return False

    def stop_sound(self, name) -> bool:
        try:
            self.sounds[name]["sound"].stop()
            return True
        except KeyError:
            return False
            print(f"Sound '{name}' not loaded in AudioManager.")

    def load_music(self, name, path):
        self.musics[name] = bf.ResourceManager().get_path(path)
        return

    def load_musics(self, *music_data:tuple[str, str]):
        for data in music_data:
            self.load_music(*data)
        return

    def play_music(self, name, loop=0, fade=500) -> bool:
        """
        Play the sound file with the given 'name'.
        Fades with the given 'fade' time in ms.
        Music will loop 'loop' times (indefinitely if -1).
        returns True if the sound was played
        """
        try:
            pygame.mixer.music.load(self.musics[name])
            pygame.mixer.music.play(loop, fade_ms=fade)
            self.current_music = name
            return True
        except KeyError:
            print(f"Music '{name}' not loaded in AudioManager.")
            return False

    def stop_music(self):
        if not self.current_music:
            return
        pygame.mixer.music.stop()

    def fadeout_music(self, fade_ms: int):
        if not self.current_music:
            return
        pygame.mixer.music.fadeout(fade_ms)

    def pause_music(self):
        if not self.current_music:
            return
        pygame.mixer.music.pause()

    def resume_music(self):
        if not self.current_music:
            return
        pygame.mixer.music.unpause()

    def get_current_music(self) -> str | None:
        return self.current_music
