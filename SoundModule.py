from ConfigsModule import GlobalGameData


class SoundMusic(GlobalGameData):
	
	# All available sound effects
	all_sounds = {}

	# Contains only path-names to music files as they are streamed for music playing
	all_music = {}

	# Default volumes for sound and music
	sm_volumes = {0: 0.5,	# Effects
				  1: 0.5}	# Music

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

		# Music (Only pathnames)
		for line in cls.tk_readFile(cls.tk_path.join(src_path_cfg, 'music.cfg')):
			cls.all_music[int(line[0])] = cls.tk_path.join('soundmusic', 'music', line[1])

		#cls.tk_mixer_music.load(cls.all_music[0])
		#cls.tk_mixer_music.set_volume(cls.sm_volumes[1])
		#cls.tk_mixer_music.play() 


	@classmethod
	def playSoundEffect(cls, _id, dist_mod=None):
		"""
			Play sound-effect by id

			_id -> int id of the needed soundeffect (See sounds.cfg for the sounds by id)
			dist_mod -> Apply distance modifier to adjust the volume to give out impression of sound occuring out in the distance
						Every 32 of dist_mod drops the sound volume by 'sm_volume_drop'
						Note:
							This will modify the sound object
							so if you are firing a weapon to the wall out far and near, they both play it back
							at the last given volume mod


			return -> None

		"""
		if dist_mod is not None: 
			cls.all_sounds[_id].set_volume(max(0, cls.sm_volumes[0] - cls.sm_volume_drop * dist_mod / 32))
		
		else:
			# Sound level of the object needs to be restored to default after mod usage
			cls.all_sounds[_id].set_volume(cls.sm_volumes[0])
		
		cls.all_sounds[_id].play()


	