import random
import time

#SCREEN_TYPE = "UNICORN"
#SCREEN_TYPE = "SCROLL"
SCREEN_TYPE = "SCROLLHD"
RGB_ENABLED = False

STUDY_LOOP = False
LOOP = False

TUNNEL_GAP_MIN = 2
TUNNEL_GAP_MAX = 6
TUNNEL_GAP_DIFF_MAX = 1
TUNNEL_MOVE_DIFF_MAX = 1

AI_VISIBILITY_DEPTH = 10
AI_REROUTE_DEPTH = 2

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
    CAVE_COLOR = [244, 164, 96]
    CAVE_NOISE = 10
    PLAYER_COLOR = [255, 0, 0]

if SCREEN_TYPE == "SCROLL":
    import scrollphat
    SCREEN_WIDTH = 11
    SCREEN_HEIGHT = 5
    scrollphat.set_brightness(1)

if SCREEN_TYPE == "SCROLLHD":
    import scrollphathd as scrollphat
    SCREEN_WIDTH = 17
    SCREEN_HEIGHT = 7
    scrollphat.set_brightness(0.25)

screen_size = (SCREEN_WIDTH, SCREEN_HEIGHT)


class GameOver(Exception):
    def __init__(self):
        print("AI found no possible moves")
        #input("quit?")

class Field:
    def __init__(self, field_size):
        self.buffer = [[0] * field_size[1]] * field_size[0]
        self.gap_buffer = [(1, 3)]

    """
    tunnel_gen - Tunnel Generator
    creates the next column for the tunnel

    Requires two random integers;
        diff_place: in range of +-1, determines where the gap is placed in relation to the last gap
        diff_width: in range of +-1, determines the gap width in relation to the last gap width
    """
    def tunnel_gen(self):
        if self.gap_buffer[-1][0] == 0:                             # Is the current place at screen edge?
            diff_place = random.randint(0, TUNNEL_MOVE_DIFF_MAX)   # Go away or stay at screen edge
        elif self.gap_buffer[-1][0] == SCREEN_HEIGHT - TUNNEL_MOVE_DIFF_MAX:           # Is the current place at screen edge?
            diff_place = random.randint(-TUNNEL_MOVE_DIFF_MAX, 0)  # Go away or stay at screen edge
        else:
            diff_place = random.randint(-TUNNEL_MOVE_DIFF_MAX, TUNNEL_MOVE_DIFF_MAX)  # Not at screen edge, can move freely

        if self.gap_buffer[-1][1] == TUNNEL_GAP_MIN:                            # Is gap at minimum?
            diff_width = random.randint(0, TUNNEL_GAP_DIFF_MAX)    # Go larger or stay at same
        elif self.gap_buffer[-1][1] == TUNNEL_GAP_MAX:                            # Is gap at maximum?
            diff_width = random.randint(-TUNNEL_GAP_DIFF_MAX, 0)   # Go smaller or stay at same
        else:
            diff_width = random.randint(-TUNNEL_GAP_DIFF_MAX, TUNNEL_GAP_DIFF_MAX)   # Adjust freely

        self.gap_buffer.append((self.gap_buffer[-1][0] + diff_place, self.gap_buffer[-1][1] + diff_width))
        if len(self.gap_buffer) > SCREEN_WIDTH: self.gap_buffer.pop(0)

        col = [1] * len(self.buffer[0])
        for pixel_i in range(0, self.gap_buffer[-1][1] + 1):
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
    def __init__(self, move_weight={-1: -1, 0: 0, 1: -1}, next_layer_weight=3, speed=0.1):
        self.distance = 0
        self.field = Field(screen_size)
        self.ai = AI(self.field, move_weight, next_layer_weight)
        self.speed = speed
        self.run = True

    def start(self):
        while self.run:
            self.step()
            if SCREEN_TYPE == "UNICORN": self.print_unicorn()
            if SCREEN_TYPE == "SCROLL" or SCREEN_TYPE == "SCROLLHD": self.print_scroll()
            time.sleep(self.speed)
        return self.distance

    def step(self):
        self.distance += 1
        if self.speed is None:
            start = time.time()
            self.ai.move()
            self.speed = time.time() - start
        else:
            self.ai.move()
        self.field.update()
        if self.field.buffer[self.ai.player.x][self.ai.player.y] == 1:
            if SCREEN_TYPE == "UNICORN": self.game_over_unicorn()
            if SCREEN_TYPE == "SCROLL" or SCREEN_TYPE == "SCROLLHD": self.game_over_scroll()

    def game_over_unicorn(self):
        width, height = unicorn.get_shape()
        for x in range(width):
            time.sleep(0.05)
            for y in range(height):
                r, g, b = [200, 0, 0]
                unicorn.set_pixel(x, y, r, g, b)
        time.sleep(0.5)
        self.run = False

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
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                scrollphat.set_pixel(x, y, n % 2 == 0)
                n += 1
        if SCREEN_TYPE == "SCROLL": scrollphat.update()
        if SCREEN_TYPE == "SCROLLHD": scrollphat.show()

    def print_unicorn(self):
        unicorn.clear()
        for x, col in enumerate(self.field.buffer):
            for y, pixel in enumerate(col):
                if pixel: r, g, b = [i + random.randint(0, CAVE_NOISE) for i in CAVE_COLOR]
                else: r, g, b = [i + random.randint(0, BG_NOISE) for i in BG_COLOR]
                unicorn.set_pixel(x, y, r, g, b)
        r, g, b = PLAYER_COLOR
        unicorn.set_pixel(self.ai.player.x, self.ai.player.y, r, g, b)
        unicorn.show()

    def print_scroll(self):
        scrollphat.clear()
        for x, col in enumerate(self.field.buffer):
            for y, pixel in enumerate(col):
                scrollphat.set_pixel(x, y, pixel)
        scrollphat.set_pixel(self.ai.player.x, self.ai.player.y, 1)
        if SCREEN_TYPE == "SCROLL": scrollphat.update()
        if SCREEN_TYPE == "SCROLLHD": scrollphat.show()

    def print_field(self):
        for col in self.field.buffer:
            print(col, self.field.gap_buffer[-1])


