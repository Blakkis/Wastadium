from ConfigsModule import GlobalGameData


class SoundMusic(GlobalGameData):
	
	# All available sound effects
	all_sounds = {}

	# Contains only path-names to music files as they are streamed for music playing
	all_music = {}

	# Default volumes for sound and music
	sm_volumes = {0: 1.0,	# Music
				  1: 1.0}	# Effects

	sm_volume_drop = 0.02

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
				if play_sound_cue: cls.playSoundEffect(188)


	@classmethod
	def playSoundEffect(cls, _id, distanced=False):
		"""
			Play sound-effect by id

			_id -> int id of the needed soundeffect (See sounds.cfg for the sounds by id)
			distanced -> Play the sound effect half the current volume
						 (Possible calculate actual distance to the sound location and use that) 
			
			return -> None

		"""
		if not isinstance(_id, int): return None

		channel = cls.all_sounds[_id].play()
		if channel is None: return
		
		channel.set_volume(cls.sm_volumes[1] / 8.0 if distanced else cls.sm_volumes[1])


	