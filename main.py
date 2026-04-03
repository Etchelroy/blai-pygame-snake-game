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
    
    # Banana shrink state: tracks how many frames to shrink snake after eating banana
    # Value > 0 means snake is actively shrinking; decrements each frame until 0
    banana_shrink_counter = 0
    BANANA_SHRINK_DURATION = 5  # Shrink for 5 game ticks
    
    score = 0
    frame = 0
    
    # Game loop
    while frame < MAX_FRAMES:
        frame += 1
        clock.tick(FPS_BASE)
        
        # Handle user input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return score, "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction[1] == 0:
                    next_dir = (0, -1)
                elif event.key == pygame.K_DOWN and direction[1] == 0:
                    next_dir = (0, 1)
                elif event.key == pygame.K_LEFT and direction[0] == 0:
                    next_dir = (-1, 0)
                elif event.key == pygame.K_RIGHT and direction[0] == 0:
                    next_dir = (1, 0)
        
        # Update direction
        direction = next_dir
        
        # Move snake
        head_x, head_y = snake[0]
        new_head = (head_x + direction[0], head_y + direction[1])
        
        # Check wall collision
        if new_head[0] < 0 or new_head[0] >= COLS or new_head[1] < 0 or new_head[1] >= ROWS:
            return score, "wall"
        
        # Check self collision
        if new_head in snake:
            return score, "self"
        
        # Check barrier collision: if snake head hits any barrier, game over
        if new_head in barriers:
            return score, "barrier"
        
        # Add new head
        snake.insert(0, new_head)
        
        # Check food collision: eat and grow
        if new_head == food:
            score += 10
            food = random_food(snake, bananas, barriers)
        else:
            # No food eaten: remove tail (normal movement)
            snake.pop()
        
        # Check banana collision: eat and initiate shrink
        if new_head in bananas:
            score += 5
            bananas.remove(new_head)
            # Activate banana shrink: snake will lose one segment per tick
            banana_shrink_counter = BANANA_SHRINK_DURATION
        
        # Apply banana shrink: remove tail segments gradually while counter > 0
        if banana_shrink_counter > 0:
            if len(snake) > 1:
                snake.pop()  # Remove tail segment
            banana_shrink_counter -= 1
        
        # Spawn new banana occasionally (every 15 frames, if < 2 bananas exist)
        if frame % 15 == 0 and len(bananas) < 2:
            new_banana = spawn_banana(snake, food, bananas, barriers)
            if new_banana:
                bananas.append(new_banana)
        
        # Spawn new barrier occasionally (every 20 frames, if < 3 barriers exist)
        if frame % 20 == 0 and len(barriers) < 3:
            new_barrier = spawn_barrier(snake, food, bananas, barriers)
            if new_barrier:
                barriers.append(new_barrier)
        
        # Clear screen
        screen.fill(BLACK)
        
        # Draw barriers as distinct purple obstacles
        for barrier in barriers:
            draw_cell(screen, barrier, PURPLE)
        
        # Draw food
        if food:
            draw_cell(screen, food, YELLOW, DKGREEN)
        
        # Draw bananas
        for banana in bananas:
            draw_cell(screen, banana, ORANGE)
        
        # Draw snake head and body
        for i, segment in enumerate(snake):
            if i == 0:
                draw_cell(screen, segment, GREEN, DKGREEN)
            else:
                draw_cell(screen, segment, GREEN)
        
        # Draw score
        score_text = f"Score: {score}"
        if font_sm:
            surf = font_sm.render(score_text, True, WHITE)
            screen.blit(surf, (10, 10))
        
        pygame.display.flip()
    
    return score, "timeout"


def main():
    """
    Main entry point. Runs game loop and displays results.
    """
    score, reason = game_loop()
    
    # Display game over screen
    screen.fill(BLACK)
    
    draw_text_centered(screen, "GAME OVER", font_big, RED, HEIGHT // 2 - 40)
    draw_text_centered(screen, f"Score: {score}", font_med, WHITE, HEIGHT // 2 + 20)
    
    reason_text = reason.upper()
    draw_text_centered(screen, f"Reason: {reason_text}", font_sm, GRAY, HEIGHT // 2 + 60)
    
    pygame.display.flip()
    
    # Wait a bit before exiting (for visual feedback in headless environments)
    pygame.time.wait(500)
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()