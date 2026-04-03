import pygame
import random
import sys

pygame.init()

CELL = 20
COLS = 30
ROWS = 24
WIDTH = COLS * CELL
HEIGHT = ROWS * CELL
FPS_BASE = 8

WHITE   = (255, 255, 255)
BLACK   = (0,   0,   0)
GREEN   = (0,   200, 0)
DKGREEN = (0,   140, 0)
RED     = (220, 50,  50)
GRAY    = (40,  40,  40)
YELLOW  = (255, 220, 0)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake")
clock = pygame.time.Clock()
font_big  = pygame.font.SysFont("monospace", 48, bold=True)
font_med  = pygame.font.SysFont("monospace", 28)
font_sm   = pygame.font.SysFont("monospace", 22)

def random_food(snake):
    occupied = set(snake)
    while True:
        pos = (random.randint(0, COLS - 1), random.randint(0, ROWS - 1))
        if pos not in occupied:
            return pos

def draw_cell(surface, pos, color, inner=None):
    x, y = pos[0] * CELL, pos[1] * CELL
    pygame.draw.rect(surface, color, (x, y, CELL, CELL))
    if inner:
        pygame.draw.rect(surface, inner, (x + 2, y + 2, CELL - 4, CELL - 4))

def draw_text_centered(surface, text, font, color, cy):
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, cy))
    surface.blit(surf, rect)

def game_loop():
    # Initial state
    snake = [(COLS // 2, ROWS // 2),
             (COLS // 2 - 1, ROWS // 2),
             (COLS // 2 - 2, ROWS // 2)]
    direction = (1, 0)
    next_dir  = (1, 0)
    food = random_food(snake)
    score = 0
    running = True

    while running:
        fps = FPS_BASE + score // 3
        clock.tick(fps)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP    and direction != (0,  1): next_dir = (0, -1)
                if event.key == pygame.K_DOWN  and direction != (0, -1): next_dir = (0,  1)
                if event.key == pygame.K_LEFT  and direction != (1,  0): next_dir = (-1, 0)
                if event.key == pygame.K_RIGHT and direction != (-1, 0): next_dir = (1,  0)

        direction = next_dir
        head = (snake[0][0] + direction[0], snake[0][1] + direction[1])

        # Wall collision
        if not (0 <= head[0] < COLS and 0 <= head[1] < ROWS):
            return score, "wall"

        # Self collision
        if head in snake:
            return score, "self"

        snake.insert(0, head)

        if head == food:
            score += 1
            food = random_food(snake)
        else:
            snake.pop()

        # Draw
        screen.fill(GRAY)

        # Grid lines (subtle)
        for x in range(0, WIDTH, CELL):
            pygame.draw.line(screen, (50, 50, 50), (x, 0), (x, HEIGHT))
        for y in range(0, HEIGHT, CELL):
            pygame.draw.line(screen, (50, 50, 50), (0, y), (WIDTH, y))

        # Food
        draw_cell(screen, food, RED)
        fx, fy = food[0] * CELL + CELL // 2, food[1] * CELL + CELL // 2
        pygame.draw.circle(screen, YELLOW, (fx, fy), CELL // 4)

        # Snake
        for i, seg in enumerate(snake):
            color = GREEN if i > 0 else DKGREEN
            draw_cell(screen, seg, color, DKGREEN if i == 0 else None)

        # Score
        score_surf = font_sm.render(f"Score: {score}  Speed: {fps}", True, WHITE)
        screen.blit(score_surf, (8, 6))

        pygame.display.flip()

def game_over_screen(score, reason):
    while True:
        screen.fill(BLACK)
        draw_text_centered(screen, "GAME OVER", font_big, RED, HEIGHT // 2 - 90)
        reason_text = "Hit a wall!" if reason == "wall" else "Hit yourself!"
        draw_text_centered(screen, reason_text, font_sm, WHITE, HEIGHT // 2 - 30)
        draw_text_centered(screen, f"Final Score: {score}", font_med, YELLOW, HEIGHT // 2 + 20)
        draw_text_centered(screen, "Press R to Restart", font_sm, WHITE, HEIGHT // 2 + 70)
        draw_text_centered(screen, "Press Q to Quit",    font_sm, WHITE, HEIGHT // 2 + 105)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    return True
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

def main():
    while True:
        score, reason = game_loop()
        restart = game_over_screen(score, reason)
        if not restart:
            break

main()