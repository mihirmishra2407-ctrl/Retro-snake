import pygame
import random
import os
import threading
import queue
import time


# ============================================================
# RETRO SNAKE GAME
# Developed by Mihir Mishra
# Visual update: directional snake head with eyes, nostrils and forked tongue
#
# Architecture:
#   Main Thread  -> Pygame / Game Engine / Rendering
#   CLI Thread   -> QCL / Remote Administration
#   Command Queue -> Safe communication between CLI and game
# ============================================================


# ============================================================
# PYGAME INITIALIZATION
# ============================================================

pygame.init()

try:
    pygame.mixer.init()
    AUDIO_AVAILABLE = True
except pygame.error:
    AUDIO_AVAILABLE = False


# ============================================================
# GAME CONFIGURATION
# ============================================================

WINDOW_WIDTH = 600
WINDOW_HEIGHT = 400

SNAKE_SIZE = 10

GRID_WIDTH = WINDOW_WIDTH // SNAKE_SIZE
GRID_HEIGHT = WINDOW_HEIGHT // SNAKE_SIZE

INITIAL_SPEED = 10

# Difficulty speed system:
# Every 20 points, the snake becomes faster.
# Soft Arcade  -> +10% per 20-point milestone, capped after 6 steps.
# Strong Arcade -> +15% per 20-point milestone, capped after 6 steps.
SPEED_MILESTONE = 20
SOFT_SPEED_INCREASE = 0.10
STRONG_SPEED_INCREASE = 0.15
MAX_SPEED_STEPS = 6

LEVEL_2_SCORE = 200
VICTORY_SCORE = 400

TITLE = "Retro Snake Game"

SCORE_FILE = "high_score.txt"

ASSET_DIRECTORY = "Asset"


# ============================================================
# COLORS
# ============================================================

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

GREEN = (0, 255, 0)
DARK_GREEN = (0, 150, 0)

RED = (213, 50, 80)

YELLOW = (255, 255, 102)

CYAN = (0, 255, 255)

GRAY = (120, 120, 120)

DARK_GRAY = (25, 25, 25)

ORANGE = (255, 165, 0)
PURPLE = (130, 70, 180)
BLUE = (70, 110, 255)
BROWN = (120, 70, 30)


# ============================================================
# FRUIT / SCORE SYSTEM
# ============================================================

# Fruit progression is based on the current score.
# Apple is the starter fruit.
#
# 0  - 19  -> Apple      -> 1 point
# 20 - 39  -> Orange     -> 2 points
# 40 - 49  -> Kiwi       -> 5 points
# 50+      -> Blueberry  -> 10 points
#
# Level progression remains unchanged:
# 200 points -> Level 2
# 400 points -> Victory

FRUIT_DATA = {
    "APPLE": {
        "name": "APPLE",
        "points": 1,
        "color": RED
    },
    "ORANGE": {
        "name": "ORANGE",
        "points": 2,
        "color": ORANGE
    },
    "KIWI": {
        "name": "KIWI",
        "points": 5,
        "color": GREEN
    },
    "BLUEBERRY": {
        "name": "BLUEBERRY",
        "points": 10,
        "color": PURPLE
    }
}


# ============================================================
# GLOBAL STATE
# ============================================================

score = 0
high_score = 0

current_level = 1

game_running = True

game_reset_requested = False

remote_level_request = None

qcl_thread = None

command_queue = queue.Queue()

shutdown_event = threading.Event()

# Mandatory pre-game difficulty selection.
# The game cannot start until the player clicks one of the two
# arcade difficulty buttons.
selected_difficulty = None


# ============================================================
# FILE SYSTEM
# ============================================================

def ensure_asset_directory():
    """
    Makes sure the Asset directory exists.
    """

    if not os.path.exists(ASSET_DIRECTORY):
        os.makedirs(ASSET_DIRECTORY)


def load_high_score():
    """
    Load persistent high score.
    """

    if not os.path.exists(SCORE_FILE):
        return 0

    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as file:
            value = file.read().strip()

            if value.isdigit():
                return int(value)

    except (OSError, ValueError):
        pass

    return 0


def save_high_score():
    """
    Save high score safely.
    """

    try:
        with open(SCORE_FILE, "w", encoding="utf-8") as file:
            file.write(str(high_score))

    except OSError as error:
        print(f"[SYSTEM] Unable to save high score: {error}")


def reset_high_score():
    """
    Reset persistent high score.
    """

    global high_score

    high_score = 0
    save_high_score()


# ============================================================
# INITIAL HIGH SCORE
# ============================================================

high_score = load_high_score()


# ============================================================
# WINDOW
# ============================================================

window = pygame.display.set_mode(
    (WINDOW_WIDTH, WINDOW_HEIGHT)
)

pygame.display.set_caption(TITLE)

clock = pygame.time.Clock()


# ============================================================
# FONTS
# ============================================================

FONT_SMALL = pygame.font.SysFont(
    "Courier New",
    14
)

FONT_NORMAL = pygame.font.SysFont(
    "Courier New",
    18
)

FONT_LARGE = pygame.font.SysFont(
    "Courier New",
    28
)

FONT_TITLE = pygame.font.SysFont(
    "Courier New",
    32,
    bold=True
)


# ============================================================
# DIFFICULTY SELECTION
# ============================================================

