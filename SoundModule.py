from ConfigsModule import GlobalGameData
from MapParser import W_errorToken

# Note: Some of the methods could be converted to decorators.
#       Since they mostly do their job at the start/end of the target functions

class SoundMusic(GlobalGameData):
    
    # All available sound effects
    all_sounds = {}

    # Contains only path-names to music files as they are streamed for music playing
    all_music = {}

    # Default volumes for sound and music
    sm_volumes = {0: 1.0,   # Music
                  1: 1.0}   # Effects

    # Volume range for falloff of the sound
    sm_max_hearing_range = 350.0
    sm_falloff = 1.0 / sm_max_hearing_range 

    snd_data = {'tracklist': None}

    
    def __init__(self):
        pass

    
    @classmethod
    @W_errorToken("Error Initializing Sound/Music Module!")
    def readSoundMusic(cls):
        """
            Read and parse sound effects and music

            return -> None

        """
        # Source path for the sound assets
        src_path_cfg = cls.tk_path.join('configs', 'sound')

        # Sounds
        for line in cls.tk_readFile(cls.tk_path.join(src_path_cfg, 'sounds.cfg')):
            cls.all_sounds[int(line[0])] = cls.tk_mixer.Sound(cls.tk_path.join('soundmusic', line[1]))
            #cls.all_sounds[int(line[0])].set_volume(cls.sm_volumes[1])

        # Music (Only pathnames)
        for line in cls.tk_readFile(cls.tk_path.join(src_path_cfg, 'music.cfg')):
            cls.all_music[int(line[0])] = cls.tk_path.join('soundmusic', 'music', line[1])
        
        # Music playlist
        # Note: 0 is special and should be reserved for menu
        tracklist = [t for t in sorted(cls.all_music.keys()) if t > 0]
        cls.snd_data['tracklist'] = cls.tk_deque(tracklist)

    
    @classmethod
    def editVolume(cls, volume_id, volume, edit=True, play_sound_cue=False):
        """
            Edit volume

            volume_id -> 0: Music, 1: Effects
            volume -> Value between 0.0 -> 1.0
            edit -> Enable edit (bool)
            play_sound_cue -> Play a test sound to indicate volume level (Effects only)

            return -> None
        """
        if edit:
            if volume_id == 0 and volume != cls.sm_volumes[volume_id]:
                cls.sm_volumes[volume_id] = volume
                cls.tk_mixer_music.set_volume(volume)

            # Effects
            elif volume_id == 1 and volume != cls.sm_volumes[volume_id]:
                cls.sm_volumes[volume_id] = volume
                if play_sound_cue: cls.playSoundEffect(188)     


    @classmethod
    def playSoundEffect(cls, _id, distance=0, env_damp=0):
        """
            Play sound-effect by id

            _id -> int id of the needed soundeffect (See sounds.cfg for the sounds by id)
            distance -> Screen position to calculate volume falloff from the center 
            env_damp -> Optional environment dampening (Use with sound effects emitted from interacting with env)
            
            return -> Channel

        """
        if not isinstance(_id, int) and not sm_volumes[1]: 
            return None

        if distance:
            distance = cls.tk_hypot(cls.tk_res_half[0] - distance[0], 
                                    cls.tk_res_half[1] - distance[1]) 

        channel = cls.all_sounds[_id].play()
        # No available channel to play on.
        if channel is None: 
            return None
        
        # Dumpen the environment effects
        volume_env_damp = env_damp * cls.sm_volumes[1]
        volume_falloff = cls.sm_falloff * distance * cls.sm_volumes[1] 
        channel.set_volume(cls.tk_clamp(cls.sm_volumes[1] - (volume_falloff + volume_env_damp), 0, 1))
      	
        return channel

    
    @classmethod
    def playMusic(cls, _id=0, loops=0, tracklist_play=False):
        """
            Play music

            _id ->
            loops -> Num of times to loop the music (-1: infinite)
            tracklist_play -> Fetch a next in queue soundtrack and spin the wheel for next tracklist fetch

            return -> None

        """
        if _id not in cls.all_music:
            return None

        if tracklist_play:
            track_id = cls.snd_data['tracklist'][0]
            cls.snd_data['tracklist'].rotate(-1)
            cls.tk_mixer_music.load(cls.all_music[track_id])
        else:
            cls.tk_mixer_music.load(cls.all_music[_id])
        
        cls.tk_mixer_music.set_volume(cls.sm_volumes[0])
        cls.tk_mixer_music.play(loops)

    
    @classmethod
    def musicStopPlayback(cls, ms=0):
        """
            Stop the playback

            ms -> Fadeout the soundtrack (milliseconds)

            return -> None
        """
        if ms > 0:
            cls.tk_mixer_music.fadeout(ms)
        else:
            cls.tk_mixer_music.stop()
 