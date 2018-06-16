from ConfigsModule import GlobalGameData


__all__ = ('Model3D', )


class Model3D(GlobalGameData):
	"Orthographic/Wireframe only"
	# Used mostly as a decoration effect in menus

	def __init__(self, vertices, indices, radius):
		# Default vertices for reseting the model
		self._m_vertices_default = vertices
		
		# Up-to-date vertices + indexes
		self._m_vertices = vertices
		self._m_vertices_indices = indices
		
		self._m_pos_x = 0
		self._m_pos_y = 0
		
		self._m_boundary_sphere = radius 


	@property
	def get_x(self): return self._m_pos_x
	
	@property
	def get_y(self): return self._m_pos_y

	@property
	def get_radius(self): return self._m_boundary_sphere
	
	
	@classmethod
	def m_getBoundarySphereDist(cls, vertices):
		"""
			Get the max boundary sphere from the input vertices

			vertices -> List of (x, y, z) points

			return -> Longest distance from center to vertice
		"""
		return max([cls.tk_sqrt((0 - x) ** 2 + (0 - y) ** 2 + (0 - z) ** 2) for x, y, z in vertices]) 	
	
	
	def m_render(self, surface, color=(0x60, 0x0, 0x0)):
		"""
			Render the model (Wireframe only)

			color -> Color of the wireframe

			return -> Boundary sphere

		"""
		
		surface.lock()

		for index in self._m_vertices_indices:
			# Index 0 is option for 'closing'
			i_offset = index[1:] 
			p = [(self._m_pos_x - self._m_vertices[i][0], 
				  self._m_pos_y - self._m_vertices[i][1]) for i in i_offset]
			
			# Faces
			if len(p) > 2: self.tk_draw_lines(surface, color, index[0], p, 1)
			
			# Edges
			else: self.tk_draw_line(surface, color, p[0], p[1])

		surface.unlock()

		return self._m_boundary_sphere  
 

	def m_reset(self): self._m_vertices = self._m_vertices_default 	
	
	def m_rotate_x(self, d):
		"""
			Rotate around X axis

			d -> Amount of rotation (Degrees)

			return -> None

		"""
		r = self.tk_radians(d) % self.tk_pi2
		cos, sin = self.tk_cos(r), self.tk_sin(r)

		self._m_vertices = [(x, 
							 y * cos - z * sin, 
							 z * cos + y * sin) for x, y, z in self._m_vertices]

	def m_rotate_y(self, d):
		"""
			Rotate around Y axis

			d -> Amount of rotation (Degrees)

			return -> None

		"""
		r = self.tk_radians(d) % self.tk_pi2
		cos, sin = self.tk_cos(r), self.tk_sin(r)

		self._m_vertices = [(x * cos - z * sin, 
							 y, 
							 z * cos + x * sin) for x, y, z in self._m_vertices]

	def m_rotate_z(self, d):
		"""
			Rotate around Z axis

			d -> Amount of rotation (Degrees)

			return -> None

		"""
		r = self.tk_radians(d) % self.tk_pi2
		cos, sin = self.tk_cos(r), self.tk_sin(r)

		self._m_vertices = [(x * cos - y * sin, 
							 x * sin + y * cos, 
							 z) for x, y, z in self._m_vertices]


	def m_translate(self, tx=0, ty=0, absolute=False):
		"""
			Translate model
			tx, ty -> Move direction
			absolute -> Apply values as absolute (from 0)

			return -> None

		"""
		if absolute: self._m_pos_x = tx; self._m_pos_y = ty
		else: self._m_pos_x += tx; self._m_pos_y += ty	

	
	def m_scale(self):
		# Implement this when needed
		# Be sure to re-calculate the bounding sphere after scale
		pass


	# ---- Append new models at the end ---- 
	# Using some what same idea as old OpenGL Begin/End
	# Provide all the vertices and indices(In which way you want them to be connected)
	# No need to render tris, just use quads
	
	@classmethod
	def m_create_BulletCasing(cls):
		"""
			TBD

			return -> None

		"""
		r_scale = cls.tk_resolution_scale
		
		# Create rings facing Y direction
		create_ring = lambda scale, y, segments=8: [(cls.tk_cos(cls.tk_radians(r)) * scale, y, 
								  		             cls.tk_sin(cls.tk_radians(r)) * scale) for r in xrange(0, 361, 360 / segments)]

		final_indices = []
		final_vertices = []

		# Add rings
		for d, l in ((12 * r_scale, -60 * r_scale), 
					 (14 * r_scale, -58 * r_scale), 
					 (12 * r_scale, -56 * r_scale), 
					 (14 * r_scale, -54 * r_scale), 
					 (14 * r_scale,  32 * r_scale), 
					 (10 * r_scale,  48 * r_scale), 
					 (10 * r_scale,  60 * r_scale)):
			
			ring = create_ring(d, l)
			final_indices.append(tuple([1] + [len(final_vertices) + i for i in xrange(len(ring) - 1)]))
			final_vertices.extend(ring)

		vert_lines = []
		# Add vertical lines connecting the rings
		for v in xrange(1, len(final_indices[0])):
			vert_lines.append(tuple([0] + [s[v] for s in final_indices[1:]]))
		
		final_indices.extend(vert_lines) 
			
		return cls(final_vertices, final_indices, cls.m_getBoundarySphereDist(final_vertices))

	
	@classmethod
	def m_create_Box(cls, scale):
		"""
			TBD

			return -> None

		""" 
		r_scale = cls.tk_resolution_scale
		
		final_indices = []

		scale = scale * r_scale
		verts = [(-scale, -scale, -scale),
				 (-scale, -scale,  scale),
				 ( scale, -scale,  scale),
				 ( scale, -scale, -scale),
				
				 (-scale,  scale, -scale),
				 (-scale,  scale,  scale),
				 ( scale,  scale,  scale),
				 ( scale,  scale, -scale)]

		# Faces and edges (index)
		pairs = {0: [0, 1, 2, 3],	# Faces*
				 1: [4, 5, 6, 7],
				 
				 2: [0, 4],	# Edges
				 3: [1, 5],
				 4: [2, 6],
				 5: [3, 7]}

		for v in pairs.itervalues(): final_indices.append(tuple([1] + v))

		return cls(verts, final_indices, cls.m_getBoundarySphereDist(verts))