def select_difficulty():
    """
    Mandatory graphical difficulty selection.

    The player must click either Soft Arcade or Strong Arcade
    before the actual Snake game begins.
    """

    global selected_difficulty

    button_soft = pygame.Rect(
        65,
        205,
        220,
        80
    )

    button_strong = pygame.Rect(
        315,
        205,
        220,
        80
    )

    soft_hover = False
    strong_hover = False

    while selected_difficulty is None and not shutdown_event.is_set():

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                shutdown_event.set()
                return None

            if event.type == pygame.MOUSEMOTION:

                soft_hover = button_soft.collidepoint(
                    event.pos
                )

                strong_hover = button_strong.collidepoint(
                    event.pos
                )

            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button != 1:
                    continue

                if button_soft.collidepoint(event.pos):

                    selected_difficulty = "SOFT"
                    break

                if button_strong.collidepoint(event.pos):

                    selected_difficulty = "STRONG"
                    break

        window.fill(BLACK)

        # Header
        title = FONT_TITLE.render(
            "RETRO SNAKE",
            True,
            GREEN
        )

        title_rect = title.get_rect(
            center=(
                WINDOW_WIDTH // 2,
                65
            )
        )

        window.blit(
            title,
            title_rect
        )

        subtitle = FONT_NORMAL.render(
            "CHOOSE YOUR ARCADE DIFFICULTY",
            True,
            WHITE
        )

        subtitle_rect = subtitle.get_rect(
            center=(
                WINDOW_WIDTH // 2,
                112
            )
        )

        window.blit(
            subtitle,
            subtitle_rect
        )

        instruction = FONT_SMALL.render(
            "CLICK ONE OPTION TO CONTINUE",
            True,
            GRAY
        )

        instruction_rect = instruction.get_rect(
            center=(
                WINDOW_WIDTH // 2,
                145
            )
        )

        window.blit(
            instruction,
            instruction_rect
        )

        # Soft Arcade button
        soft_color = (
            (0, 185, 0)
            if soft_hover
            else DARK_GREEN
        )

        pygame.draw.rect(
            window,
            soft_color,
            button_soft
        )

        pygame.draw.rect(
            window,
            GREEN,
            button_soft,
            2
        )

        soft_title = FONT_NORMAL.render(
            "SOFT ARCADE",
            True,
            WHITE
        )

        soft_title_rect = soft_title.get_rect(
            center=button_soft.center
        )

        window.blit(
            soft_title,
            soft_title_rect
        )

        soft_info = FONT_SMALL.render(
            "+10% SPEED / 20 PTS",
            True,
            WHITE
        )

        soft_info_rect = soft_info.get_rect(
            center=(
                button_soft.centerx,
                button_soft.centery + 24
            )
        )

        window.blit(
            soft_info,
            soft_info_rect
        )

        # Strong Arcade button
        strong_color = (
            (185, 55, 55)
            if strong_hover
            else (120, 35, 35)
        )

        pygame.draw.rect(
            window,
            strong_color,
            button_strong
        )

        pygame.draw.rect(
            window,
            RED,
            button_strong,
            2
        )

        strong_title = FONT_NORMAL.render(
            "STRONG ARCADE",
            True,
            WHITE
        )

        strong_title_rect = strong_title.get_rect(
            center=button_strong.center
        )

        window.blit(
            strong_title,
            strong_title_rect
        )

        strong_info = FONT_SMALL.render(
            "+15% SPEED / 20 PTS",
            True,
            WHITE
        )

        strong_info_rect = strong_info.get_rect(
            center=(
                button_strong.centerx,
                button_strong.centery + 24
            )
        )

        window.blit(
            strong_info,
            strong_info_rect
        )

        pygame.display.flip()

        clock.tick(60)

    return selected_difficulty


# ============================================================
# SOUND MANAGER
# ============================================================

class SoundManager:

    def __init__(self):

        self.enabled = AUDIO_AVAILABLE

        self.music = None

        self.sounds = {}

        self.asset_files = {
            "music": [
                "snakeMusicAsset1.mp3",
                "snakeMusicAsset1.ogg",
                "background.mp3",
                "background.ogg",
            ],

            "move": [
                "snakeMoveAsset.wav",
                "snakeMoveAsset.mp3",
                "move.wav",
            ],

            "level_up": [
                "snakeLevelUpAsset.wav",
                "snakeLevelUpAsset.mp3",
                "levelup.wav",
            ],

            "lose": [
                "snakeLoseAsset.mp3",
                "snakeLoseAsset.wav",
                "lose.wav",
            ],

            "won": [
                "snakeWonAsset.mp3",
                "snakeWonAsset.wav",
                "won.wav",
            ],
        }

        self._load_assets()


    def _find_asset(self, names):

        for name in names:

            path = os.path.join(
                ASSET_DIRECTORY,
                name
            )

            if os.path.exists(path):
                return path

        # Also support assets directly beside this script.
        for name in names:

            if os.path.exists(name):
                return name

        return None


    def _load_assets(self):

        if not self.enabled:
            return

        for category, names in self.asset_files.items():

            path = self._find_asset(names)

            if not path:
                continue

            try:

                if category == "music":

                    self.music = path

                else:

                    self.sounds[category] = pygame.mixer.Sound(path)

            except pygame.error as error:

                print(
                    f"[AUDIO] Could not load {path}: {error}"
                )


    def play_music(self):

        if not self.enabled:
            return

        if not self.music:
            return

        try:

            pygame.mixer.music.load(self.music)

            pygame.mixer.music.play(-1)

        except pygame.error as error:

            print(
                f"[AUDIO] Music error: {error}"
            )


    def stop_music(self):

        if not self.enabled:
            return

        try:
            pygame.mixer.music.stop()
        except pygame.error:
            pass


    def pause_music(self):

        if not self.enabled:
            return

        try:
            pygame.mixer.music.pause()
        except pygame.error:
            pass


    def resume_music(self):

        if not self.enabled:
            return

        try:
            pygame.mixer.music.unpause()
        except pygame.error:
            pass


    def play(self, sound_name):

        if not self.enabled:
            return

        sound = self.sounds.get(sound_name)

        if sound:

            try:
                sound.play()
            except pygame.error:
                pass


    def play_move(self):
        self.play("move")


    def play_level_up(self):
        self.play("level_up")


    def play_lose(self):

        self.stop_music()

        self.play("lose")


    def play_won(self):

        self.stop_music()

        self.play("won")


