#!/usr/bin/env python3
# Example file showing a circle moving on screen
import pygame
from icecream import ic

SQW = 20
BOARD_W = 50
BOARD_H = 15

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


def rot_cw(m):
    return list(zip(*m))[::-1]

def rot_ccw(m):
    return list(zip(*m[::-1]))


shapes = {
    'L': ((0, 1, 0),
          (0, 1, 0),
          (0, 1, 1)),

    'J': ((0, 1, 0),
          (0, 1, 0),
          (1, 1, 0)),

    'T': ((0, 1, 0),
          (1, 1, 1),
          (0, 0, 0)),

    'S': ((0, 0, 0),
          (0, 1, 1),
          (1, 1, 0)),

    'Z': ((0, 0, 0),
          (1, 1, 0),
          (0, 1, 1)),

    'SQ': ((1, 1),
           (1, 1)),

    'I': ((0, 1, 0, 0),
          (0, 1, 0, 0),
          (0, 1, 0, 0),
          (0, 1, 0, 0))
}


def draw_shape(sf, sh_name, pos, rot=0):
    sh = shapes[sh_name]
    match rot % 4:
        case 1:
            sh = rot_cw(sh)
        case 2:
            sh = rot_cw(rot_cw(sh))
        case 3:
            sh = rot_ccw(sh)

    for y, l in enumerate(sh):
        for x, c in enumerate(l):
            if not c:
                continue
            xp = (pos.x + x) * SQW
            yp = (pos.y + y) * SQW
            pygame.draw.rect(sf, "red", ((xp, yp), (SQW, SQW)))


def draw_frame(s):
    screen.fill("gray")

    board = pygame.Surface((BOARD_W * SQW, BOARD_H * SQW))

    pygame.draw.rect(screen, "red", (s.player_pos, (SQW, SQW)))
    for i, shape in enumerate(shapes.keys()):
        r = pygame.time.get_ticks() // 1000
        draw_shape(board, shape, pygame.Vector2(5 * i, 1), r)

    screen.blit(board, (100, 100))
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