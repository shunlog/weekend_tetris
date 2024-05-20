#!/usr/bin/env python3
# Example file showing a circle moving on screen
import pygame

pygame.init()
screen = pygame.display.set_mode((1280, 720))

clock = pygame.time.Clock()
dt = 0


class State:
    def __init__(self):
        self.player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)
        self.dropping = False
        self.mov_right = False
        self.mov_left = False
        self.last_dir_r = False   # last dir was right
        self.running = True



def handle_input(s):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            s.running = False
        elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
            match event.key:
                case pygame.K_RIGHT:
                    if event.type == pygame.KEYDOWN:
                        s.mov_right = True
                        s.last_dir_r = True
                    else:
                        s.mov_right = False
                case pygame.K_LEFT:
                    if event.type == pygame.KEYDOWN:
                        s.mov_left = True
                        s.last_dir_r = False
                    else:
                        s.mov_left = False
                case pygame.K_DOWN:
                    pass


def draw_frame(s):
    screen.fill("gray")
    pygame.draw.circle(screen, "red", s.player_pos, 40)
    pygame.display.flip()


def update(s):
    if keys[pygame.K_UP]:
        s.player_pos.y -= 300 * dt
    if keys[pygame.K_DOWN]:
        s.player_pos.y += 300 * dt
    if s.mov_right and (s.last_dir_r or (not s.mov_left)):
        s.player_pos.x += 300 * dt
    if s.mov_left and ((not s.last_dir_r) or (not s.mov_right)):
        s.player_pos.x -= 300 * dt


s = State()
while s.running:
    keys = pygame.key.get_pressed()
    # TODO make these functions pure?
    handle_input(s)
    update(s)
    draw_frame(s)

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
