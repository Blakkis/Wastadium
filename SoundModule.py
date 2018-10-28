from ConfigsModule import GlobalGameData


class SoundMusic(GlobalGameData):
    
    # All available sound effects
    all_sounds = {}

    # Contains only path-names to music files as they are streamed for music playing
    all_music = {}

    # Default volumes for sound and music
    sm_volumes = {0: 1.0,   # Music
                  1: 1.0}   # Effects

    # Max distance at which effects can be heard at
    __sm_volume_max_dist = 320.0
    __sm_fade_out_tuning = 1.5	# Fine-tune for the max distance fadeout 

    # Volume falloff scalar
    __sm_volume_falloff = (sm_volumes[1] * __sm_fade_out_tuning) / __sm_volume_max_dist

    def __init__(self):
        pass

    @classmethod
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

        #cls.tk_mixer_music.load(cls.all_music[0])
        #cls.tk_mixer_music.set_volume(cls.sm_volumes[0])
        #cls.tk_mixer_music.play(-1) 

    
    @classmethod
    def editVolume(cls, volume_id, volume, edit=False, play_sound_cue=False):
        """
            Edit volume

            volume_id -> 0: Music, 1: Effects
            volume -> Value between 0.0 -> 1.0
            edit -> Enable edit (bool)
            play_sound_cue -> Play a test sound to indicate volume level (Effects only)

            return -> None
        """
        if edit:
            # Music
            if volume_id == 0 and volume != cls.sm_volumes[volume_id]:
                print 'Music!'

            # Effects
            elif volume_id == 1 and volume != cls.sm_volumes[volume_id]:
                cls.sm_volumes[volume_id] = volume
                if play_sound_cue: 
                	cls.playSoundEffect(188)

                # Re-calculate the volume falloff
            	cls.__sm_volume_falloff = (cls.sm_volumes[volume_id] * __sm_fade_out_tuning) / cls.__sm_volume_max_dist     


    @classmethod
    def playSoundEffect(cls, _id, distance=0):
        """
            Play sound-effect by id

            _id -> int id of the needed soundeffect (See sounds.cfg for the sounds by id)
            distance -> Screen position to calculate volume falloff from the center(Player perspective) 
            
            return -> None

        """
        if not isinstance(_id, int) and not sm_volumes[1]: 
        	return None

        if distance:
        	dist = cls.tk_hypot(cls.tk_res_half[0] - distance[0], cls.tk_res_half[1] - distance[1]) 
        	distance = cls.__sm_volume_falloff * min(cls.__sm_volume_max_dist, dist)

        channel = cls.all_sounds[_id].play()
        # No available channel to play on
        if channel is None: 
        	return None
        
        # Set the volume for the channel
        channel.set_volume(cls.tk_clamp(cls.sm_volumes[1] - distance, 0, 1))


    
