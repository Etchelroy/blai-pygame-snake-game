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
CELL = 20
COLS = 30
ROWS = 24
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL
FPS_BASE = 8
MAX_FRAMES = 1000  # Safety limit for headless/test environments

# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------
WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
GREEN   = (0,   200, 0)
DKGREEN = (0,   140, 0)
RED     = (220, 50,  50)
GRAY    = (40,  40,  40)
YELLOW  = (255, 220, 0)
ORANGE  = (255, 165, 0)      # Banana color
PURPLE  = (128, 0,   128)    # Barrier color

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()

font_big = None
font_med = None
font_sm  = None

try:
    pygame.font.init()
    if pygame.font.get_init():
        default_font = pygame.font.get_default_font()
        font_big = pygame.font.Font(default_font, 48)
        font_med = pygame.font.Font(default_font, 28)
        font_sm  = pygame.font.Font(default_font, 22)
except Exception:
    font_big = None
    font_med = None
    font_sm  = None


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def random_food(snake, bananas=None, barriers=None):
    """
    Spawn food at a random location not occupied by snake, bananas, or barriers.
    
    Args:
        snake: List of snake segment positions
        bananas: List of banana positions (default: None)
        barriers: List of barrier positions (default: None)
    
    Returns:
        Tuple (x, y) of food position, or None if no free cells exist
    """
    occupied = set(snake)
    if bananas:
        occupied.update(bananas)
    if barriers:
        occupied.update(barriers)
    
    all_cells = [(x, y) for x in range(COLS) for y in range(ROWS)]
    free = [c for c in all_cells if c not in occupied]
    if not free:
        return None
    return random.choice(free)


def spawn_banana(snake, food, bananas, barriers):
    """
    Spawn a new banana at a random unoccupied location.
    
    Args:
        snake: List of snake segment positions
        food: Current food position
        bananas: List of banana positions
        barriers: List of barrier positions
    
    Returns:
        New banana position, or None if no free cells exist
    """
    occupied = set(snake)
    occupied.update(bananas)
    if barriers:
        occupied.update(barriers)
    if food:
        occupied.add(food)
    
    all_cells = [(x, y) for x in range(COLS) for y in range(ROWS)]
    free = [c for c in all_cells if c not in occupied]
    if not free:
        return None
    return random.choice(free)


def spawn_barrier(snake, food, bananas, barriers):
    """
    Spawn a new barrier at a random unoccupied location.
    
    Args:
        snake: List of snake segment positions
        food: Current food position
        bananas: List of banana positions
        barriers: List of barrier positions
    
    Returns:
        New barrier position, or None if no free cells exist
    """
    occupied = set(snake)
    occupied.update(bananas)
    if barriers:
        occupied.update(barriers)
    if food:
        occupied.add(food)
    
    all_cells = [(x, y) for x in range(COLS) for y in range(ROWS)]
    free = [c for c in all_cells if c not in occupied]
    if not free:
        return None
    return random.choice(free)


def draw_cell(surface, pos, color, inner=None):
    """
    Draw a single grid cell at the given position.
    
    Args:
        surface: Pygame surface to draw on
        pos: Tuple (x, y) of grid cell position
        color: Outer color (RGB tuple)
        inner: Inner color for highlighting (RGB tuple, optional)
    """
    x, y = pos[0] * CELL, pos[1] * CELL
    pygame.draw.rect(surface, color, (x, y, CELL, CELL))
    if inner:
        pygame.draw.rect(surface, inner, (x + 2, y + 2, CELL - 4, CELL - 4))


def draw_text_centered(surface, text, font, color, cy):
    """
    Draw text centered horizontally at a given y-coordinate.
    
    Args:
        surface: Pygame surface to draw on
        text: String to render
        font: Pygame font object
        color: Text color (RGB tuple)
        cy: Center y-coordinate
    """
    if font is None:
        return
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, cy))
    surface.blit(surf, rect)


