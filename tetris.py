import pygame
import random

# 초기화
pygame.init()

# 설정 및 상수
CELL_SIZE = 30
COLS = 10
ROWS = 20
SCREEN_WIDTH = COLS * CELL_SIZE
SCREEN_HEIGHT = ROWS * CELL_SIZE
FPS = 60

# 색상 정의 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
COLORS = [
    (0, 255, 255),  # 하늘색 (I)
    (255, 255, 0),  # 노란색 (O)
    (128, 0, 128),  # 보라색 (T)
    (0, 255, 0),    # 녹색 (S)
    (255, 0, 0),    # 빨간색 (Z)
    (0, 0, 255),    # 파란색 (J)
    (255, 165, 0)   # 주황색 (L)
]

# 테트리스 블록 모양 정의 (4x4 Matrix 구조)
SHAPES = [
    [[1, 1, 1, 1]], # I
    [[1, 1], [1, 1]], # O
    [[0, 1, 0], [1, 1, 1]], # T
    [[0, 1, 1], [1, 1, 0]], # S
    [[1, 1, 0], [0, 1, 1]], # Z
    [[1, 0, 0], [1, 1, 1]], # J
    [[0, 0, 1], [1, 1, 1]]  # L
]

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris")
        self.clock = pygame.time.Clock()
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.game_over = False
        self.score = 0
        self.new_piece()

    def new_piece(self):
        self.shape_index = random.randint(0, len(SHAPES) - 1)
        self.shape = SHAPES[self.shape_index]
        self.color = COLORS[self.shape_index]
        # 블록 시작 위치 (중앙 상단)
        self.piece_x = COLS // 2 - len(self.shape[0]) // 2
        self.piece_y = 0

        if self.check_collision(self.piece_x, self.piece_y, self.shape):
            self.game_over = True

    def check_collision(self, nx, ny, shape):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    if (nx + c < 0 or nx + c >= COLS or 
                        ny + r >= ROWS or 
                        (ny + r >= 0 and self.grid[ny + r][nx + c])):
                        return True
        return False

    def lock_piece(self):
        for r, row in enumerate(self.shape):
            for c, cell in enumerate(row):
                if cell:
                    if self.piece_y + r >= 0:
                        self.grid[self.piece_y + r][self.piece_x + c] = self.color
        self.clear_lines()
        self.new_piece()

    def clear_lines(self):
        new_grid = [row for row in self.grid if any(cell == 0 for cell in row)]
        cleared = ROWS - len(new_grid)
        self.score += cleared * 100
        while len(new_grid) < ROWS:
            new_grid.insert(0, [0] * COLS)
        self.grid = new_grid

    def rotate_piece(self):
        # 2차원 리스트 시계방향 회전
        rotated = [list(x) for x in zip(*self.shape[::-1])]
        if not self.check_collision(self.piece_x, self.piece_y, rotated):
            self.shape = rotated

    def move(self, dx, dy):
        if not self.check_collision(self.piece_x + dx, self.piece_y + dy, self.shape):
            self.piece_x += dx
            self.piece_y += dy
            return True
        return False

    def draw(self):
        self.screen.fill(BLACK)
        
        # 1. 고정된 그리드 블록 그리기
        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(self.screen, cell, (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1))
        
        # 2. 현재 떨어지는 블록 그리기
        if not self.game_over:
            for r, row in enumerate(self.shape):
                for c, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(self.screen, self.color, 
                                         ((self.piece_x + c) * CELL_SIZE, (self.piece_y + r) * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1))
        
        # 3. 격자 배경 선 그리기
        for c in range(COLS):
            pygame.draw.line(self.screen, GRAY, (c * CELL_SIZE, 0), (c * CELL_SIZE, SCREEN_HEIGHT), 1)
        for r in range(ROWS):
            pygame.draw.line(self.screen, GRAY, (0, r * CELL_SIZE), (SCREEN_WIDTH, r * CELL_SIZE), 1)

        pygame.display.flip()

    def run(self):
        fall_time = 0
        fall_speed = 500 # 블록이 떨어지는 속도 (ms 단위)

        while not self.game_over:
            dt = self.clock.tick(FPS)
            fall_time += dt

            # 일정 시간마다 블록 아래로 떨어뜨리기
            if fall_time >= fall_speed:
                if not self.move(0, 1):
                    self.lock_piece()
                fall_time = 0

            # 이벤트 처리 (키보드 입력)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.move(0, 1)
                    elif event.key == pygame.K_UP:
                        self.rotate_piece()
                    elif event.key == pygame.K_SPACE: # 즉시 떨어뜨리기
                        while self.move(0, 1):
                            pass
                        self.lock_piece()

            self.draw()

        print(f"Game Over! 최종 점수: {self.score}")
        pygame.quit()

if __name__ == "__main__":
    game = Tetris()
    game.run()