# ============================================================
# SOUND INSTANCE
# ============================================================

snd = SoundManager()


# ============================================================
# GAME ENGINE
# ============================================================

class SnakeGame:

    def __init__(self):

        self.reset()


    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    def reset(self):

        self.x = WINDOW_WIDTH // 2
        self.y = WINDOW_HEIGHT // 2

        self.x_change = 0
        self.y_change = 0

        self.snake = [
            (self.x, self.y)
        ]

        self.snake_length = 1

        self.score = 0

        self.level = 1

        self.game_over = False
        self.game_won = False

        self.paused = False

        self.started = False

        self.food = self.generate_food()
        self.fruit_type = self.get_fruit_type()

        self.last_direction = None

        self.message = ""

        self.message_timer = 0

        self.music_started = False


    # --------------------------------------------------------
    # FRUIT TYPE
    # --------------------------------------------------------

    def get_fruit_type(self):
        """
        Select the fruit according to the current score.

        Apple is the starter fruit. Once the score reaches each
        threshold, the next fruit becomes active.
        """

        if self.score >= 50:
            return "BLUEBERRY"

        if self.score >= 40:
            return "KIWI"

        if self.score >= 20:
            return "ORANGE"

        return "APPLE"


    # --------------------------------------------------------
    # FOOD GENERATOR
    # --------------------------------------------------------

    def generate_food(self):

        occupied = set(self.snake)

        available = []

        for grid_y in range(GRID_HEIGHT):

            for grid_x in range(GRID_WIDTH):

                position = (
                    grid_x * SNAKE_SIZE,
                    grid_y * SNAKE_SIZE
                )

                if position not in occupied:

                    available.append(position)

        if not available:

            return (
                0,
                0
            )

        return random.choice(available)


    # --------------------------------------------------------
    # START
    # --------------------------------------------------------

    def start(self):

        if not self.music_started:

            snd.play_music()

            self.music_started = True


    # --------------------------------------------------------
    # DIRECTION
    # --------------------------------------------------------

    def change_direction(self, direction):

        if self.paused:
            return

        if self.game_over or self.game_won:
            return

        opposite = {
            "LEFT": "RIGHT",
            "RIGHT": "LEFT",
            "UP": "DOWN",
            "DOWN": "UP"
        }

        if self.last_direction:

            if direction == opposite.get(
                self.last_direction
            ):
                return

        if direction == "LEFT":

            self.x_change = -SNAKE_SIZE
            self.y_change = 0

        elif direction == "RIGHT":

            self.x_change = SNAKE_SIZE
            self.y_change = 0

        elif direction == "UP":

            self.y_change = -SNAKE_SIZE
            self.x_change = 0

        elif direction == "DOWN":

            self.y_change = SNAKE_SIZE
            self.x_change = 0

        else:
            return

        self.last_direction = direction

        self.started = True

        snd.play_move()


    # --------------------------------------------------------
    # PAUSE
    # --------------------------------------------------------

    def toggle_pause(self):

        if self.game_over or self.game_won:
            return

        self.paused = not self.paused

        if self.paused:

            snd.pause_music()

        else:

            snd.resume_music()


    # --------------------------------------------------------
    # SCORE / LEVEL
    # --------------------------------------------------------

    def update_level(self):

        global current_level

        old_level = self.level

        if self.score >= VICTORY_SCORE:

            self.level = 3

        elif self.score >= LEVEL_2_SCORE:

            self.level = 2

        else:

            self.level = 1

        current_level = self.level

        if self.level != old_level:

            if self.level == 2:

                self.message = (
                    "LEVEL 2 UNLOCKED!"
                )

                snd.play_level_up()

            elif self.level == 3:

                self.message = (
                    "400 POINTS - VICTORY!"
                )

                snd.play_won()

                self.game_won = True

                self.x_change = 0
                self.y_change = 0

            self.message_timer = 180


    # --------------------------------------------------------
    # EAT FOOD
    # --------------------------------------------------------

    def eat_food(self):

        global score
        global high_score

        # The fruit currently on the board determines the score.
        fruit = FRUIT_DATA.get(
            self.fruit_type,
            FRUIT_DATA["APPLE"]
        )

        self.snake_length += 1

        self.score += fruit["points"]

        score = self.score

        if self.score > high_score:

            high_score = self.score

            save_high_score()

        # Fruit progression is recalculated from the new score.
        self.fruit_type = self.get_fruit_type()

        self.food = self.generate_food()

        self.update_level()


    # --------------------------------------------------------
    # COLLISION
    # --------------------------------------------------------

    def collision(self):

        # Wall collision

        if (
            self.x < 0
            or self.x >= WINDOW_WIDTH
            or self.y < 0
            or self.y >= WINDOW_HEIGHT
        ):

            return True

        # Self collision

        head = (
            self.x,
            self.y
        )

        if head in self.snake[:-1]:

            return True

        return False


    # --------------------------------------------------------
    # UPDATE
    # --------------------------------------------------------

    def update(self):

        global score

        if self.game_over:
            return

        if self.game_won:
            return

        if self.paused:
            return

        if not self.started:
            return

        self.x += self.x_change
        self.y += self.y_change

        head = (
            self.x,
            self.y
        )

        self.snake.append(head)

        if len(self.snake) > self.snake_length:

            del self.snake[0]

        if self.collision():

            self.game_over = True

            snd.play_lose()

            return

        if head == self.food:

            self.eat_food()

        score = self.score


    # --------------------------------------------------------
    # SPEED
    # --------------------------------------------------------

    def get_speed(self):

        # Speed is controlled by the selected arcade difficulty.
        # Every 20 points adds one speed step.
        # The six-step cap prevents the game from becoming
        # unnecessarily uncontrollable at very high scores.
        return get_speed_for_score(self.score)


    # --------------------------------------------------------
    # DRAW TEXT
    # --------------------------------------------------------

    def draw_text(
        self,
        text,
        font,
        color,
        center
    ):

        surface = font.render(
            text,
            True,
            color
        )

        rectangle = surface.get_rect(
            center=center
        )

        window.blit(
            surface,
            rectangle
        )


    # --------------------------------------------------------
    # DRAW GRID
    # --------------------------------------------------------

    def draw_grid(self):

        for x in range(
            0,
            WINDOW_WIDTH,
            SNAKE_SIZE
        ):

            pygame.draw.line(
                window,
                (15, 15, 15),
                (x, 0),
                (x, WINDOW_HEIGHT)
            )

        for y in range(
            0,
            WINDOW_HEIGHT,
            SNAKE_SIZE
        ):

            pygame.draw.line(
                window,
                (15, 15, 15),
                (0, y),
                (WINDOW_WIDTH, y)
            )


    # --------------------------------------------------------
    # DRAW HUD
    # --------------------------------------------------------

    def draw_hud(self):

        score_text = (
            f"SCORE:{self.score:03d}"
        )

        high_text = (
            f"HIGH:{high_score:03d}"
        )

        level_text = (
            f"LEVEL:{self.level}"
        )

        window.blit(
            FONT_SMALL.render(
                score_text,
                True,
                WHITE
            ),
            (8, 8)
        )

        window.blit(
            FONT_SMALL.render(
                high_text,
                True,
                WHITE
            ),
            (90, 8)
        )

        level_color = (
            GREEN
            if self.level == 1
            else YELLOW
            if self.level == 2
            else CYAN
        )

        window.blit(
            FONT_SMALL.render(
                level_text,
                True,
                level_color
            ),
            (170, 8)
        )

        difficulty_text = (
            "SOFT"
            if selected_difficulty == "SOFT"
            else "STRONG"
        )

        window.blit(
            FONT_SMALL.render(
                difficulty_text,
                True,
                GREEN if selected_difficulty == "SOFT" else RED
            ),
            (245, 8)
        )

        speed_text = (
            f"SPD:{self.get_speed():.1f}"
        )

        window.blit(
            FONT_SMALL.render(
                speed_text,
                True,
                WHITE
            ),
            (330, 8)
        )

        milestone = (
            f"NEXT:"
            f"{LEVEL_2_SCORE if self.level == 1 else VICTORY_SCORE}"
        )

        window.blit(
            FONT_SMALL.render(
                milestone,
                True,
                GRAY
            ),
            (390, 8)
        )

        fruit = FRUIT_DATA.get(
            self.fruit_type,
            FRUIT_DATA["APPLE"]
        )

        fruit_text = (
            f"{fruit['name']}:+{fruit['points']}"
        )

        window.blit(
            FONT_SMALL.render(
                fruit_text,
                True,
                fruit["color"]
            ),
            (455, 8)
        )


    # --------------------------------------------------------
    # DRAW SNAKE HEAD
    # --------------------------------------------------------

    def draw_snake_head(self, x, y):

        """
        Draw a more natural retro snake head instead of a square.

        The head automatically rotates with the current movement
        direction.  The body and game logic remain grid based.
        """

        cx = x + SNAKE_SIZE // 2
        cy = y + SNAKE_SIZE // 2

        # Direction vector.
        direction = self.last_direction

        vectors = {
            "LEFT": (-1, 0),
            "RIGHT": (1, 0),
            "UP": (0, -1),
            "DOWN": (0, 1)
        }

        dx, dy = vectors.get(direction, (1, 0))

        # Perpendicular vector.
        px = -dy
        py = dx

        # Head dimensions are intentionally slightly larger than
        # one grid cell so it feels like an actual snake head.
        nose_distance = 7
        side_distance = 5
        back_distance = 4

        nose = (
            cx + dx * nose_distance,
            cy + dy * nose_distance
        )

        left_front = (
            cx + dx * 3 + px * side_distance,
            cy + dy * 3 + py * side_distance
        )

        right_front = (
            cx + dx * 3 - px * side_distance,
            cy + dy * 3 - py * side_distance
        )

        left_back = (
            cx - dx * back_distance + px * 4,
            cy - dy * back_distance + py * 4
        )

        right_back = (
            cx - dx * back_distance - px * 4,
            cy - dy * back_distance - py * 4
        )

        # Main head silhouette.
        pygame.draw.polygon(
            window,
            DARK_GREEN,
            [
                nose,
                left_front,
                left_back,
                right_back,
                right_front
            ]
        )

        # Soft green inner face.
        inner_nose = (
            cx + dx * 5,
            cy + dy * 5
        )

        inner_left = (
            cx + dx * 2 + px * 3,
            cy + dy * 2 + py * 3
        )

        inner_right = (
            cx + dx * 2 - px * 3,
            cy + dy * 2 - py * 3
        )

        pygame.draw.polygon(
            window,
            GREEN,
            [
                inner_nose,
                inner_left,
                inner_right
            ]
        )

        # Eyes sit toward the front and on opposite sides.
        eye_forward = 2
        eye_side = 3

        left_eye = (
            cx + dx * eye_forward + px * eye_side,
            cy + dy * eye_forward + py * eye_side
        )

        right_eye = (
            cx + dx * eye_forward - px * eye_side,
            cy + dy * eye_forward - py * eye_side
        )

        for eye in (left_eye, right_eye):
            pygame.draw.circle(
                window,
                YELLOW,
                eye,
                2
            )
            pygame.draw.circle(
                window,
                BLACK,
                eye,
                1
            )

        # Small nostrils near the nose.
        nostril_forward = 5
        nostril_side = 2

        left_nostril = (
            cx + dx * nostril_forward + px * nostril_side,
            cy + dy * nostril_forward + py * nostril_side
        )

        right_nostril = (
            cx + dx * nostril_forward - px * nostril_side,
            cy + dy * nostril_forward - py * nostril_side
        )

        pygame.draw.circle(
            window,
            BLACK,
            left_nostril,
            1
        )

        pygame.draw.circle(
            window,
            BLACK,
            right_nostril,
            1
        )

        # Forked tongue extending from the nose.
        tongue_start = (
            cx + dx * 7,
            cy + dy * 7
        )

        tongue_mid = (
            cx + dx * 10,
            cy + dy * 10
        )

        tongue_left = (
            tongue_mid[0] + px * 2,
            tongue_mid[1] + py * 2
        )

        tongue_right = (
            tongue_mid[0] - px * 2,
            tongue_mid[1] - py * 2
        )

        pygame.draw.line(
            window,
            RED,
            tongue_start,
            tongue_mid,
            1
        )

        pygame.draw.line(
            window,
            RED,
            tongue_mid,
            tongue_left,
            1
        )

        pygame.draw.line(
            window,
            RED,
            tongue_mid,
            tongue_right,
            1
        )


    # --------------------------------------------------------
    # DRAW SNAKE
    # --------------------------------------------------------

    def draw_snake(self):

        # Draw the body first.
        for index, segment in enumerate(
            self.snake
        ):

            if index == len(self.snake) - 1:
                continue

            pygame.draw.rect(
                window,
                GREEN,
                [
                    segment[0],
                    segment[1],
                    SNAKE_SIZE,
                    SNAKE_SIZE
                ]
            )

            # Small darker connection detail makes the body
            # look less like independent square blocks.
            pygame.draw.rect(
                window,
                DARK_GREEN,
                [
                    segment[0] + 2,
                    segment[1] + 2,
                    SNAKE_SIZE - 4,
                    SNAKE_SIZE - 4
                ],
                1
            )

        # Draw the natural-looking head last.
        if self.snake:
            head_x, head_y = self.snake[-1]
            self.draw_snake_head(
                head_x,
                head_y
            )


    # --------------------------------------------------------
    # DRAW FOOD
    # --------------------------------------------------------

    def draw_food(self):

        x, y = self.food

        # Keep the fruit centered on the existing 10x10 grid.
        cx = x + SNAKE_SIZE // 2
        cy = y + SNAKE_SIZE // 2

        if self.fruit_type == "APPLE":

            # Retro pixel-art apple.
            pygame.draw.circle(
                window,
                RED,
                (cx - 2, cy + 1),
                4
            )

            pygame.draw.circle(
                window,
                RED,
                (cx + 2, cy + 1),
                4
            )

            pygame.draw.rect(
                window,
                RED,
                (cx - 3, cy, 6, 4)
            )

            pygame.draw.line(
                window,
                BROWN,
                (cx, cy - 3),
                (cx + 1, cy - 6),
                2
            )

            pygame.draw.circle(
                window,
                GREEN,
                (cx + 3, cy - 5),
                2
            )

        elif self.fruit_type == "ORANGE":

            # Orange fruit with a small leaf.
            pygame.draw.circle(
                window,
                ORANGE,
                (cx, cy),
                5
            )

            pygame.draw.circle(
                window,
                YELLOW,
                (cx - 2, cy - 2),
                1
            )

            pygame.draw.line(
                window,
                BROWN,
                (cx, cy - 4),
                (cx + 1, cy - 6),
                1
            )

            pygame.draw.circle(
                window,
                GREEN,
                (cx + 3, cy - 5),
                2
            )

        elif self.fruit_type == "KIWI":

            # Kiwi: green body with darker center/seeds.
            pygame.draw.circle(
                window,
                GREEN,
                (cx, cy),
                5
            )

            pygame.draw.circle(
                window,
                YELLOW,
                (cx, cy),
                2
            )

            for seed_x, seed_y in (
                (cx - 2, cy - 1),
                (cx + 2, cy - 1),
                (cx - 1, cy + 2),
                (cx + 1, cy + 2)
            ):
                pygame.draw.rect(
                    window,
                    BLACK,
                    (seed_x, seed_y, 1, 1)
                )

        else:

            # Blueberry: purple/blue berry with a small crown.
            pygame.draw.circle(
                window,
                PURPLE,
                (cx, cy + 1),
                5
            )

            pygame.draw.circle(
                window,
                BLUE,
                (cx - 2, cy - 1),
                2
            )

            pygame.draw.polygon(
                window,
                GREEN,
                [
                    (cx - 3, cy - 4),
                    (cx, cy - 6),
                    (cx + 3, cy - 4),
                    (cx, cy - 2)
                ]
            )


    # --------------------------------------------------------
    # DRAW CENTER MESSAGE
    # --------------------------------------------------------

    def draw_message(self):

        if self.game_won:

            self.draw_text(
                "VICTORY!",
                FONT_TITLE,
                CYAN,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2 - 45
                )
            )

            self.draw_text(
                "400 POINTS ACHIEVED",
                FONT_NORMAL,
                WHITE,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2
                )
            )

            self.draw_text(
                "R = PLAY AGAIN    ESC = EXIT",
                FONT_SMALL,
                YELLOW,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2 + 35
                )
            )

            return

        if self.game_over:

            self.draw_text(
                "GAME OVER",
                FONT_TITLE,
                RED,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2 - 40
                )
            )

            self.draw_text(
                f"SCORE: {self.score}",
                FONT_NORMAL,
                WHITE,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2
                )
            )

            self.draw_text(
                "R = RESTART    ESC = EXIT",
                FONT_SMALL,
                YELLOW,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2 + 35
                )
            )

            return

        if self.paused:

            self.draw_text(
                "PAUSED",
                FONT_TITLE,
                YELLOW,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2
                )
            )

            self.draw_text(
                "PRESS SPACE TO CONTINUE",
                FONT_SMALL,
                WHITE,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2 + 40
                )
            )

            return

        if not self.started:

            self.draw_text(
                "RETRO SNAKE",
                FONT_TITLE,
                GREEN,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2 - 40
                )
            )

            self.draw_text(
                "USE ARROW KEYS TO START",
                FONT_SMALL,
                WHITE,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2 + 5
                )
            )

            self.draw_text(
                "SPACE = PAUSE",
                FONT_SMALL,
                GRAY,
                (
                    WINDOW_WIDTH // 2,
                    WINDOW_HEIGHT // 2 + 30
                )
            )

        if self.message_timer > 0:

            self.draw_text(
                self.message,
                FONT_NORMAL,
                CYAN,
                (
                    WINDOW_WIDTH // 2,
                    50
                )
            )

            self.message_timer -= 1


    # --------------------------------------------------------
    # DRAW
    # --------------------------------------------------------

    def draw(self):

        window.fill(BLACK)

        self.draw_grid()

        self.draw_food()

        self.draw_snake()

        self.draw_hud()

        self.draw_message()

        pygame.display.flip()


