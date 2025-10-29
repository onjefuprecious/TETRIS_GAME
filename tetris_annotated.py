import pygame  # import the pygame library which provides functionality for making games
import random  # import random for shuffling piece order and randomness
import sys  # import sys to access command-line arguments and to exit the program

# --- CONFIG ---
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600  # configure the window size for the game display
GRID_WIDTH, GRID_HEIGHT = 23, 22  # configure the logical grid width (columns) and height (rows)
CELL_SIZE = 25 # size in pixels of each square cell in the grid
GRID_ORIGIN = (20, 40)  # top-left pixel offset for where the grid is drawn on the window

# COLORS list maps numeric cell ids to RGB color tuples used for drawing
COLORS = [
    (0, 0, 0),       # 0: Empty cell color (black)
    (0, 240, 240),   # 1: I piece color (cyan-like)
    (0, 0, 240),     # 2: J piece color (blue)
    (240, 160, 0),   # 3: L piece color (orange)
    (240, 240, 0),   # 4: O piece color (yellow)
    (0, 100, 0),     # 5: R piece color (dark green) - custom piece
    (128, 0, 128),   # 6: S piece color (purple) - custom mapping
    (100, 0, 0),     # 7: T piece color (dark red) - custom mapping
    (240, 0, 0),     # 8: U piece / ghost outline color (red) used for ghost outlines in draw
    (255, 255, 255), # 9: V piece color (white)
    (0, 128, 128),   # 10: W piece color (teal)
    (0, 240, 0),     # 11: X piece color (bright green)
    (128, 240, 160), # 12: Y piece color (light green)
    (240, 0, 128),   # 13: Z piece color (magenta-like)
    (160, 240, 100), # 14: A piece color (light lime)
    (128, 128, 128)  # 15: Gray color (could be used for ghosts or other UI elements)
]

# PIECES dictionary: names map to 2D arrays where nonzero values indicate occupied cells.
# The numeric values inside these shapes are not strictly used as ids by the Piece class
# (the code uses truthiness), but they can be used to vary visual patterns if desired.
PIECES = {
    'I': [[1, 1, 1, 1]],  # I piece: four horizontal blocks in a row
    'J': [[2, 0, 0], [2, 2, 2]],  # J piece: 2 at top-left and a row of three below
    'L': [[0, 0, 3], [3, 3, 3]],  # L piece: mirrored J shaped
    'O': [[4, 4], [4, 4]],  # O piece: 2x2 square
    'R': [[0, 5, 5], [5, 5, 0]],  # R: custom "Z-like" piece mapped to id 5
    'S': [[0, 10, 0], [6, 6, 6]],  # S: irregular entry (values differ), used by truthiness
    'T': [[7, 7, 0], [0, 7, 7]],  # T: also looks like a skewed shape here
    'U': [[2, 2, 2, 3], [2, 2, 2, 3]],  # U: custom shape (two identical rows)
    'V': [[3, 0], [3, 0]],  # V: a 2x2 column-ish shape
    'W': [[1, 0]],  # W: single-row piece (effectively 1 block plus empty space)
    'X': [[0, 2], [2, 2]],  # X: small 2x2 block with one empty cell
    'Y': [[0, 3], [0, 3], [0, 3]],  # Y: 3x2 tall column with left column empty
    'Z': [[9, 4], [1, 1],[2, 2]],  # Z: inconsistent shape rows - still truthy cells
    'A': [[3, 3, 3], [3, 3, 3], [3, 3, 3]]  # A: 3x3 full block (nonstandard)
}

# PIECE_ORDER is the list of names used when building a bag to spawn pieces
PIECE_ORDER = ['I', 'J', 'L', 'O', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'A']


def rotate(shape):
    """Rotate a shape matrix clockwise and return the rotated matrix.
    This function takes the 2D list `shape` and returns a new 2D list that
    represents the original matrix rotated 90 degrees clockwise.
    """
    return [list(row) for row in zip(*shape[::-1])]  # reverse rows then transpose using zip
        #This line rotates a 2D matrix (like a Tetris shape) 90 degrees clockwise # The * operator unpacks the rows.


