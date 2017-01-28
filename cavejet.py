import random
import time

SCREEN_TYPE = "UNICORN"
#SCREEN_TYPE = "SCROLL"
RGB_ENABLED = True

if SCREEN_TYPE == "UNICORN":
	import unicornhat as unicorn
	unicorn.set_layout(unicorn.AUTO)
	unicorn.rotation(0)
	unicorn.brightness(0.7)
	SCREEN_WIDTH, SCREEN_HEIGHT = unicorn.get_shape()
	screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
	RGB_ENABLED = True

	BG_COLOR = [0, 150, 200]
	BG_NOISE = 2
	CAVE_COLOR = [244,164,96]
	CAVE_NOISE = 10
	PLAYER_COLOR = [255, 0, 0]

if SCREEN_TYPE == "SCROLL":
	import scrollphat
	SCREEN_WIDTH = 11
	SCREEN_HEIGHT = 5
	scrollphat.set_brightness(1)

screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)

class Field:
	def __init__(self, field_size):
		self.buffer = [[0] * field_size[0]] * field_size[1]
		self.gap_buffer = [(1,3)]

	"""
	tunnel_gen - Tunnel Generator
	creates the next column for the tunnel
	
	Requires two random integers;
		gap_place: in range of +-1, determines where the gap is placed in relation to the last gap
		gap_width: in range of 2-5, determines the gap width
	"""
	def tunnel_gen(self):
		diff_place = -99
		while (self.gap_buffer[-1][0] + diff_place < 0) or (self.gap_buffer[-1][0] + diff_place > 4) :
			diff_place = random.randint(-1,1)
		diff_width = random.randint(-1,1)
		if diff_width + self.gap_buffer[-1][1] <= 1: diff_width = 1 
		if diff_width + self.gap_buffer[-1][1] > screen_size[0]: diff_width = -1 

		self.gap_buffer.append((self.gap_buffer[-1][0] + diff_place, self.gap_buffer[-1][1] + diff_width))
		if len(self.gap_buffer) > 16: self.gap_buffer.pop(0)
		
		col = [1] * len(self.buffer[0])
		for pixel_i in range(0, self.gap_buffer[-1][1]):
			try: col[pixel_i + self.gap_buffer[-1][0]] = 0
			except IndexError: pass

		return col

	def update(self):
		new_col = self.tunnel_gen()
		self.buffer.append(new_col)
		self.buffer.pop(0)

class Player:
	def __init__(self):
		self.x = 1
		self.y = 2

class Game:
	def __init__(self):
		self.distance = 0
		self.field = Field(screen_size)
		self.ai = AI(self.field)
		self.speed = 0.05
		self.run = True

		while self.run:
			self.step()
			if SCREEN_TYPE == "UNICORN": self.print_unicorn()
			if SCREEN_TYPE == "SCROLL": self.print_scroll()
			print(self.distance)
			time.sleep(self.speed)

	def step(self):
		self.distance += 1
		self.field.update()
		self.ai.better_move(50) # Number determines the number of iterations done every move, affected by CPU-power
		if self.field.buffer[self.ai.player.x][self.ai.player.y] == 1:
			if SCREEN_TYPE == "UNICORN": self.game_over_unicorn()
			if SCREEN_TYPE == "SCROLL": self.game_over_scroll()

	def game_over_unicorn(self):
		#shader = lambda x, y: return (x/7.0) * 255, 0, (y/7.0) * 255
		width, height = unicorn.get_shape()
		for x in range(width):
			time.sleep(0.05)
			for y in range(height):
				r, g, b = [200,0,0]
				unicorn.set_pixel(x, y, r, g, b)

	def game_over_scroll(self):
		for i in range(1):
			self.set_checker(0)
			time.sleep(0.5)
			self.set_checker(1)
			time.sleep(0.5)
		self.run = False

	def set_checker(self, offset):
		scrollphat.clear()
		n = offset
		for y in range(5):
			for x in range(11):
				scrollphat.set_pixel(x,y,n % 2 == 0)
				n += 1
		scrollphat.update()

	def print_unicorn(self):
		unicorn.clear()
		for x, col in enumerate(self.field.buffer):
			for y, pixel in enumerate(col):
				if pixel: r, g, b = [i + random.randint(0,CAVE_NOISE) for i in CAVE_COLOR]
				else: r, g, b = [i + random.randint(0,BG_NOISE) for i in BG_COLOR]
				unicorn.set_pixel(x, y, r, g, b)
		r, g, b = PLAYER_COLOR
		unicorn.set_pixel(self.ai.player.x, self.ai.player.y, r, g, b)
		unicorn.show()

	def print_scroll(self):
		scrollphat.clear()
		for x, col in enumerate(self.field.buffer):
			for y, pixel in enumerate(col):
				scrollphat.set_pixel(x,y,pixel)
		scrollphat.set_pixel(self.ai.player.x, self.ai.player.y, 1)
		scrollphat.update()
	
	def print_field(self):
		for col in self.field.buffer:
			print(col, self.field.gap_buffer[-1])