class AI:
    def __init__(self, field, move_weight={-1: -1, 0: 0, 1: -1}, next_layer_weight=3):
        self.player = Player()
        self.next_moves = []
        self.field = field
        self.move_weight = move_weight  # Every decision is dependent on these numbers. Change these and you will get better or worse AI.
        self.next_layer_weight = next_layer_weight  # This is also very important.

    """
    Filter possible moves

    This is simple fundtion to figure out where player can move
    """
    def filter_moves(self, layer, player_y):
        possible_moves = [0, -1, 1]  # List all possible moves player can take; move up, move down or keep the place

        # Detect that the player is next to the screen edge
        if player_y == SCREEN_HEIGHT - 1:
            try: possible_moves.remove(1)
            except ValueError: pass
            if layer[player_y - 1] == 1:
                try: possible_moves.remove(-1)
                except ValueError: pass
        elif 1 <= player_y <= 3:
            if layer[player_y - 1] == 1:
                try: possible_moves.remove(-1)
                except ValueError: pass
            if layer[player_y + 1] == 1:
                try: possible_moves.remove(1)
                except ValueError: pass
        elif player_y == 0:
            try: possible_moves.remove(-1)
            except ValueError: pass
            if layer[player_y + 1] == 1:
                try: possible_moves.remove(1)
                except ValueError: pass
        """
        if len(possible_moves) == 0:
            print("No possible moves to next layer!!")
        if len(possible_moves) == 1:
            print("Only one possible move")
        """
        return possible_moves

    """
    Evaluate path

    This function gives score for each path
    """
    def evaluate_path(self, moves):
        score = 0

        for move in moves:
            score += (self.move_weight[move] + self.next_layer_weight)
        return score

    """
    Move player

    Uses some available AI-algo to figure out the next move
    """
    def move(self):
        self.player_coords = {'x': self.player.x, 'y': self.player.y}
        if len(self.next_moves) <= AI_REROUTE_DEPTH:
            #self.player.y += self.next_move()[0]
            #self.player.y += self.better_move(50)[0]
            possible_paths = self.even_better_move(AI_VISIBILITY_DEPTH, [])
            if possible_paths is None:
                #print("Path finder returned None")
                raise GameOver
            if len(possible_paths) == 0:
                #print("Path finder returned empty list of paths")
                raise GameOver
            for path in possible_paths:
                path_score = self.evaluate_path(path)
                #print("Path:", path, "Score:", path_score)
            self.next_moves = max(possible_paths, key=lambda x: self.evaluate_path(x))  # Selecting the best path using evaluation-function
            #print("Selected path:", self.next_moves, "With value:", self.evaluate_path(self.next_moves))
            #print("selected path length:", len(self.next_moves))
            #next_moves = self.better_move(50)

            if len(self.next_moves) == 0:
                #print("Selected empty list of paths")
                raise GameOver
        self.player.y += self.next_moves.pop(0)

    """
    Myopic AI

    This algorithm is very very near-sighted, and it's flying in fog, and it's raining... wait, can that happen? *wanders off to r/askreddit/*
    """
    def next_move(self):
        next_col = self.field.buffer[self.player.x + 1]
        if next_col[self.player.y] == 1:
            if self.player.y < 4:
                if next_col[self.player.y + 1] == 0:
                    return [1]
            if self.player.y > 0:
                if next_col[self.player.y - 1] == 0:
                    return [-1]

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
        best = {"score": 0, "moves": []}
        for iteration in range(iterations):  # Iterations to find most of the move combinations
            self.player_coords = {'x': self.player.x, 'y': self.player.y}
            moves = []
            for layer in self.field.buffer[self.player_coords['x']:]:
                if layer[self.player_coords['y']] == 1:
                    break
                possible_moves = self.filter_moves(layer, self.player_coords['y'])
                move = random.choice(possible_moves)

                self.player_coords['y'] += move
                moves.append(move)
                self.player_coords['x'] += 1

            score = self.evaluate_path(moves)
            if best["score"] < score:
                best["score"] = score
                best["moves"] = moves

        return best["moves"]

    """
    Recursive AI

    Now this starts to be something you can call efficient. (If you disagree, take a look at the other two)

    Idea is simple:
        1) We take a path that has no intersections and continue until we have to make a choise or until player hit's a wall
        2) Start new instances of this function for each choise and wait for them to return their moves.
        3) Calculate scores for the routes we received.
        4) Move player according to the best move we know.

    It is quite clear that if we calculate this after every step player takes, and the field is giving us lots of room to move,
    this recursive tactic spirals out of control pretty fast. It's dependent on how much memory and CPU-power we have, but there
    should be some way of controlling this recursion.
    Thus, the only parameter given to the algorithm is very very very important. It behaves like TTL-value in network packets.
    The depth_limit is reduced by one each time it is passed onwards and checked if it reaches zero. If it does, the recursion ends
    and the result is passed to the parent-function.

    By increasing the depth-limit, more possible routes will be evaluated and also slower the code execution will be.

    """
    def even_better_move(self, depth_limit, moves=[]):
        depth_limit -= 1
        if depth_limit == 0:            # Hit depth limit without hitting the wall
            """
            print(" " * self.player_coords['x'] + ''.join(str(move) for move in moves))
            for y in range(SCREEN_HEIGHT):
                row = ""
                for x, layer in enumerate(self.field.buffer):
                    if x == self.player_coords['x'] and y == self.player_coords['y']:
                        row += "X"
                    elif layer[y] == 1:
                        row += "*"
                    else:
                        row += " "
                print(row)
            """
            return moves                # Returing route
        else:
            next_layer = self.field.buffer[self.player_coords['x'] + len(moves)]
            player_y = self.player_coords['y']
            
            if len(moves) > 0:
                for layer_i, y_move in enumerate(moves):
                    move_layer = self.field.buffer[self.player_coords['x'] + layer_i + 1]
                    player_y += y_move
                    if move_layer[player_y] == 1:    # Hit a wall with this route
                        #print("layer:", move_layer)
                        #print("This path", moves, "hits the wall, returning None")
                        return None            # Returning None
            
            possible_moves = self.filter_moves(next_layer, player_y)

            paths = []
            for move in possible_moves:
                returned_path = self.even_better_move(depth_limit, moves + [move])
                if returned_path is not None:       # Path did not hit the wall
                    if type(returned_path[0]) != list:  # Check if we got list of paths or just one path
                        paths.append(returned_path)     # Adding path to list of possible paths
                    else:
                        paths += returned_path          # Return is already list of paths, summing it to the path list

            if len(paths) > 0:
                return paths
            else:
                return None        # Found no paths that would not hit the wall