# ============================================================
# QCL
# ============================================================

def get_difficulty_name():

    if selected_difficulty == "STRONG":
        return "STRONG ARCADE"

    return "SOFT ARCADE"


def get_speed_increase_percent():

    if selected_difficulty == "STRONG":
        return int(STRONG_SPEED_INCREASE * 100)

    return int(SOFT_SPEED_INCREASE * 100)


def get_speed_for_score(game_score):

    steps = min(
        game_score // SPEED_MILESTONE,
        MAX_SPEED_STEPS
    )

    increase = (
        STRONG_SPEED_INCREASE
        if selected_difficulty == "STRONG"
        else SOFT_SPEED_INCREASE
    )

    return INITIAL_SPEED * (
        1 + increase * steps
    )


def game_fruit_name():

    if score >= 50:
        return "BLUEBERRY"

    if score >= 40:
        return "KIWI"

    if score >= 20:
        return "ORANGE"

    return "APPLE"


def game_fruit_points():

    fruit_name = game_fruit_name()

    return FRUIT_DATA[fruit_name]["points"]


def print_qcl_help():

    print()
    print("=" * 55)
    print(" RETRO SNAKE — QUESTION COMMAND LINE")
    print("=" * 55)
    print()
    print("GAME   -> Start/reset the game")
    print("RST    -> Reset current game")
    print("RTHS   -> Reset persistent high score")
    print("RTLV   -> Remote level control")
    print("SCR    -> Show current score")
    print("HSCR   -> Show high score")
    print("LVL    -> Show current level")
    print("FRUIT  -> Show current fruit and points")
    print("DIFF   -> Show arcade difficulty and speed system")
    print("QCL    -> Question Command Line")
    print("HELP   -> Show commands")
    print("EXT    -> Exit game")
    print()


