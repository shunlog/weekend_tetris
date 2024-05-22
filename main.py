#!/usr/bin/env python3
# Example file showing a circle moving on screen
import pygame
import random
from icecream import ic
from dataclasses import dataclass

SQW = 20
BOARD_X = 10
BOARD_Y_BUF = 4  # top rows are a hidden "buffer"
BOARD_Y = 20 + BOARD_Y_BUF
BOARD_W = BOARD_X * SQW
BOARD_H = BOARD_Y * SQW
GRID_COLOR = pygame.Color(50, 50, 50)
FALL_SPEED = 400  # ms
SOFT_DROP_SPEED = 40  # ms
MOVE_SPEED = 200
DAS = 200  # delayed auto-shift (ms holding before start)
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


def rot_cw(m):
    return list(zip(*m))[::-1]


def rot_ccw(m):
    return list(zip(*m[::-1]))


shapes = {}  # (shape_name, rot) -> set(Square)
for sn, sh in shapes_m.items():
    for rot in range(4):
        shapes[(sn, rot)] = set(Coord(x, y) for (x, y) in matrix_to_set(sh))
        sh = rot_ccw(sh)


# position = top-left corner
shape_spawn_pos = {
    'L': Coord(3, 1),
    'J': Coord(4, 1),
    'T': Coord(4, 2),
    'S': Coord(4, 1),
    'Z': Coord(4, 1),
    'SQ': Coord(4, 2),
    'I': Coord(4, 0)
}


def draw_sq(sf, pos, col):
    xp = pos.x * SQW
    yp = pos.y * SQW
    pygame.draw.rect(sf, col, ((xp, yp), (SQW, SQW)))


class Block:
    def __init__(self, sh_name, pos, rot=0):
        self.sh_name = sh_name
        self.pos = pos  # top-left corner of the shape matrix
        self.rot = rot
        self.col = colors[self.sh_name]

    def pos_ls(self):
        l = []
        for sq_pos in shapes[(self.sh_name, self.rot)]:
            npos = self.pos + sq_pos
            l.append(npos)
        return l

    def draw_on(self, sf):
        for p in self.pos_ls():
            draw_sq(sf, p, self.col)

    def rotate_cw(self):
        self.rot = (self.rot + 1) % 4

    def rotate_ccw(self):
        self.rot = (self.rot - 1) % 4


class State:
    def __init__(self):
        self.running = True

        self.dropping = False
        self.prev_drop_t = 0
        self.soft_drop = False

        self.mov_right = False  # Right arrow pressed
        self.mov_left = False  # Left arrow pressed
        self.last_dir_r = False   # Check what direction was pressed last
        self.last_mov_t = 0  # Time when last dir key was pressed/released
        self.auto_rep = False
        self.DAS_prev_t = 0

        self.sqrs = []  # board matrix, value at (x, y) = pygame.Color
        for _ in range(BOARD_Y):
            self.sqrs.append([None]*BOARD_X)

        self.spawn_block()

    def spawn_block(self):
        sh_name = random.choice(list(shapes_m.keys()))
        self.blck = Block(sh_name, shape_spawn_pos[sh_name])

    def direction(self):
        if self.mov_right and (self.last_dir_r or (not self.mov_left)):
            return 1
        if self.mov_left and (not self.last_dir_r or (not self.mov_right)):
            return -1
        return 0

    def pos_overlapping(self, p):
        if p.y < 0:
            return False
        return p.y >= BOARD_Y \
            or p.x < 0 or p.x >= BOARD_X \
            or (self.sqrs[p.y][p.x] is not None)

    def pos_on_floor(self, p):
        return self.pos_overlapping(p + Coord(0, 1))

    def block_overlapping(self):
        return any(self.pos_overlapping(pos) for pos in self.blck.pos_ls())

    def block_on_floor(self):
        return any(self.pos_on_floor(pos) for pos in self.blck.pos_ls())

    def settle_block(self):
        for pos in self.blck.pos_ls():
            self.sqrs[pos.y][pos.x] = self.blck.col

        self.kill_completed_lines()

        self.spawn_block()

    def line_complete(self, y):
        return all(self.sqrs[y])

    def kill_completed_lines(self):
        # assumes the pos_ls are both in matrix and block
        lines_complete = {y for pos in self.blck.pos_ls() if self.line_complete(y := pos.y)}
        for i, y in enumerate(sorted(lines_complete)):
            # del from bottom to top
            del self.sqrs[y]
            self.sqrs.insert(0, [None]*BOARD_X)

    def fall(self):
        t = pygame.time.get_ticks()
        delay = SOFT_DROP_SPEED if self.soft_drop else FALL_SPEED
        if t - self.prev_drop_t < delay:
            return
        self.prev_drop_t += delay
        self.move_down()

    def move_down(self):
        # return True if hit floor
        if self.block_on_floor():
            self.settle_block()
            return True

        self.blck.pos += Coord(0, 1)

    def handle_DAS(self):
        t = pygame.time.get_ticks()
        if t - self.last_mov_t < DAS or self.direction() == 0:
            return

        if self.DAS_prev_t < self.last_mov_t:
            self.DAS_prev_t = self.last_mov_t + DAS - ARR

        if t - self.DAS_prev_t < ARR:
            return

        self.DAS_prev_t += ARR
        self.move_side()

    def move_side(self):
        self.blck.pos += Coord(self.direction(), 0)
        if self.block_overlapping():
            self.blck.pos -= Coord(self.direction(), 0)

    def drop(self):
        while not self.move_down():
            pass

    def rotate_cw(self):
        self.blck.rotate_cw()
        if self.block_overlapping():
            self.blck.rotate_ccw()

    def rotate_ccw(self):
        self.blck.rotate_ccw()
        if self.block_overlapping():
            self.blck.rotate_cw()

    def rotate_180(self):
        self.blck.rotate_ccw()
        self.blck.rotate_ccw()
        if self.block_overlapping():
            self.blck.rotate_cw()
            self.blck.rotate_cw()


def draw_board(s):
    board = pygame.Surface((BOARD_W, BOARD_H))
    pygame.draw.rect(board, "gray", ((0, 0), (BOARD_W, BOARD_Y_BUF * SQW)))
    for i in range(BOARD_X):
        x = i * SQW
        pygame.draw.aaline(board, GRID_COLOR, (x, 0), (x, BOARD_H))
    for j in range(BOARD_Y):
        y = j * SQW
        pygame.draw.aaline(board, GRID_COLOR, (0, y), (BOARD_W, y))
    for y, ln in enumerate(s.sqrs):
        for x, col in enumerate(ln):
            if not col:
                continue
            pos = Coord(x, y)
            draw_sq(board, pos, col)
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
                case pygame.K_a if event.type == pygame.KEYDOWN:
                    s.rotate_180()
                case pygame.K_z if event.type == pygame.KEYDOWN:
                    s.rotate_ccw()
                case pygame.K_UP | pygame.K_x if event.type == pygame.KEYDOWN:
                    s.rotate_cw()
                case pygame.K_SPACE if event.type == pygame.KEYDOWN:
                    s.drop()
                case pygame.K_DOWN:
                    s.soft_drop = True if event.type == pygame.KEYDOWN else False
                    pass
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


def update(s):
    s.fall()
    s.handle_DAS()


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