def run_game():
    try:
        #move_cost = -16
        #layer_reward = 34
        move_cost = -1
        layer_reward = 10
        game = Game(move_weight={-1: move_cost, 0: 0, 1: move_cost}, next_layer_weight=layer_reward)
        game.start()
    except GameOver:
        print({"score": game.distance, "move_cost": move_cost, "layer_reward": layer_reward})
    except KeyboardInterrupt:
        print("Quitting")

def study_loop():
    logfile = open("cavejet_AI.log", 'a+')
    record = 0
    history = []
    while True:
        try:
            move_cost = random.randint(-18, -15)
            layer_reward = random.randint(32, 36)
            game = Game(move_weight={-1: move_cost, 0: 0, 1: move_cost}, next_layer_weight=layer_reward, speed=0)
            game.start()
        except GameOver:
            history.append({"score": game.distance, "move_cost": move_cost, "layer_reward": layer_reward})
            logfile.write(str(game.distance) + ',' + str(move_cost) + ',' + str(layer_reward) + '\r\n')
            if record < game.distance:
                record = game.distance
            print("Score:", game.distance, " | Best score:", record)
        except KeyboardInterrupt:
            logfile.close()
            raise

if __name__ == "__main__":
    if STUDY_LOOP:
        study_loop()
    elif LOOP:
        while True:
            run_game()
    else:
        run_game()