def run_qcl_questions():

    while not shutdown_event.is_set():

        print()
        print("--------------- QCL QUESTIONS ---------------")
        print("1. Who created this game?")
        print("2. What are the main features?")
        print("3. How do I play?")
        print("4. What are the milestone levels?")
        print("5. What are the fruits and their points?")
        print("6. What is the arcade difficulty system?")
        print("7. What is the QCL?")
        print("8. Return")
        print("---------------------------------------------")

        try:

            choice = input(
                "Question number :: "
            ).strip()

        except (EOFError, KeyboardInterrupt):

            return

        if choice == "1":

            print()
            print(
                "Answer: This game was developed by "
                "Mihir Mishra using Python and Pygame."
            )

        elif choice == "2":

            print()
            print(
                "Answer: Retro graphics, persistent high score, "
                "multi-threaded QCL, sound management, "
                "level progression and remote administration."
            )

        elif choice == "3":

            print()
            print(
                "Answer: Use the arrow keys to move the snake. "
                "Eat food, grow longer and avoid walls and yourself."
            )

        elif choice == "4":

            print()
            print(
                "Answer:"
            )
            print(
                "Level 1 -> 0-199 points"
            )
            print(
                "Level 2 -> 200-399 points"
            )
            print(
                "Victory -> 400 points"
            )

        elif choice == "5":

            print()
            print("Answer:")
            print("Apple      -> 1 point  | Starter | Score 0-19")
            print("Orange     -> 2 points | Score 20-39")
            print("Kiwi       -> 5 points | Score 40-49")
            print("Blueberry  -> 10 points | Score 50+")

        elif choice == "6":

            print()
            print("Answer:")
            print(
                "The player must click an arcade difficulty before "
                "the game starts."
            )
            print(
                "Soft Arcade -> speed increases by 10% every 20 points."
            )
            print(
                "Strong Arcade -> speed increases by 15% every 20 points."
            )
            print(
                "The speed increase is capped after six 20-point steps."
            )

        elif choice == "7":

            print()
            print(
                "Answer: QCL means Question Command Line. "
                "It provides terminal-based information and "
                "administration while the graphical game is running."
            )

        elif choice == "8":

            return

        else:

            print(
                "Invalid question number."
            )