# This _init_ method is used to initialize a new Tetris piece with its name, shape, starting position, and ID.
class Piece:
    def __init__(self, name):
        self.name = name  # store the name (e.g., 'I') for reference
        self.shape = [row[:] for row in PIECES[name]]  # deep copy of the base shape from PIECES
        # center the piece horizontally on the grid: take grid width and subtract shape width
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0  # start the piece at the top (row 0)
        self.id = PIECE_ORDER.index(name) + 1  # numeric id used to color locked cells

    def get_cells(self, x_off=0, y_off=0, shape=None):
        """Return a list of (x, y) coordinates for nonzero cells in the piece.
        x_off and y_off shift the returned coordinates relative to the piece origin.
        If `shape` is provided, use that 2D array instead of the piece's current shape.
        """
        cells = []  # accumulator for coordinates
        use_shape = shape if shape is not None else self.shape  # choose which shape data to use
        for dy, row in enumerate(use_shape):  # iterate rows with index dy
            for dx, val in enumerate(row):  # iterate columns with index dx
                if val:  # truthy means this cell is occupied
                    cells.append((self.x + dx + x_off, self.y + dy + y_off))  # append absolute grid cords
        return cells  # list of tuples (x, y)

    def rotate(self):
        return rotate(self.shape)  # return a rotated version of the current shape (doesn't mutate)
    # It does not modify the original shape — it just returns the rotated one.


    def width(self):
        return len(self.shape[0])  # return the width in cells of the current shape i.e the number of column in the first shape(the number of columns)

    def height(self):
        return len(self.shape)  # return the height in cells of the current shape (the number of rows)


class Board:
    def __init__(self, w, h):
        self.w, self.h = w, h  # store the grid dimensions
        self.grid = [[0] * w for _ in range(h)]  # create h rows each with w zeros (0 means empty)

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h  # True if the coordinate lies inside the board bounds

    def valid(self, piece, x_off=0, y_off=0, shape=None):
        # Check every occupied cell of `piece` (optionally with offsets or using a provided shape)
        for x, y in piece.get_cells(x_off, y_off, shape):
            # If any occupied cell is outside or collides with a nonzero grid cell, it's invalid
            if not self.inside(x, y) or (y >= 0 and self.grid[y][x]):
                return False
        return True  # all cells fit and don't collide

    def lock_piece(self, piece):
        # Write the piece id into the board grid for each occupied cell of the piece
        for x, y in piece.get_cells():
            if y >= 0:  # only lock cells that are within the visible grid (y >= 0)
                self.grid[y][x] = piece.id

    def clear_lines(self):
        # Remove rows that are completely filled (no zeros) and return how many lines cleared
        new_grid = [row for row in self.grid if any(v == 0 for v in row)]
        lines_cleared = self.h - len(new_grid)  # difference in rows equals cleared lines
        for _ in range(lines_cleared):
            new_grid.insert(0, [0] * self.w)  # insert empty rows at top to maintain height
        self.grid = new_grid  # replace the grid with the new one
        return lines_cleared  # return the number of cleared rows

    def game_over(self):
        return any(self.grid[0])  # game over if any cell in the top row is nonzero

    def copy(self):
        b = Board(self.w, self.h)  # create a new board with same dimensions
        b.grid = [row[:] for row in self.grid]  # deep copy the grid rows
        return b  # return the copy


