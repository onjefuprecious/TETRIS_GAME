import pygame
import random
import sys

# --- CONFIG ---
WINDOW_WIDTH, WINDOW_HEIGHT = 600, 600
GRID_WIDTH, GRID_HEIGHT = 10, 20
CELL_SIZE = 24
GRID_ORIGIN = (20, 40)

COLORS = [
    (0, 0, 0),       # 0: Empty
    (0, 240, 240),   # 1: I
    (0, 0, 240),     # 2: J
    (240, 160, 0),   # 3: L
    (240, 240, 0),   # 4: O
    (0, 100, 0),     # 5: R
    (128, 0, 128),   # 6: S
    (100, 0, 0),     # 7: T
    (240, 0, 0),     # 8: U
    (255, 255, 255), # 9: V
    (0, 128, 128),     # 10: W
    (0, 240, 0),     # 11: X
    (128, 240, 160), # 12: Y
    (240, 0, 128),   # 13: Z
    (160, 240, 100), # 14: A
    (128, 128, 128)  # 8: Ghost piece
]

PIECES = {
    'I': [[1, 1, 1, 1]],
    'J': [[2, 0, 0], [2, 2, 2]],
    'L': [[0, 0, 3], [3, 3, 3]],
    'O': [[4, 4], [4, 4]],
    'R': [[0, 5, 5], [5, 5, 0]],
    'S': [[0, 10, 0], [6, 6, 6]],
    'T': [[7, 7, 0], [0, 7, 7]],
    'U': [[2, 2, 2, 3], [2, 2, 2, 3]],
    'V': [[3, 0], [3, 0]],
    'W': [[1, 0]],
    'X': [[0, 2], [2, 2]],
    'Y': [[0, 3], [0, 3], [0, 3]],
    'Z': [[9, 4], [1, 1],[2, 2]],
    'A': [[3, 3, 3], [3, 3, 3], [3, 3, 3]]
}

PIECE_ORDER = ['I', 'J', 'L', 'O', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'A']

def rotate(shape):
    """Rotate a shape matrix clockwise."""
    return [list(row) for row in zip(*shape[::-1])]

class Piece:
    def __init__(self, name):
        self.name = name
        self.shape = [row[:] for row in PIECES[name]]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
        self.id = PIECE_ORDER.index(name) + 1

    def get_cells(self, x_off=0, y_off=0, shape=None):
        """Return list of (x, y) for nonzero cells."""
        cells = []
        use_shape = shape if shape is not None else self.shape
        for dy, row in enumerate(use_shape):
            for dx, val in enumerate(row):
                if val:
                    cells.append((self.x + dx + x_off, self.y + dy + y_off))
        return cells

    def rotate(self):
        return rotate(self.shape)

    def width(self):
        return len(self.shape[0])

    def height(self):
        return len(self.shape)

class Board:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.grid = [[0] * w for _ in range(h)]

    def inside(self, x, y):
        return 0 <= x < self.w and 0 <= y < self.h

    def valid(self, piece, x_off=0, y_off=0, shape=None):
        for x, y in piece.get_cells(x_off, y_off, shape):
            if not self.inside(x, y) or (y >= 0 and self.grid[y][x]):
                return False
        return True

    def lock_piece(self, piece):
        for x, y in piece.get_cells():
            if y >= 0:
                self.grid[y][x] = piece.id

    def clear_lines(self):
        new_grid = [row for row in self.grid if any(v == 0 for v in row)]
        lines_cleared = self.h - len(new_grid)
        for _ in range(lines_cleared):
            new_grid.insert(0, [0] * self.w)
        self.grid = new_grid
        return lines_cleared

    def game_over(self):
        return any(self.grid[0])

    def copy(self):
        b = Board(self.w, self.h)
        b.grid = [row[:] for row in self.grid]
        return b