class AI:
	def __init__(self, field):
		self.player = Player()
		self.field = field

	"""
	Myopic AI

	This algorithm is very very near-sighted, and it's flying in fog, and it's raining... wait, can that happen? *wanders off to r/askreddit/*
	"""
	def next_move(self):
		next_col = self.field.buffer[self.player.x + 1]
		print(next_col, next_col[self.player.y])
		if next_col[self.player.y] == 1:
			if self.player.y < 4:
				if next_col[self.player.y + 1] == 0:
					self.player.y += 1
					return 0
			if self.player.y > 0:
				if next_col[self.player.y - 1] == 0:
					self.player.y -= 1
					return 0

	"""
	Random path finding AI

	This algorithm takes all the possible moves and in the case of selection,
	takes random direction and continues.
	
	Algorithm is given number of iterations (computing time) to calculate paths.
	Each path is evaluated based on pretermined weights (more direct path is better,
	path that gives player best chances of survival is also better)

	This is better AI than nothing at all, but it still misses a lot of cleverness.
	It always choses random path, but nothing prevents it to taking the same path twice.
	So, this AI is waisting valuable computing time, most likely comparing very similar paths.
	"""
	def better_move(self, iterations):
		move_weight = {-1: -1, 0: 0, 1: -1} ## Every decision is dependent on these numbers. Change these and you will get better or worse AI.
		next_layer_weight = 1 ## This is also very important.

		## Let the magic happen
		best = {"score": 0, "moves": []}
		for iteration in range(iterations): # Iterations to find most of the move combinations
			player_coords = {'x': self.player.x, 'y': self.player.y}
			moves = []
			for layer in self.field.buffer[player_coords['x']:]:
				if layer[player_coords['y']] == 1:
					break
				possible_moves = [-1, 0, 1] # List all possible moves player can take; move up, move down or keep the place

				# Detect that the player is next to the screen edge
				if player_coords['y'] == SCREEN_HEIGHT - 1:
					try: possible_moves.remove(1)
					except ValueError: pass
					if layer[player_coords['y'] - 1] == 1:
						try: possible_moves.remove(-1)
						except ValueError: pass
				elif 1 <= player_coords['y'] <= 3:
					if layer[player_coords['y'] - 1] == 1:
						try: possible_moves.remove(-1)
						except ValueError: pass
					if layer[player_coords['y'] + 1] == 1:
						try: possible_moves.remove(1)
						except ValueError: pass
				elif player_coords['y'] == 0:
					try: possible_moves.remove(-1)
					except ValueError: pass
					if layer[player_coords['y'] + 1] == 1:
						try: possible_moves.remove(1)
						except ValueError: pass
				move = random.choice(possible_moves)
					
				player_coords['y'] += move
				moves.append(move)
				player_coords['x'] += 1
			score = 0
			for move in moves:
				score += move_weight[move] + next_layer_weight
			if best["score"] < score: 
				best["score"] = score
				best["moves"] = moves
		if len(best["moves"]) >= 1: 
			self.player.y += best["moves"][0] # Found some good moves!
		else:
			self.player.y += 0 # Oh no! There seems to be nothing I can do, so best to head straight and hope that the wall is thin..

	"""
	Recursive AI

	Now this starts to be something you can call efficient. (If you disagree, take a look at the other two)

	Idea is simple: 
		1) We take a path that has no intersections and continue until we have to make a choise or until player hit's a wall
		2) Start new instances of this function for each choise and wait for them to return their moves.
		3) Calculate scores for the routes we received.
		4) Move player according to the best move we know.

	It is quite clear that if we calculate this after every step player takes, and the field is giving us lots of room to move, 
	this recursive tactic spirals out of control prettu fast. It's dependent on how much memory and CPU-power we have, but there
	should be some way of controlling this recursion.
	Thus, the only parameter given to the algorithm is very very very important. It behaves like TTL-value in network packets.
	The depth_limit is reduced by one each time it is passed onwards and checked if it reaches zero. If it does, the recursion ends
	and the result is passed to the parent-function.

	By increasing the depth-limit, more possible routes will be evaluated and also slower the code execution will be.

	"""
	def even_better_move(self, depth_limit, moves = []):
		depth_limit -= 1
		if depth_limit == 0:
			return 0

if __name__ == "__main__":
	while True:
		game = Game()