# ============================================================
# CLI COMMAND HANDLING
# ============================================================

def game_speed_for_qcl():

    return get_speed_for_score(score)


def handle_command(command):

    global high_score

    command = command.strip().upper()

    if not command:
        return


    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if command == "HELP":

        print_qcl_help()


    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    elif command == "SCR":

        print(
            f"[QCL] Current Score: {score}"
        )


    # --------------------------------------------------------
    # HIGH SCORE
    # --------------------------------------------------------

    elif command == "HSCR":

        print(
            f"[QCL] High Score: {high_score}"
        )


    # --------------------------------------------------------
    # LEVEL
    # --------------------------------------------------------

    elif command == "LVL":

        print(
            f"[QCL] Current Level: {current_level}"
        )


    # --------------------------------------------------------
    # GAME RESET
    # --------------------------------------------------------

    elif command == "RST":

        command_queue.put(
            {
                "type": "RESET_GAME"
            }
        )

        print(
            "[QCL] Game reset request sent."
        )


    # --------------------------------------------------------
    # REMOTE HIGH SCORE RESET
    # --------------------------------------------------------

    elif command == "RTHS":

        reset_high_score()

        print(
            "[QCL] Remote High Score Reset."
        )


    # --------------------------------------------------------
    # REMOTE LEVEL
    # --------------------------------------------------------

    elif command == "RTLV":

        print()
        print(
            "Remote Level Control"
        )
        print(
            "1 = Level 1"
        )
        print(
            "2 = Level 2"
        )
        print(
            "3 = Victory State"
        )

        try:

            selected = input(
                "Select level :: "
            ).strip()

        except (EOFError, KeyboardInterrupt):

            return

        if selected in ("1", "2", "3"):

            command_queue.put(
                {
                    "type": "SET_LEVEL",
                    "level": int(selected)
                }
            )

            print(
                f"[QCL] Remote level request: {selected}"
            )

        else:

            print(
                "[QCL] Invalid level."
            )


    # --------------------------------------------------------
    # GAME
    # --------------------------------------------------------

    elif command == "GAME":

        command_queue.put(
            {
                "type": "RESET_GAME"
            }
        )

        print(
            "[QCL] New game request sent."
        )


    # --------------------------------------------------------
    # FRUIT
    # --------------------------------------------------------

    elif command == "FRUIT":

        print()
        print("[QCL] Current Fruit System")
        print("--------------------------")
        print("APPLE      -> 1 point  | Starter | Score 0-19")
        print("ORANGE     -> 2 points | Score 20-39")
        print("KIWI       -> 5 points | Score 40-49")
        print("BLUEBERRY  -> 10 points | Score 50+")
        print()
        print(
            f"[QCL] Current fruit: {game_fruit_name()}"
        )
        print(
            f"[QCL] Current fruit value: {game_fruit_points()} point(s)"
        )


    # --------------------------------------------------------
    # DIFFICULTY
    # --------------------------------------------------------

    elif command == "DIFF":

        print()
        print("[QCL] Arcade Difficulty System")
        print("-------------------------------")
        print(
            f"Selected mode: {get_difficulty_name()}"
        )
        print(
            f"Speed increase: +{get_speed_increase_percent()}% every "
            f"{SPEED_MILESTONE} points"
        )
        print(
            "Speed steps: 0, 20, 40, 60, 80, 100, 120+"
        )
        print(
            f"Current speed: {game_speed_for_qcl():.1f}"
        )


    # --------------------------------------------------------
    # QUESTIONS
    # --------------------------------------------------------

    elif command == "QCL":

        run_qcl_questions()


    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    elif command == "EXT":

        command_queue.put(
            {
                "type": "EXIT"
            }
        )

        print(
            "[QCL] Exit request sent."
        )

        return False


    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

    else:

        print(
            "[QCL] Invalid command."
        )

    return True