class Game:
    def __init__(self):
        self.board = Board(GRID_WIDTH, GRID_HEIGHT)  # create a new board for gameplay
        self.score = 0  # initialize score to 0
        self.paused = False  # paused flag
        self.game_over = False  # game over flag
        self.bag = []  # piece bag used for randomizing piece order
        self.next_piece = self._next_piece()  # pre-generate next piece
        self.current_piece = self._next_piece()  # spawn initial current piece
        self.drop_timer = 0  # timer accumulator in milliseconds for automatic drops
        self.drop_speed = 500  # ms between automatic soft drops by default

    def _next_piece(self):
        # Refill and shuffle the bag when empty, pop one piece from the bag and return a Piece
        if not self.bag:
            self.bag = PIECE_ORDER[:]  # copy the order
            random.shuffle(self.bag)  # shuffle in place for randomness
        return Piece(self.bag.pop())  # remove last entry and construct a Piece

    def spawn_piece(self):
        # Move next_piece to current_piece and pre-generate a new next_piece
        self.current_piece = self.next_piece
        self.next_piece = self._next_piece()
        # Recenter the newly spawned piece horizontally
        self.current_piece.x = GRID_WIDTH // 2 - self.current_piece.width() // 2
        self.current_piece.y = 0  # start at top
        if not self.board.valid(self.current_piece):  # if the new piece collides immediately
            self.game_over = True  # set game over flag

    def move(self, dx, dy):
        # Attempt to move the current piece by dx,dy; return True if moved
        if self.board.valid(self.current_piece, dx, dy):
            self.current_piece.x += dx  # apply horizontal shift
            self.current_piece.y += dy  # apply vertical shift
            return True
        return False

    def hard_drop(self):
        # Drop the piece all the way until it collides, then lock it and continue
        while self.move(0, 1):
            pass  # keep moving down while valid
        self.lock_and_continue()  # lock piece and spawn next

    def rotate(self):
        # Calculate the rotated shape
        new_shape = self.current_piece.rotate()
        # Try common wall kick offsets (0, left, right, more left, more right)
        for dx in [0, -1, 1, -2, 2]:
            if self.board.valid(self.current_piece, dx, 0, new_shape):
                # If valid with this offset, accept rotation: replace shape and shift x by dx
                self.current_piece.shape = new_shape
                self.current_piece.x += dx
                return True
        return False  # no valid rotation found

    def lock_and_continue(self):
        # Lock the current piece into the board grid
        self.board.lock_piece(self.current_piece)
        # Clear filled lines and update score based on number of cleared lines
        lines = self.board.clear_lines()
        # Score table for 0..4 lines cleared at once; if more than 4 use fallback multiplier
        self.score += [0, 100, 300, 500, 800][lines] if lines < 5 else lines * 200
        self.spawn_piece()  # spawn the next piece

    def soft_drop(self):
        # Try to move down by one; if can't, lock and continue
        if not self.move(0, 1):
            self.lock_and_continue()

    def update(self, dt):
        # Advance the game state by dt milliseconds
        if self.paused or self.game_over:
            return  # do nothing if paused or game over
        self.drop_timer += dt  # accumulate time
        if self.drop_timer > self.drop_speed:  # if enough time passed for automatic drop
            self.soft_drop()  # perform a soft drop
            self.drop_timer = 0  # reset the timer

    def reset(self):
        # Reset the whole game state by reinitializing the Game object
        self.__init__()

    def get_ghost_piece_y(self):
        # Create a temporary Piece matching current piece and drop it down until collision to find ghost y position
        piece = Piece(self.current_piece.name)
        piece.shape = [row[:] for row in self.current_piece.shape]
        piece.x = self.current_piece.x
        piece.y = self.current_piece.y
        while self.board.valid(piece, 0, 1):
            piece.y += 1  # move ghost downward while valid
        return piece.y  # return final y of ghost position


