import pygame
import random
import os

# 초기화
pygame.init()
pygame.mixer.init()  # 사운드 시스템 초기화 추가

# 설정 및 상수
CELL_SIZE = 30
COLS = 10
ROWS = 20
GAME_WIDTH = COLS * CELL_SIZE
SIDEBAR_WIDTH = 200
SCREEN_WIDTH = GAME_WIDTH + SIDEBAR_WIDTH
SCREEN_HEIGHT = ROWS * CELL_SIZE
FPS = 60

# 색상 정의 (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (40, 40, 40)
LIGHT_GRAY = (150, 150, 150)
PANEL_BG = (25, 25, 25)
COLORS = [
    (0, 255, 255),
    (255, 255, 0),
    (128, 0, 128),
    (0, 255, 0),
    (255, 0, 0),
    (0, 0, 255),
    (255, 165, 0),
]

# 테트리스 블록 모양 정의
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]],  # Z
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
]


class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris - Score, Next & BGM")
        self.clock = pygame.time.Clock()
        self.grid = [[0] * COLS for _ in range(ROWS)]
        self.game_over = False
        self.score = 0

        # 폰트 설정
        self.font_title = pygame.font.SysFont("arial", 16, bold=True)
        self.font_score = pygame.font.SysFont("arial", 24, bold=True)

        # 첫 블록과 다음 블록 생성
        self.next_shape_index = random.randint(0, len(SHAPES) - 1)
        self.new_piece()

        # --- 배경음악 설정 추가 ---
        self.bgm_path = "bgm.mp3"  # 재생할 음악 파일 이름
        self.play_bgm()

    def play_bgm(self):
        """배경음악을 불러와 무한 반복 재생하는 함수"""
        # 음악 파일이 실제로 존재할 때만 실행 (에러 방지)
        if os.path.exists(self.bgm_path):
            try:
                pygame.mixer.music.load(self.bgm_path)
                # loops=-1 은 무한 반복 재생을 의미합니다.
                pygame.mixer.music.play(loops=-1)
                pygame.mixer.music.set_volume(0.5)  # 볼륨 설정 (0.0 ~ 1.0)
            except Exception as e:
                print(f"음악을 재생할 수 없습니다: {e}")
        else:
            print(
                f"안내: '{self.bgm_path}' 파일이 폴더에 없습니다. 음악 없이 게임을 시작합니다."
            )

    def new_piece(self):
        self.shape_index = self.next_shape_index
        self.shape = SHAPES[self.shape_index]
        self.color = COLORS[self.shape_index]
        self.next_shape_index = random.randint(0, len(SHAPES) - 1)
        self.piece_x = COLS // 2 - len(self.shape[0]) // 2
        self.piece_y = 0

        if self.check_collision(self.piece_x, self.piece_y, self.shape):
            self.game_over = True
            # 게임 오버 시 음악 정지
            pygame.mixer.music.stop()

    def check_collision(self, nx, ny, shape):
        for r, row in enumerate(shape):
            for c, cell in enumerate(row):
                if cell:
                    if (
                        nx + c < 0
                        or nx + c >= COLS
                        or ny + r >= ROWS
                        or (ny + r >= 0 and self.grid[ny + r][nx + c])
                    ):
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
        rotated = [list(x) for x in zip(*self.shape[::-1])]
        if not self.check_collision(self.piece_x, self.piece_y, rotated):
            self.shape = rotated

    def move(self, dx, dy):
        if not self.check_collision(self.piece_x + dx, self.piece_y + dy, self.shape):
            self.piece_x += dx
            self.piece_y += dy
            return True
        return False

    def draw_sidebar(self):
        pygame.draw.rect(
            self.screen, PANEL_BG, (GAME_WIDTH, 0, SIDEBAR_WIDTH, SCREEN_HEIGHT)
        )
        pygame.draw.line(
            self.screen, LIGHT_GRAY, (GAME_WIDTH, 0), (GAME_WIDTH, SCREEN_HEIGHT), 2
        )

        # SCORE 영역
        score_title = self.font_title.render("SCORE", True, LIGHT_GRAY)
        score_val = self.font_score.render(str(self.score), True, WHITE)
        self.screen.blit(score_title, (GAME_WIDTH + 20, 30))
        self.screen.blit(score_val, (GAME_WIDTH + 20, 55))

        # NEXT PIECE 영역
        next_title = self.font_title.render("NEXT", True, LIGHT_GRAY)
        self.screen.blit(next_title, (GAME_WIDTH + 20, 130))

        box_x, box_y = GAME_WIDTH + 20, 160
        box_w, box_h = 100, 100
        pygame.draw.rect(self.screen, BLACK, (box_x, box_y, box_w, box_h))
        pygame.draw.rect(self.screen, GRAY, (box_x, box_y, box_w, box_h), 1)

        next_shape = SHAPES[self.next_shape_index]
        next_color = COLORS[self.next_shape_index]
        preview_cell_size = 20

        start_x = box_x + (box_w - len(next_shape[0]) * preview_cell_size) // 2
        start_y = box_y + (box_h - len(next_shape) * preview_cell_size) // 2

        for r, row in enumerate(next_shape):
            for c, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.screen,
                        next_color,
                        (
                            start_x + c * preview_cell_size,
                            start_y + r * preview_cell_size,
                            preview_cell_size - 1,
                            preview_cell_size - 1,
                        ),
                    )

    def draw(self):
        self.screen.fill(BLACK)

        for r, row in enumerate(self.grid):
            for c, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        self.screen,
                        cell,
                        (c * CELL_SIZE, r * CELL_SIZE, CELL_SIZE - 1, CELL_SIZE - 1),
                    )

        if not self.game_over:
            for r, row in enumerate(self.shape):
                for c, cell in enumerate(row):
                    if cell:
                        pygame.draw.rect(
                            self.screen,
                            self.color,
                            (
                                (self.piece_x + c) * CELL_SIZE,
                                (self.piece_y + r) * CELL_SIZE,
                                CELL_SIZE - 1,
                                CELL_SIZE - 1,
                            ),
                        )

        for c in range(COLS + 1):
            pygame.draw.line(
                self.screen, GRAY, (c * CELL_SIZE, 0), (c * CELL_SIZE, SCREEN_HEIGHT), 1
            )
        for r in range(ROWS):
            pygame.draw.line(
                self.screen, GRAY, (0, r * CELL_SIZE), (GAME_WIDTH, r * CELL_SIZE), 1
            )

        self.draw_sidebar()
        pygame.display.flip()

    def run(self):
        fall_time = 0
        fall_speed = 400

        while not self.game_over:
            dt = self.clock.tick(FPS)
            fall_time += dt

            if fall_time >= fall_speed:
                if not self.move(0, 1):
                    self.lock_piece()
                fall_time = 0

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
                    elif event.key == pygame.K_SPACE:
                        while self.move(0, 1):
                            pass
                        self.lock_piece()

            self.draw()

        print(f"Game Over! 최종 점수: {self.score}")
        pygame.quit()


if __name__ == "__main__":
    game = Tetris()
    game.run()
