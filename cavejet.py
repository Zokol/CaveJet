import random
import time

SCREEN_TYPE = "UNICORN"
#SCREEN_TYPE = "SCROLL"
RGB_ENABLED = True

if SCREEN_TYPE == "UNICORN":
	import unicornhat as unicorn
	unicorn.set_layout(unicorn.AUTO)
	unicorn.rotation(0)
	unicorn.brightness(0.2)
	SCREEN_WIDTH, SCREEN_HEIGHT = unicorn.get_shape()
	screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)
	RGB_ENABLED = True

	BG_COLOR = [0, 0, 0]
	CAVE_COLOR = [255, 255, 255]
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
			#self.print_field()
			if SCREEN_TYPE == "UNICORN": self.print_unicorn()
			if SCREEN_TYPE == "SCROLL": self.print_scroll()
			print(self.distance)
			time.sleep(self.speed)

	def step(self):
		self.distance += 1
		self.field.update()
		#self.ai.next_move()
		self.ai.better_move(50) # Number determines the number of iterations done every move, affected by CPU-power
		if self.field.buffer[self.ai.player.x][self.ai.player.y] == 1:
			if SCREEN_TYPE == "UNICORN": self.game_over_unicorn()
			if SCREEN_TYPE == "SCROLL": self.game_over_scroll()

	def game_over_unicorn(self):
		#shader = lambda x, y: return (x/7.0) * 255, 0, (y/7.0) * 255
		width, height = get_shape()
		for x in range(width):
			time.sleep(0.05)
			for y in range(height):
				r, g, b = [200,0,0]
				set_pixel(x, y, r, g, b)

	def game_over_scroll(self):
		for i in range(1):
			self.set_checker(0)
			time.sleep(0.5)
			self.set_checker(1)
			time.sleep(0.5)
		self.run = False

	# XXX make separate end-game-function for different screens
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
				if pixel: r, g, b = CAVE_COLOR
				else: r, g, b = BG_COLOR
				unicorn.set_pixel(x, y, r, g, b)
		r, g, b = PLAYER_COLOR
		unicorn.set_pixel(self.ai.player.x, self.ai.player.y, r, g, b)
		unicorn.show()

	def print_scroll(self):
		scrollphat.clear()
		#print(self.ai.player.x, self.ai.player.y)
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

	def next_move(self):
		next_col = self.field.buffer[self.player.x + 1]
		#next2_col = self.field.buffer[self.player.x + 2]
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
		elif next2_col[self.player.y] == 1:
			if self.player.y < 3:
				if next2_col[self.player.y + 2] == 0:
					self.player.y += 1
					return 0
			if self.player.y > 1:
				if next2_col[self.player.y - 2] == 0:
					self.player.y -= 1
					return 0
		"""

	def better_move(self, iterations):
		move_weight = {-1: -1, 0: 0, 1: -1}
		next_layer_weight = 1
		best = {"score": 0, "moves": []}
		for iteration in range(iterations):
			player_coords = {'x': self.player.x, 'y': self.player.y}
			moves = []
			for layer in self.field.buffer[player_coords['x']:]:
				if layer[player_coords['y']] == 1:
					break
				possible_moves = [-1, 0, 1]
				if player_coords['y'] == 4:
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
		self.player.y += best["moves"][0]

if __name__ == "__main__":
	while True:
		game = Game()
