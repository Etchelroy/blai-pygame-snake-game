import pygame
import random
import sys
import os

# ---------------------------------------------------------------------------
# Environment setup for headless / CI environments
# ---------------------------------------------------------------------------
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')

pygame.init()

# ---------------------------------------------------------------------------
# Grid / window constants
# ---------------------------------------------------------------------------
CELL   = 20          # Pixel size of each grid cell
COLS   = 30          # Number of columns in the grid
ROWS   = 24          # Number of rows in the grid
WIDTH  = COLS * CELL
HEIGHT = ROWS * CELL

FPS_BASE   = 8       # Starting FPS; increases with score
MAX_FRAMES = 1000    # Safety frame cap for headless / test runs

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
WHITE    = (255, 255, 255)
BLACK    = (0,   0,   0)
GREEN    = (0,   200, 0)
DKGREEN  = (0,   140, 0)
RED      = (220, 50,  50)
GRAY     = (40,  40,  40)
YELLOW   = (255, 220, 0)
ORANGE   = (255, 165, 0)   # Banana colour
DARKGRAY = (80,  80,  80)  # Barrier colour

# ---------------------------------------------------------------------------
# Banana / barrier spawn tuning
# ---------------------------------------------------------------------------
BANANA_SPAWN_CHANCE   = 0.005   # Per-tick probability a banana spawns (if none present)
BARRIER_SPAWN_CHANCE  = 0.003   # Per-tick probability a new barrier spawns
MAX_BARRIERS          = 8       # Upper limit on simultaneous barrier cells
BANANA_SHRINK_TICKS   = 3       # How many segments to remove after eating a banana
                                 # (one removal per game tick, spread across this many ticks)

# ---------------------------------------------------------------------------
# Pygame surface / clock setup
# ---------------------------------------------------------------------------
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()

# ---------------------------------------------------------------------------
# Font initialisation (gracefully degrades if fonts unavailable)
# ---------------------------------------------------------------------------
font_big = font_med = font_sm = None
try:
    pygame.font.init()
    if pygame.font.get_init():
        default_font = pygame.font.get_default_font()
        font_big = pygame.font.Font(default_font, 48)
        font_med = pygame.font.Font(default_font, 28)
        font_sm  = pygame.font.Font(default_font, 22)
except Exception:
    pass  # Fonts unavailable; text rendering calls will be no-ops


# ---------------------------------------------------------------------------
# Helper: pick a random free grid cell
# ---------------------------------------------------------------------------
def random_free_cell(occupied: set) -> tuple | None:
    """Return a random cell not in *occupied*, or None if the grid is full."""
    all_cells = [(x, y) for x in range(COLS) for y in range(ROWS)]
    free = [c for c in all_cells if c not in occupied]
    return random.choice(free) if free else None


# ---------------------------------------------------------------------------
# Helper: draw a filled grid cell, optionally with a smaller inner rectangle
# ---------------------------------------------------------------------------
def draw_cell(surface, pos, color, inner=None):
    """Draw a grid cell at *pos* (col, row) with *color*.

    If *inner* is provided a 4-px-inset rectangle is drawn over the cell in
    that colour, giving a simple bordered look for the snake head.
    """
    x, y = pos[0] * CELL, pos[1] * CELL
    pygame.draw.rect(surface, color, (x, y, CELL, CELL))
    if inner:
        pygame.draw.rect(surface, inner, (x + 2, y + 2, CELL - 4, CELL - 4))