class Game:
    def __init__(self):
        self.board = Board(GRID_WIDTH, GRID_HEIGHT)
        self.score = 0
        self.paused = False
        self.game_over = False
        self.bag = []
        self.next_piece = self._next_piece()
        self.current_piece = self._next_piece()
        self.drop_timer = 0
        self.drop_speed = 500  # ms

    def _next_piece(self):
        if not self.bag:
            self.bag = PIECE_ORDER[:]
            random.shuffle(self.bag)
        return Piece(self.bag.pop())

    def spawn_piece(self):
        self.current_piece = self.next_piece
        self.next_piece = self._next_piece()
        self.current_piece.x = GRID_WIDTH // 2 - self.current_piece.width() // 2
        self.current_piece.y = 0
        if not self.board.valid(self.current_piece):
            self.game_over = True

    def move(self, dx, dy):
        if self.board.valid(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def hard_drop(self):
        while self.move(0, 1):
            pass
        self.lock_and_continue()

    def rotate(self):
        new_shape = self.current_piece.rotate()
        # Try wall kicks
        for dx in [0, -1, 1, -2, 2]:
            if self.board.valid(self.current_piece, dx, 0, new_shape):
                self.current_piece.shape = new_shape
                self.current_piece.x += dx
                return True
        return False

    def lock_and_continue(self):
        self.board.lock_piece(self.current_piece)
        lines = self.board.clear_lines()
        self.score += [0, 100, 300, 500, 800][lines] if lines < 5 else lines * 200
        self.spawn_piece()

    def soft_drop(self):
        if not self.move(0, 1):
            self.lock_and_continue()

    def update(self, dt):
        if self.paused or self.game_over:
            return
        self.drop_timer += dt
        if self.drop_timer > self.drop_speed:
            self.soft_drop()
            self.drop_timer = 0

    def reset(self):
        self.__init__()

    def get_ghost_piece_y(self):
        piece = Piece(self.current_piece.name)
        piece.shape = [row[:] for row in self.current_piece.shape]
        piece.x = self.current_piece.x
        piece.y = self.current_piece.y
        while self.board.valid(piece, 0, 1):
            piece.y += 1
        return piece.y

# --- UI Functions ---
def draw_grid(screen, board, piece, next_piece, score, paused, game_over):
    screen.fill((30, 30, 30))
    ox, oy = GRID_ORIGIN
    # Draw shadow/ghost piece
    ghost_y = piece.y
    temp_piece = Piece(piece.name)
    temp_piece.shape = [row[:] for row in piece.shape]
    temp_piece.x = piece.x
    temp_piece.y = piece.y
    while board.valid(temp_piece, 0, 1):
        temp_piece.y += 1
    for x, y in temp_piece.get_cells():
        if y >= 0:
            pygame.draw.rect(screen, COLORS[8], (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
    # Draw locked blocks
    for y, row in enumerate(board.grid):
        for x, v in enumerate(row):
            if v:
                pygame.draw.rect(screen, COLORS[v], (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, (50, 50, 50), (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
    # Draw current piece
    for x, y in piece.get_cells():
        if y >= 0:
            pygame.draw.rect(screen, COLORS[piece.id], (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, (255, 255, 255), (ox + x * CELL_SIZE, oy + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
    # Draw next piece
    font = pygame.font.SysFont("consolas", 20)
    screen.blit(font.render("Next:", True, (255, 255, 255)), (280, 40))
    for y, row in enumerate(next_piece.shape):
        for x, v in enumerate(row):
            if v:
                pygame.draw.rect(screen, COLORS[next_piece.id], (300 + x * CELL_SIZE, 70 + y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(screen, (255, 255, 255), (300 + x * CELL_SIZE, 70 + y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
    # Draw score
    screen.blit(font.render(f"Score: {score}", True, (255, 255, 0)), (280, 200))
    # Pause/game over
    if paused:
        s = font.render("Paused", True, (255, 0, 0))
        screen.blit(s, (280, 260))
    if game_over:
        s = font.render("Game Over!", True, (255, 0, 0))
        screen.blit(s, (100, 220))
        s = font.render("Press R to restart", True, (255, 255, 255))
        screen.blit(s, (100, 250))

def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()
    pygame.display.set_caption("Tetris")
    game = Game()
    while True:
        dt = clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    game.paused = not game.paused
                elif event.key == pygame.K_r and game.game_over:
                    game.reset()
                if game.paused or game.game_over:
                    continue
                if event.key == pygame.K_LEFT:
                    game.move(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    game.move(1, 0)
                elif event.key == pygame.K_DOWN:
                    game.soft_drop()
                elif event.key == pygame.K_UP:
                    game.rotate()
                elif event.key == pygame.K_SPACE:
                    game.hard_drop()
        game.update(dt)
        draw_grid(screen, game.board, game.current_piece, game.next_piece, game.score, game.paused, game.game_over)
        pygame.display.flip()

# --- TESTS ---
def test_rotation():
    # Test that rotation works and wall kicks
    board = Board(10, 20)
    piece = Piece('I')
    piece.x, piece.y = 0, 0
    # Try rotating near the left wall
    for _ in range(4):
        shape = piece.rotate()
        valid = board.valid(piece, 0, 0, shape)
        if not valid:
            # Try to kick right
            valid = board.valid(piece, 1, 0, shape)
        assert valid, "Rotation with wall kick failed at left wall"
        piece.shape = shape
    print("Rotation test passed.")

def test_line_clear():
    board = Board(10, 20)
    # Fill bottom row
    board.grid[-1] = [1]*10
    lines = board.clear_lines()
    assert lines == 1, f"Expected 1 line, got {lines}"
    print("Line clear test passed.")

def run_tests():
    test_rotation()
    test_line_clear()
    print("All tests passed.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_tests()
    else:
        main()