# ============================================================
# QCL THREAD
# ============================================================

def input_command():

    print()
    print("=" * 55)
    print(" RETRO SNAKE QCL ONLINE")
    print("=" * 55)

    print(
        "Type HELP for available commands."
    )

    print()

    while not shutdown_event.is_set():

        try:

            command = input(
                "QCL:: "
            )

        except (EOFError, KeyboardInterrupt):

            command_queue.put(
                {
                    "type": "EXIT"
                }
            )

            break

        try:

            keep_running = handle_command(
                command
            )

        except Exception as error:

            print(
                f"[QCL ERROR] {error}"
            )

            keep_running = True

        if not keep_running:

            break


# ============================================================
# MAIN COMMAND PROCESSOR
# ============================================================

def process_commands(game):

    global game_reset_requested

    while True:

        try:

            command = command_queue.get_nowait()

        except queue.Empty:

            break

        command_type = command.get("type")


        # ----------------------------------------------------
        # RESET GAME
        # ----------------------------------------------------

        if command_type == "RESET_GAME":

            game.reset()

            game.start()

            print(
                "[GAME] Reset completed."
            )


        # ----------------------------------------------------
        # SET LEVEL
        # ----------------------------------------------------

        elif command_type == "SET_LEVEL":

            requested_level = command.get(
                "level",
                1
            )

            if requested_level == 1:

                game.score = 0
                game.level = 1

            elif requested_level == 2:

                game.score = LEVEL_2_SCORE
                game.level = 2

            elif requested_level == 3:

                game.score = VICTORY_SCORE
                game.level = 3
                game.game_won = True
                game.x_change = 0
                game.y_change = 0

            # Keep fruit selection synchronized with the remote
            # score change without changing level mechanics.
            game.fruit_type = game.get_fruit_type()

            game.message = (
                f"REMOTE LEVEL {requested_level}"
            )

            game.message_timer = 180

            print(
                f"[GAME] Remote level changed to "
                f"{requested_level}."
            )


        # ----------------------------------------------------
        # EXIT
        # ----------------------------------------------------

        elif command_type == "EXIT":

            shutdown_event.set()


