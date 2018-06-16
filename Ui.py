from ConfigsModule import GlobalGameData#, TkCounter
from TextureLoader import uiElements
from Weapons import Weapons
from EventManager import EventManager
from Inventory import Inventory


__all__ = ('uiOverlay', )

# NOTE: Replace the hardcoded shit with more robust system

	
class uiOverlay(uiElements, EventManager, Inventory):
	"""
		Handle and render gameplay overlay

		NOTE: Make sure 'uiElements' has been loaded before creating instance of this class

		return -> None
		
	"""
	
	def __init__(self):  		   
		# NOTE: Most of these hardcoded stuff is for the textures which do not scale with resolution (in-game)
		
		self.olFont_1 = self.tk_font(self.ElementFonts[0], 20)
		self.olFont_2 = self.tk_font(self.ElementFonts[0], 24)


		w, h = self.olFont_1.size('99:99:99')	# estimating the size before rendering it
		self.olDisplayTimer_bg = self.tk_gradient_rect(w + 32, h, (0xff, 0x0, 0x0), 0xaa)
		self.olDisplayTimer_bg_pos = self.tk_res_half[0] -  self.olDisplayTimer_bg.get_width() / 2, 0 

		self.olDisplayTimer_bg_outline = self.tk_gradient_rect(w + 64, 1, (0xff, 0x0, 0x0), 0xaa)
		self.olDisplayTimer_bg_outline_pos = (self.tk_res_half[0] -  self.olDisplayTimer_bg_outline.get_width() / 2, 
											  self.olDisplayTimer_bg.get_height())  
 		
 		self.olGameTimer = self.tk_counter(-1); self.updateGameTimer() 

		# NOTE: Most of this is just Overlay decoration

		# Weapon 
		self.olWeaponElem = self.ol_buildElement((4, self.tk_resolution[1] - 84), 64, 64)
		
		# Ammo 
		self.olAmmoElem	  = self.ol_buildElement((4, self.tk_resolution[1] - 136), 128, 32)
		self.tk_draw_aaline(self.olAmmoElem[0], (0xff, 0x0, 0x0), (48, 8), (48, 39))	# Separation of icon and ammo count
		self.AmmoBar = self.tk_surface((80, 28), self.tk_srcalpha)
		self.AmmoBar.fill((0x80, 0x0, 0x0, 0xaa))
		
		# Health and armor bg
		self.olHpArmsElem = self.ol_buildElement((88, self.tk_resolution[1] - 84), 144, 64)
		
		# Decoration for the health and armor slot (Endcaps)
		self.tk_draw_aaline(self.olHpArmsElem[0], (0xff, 0x0, 0x0), (44,  11), (44,  38))		# Health endcaps
		self.tk_draw_aaline(self.olHpArmsElem[0], (0xff, 0x0, 0x0), (146, 11), (146, 38))

		self.tk_draw_aaline(self.olHpArmsElem[0], (0xff, 0x0, 0x0), (44,  43), (44,  70))		# Armor endcaps
		self.tk_draw_aaline(self.olHpArmsElem[0], (0xff, 0x0, 0x0), (146, 43), (146, 70))

		# Health 
		self.healthBar = self.tk_surface((96, 28), self.tk_srcalpha)
		self.heartBeatCycle = self.tk_cycle(self.__heartBeatGenerator(self.i_playerStats['health'][0]))
		self.heartBeatCycleTimer = self.tk_event_trigger(1)

		self.healthBarCriticalCycle = self.tk_cycle(self.tk_chain(xrange(0, 128, 4), xrange(128, 0, -4)))
		self.healthBarCritical = self.tk_surface((96, 28), self.tk_srcalpha)
		self.healthBarCritical.fill((0x80, 0x0, 0x0, 0xaa))

		# Armor 
		self.armorBar = self.tk_surface((96, 28), self.tk_srcalpha)
		self.armorBar.fill((0x80, 0x0, 0x0, 0xaa))

		# Ui Events
		EventManager.__init__(self)
		self.Event_newEvent(1000, self.updateGameTimer)
		self.Event_newEvent(1, self.overlayExtraEffects)


	def __heartBeatGenerator(self, delay=8):
		"""
			Create an 'Heartbeat' between delays

			delay -> Rest time between beats. 
					 Note: Minimum of delay should be 8!

			return -> Generator

		"""
		# Full 360 heartbeat
		for beat in xrange(0, 360, 10):
			yield self.tk_sin(self.tk_radians(beat))

		yield None	# Do an action between the beat and at start of rest	
		
		# Rest time between heartbeats
		for rest in xrange(min(72, max(8, delay))):
			yield 0
	
	
	def updateGameTimer(self):
		"""
			Update gametimer and re-render the font texture

			return -> None

		"""
		self.olGameTimer += 1
		# Update the text surface every second
		self.olDisplayTimerRender = self.tk_renderText(self.olFont_1, 
									str(self.tk_timedelta(seconds=self.olGameTimer())), 1, (0xff, 0x0, 0x0), shadow=1)

	
	
	def overlayExtraEffects(self):
		"""
			Update overlays visual effects

			return -> None

		"""
		beat = self.heartBeatCycle.next()
		if beat is None: return beat
		
		# Convert the sine wave to triangle wave
		beat = int(self.tk_asin(beat) * 6)
		
		# Health is critical, flash the healthbar : Redo this
		if self.i_playerStats['health'][0] < self.i_playerStats['health'][1] / 4:
			critical = self.healthBarCriticalCycle.next()
			self.healthBarCritical.fill((0xaa, 0x0, critical, critical))

		self.tk_draw_circle(self.healthBar, (0xff, 0x0, 0x0), (93, 14 + beat), 2)
		self.healthBar.scroll(-1, 0) 


	def ol_buildElement(self, pos, w, h, ipad=8):
		"""
			Build an uielement with alpha background and element anchor pos

			anchor pos is located at topleft, offset by ipad 

			return -> surf, position, anchor position for icons inside the surface 

		"""
		# Small extension for the 'tk_draw_rounded_rect' tho should move it inside the actual function
		bg = self.tk_draw_rounded_rect(w + ipad, h + ipad, 10, (0xcc, 0x0, 0x0), 0x90)
		anchor = pos[0] + ipad, pos[1] + ipad
		return bg, pos, anchor

	
	def drawOverlay(self, surface):
		"""
			Draw the overlay during gameplay

			surface -> Surface to draw the overlay on

			return -> None

		"""
		# Note: Most of the stuff is 'harcoded', so scaling will be issue
		#		Also changing the font will be issue too

		# Render a background for the timer
		surface.blit(self.olDisplayTimer_bg, self.olDisplayTimer_bg_pos)

		surface.blit(self.olDisplayTimer_bg_outline, self.olDisplayTimer_bg_outline_pos)
		
		# Render gametime 
		surface.blit(self.olDisplayTimerRender, (self.tk_res_half[0] - self.olDisplayTimerRender.get_width() / 2, 0)) 
		
		# Weapon
		surface.blit(*self.olWeaponElem[:2])
		surface.blit(self.all_weapons_data[self.i_playerStats['weapon']][1], self.olWeaponElem[2])

		# Health/Armor
		surface.blit(*self.olHpArmsElem[:2])
		pos = self.olHpArmsElem[2]
		surface.blit(self.ElementTextures[0], pos)							# Health/Armor Icon
		surface.blit(self.healthBarCritical, (pos[0] + 40, pos[1] + 3)) 	# HealthBar bg which flashes
		surface.blit(self.healthBar,         (pos[0] + 40, pos[1] + 3))		# Healthbar bg which contains the ECG effect
		surface.blit(self.armorBar,          (pos[0] + 40, pos[1] + 35))	# Armorbar bg
		
		# Health text (Separated from the blit to get the size of the string, so it can be anchored by the right side)
		text_surf =	self.tk_renderText(self.olFont_1, str(self.i_playerStats['health'][0]), 
					1, (0xff, 0x0, 0x0), shadow=1) 
		surface.blit(text_surf, (pos[0] + 134 - text_surf.get_width(), pos[1] + 16))
		
		# Armor text
		text_surf =	self.tk_renderText(self.olFont_1, str(self.i_playerStats['armor'][0]), 
					1, (0xff, 0x0, 0x0), shadow=1)
		surface.blit(text_surf, (pos[0] + 134 - text_surf.get_width(), pos[1] + 48))  

		# Weapons with infinite ammo, do not need the ammo gui element
		ammo_id = self.all_weapons_data[self.i_playerStats['weapon']][0]
		if ammo_id != -1: self.ol_render_ammo_gui(surface, ammo_id)
			 
		surface.blit(*self.tk_drawCursor(self.ElementCursors[0]))

	
	def ol_render_ammo_gui(self, surface, ammo_id):
		"""
			Render ammo icon/count if needed

			ammo element doesn't get rendered if ammo_id is -1 (Infinite ammo)

			return -> None
		"""
		# Ammo text
		surface.blit(*self.olAmmoElem[:2])
		pos = self.olAmmoElem[2] 
		surface.blit(self.all_ammo_data[ammo_id][2], pos)    	# Ammo Icon
		surface.blit(self.AmmoBar, (pos[0] + 48, pos[1] + 2))	# Ammo Count bg

		# Ammo count text (Limit the bullet count rendering to 99999)
		ammo_count_surf = self.tk_renderText(self.olFont_2, str(min(self.i_playerAmmo[ammo_id], 99999)), 
					 						 1, (0xff, 0x0, 0x0), shadow=1) 
		
		surface.blit(ammo_count_surf, ((pos[0] + 48) + self.AmmoBar.get_width() / 2 - ammo_count_surf.get_width() / 2, 
									    pos[1] + 2))	


if __name__ == '__main__':
	pass