# ---------------------------------------------------------------------------
# Helper: render centred text onto *surface*
# ---------------------------------------------------------------------------
def draw_text_centered(surface, text, font, color, cy):
    """Blit *text* horizontally centred at vertical position *cy*."""
    if font is None:
        return
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, cy))
    surface.blit(surf, rect)


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------
def game_loop():
    """Run one full game and return (score, reason_string) when it ends."""

    # ── Snake state ──────────────────────────────────────────────────────────
    snake     = [(COLS // 2, ROWS // 2),
                 (COLS // 2 - 1, ROWS // 2),
                 (COLS // 2 - 2, ROWS // 2)]
    direction = (1, 0)
    next_dir  = (1, 0)

    # ── Food (red apple) ─────────────────────────────────────────────────────
    occupied = set(snake)
    food = random_free_cell(occupied)

    # ── Banana state ─────────────────────────────────────────────────────────
    # banana        : grid position of the current banana, or None
    # shrink_pending: number of segments still to be removed (one per tick)
    #                 after the snake has eaten a banana.
    banana         = None   # type: tuple | None
    shrink_pending = 0      # segments left to strip this banana effect

    # ── Barrier state ────────────────────────────────────────────────────────
    # barriers: set of grid cells that are impassable obstacles.
    barriers: set = set()

    score       = 0
    frame_count = 0

    while True:
        # ── Frame-rate scales with score ─────────────────────────────────────
        fps = FPS_BASE + score // 3
        clock.tick(fps)
        frame_count += 1

        # Safety cap for headless / automated test environments
        if frame_count >= MAX_FRAMES:
            return score, "timeout"

        # ── Event handling ───────────────────────────────────────────────────
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                # Prevent 180-degree reversal
                if event.key == pygame.K_UP    and direction != (0,  1):
                    next_dir = (0, -1)
                if event.key == pygame.K_DOWN  and direction != (0, -1):
                    next_dir = (0,  1)
                if event.key == pygame.K_LEFT  and direction != (1,  0):
                    next_dir = (-1, 0)
                if event.key == pygame.K_RIGHT and direction != (-1, 0):
                    next_dir = (1,  0)

        # ── Movement ─────────────────────────────────────────────────────────
        direction = next_dir
        head = (snake[0][0] + direction[0], snake[0][1] + direction[1])

        # Wall collision
        if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS):
            return score, "wall"

        # Self collision
        if head in snake:
            return score, "self"

        # Barrier collision — hitting any barrier cell ends the game
        if head in barriers:
            return score, "barrier"

        # Advance the snake: always insert new head …
        snake.insert(0, head)

        # … remove tail only if not growing from food
        if food is not None and head == food:
            # Eat food: grow snake and spawn new food
            score += 1
            occupied = set(snake) | barriers
            food = random_free_cell(occupied)
        else:
            snake.pop()

        # ── Banana effect: gradual shrink ─────────────────────────────────────
        # Each tick while shrink_pending > 0, remove one tail segment.
        # The snake must keep at least 1 segment to remain alive.
        if shrink_pending > 0:
            if len(snake) > 1:
                snake.pop()           # Remove one tail segment this tick
            shrink_pending -= 1       # Decrement remaining removals

        # ── Banana collision ──────────────────────────────────────────────────
        if banana is not None and head == banana:
            # Snake ate the banana: schedule gradual shrink over several ticks
            shrink_pending = BANANA_SHRINK_TICKS   # e.g. remove 3 segments, 1/tick
            banana = None                           # Banana disappears immediately

        # ── Banana spawn ──────────────────────────────────────────────────────
        # At most one banana on screen at a time; random chance each tick.
        if banana is None and random.random() < BANANA_SPAWN_CHANCE:
            occupied = set(snake) | barriers | ({food} if food else set())
            banana = random_free_cell(occupied)

        # ── Barrier spawn ─────────────────────────────────────────────────────
        # A new barrier cell may appear each tick up to MAX_BARRIERS total.
        # Barriers never spawn on the snake, food, or banana.
        if len(barriers) < MAX_BARRIERS and random.random() < BARRIER_SPAWN_CHANCE:
            occupied = set(snake) | barriers | ({food} if food else set()) | ({banana} if banana else set())
            new_barrier = random_free_cell(occupied)
            if new_barrier is not None:
                barriers.add(new_barrier)

        # ── Rendering ────────────────────────────────────────────────────────
        screen.fill(GRAY)

        # Grid lines
        for x in range(0, WIDTH, CELL):
            pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL):
            pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

        # Draw barriers as dark-grey filled cells with a lighter border
        for bpos in barriers:
            draw_cell(screen, bpos, DARKGRAY)
            bx, by = bpos[0] * CELL, bpos[1] * CELL
            pygame.draw.rect(screen, (120, 120, 120), (bx + 1, by + 1, CELL - 2, CELL - 2), 2)

        # Draw food (red circle with yellow highlight)
        if food is not None:
            draw_cell(screen, food, RED)
            fx = food[0] * CELL + CELL // 2
            fy = food[1] * CELL + CELL // 2
            pygame.draw.circle(screen, YELLOW, (fx, fy), CELL // 4)

        # Draw banana as an orange cell with a small "B" marker
        if banana is not None:
            draw_cell(screen, banana, ORANGE)
            if font_sm is not None:
                b_surf = font_sm.render("B", True, BLACK)
                bx = banana[0] * CELL + (CELL - b_surf.get_width()) // 2
                by = banana[1] * CELL + (CELL - b_surf.get_height()) // 2
                screen.blit(b_surf, (bx, by))

        # Draw snake body then head
        for i, seg in enumerate(snake):
            color = GREEN if i > 0 else DKGREEN
            draw_cell(screen, seg, color, DKGREEN if i == 0 else None)

        # HUD: score, speed, and active shrink indicator
        if font_sm is not None:
            hud = f"Score: {score}  Speed: {fps}"
            if shrink_pending > 0:
                hud += f"  [Shrinking: {shrink_pending}]"
            score_surf = font_sm.render(hud, True, WHITE)
            screen.blit(score_surf, (8, 6))

        pygame.display.flip()


# ---------------------------------------------------------------------------
# Game-over screen
# ---------------------------------------------------------------------------
def game_over_screen(score, reason):
    """Display the game-over overlay and wait for SPACE / Q."""
    reason_map = {
        "wall":    "Hit the wall!",
        "self":    "Bit yourself!",
        "barrier": "Hit a barrier!",   # New barrier death message
        "timeout": "Time limit reached.",
    }
    reason_text = reason_map.get(reason, "Game Over")

    frame_count = 0
    while True:
        frame_count += 1
        if frame_count >= MAX_FRAMES:
            return "quit"

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "restart"
                if event.key in (pygame.K_q, pygame.K_ESCAPE):
                    return "quit"

        screen.fill(BLACK)
        draw_text_centered(screen, "GAME OVER",    font_big, RED,   HEIGHT // 2 - 70)
        draw_text_centered(screen, reason_text,    font_med, WHITE, HEIGHT // 2 - 10)
        draw_text_centered(screen, f"Score: {score}", font_med, YELLOW, HEIGHT // 2 + 40)
        draw_text_centered(screen, "SPACE = Restart   Q = Quit", font_sm, WHITE, HEIGHT // 2 + 90)
        pygame.display.flip()
        clock.tick(30)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    while True:
        score, reason = game_loop()
        action = game_over_screen(score, reason)
        if action == "quit":
            break

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()