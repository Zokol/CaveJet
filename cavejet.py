import scrollphat
import random
import time

screen_size = (5, 11)

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
		if diff_width + self.gap_buffer[-1][1] > 5: diff_width = -1 

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
		self.field = Field(screen_size)
		self.ai = AI(self.field)
		self.speed = 0.1
		self.run = True

		while self.run:
			self.step()
			#self.print_field()
			self.print_phat()
			time.sleep(self.speed)

	def step(self):
		self.field.update()
		self.ai.next_move()
		if self.field.buffer[self.ai.player.x][self.ai.player.y] == 1:
			self.game_over()

	def game_over(self):
		for i in range(5):
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

	def print_phat(self):
		scrollphat.clear()

		print(self.ai.player.x, self.ai.player.y)
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

if __name__ == "__main__":
	while True:
		game = Game()