# ============================================================
# KEYBOARD EVENT PROCESSOR
# ============================================================

def process_events(game):

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            shutdown_event.set()

            return


        if event.type != pygame.KEYDOWN:
            continue


        # ----------------------------------------------------
        # ESC
        # ----------------------------------------------------

        if event.key == pygame.K_ESCAPE:

            if game.game_over or game.game_won:

                shutdown_event.set()

            else:

                shutdown_event.set()

            continue


        # ----------------------------------------------------
        # SPACE
        # ----------------------------------------------------

        if event.key == pygame.K_SPACE:

            game.toggle_pause()

            continue


        # ----------------------------------------------------
        # RESTART
        # ----------------------------------------------------

        if event.key == pygame.K_r:

            if game.game_over or game.game_won:

                game.reset()

                game.start()

            continue


        # ----------------------------------------------------
        # MOVEMENT
        # ----------------------------------------------------

        if event.key == pygame.K_LEFT:

            game.change_direction(
                "LEFT"
            )

        elif event.key == pygame.K_RIGHT:

            game.change_direction(
                "RIGHT"
            )

        elif event.key == pygame.K_UP:

            game.change_direction(
                "UP"
            )

        elif event.key == pygame.K_DOWN:

            game.change_direction(
                "DOWN"
            )


# ============================================================
# MAIN GAME ENGINE
# ============================================================

def game_loop():

    game = SnakeGame()

    game.start()

    accumulator = 0

    previous_time = time.perf_counter()

    while not shutdown_event.is_set():

        current_time = time.perf_counter()

        delta_time = (
            current_time
            - previous_time
        )

        previous_time = current_time

        accumulator += delta_time


        # ----------------------------------------------------
        # PROCESS QCL COMMANDS
        # ----------------------------------------------------

        process_commands(game)


        # ----------------------------------------------------
        # PYGAME EVENTS
        # ----------------------------------------------------

        process_events(game)


        # ----------------------------------------------------
        # UPDATE GAME
        # ----------------------------------------------------

        step_time = 1.0 / game.get_speed()

        while accumulator >= step_time:

            game.update()

            accumulator -= step_time


        # ----------------------------------------------------
        # DRAW
        # ----------------------------------------------------

        game.draw()


        # ----------------------------------------------------
        # SMALL CPU DELAY
        # ----------------------------------------------------

        clock.tick(60)


    # --------------------------------------------------------
    # SHUTDOWN
    # --------------------------------------------------------

    snd.stop_music()

    pygame.quit()


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

def main():

    global qcl_thread

    ensure_asset_directory()

    # --------------------------------------------------------
    # MANDATORY ARCADE DIFFICULTY SELECTION
    # --------------------------------------------------------

    difficulty = select_difficulty()

    if difficulty is None:

        shutdown_event.set()

        if pygame.get_init():
            pygame.quit()

        print()
        print(
            "[SYSTEM] No arcade difficulty selected. "
            "Retro Snake terminated."
        )

        return

    print()
    print("=" * 55)
    print("        RETRO SNAKE GAME")
    print("        Developed by Mihir Mishra")
    print("=" * 55)
    print()
    print(
        f"Persistent High Score: {high_score}"
    )
    print(
        "Milestones: 200 = Level 2 | 400 = Victory"
    )
    print(
        "Fruits: Apple=1 | Orange=2 | Kiwi=5 | Blueberry=10"
    )
    print(
        "Fruit progression: 0 -> Apple | 20 -> Orange | "
        "40 -> Kiwi | 50 -> Blueberry"
    )
    print(
        f"Arcade mode: {get_difficulty_name()} "
        f"(+{get_speed_increase_percent()}% speed / 20 points)"
    )
    print()

    # --------------------------------------------------------
    # START QCL THREAD
    # --------------------------------------------------------

    qcl_thread = threading.Thread(
        target=input_command,
        name="QCL-Thread",
        daemon=True
    )

    qcl_thread.start()

    # --------------------------------------------------------
    # START MAIN GAME
    # --------------------------------------------------------

    try:

        game_loop()

    except KeyboardInterrupt:

        print(
            "\n[SYSTEM] Keyboard interruption."
        )

    except Exception as error:

        print(
            f"\n[SYSTEM ERROR] {error}"
        )

    finally:

        shutdown_event.set()

        save_high_score()

        if pygame.get_init():

            pygame.quit()

        print()
        print(
            "[SYSTEM] Retro Snake terminated."
        )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()