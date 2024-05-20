#!/usr/bin/env python3
# Example file showing a circle moving on screen
import pygame
import random
from icecream import ic

SQW = 20
BOARD_WN = 10
BOARD_HN = 20
BOARD_W = BOARD_WN * SQW
BOARD_H = BOARD_HN * SQW
GRID_COLOR = pygame.Color(50, 50, 50)
DROP_MS = 200

pygame.init()
screen = pygame.display.set_mode((1280, 720))

clock = pygame.time.Clock()
dt = 0




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


colors = {
    'L': "orange",
    'J': "blue",
    'T': "purple",
    'S': "green",
    'Z':  "red",
    'SQ': "yellow",
    'I': "cyan"
}

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

# position = top-left corner
shape_start_pos = {
    'L': pygame.Vector2(3, -3),
    'J': pygame.Vector2(4, -3),
    'T': pygame.Vector2(4, -2),
    'S': pygame.Vector2(4, -3),
    'Z': pygame.Vector2(4, -3),
    'SQ': pygame.Vector2(4, -2),
    'I': pygame.Vector2(4, -4)
}


class Block:
    def __init__(self, sh_name, pos, rot=0):
        self.sh_name = sh_name
        self.pos = pos
        self.rot = rot


    def draw(self, sf):
        sh = shapes[self.sh_name]
        match self.rot % 4:
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
                xp = (self.pos.x + x) * SQW
                yp = (self.pos.y + y) * SQW
                pygame.draw.rect(sf, colors[self.sh_name], ((xp, yp), (SQW, SQW)))


class State:
    def __init__(self):
        self.running = True

        self.prev_drop_t = 0
        self.dropping = False
        self.mov_right = False
        self.mov_left = False
        self.last_dir_r = False   # last dir was right
        self.blocks = []
        sh_name = random.choice(list(shapes.keys()))
        self.blck = Block(sh_name, shape_start_pos[sh_name])


def draw_board(s):
    board = pygame.Surface((BOARD_WN * SQW, BOARD_HN * SQW))
    for i in range(BOARD_WN):
        x = i * SQW
        pygame.draw.aaline(board, GRID_COLOR, (x, 0), (x, BOARD_H))
    for j in range(BOARD_HN):
        y = j * SQW
        pygame.draw.aaline(board, GRID_COLOR, (0, y), (BOARD_W, y))
    for b in s.blocks:
        b.draw(board)
    s.blck.draw(board)

    return board


def draw_frame(s):
    screen.fill("gray")

    board = draw_board(s)
    screen.blit(board, (100, 100))

    pygame.display.flip()


def update(s):
    t = pygame.time.get_ticks()
    diff = t - s.prev_drop_t
    if diff > DROP_MS:
        s.blck.pos += pygame.Vector2(0, 1)
        s.prev_drop_t = s.prev_drop_t + DROP_MS



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
