import pygame
import batFramework as bf

class AudioManager(metaclass=bf.Singleton):
    def __init__(self) -> None:
        self._sounds: dict[str, dict] = {}
        self._musics: dict[str, str] = {}
        self._current_music: str | None = None
        self._music_volume: float = 1.0
        self._sound_volume: float = 1.0

        self._channels: dict[str, pygame.mixer.Channel] = {}
        self._channel_volumes: dict[str, float] = {}
        self._use_custom_channels: bool = False

        pygame.mixer.music.set_endevent(bf.const.MUSIC_END_EVENT)

    # --- Channel management ---
    def setup_channels(self, channels: dict[str, int]) -> None:
        """
        Setup channels by providing a dict of {channel_name: channel_index}.
        Enables custom channel management.
        """
        pygame.mixer.set_num_channels(max(channels.values()) + 1)
        self._channels = {
            name: pygame.mixer.Channel(idx) for name, idx in channels.items()
        }
        self._channel_volumes = {name: 1.0 for name in channels.keys()}
        self._use_custom_channels = True

    def set_channel_volume(self, channel_name: str, volume: float) -> None:
        if channel_name in self._channels:
            clamped = max(0.0, min(volume, 1.0))
            self._channel_volumes[channel_name] = clamped
            self._channels[channel_name].set_volume(clamped)

    def get_channel_volume(self, channel_name: str) -> float:
        return self._channel_volumes.get(channel_name, 1.0)

    # --- Sound management ---
    def load_sound(self, name: str, path: str, persistent: bool = False) -> pygame.mixer.Sound:
        if name in self._sounds:
            return self._sounds[name]["sound"]
        path = bf.ResourceManager().get_path(path)
        sound = pygame.mixer.Sound(path)
        self._sounds[name] = {
            "sound": sound,
            "path": path,
            "persistent": persistent,
        }
        return sound

    def load_sounds(self, sounds_data: list[tuple[str, str, bool]]) -> None:
        for name, path, persistent in sounds_data:
            self.load_sound(name, path, persistent)

    def play_sound(self, name: str, volume: float = 1.0, channel_name: str | None = None) -> bool:
        sound_data = self._sounds.get(name)
        if not sound_data:
            print(f"[AudioManager] Sound '{name}' not loaded.")
            return False
        sound = sound_data["sound"]
        volume = max(0.0, min(volume, 1.0)) * self._sound_volume

        if self._use_custom_channels and channel_name:
            channel = self._channels.get(channel_name)
            if not channel:
                print(f"[AudioManager] Channel '{channel_name}' not found. Using default channel.")
                sound.set_volume(volume)
                sound.play()
                return True
            channel.set_volume(volume * self._channel_volumes.get(channel_name, 1.0))
            channel.play(sound)
        else:
            # Default pygame behavior: auto assign a free channel
            sound.set_volume(volume)
            sound.play()
        return True

    def stop_sound(self, name: str) -> bool:
        sound_data = self._sounds.get(name)
        if not sound_data:
            print(f"[AudioManager] Sound '{name}' not loaded.")
            return False
        sound_data["sound"].stop()
        return True

    def free_sounds(self, force: bool = False) -> None:
        if force:
            self._sounds.clear()
        else:
            self._sounds = {
                name: data for name, data in self._sounds.items() if data["persistent"]
            }

    def set_sound_volume(self, volume: float) -> None:
        self._sound_volume = max(0.0, min(volume, 1.0))

    def get_sound_volume(self) -> float:
        return self._sound_volume

    # --- Music management ---
    def load_music(self, name: str, path: str) -> None:
        self._musics[name] = bf.ResourceManager().get_path(path)

    def load_musics(self, musics_data: list[tuple[str, str]]) -> None:
        for name, path in musics_data:
            self.load_music(name, path)

    def play_music(self, name: str, loops: int = 0, fade_ms: int = 500) -> bool:
        path = self._musics.get(name)
        if not path:
            print(f"[AudioManager] Music '{name}' not loaded.")
            return False
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(self._music_volume)
            pygame.mixer.music.play(loops=loops, fade_ms=fade_ms)
            self._current_music = name
            return True
        except pygame.error as e:
            print(f"[AudioManager] Failed to play music '{name}': {e}")
            return False

    def stop_music(self) -> None:
        if self._current_music:
            pygame.mixer.music.stop()
            self._current_music = None

    def fadeout_music(self, fade_ms: int) -> None:
        if self._current_music:
            pygame.mixer.music.fadeout(fade_ms)
            self._current_music = None

    def pause_music(self) -> None:
        if self._current_music:
            pygame.mixer.music.pause()

    def resume_music(self) -> None:
        if self._current_music:
            pygame.mixer.music.unpause()

    def free_music(self) -> None:
        if self._current_music:
            pygame.mixer.music.unload()
            self._current_music = None

    def set_music_volume(self, volume: float) -> None:
        self._music_volume = max(0.0, min(volume, 1.0))
        pygame.mixer.music.set_volume(self._music_volume)

    def get_music_volume(self) -> float:
        return self._music_volume

    def get_current_music(self) -> str | None:
        return self._current_music