def game_loop():
    """
    Main game loop. Handles snake movement, food/banana/barrier spawning,
    collisions, and scoring.
    
    Returns:
        Tuple (score, reason) where reason is one of:
        - "wall": Snake hit boundary
        - "self": Snake hit itself
        - "barrier": Snake hit a barrier
        - "timeout": Frame limit exceeded (testing safety)
    """
    # Initialize snake in center of screen
    snake = [(COLS // 2, ROWS // 2),
             (COLS // 2 - 1, ROWS // 2),
             (COLS // 2 - 2, ROWS // 2)]
    
    direction = (1, 0)
    next_dir  = (1, 0)
    
    # Initialize game state
    food = random_food(snake)
    bananas = []
    barriers = []
    
    # Banana shrink state: tracks how many frames to shrink snake
    # Value > 0 means banana is active; decrements each frame
    banana_shrink_counter = 0
    BANANA_SHRINK_DURATION = 5  # Shrink for 5 game ticks
    
    # Spawn timing counters
    banana_spawn_timer = 0
    barrier_spawn_timer = 0
    BANANA_SPAWN_INTERVAL = 15  # Attempt spawn every 15 frames
    BARRIER_SPAWN_INTERVAL = 20  # Attempt spawn every 20 frames
    
    score = 0
    frame_count = 0

    while True:
        fps = FPS_BASE + score // 3
        clock.tick(fps)
        frame_count += 1

        if frame_count >= MAX_FRAMES:
            return score, "timeout"

        # -------------------------------------------------------------------
        # Event handling
        # -------------------------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP    and direction != (0,  1): 
                    next_dir = (0, -1)
                if event.key == pygame.K_DOWN  and direction != (0, -1): 
                    next_dir = (0,  1)
                if event.key == pygame.K_LEFT  and direction != (1,  0): 
                    next_dir = (-1, 0)
                if event.key == pygame.K_RIGHT and direction != (-1, 0): 
                    next_dir = (1,  0)

        # -------------------------------------------------------------------
        # Snake movement
        # -------------------------------------------------------------------
        direction = next_dir
        head = (snake[0][0] + direction[0], snake[0][1] + direction[1])

        # Check wall collision
        if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS):
            return score, "wall"

        # Check self collision
        if head in snake:
            return score, "self"

        # Check barrier collision
        if head in barriers:
            return score, "barrier"

        snake.insert(0, head)

        # -------------------------------------------------------------------
        # Food eating
        # -------------------------------------------------------------------
        if food is not None and head == food:
            score += 1
            food = random_food(snake, bananas, barriers)
        else:
            snake.pop()

        # -------------------------------------------------------------------
        # Banana eating
        # -------------------------------------------------------------------
        if head in bananas:
            # Remove eaten banana
            bananas.remove(head)
            # Activate banana shrink effect
            banana_shrink_counter = BANANA_SHRINK_DURATION
            score += 1

        # -------------------------------------------------------------------
        # Banana shrink effect (gradual segment loss)
        # Duration: BANANA_SHRINK_DURATION frames
        # Each frame where banana_shrink_counter > 0, remove tail segment
        # -------------------------------------------------------------------
        if banana_shrink_counter > 0:
            # Remove one segment per frame while shrinking
            if len(snake) > 1:
                snake.pop()
            banana_shrink_counter -= 1

        # -------------------------------------------------------------------
        # Banana spawning (random at intervals)
        # Bananas spawn every BANANA_SPAWN_INTERVAL frames with some randomness
        # -------------------------------------------------------------------
        banana_spawn_timer += 1
        if banana_spawn_timer >= BANANA_SPAWN_INTERVAL and len(bananas) < 2:
            # Limit max bananas to 2 for gameplay balance
            new_banana = spawn_banana(snake, food, bananas, barriers)
            if new_banana:
                bananas.append(new_banana)
            banana_spawn_timer = 0

        # -------------------------------------------------------------------
        # Barrier spawning (random at intervals)
        # Barriers spawn every BARRIER_SPAWN_INTERVAL frames
        # -------------------------------------------------------------------
        barrier_spawn_timer += 1
        if barrier_spawn_timer >= BARRIER_SPAWN_INTERVAL and len(barriers) < 3:
            # Limit max barriers to 3 for gameplay balance
            new_barrier = spawn_barrier(snake, food, bananas, barriers)
            if new_barrier:
                barriers.append(new_barrier)
            barrier_spawn_timer = 0

        # -------------------------------------------------------------------
        # Rendering
        # -------------------------------------------------------------------
        screen.fill(GRAY)

        # Draw grid
        for x in range(0, WIDTH, CELL):
            pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL):
            pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

        # Draw barriers (purple rectangles)
        for barrier_pos in barriers:
            draw_cell(screen, barrier_pos, PURPLE)

        # Draw food (red cell with yellow circle inside)
        if food is not None:
            draw_cell(screen, food, RED)
            fx, fy = food[0] * CELL + CELL // 2, food[1] * CELL + CELL // 2
            pygame.draw.circle(screen, YELLOW, (fx, fy), CELL // 4)

        # Draw bananas (orange cells with distinctive pattern)
        for banana_pos in bananas:
            draw_cell(screen, banana_pos, ORANGE)
            # Draw a small circle to distinguish banana from food
            bx, by = banana_pos[0] * CELL + CELL // 2, banana_pos[1] * CELL + CELL // 2
            pygame.draw.circle(screen, YELLOW, (bx, by), CELL // 5)

        # Draw snake
        for i, seg in enumerate(snake):
            color = GREEN if i > 0 else DKGREEN
            draw_cell(screen, seg, color, DKGREEN if i == 0 else None)

        # Draw UI text (score and speed)
        if font_sm is not None:
            score_surf = font_sm.render(
                f"Score: {score}  Speed: {fps}  Shrink: {banana_shrink_counter}",
                True, WHITE
            )
            screen.blit(score_surf, (8, 6))

        pygame.display.flip()


def game_over_screen(score, reason):
    """
    Display game over screen with final score and reason.
    
    Args:
        score: Final score achieved
        reason: String describing why game ended
            - "wall": Hit boundary
            - "self": Hit self
            - "barrier": Hit barrier
            - "timeout": Frame limit exceeded
    """
    reason_text = {
        "wall": "You hit a wall!",
        "self": "You hit yourself!",
        "barrier": "You hit a barrier!",
        "timeout": "Game timed out (test mode)"
    }
    
    frame_count = 0
    while frame_count < 300:  # Show game over screen for ~5 seconds at 60 FPS
        clock.tick(60)
        frame_count += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                return

        screen.fill(BLACK)
        draw_text_centered(screen, "GAME OVER", font_big, RED, HEIGHT // 3)
        draw_text_centered(screen, reason_text.get(reason, "Unknown reason"), 
                          font_med, WHITE, HEIGHT // 2)
        draw_text_centered(screen, f"Final Score: {score}", font_med, YELLOW, 
                          HEIGHT // 2 + 60)
        draw_text_centered(screen, "Press any key to exit", font_sm, WHITE, 
                          HEIGHT // 2 + 120)

        pygame.display.flip()


def main():
    """
    Main entry point. Runs game loop and displays game over screen.
    """
    score, reason = game_loop()
    game_over_screen(score, reason)
    pygame.quit()


if __name__ == "__main__":
    main()