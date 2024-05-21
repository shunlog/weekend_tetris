#!/usr/bin/env python3
# Example file showing a circle moving on screen
import pygame
import random
from icecream import ic
from dataclasses import dataclass

SQW = 20
BOARD_WN = 50
BOARD_HN = 20
BOARD_W = BOARD_WN * SQW
BOARD_H = BOARD_HN * SQW
GRID_COLOR = pygame.Color(50, 50, 50)
FALL_SPEED = 100  # ms
MOVE_SPEED = 200
DAS = 300  # delayed auto-shift (ms holding before start)
ARR = 1 / 20  # Auto-repeat rate (ms)

pygame.init()
screen = pygame.display.set_mode((1280, 720))

clock = pygame.time.Clock()
dt = 0


class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f'<Coord({self.x},{self.y})>'

    def __add__(self, other):
        return Coord(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return Coord(self.x - other.x, self.y - other.y)

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

shapes_m = {
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


def matrix_to_set(m):
    s = set()
    for y, l in enumerate(sh):
        for x, c in enumerate(l):
            if c == 1:
                s.add((x, y))
    return s


shapes = {}  # (shape_name, rot) -> set(Square)
for sn, sh in shapes_m.items():
    for rot in range(4):
        shapes[(sn, rot)] = set(Coord(x, y) for (x, y) in matrix_to_set(sh))
        sh = rot_cw(sh)



# position = top-left corner
shape_start_pos = {
    'L': Coord(3, -3),
    'J': Coord(4, -3),
    'T': Coord(4, -2),
    'S': Coord(4, -3),
    'Z': Coord(4, -3),
    'SQ': Coord(4, -2),
    'I': Coord(4, -4)
}



@dataclass
class Square:
    pos: Coord
    col: pygame.Color

    def draw_on(self, sf):
        xp = self.pos.x * SQW
        yp = self.pos.y * SQW
        pygame.draw.rect(sf, self.col, ((xp, yp), (SQW, SQW)))


class Block:
    def __init__(self, sh_name, pos, rot=0):
        self.sh_name = sh_name
        self.pos = pos  # top-left corner of the shape matrix
        self.rot = rot
        self.col = colors[self.sh_name]

    def squares(self):
        sqrs = []
        for sq_pos in shapes[(self.sh_name, self.rot)]:
            npos = self.pos + sq_pos
            sqrs.append(Square(npos, self.col))
        return sqrs

    def draw_on(self, sf):
        for sq in self.squares():
            sq.draw_on(sf)


class State:
    def __init__(self):
        self.running = True

        self.dropping = False
        self.prev_drop_t = 0

        self.mov_right = False  # Right arrow pressed
        self.mov_left = False  # Left arrow pressed
        self.last_dir_r = False   # Check what direction was pressed last
        self.last_mov_t = 0  # Time when last dir key was pressed/released
        self.auto_rep = False
        self.arr_prev_t = 0

        self.sqrs = []
        for _ in range(BOARD_H):
            self.sqrs.append([None]*BOARD_W)

        sh_name = random.choice(list(shapes_m.keys()))
        self.blck = Block(sh_name, shape_start_pos[sh_name])

    def direction(self):
        if self.mov_right and (self.last_dir_r or (not self.mov_left)):
            return 1
        if self.mov_left and (not self.last_dir_r or (not self.mov_right)):
            return -1
        return 0

    def square_on_floor(self, sq):
        p = sq.pos + Coord(0, 1)
        return p.y >= BOARD_HN or (self.sqrs[p.y][p.x] is not None)

    def block_on_floor(self):
        return any(self.square_on_floor(sq) for sq in self.blck.squares())

    def fall(self):
        t = pygame.time.get_ticks()
        if t - s.prev_drop_t < FALL_SPEED:
            return
        s.prev_drop_t += FALL_SPEED

        if self.block_on_floor():
            return

        self.blck.pos += Coord(0, 1)

    def autorepeat(self):
        t = pygame.time.get_ticks()
        if t - self.last_mov_t < DAS or self.direction() == 0:
            return

        if self.arr_prev_t < self.last_mov_t:
            self.arr_prev_t = self.last_mov_t + DAS - ARR

        if t - self.arr_prev_t < ARR:
            return

        self.arr_prev_t += ARR
        self.move_side()

    def move_side(self):
        self.blck.pos += Coord(s.direction(), 0)


def draw_board(s):
    board = pygame.Surface((BOARD_WN * SQW, BOARD_HN * SQW))
    for i in range(BOARD_WN):
        x = i * SQW
        pygame.draw.aaline(board, GRID_COLOR, (x, 0), (x, BOARD_H))
    for j in range(BOARD_HN):
        y = j * SQW
        pygame.draw.aaline(board, GRID_COLOR, (0, y), (BOARD_W, y))
    for ln in s.sqrs:
        for sq in ln:
            if not sq:
                continue
            sq.draw_on(board)
    s.blck.draw_on(board)

    return board


def draw_frame(s):
    screen.fill("gray")

    board = draw_board(s)
    screen.blit(board, (100, 100))

    pygame.display.flip()


def handle_input(s):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            s.running = False
        elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
            match event.key:
                case pygame.K_RIGHT:
                    s.last_mov_t = pygame.time.get_ticks()
                    if event.type == pygame.KEYDOWN:
                        s.mov_right = True
                        s.last_dir_r = True
                        s.move_side()
                    else:
                        s.mov_right = False
                case pygame.K_LEFT:
                    s.last_mov_t = pygame.time.get_ticks()
                    if event.type == pygame.KEYDOWN:
                        s.mov_left = True
                        s.last_dir_r = False
                        s.move_side()
                    else:
                        s.mov_left = False
                case pygame.K_DOWN:
                    pass


def update(s):
    s.fall()
    s.autorepeat()


s = State()
s.blck.pos += Coord(0, 1)

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