# --- UI Functions ---
def draw_grid(screen, board, piece, next_piece, score, paused, game_over):
    # Clear the screen with a dark background color
    screen.fill((30, 30, 30))
    ox, oy = GRID_ORIGIN  # unpack origin offset for drawing grid cells
    # Draw shadow/ghost piece by copying the piece, dropping it until collision and outlining
    ghost_y = piece.y  # store current piece y (not strictly used later)
    temp_piece = Piece(piece.name)  # create a temporary piece instance with same name
    temp_piece.shape = [row[:] for row in piece.shape]  # copy the shape content
    temp_piece.x = piece.x  # copy horizontal position
    temp_piece.y = piece.y  # copy vertical position
    while board.valid(temp_piece, 0, 1):
        temp_piece.y += 1  # drop ghost until it would collide
    for x, y in temp_piece.get_cells():
        if y >= 0:  # only draw visible ghost cells
            # draw a rectangle outline for the ghost using color index 8
            pygame.draw.rect(screen, COLORS[8], (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
    # Draw locked blocks from the board grid
    for y, row in enumerate(board.grid):
        for x, v in enumerate(row):
            if v:  # nonzero -> occupied by a locked piece
                pygame.draw.rect(screen, COLORS[v], (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, (50, 50, 50), (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)  # border
    # Draw current falling piece using its id for color
    for x, y in piece.get_cells():
        if y >= 0:  # only draw if on or below the visible top
            pygame.draw.rect(screen, COLORS[piece.id], (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (255, 255, 255), (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)  # highlight border
    # Draw next piece preview at a fixed UI location
    font = pygame.font.SysFont("consolas", 20)  # create a font for labels and text
    screen.blit(font.render("Next:", True, (255, 255, 255)), (280, 40))  # draw "Next:" label
    for y, row in enumerate(next_piece.shape):
        for x, v in enumerate(row):
            if v:  # if cell is occupied in next piece shape
                pygame.draw.rect(screen, COLORS[next_piece.id], (300 + x * CELL_SIZE, 70 + y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, (255, 255, 255), (300 + x * CELL_SIZE, 70 + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)  # border
    # Draw score label and value
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 0)), (280, 200))
    # If paused, show a paused message
    if paused:
        s = font.render("Paused", True, (255, 0, 0))
        screen.blit(s, (280, 260))
    # If game over, show game over text and restart hint
    if game_over:
        s = font.render("Game Over!", True, (255, 0, 0))
        screen.blit(s, (100, 220))
        s = font.render("Press R to restart", True, (255, 255, 255))
        screen.blit(s, (100, 250))


def main():
    pygame.init()  # initialize all imported pygame modules
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))  # create the main window surface
    clock = pygame.time.Clock()  # create a Clock to manage frame rate
    pygame.display.set_caption("Tetris")  # set the window caption
    game = Game()  # create a Game instance which holds game state
    while True:  # main game loop runs until the program exits
        dt = clock.tick(60)  # limit to ~60 FPS and get the time passed since last tick in ms
        for event in pygame.event.get():  # iterate over pygame events
            if event.type == pygame.QUIT:  # user clicked the window close button
                pygame.quit(); sys.exit()  # clean up pygame and exit the python process
            elif event.type == pygame.KEYDOWN:  # a keyboard key was pressed
                if event.key == pygame.K_p:  # toggle pause on 'p'
                    game.paused = not game.paused
                elif event.key == pygame.K_r and game.game_over:  # restart if 'r' and game was over
                    game.reset()
                if game.paused or game.game_over:  # ignore other key input when paused or game-over
                    continue
                if event.key == pygame.K_LEFT:  # left arrow -> move left
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:  # right arrow -> move right
                    game.move(1, 0)
                elif event.key == pygame.K_DOWN:  # down arrow -> soft drop
                    game.soft_drop()
                elif event.key == pygame.K_UP:  # up arrow -> rotate
                    game.rotate()
                elif event.key == pygame.K_SPACE:  # space -> hard drop
                    game.hard_drop()
        game.update(dt)  # update the game logic with elapsed time dt
        draw_grid(screen, game.board, game.current_piece, game.next_piece, game.score, game.paused, game.game_over)  # draw everything
        pygame.display.flip()  # update the display with what we drew on the screen surface


# --- TESTS ---
def test_rotation():
    # Test that rotation works and wall kicks near left wall
    board = Board(10, 20)  # create a fresh board for the test
    piece = Piece('I')  # create an I piece
    piece.x, piece.y = 0, 0  # position piece at left edge
    # Try rotating multiple times and ensure it's valid or can be kicked right
    for _ in range(4):
        shape = piece.rotate()  # get rotated shape without changing piece yet
        valid = board.valid(piece, 0, 0, shape)  # check if rotation is valid in place
        if not valid:
            # Try to kick rotation one cell to the right
            valid = board.valid(piece, 1, 0, shape)
        assert valid, "Rotation with wall kick failed at left wall"  # assert will raise if invalid
        piece.shape = shape  # accept rotation for next iteration
    print("Rotation test passed.")  # print success message


def test_line_clear():
    board = Board(10, 20)  # fresh board
    # Fill bottom row with nonzero ids to simulate a completed line
    board.grid[-1] = [1]*10
    lines = board.clear_lines()  # call clear_lines which should remove that row
    assert lines == 1, f"Expected 1 line, got {lines}"  # verify exactly one line cleared
    print("Line clear test passed.")


def run_tests():
    test_rotation()  # run rotation test
    test_line_clear()  # run line clear test
    print("All tests passed.")  # final success output


if __name__ == "__main__":
    # If the script is run with argument "test" run tests; otherwise start the game main loop
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        main()
