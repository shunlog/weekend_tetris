#!/usr/bin/env python3
# Example file showing a circle moving on screen
import pygame
import random
import enum
from icecream import ic

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
LOCK_DELAY = 500



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


class Shape(enum.Enum):
    L = enum.auto()
    J = enum.auto()
    T = enum.auto()
    S = enum.auto()
    Z = enum.auto()
    O = enum.auto()
    I = enum.auto()


class Rotation(enum.Enum):
    CW = enum.auto()
    DOUBLE = enum.auto()
    CCW = enum.auto()

    def undo(self):
        match self:
            case Rotation.CW:
                return Rotation.CCW
            case Rotation.DOUBLE:
                return Rotation.DOUBLE
            case Rotation.CCW:
                return Rotation.CW


class RotationState(enum.Enum):
    R0 = 0
    R1 = 1
    R2 = 2
    R3 = 3

    def rotate(self, rot):
        match rot:
            case Rotation.CW:
                return RotationState((self.value + 1) % 4)
            case Rotation.DOUBLE:
                return RotationState((self.value + 2) % 4)
            case Rotation.CCW:
                return RotationState((self.value + 3) % 4)


colors = {
    Shape.L: "orange",
    Shape.J: "blue",
    Shape.T: "purple",
    Shape.S: "green",
    Shape.Z: "red",
    Shape.O: "yellow",
    Shape.I: "cyan"
}

shapes_m = {
    Shape.L: ((0, 0, 1),
          (1, 1, 1),
          (0, 0, 0)),

    Shape.J: ((1, 0, 0),
          (1, 1, 1),
          (0, 0, 0)),

    Shape.T: ((0, 1, 0),
          (1, 1, 1),
          (0, 0, 0)),

    Shape.S: ((0, 1, 1),
          (1, 1, 0),
          (0, 0, 0)),

    Shape.Z: ((1, 1, 0),
          (0, 1, 1),
          (0, 0, 0)),

    Shape.O: ((1, 1),
           (1, 1)),

    Shape.I: ((0, 0, 0, 0),
          (1, 1, 1, 1),
          (0, 0, 0, 0),
          (0, 0, 0, 0))
}

# position = top-left corner
shape_spawn_pos = {
    Shape.L: Coord(3, 1),
    Shape.J: Coord(3, 1),
    Shape.T: Coord(3, 1),
    Shape.S: Coord(3, 1),
    Shape.Z: Coord(3, 1),
    Shape.O: Coord(4, 1),
    Shape.I: Coord(3, 1)
}


# Wall kick data from https://tetris.wiki/Super_Rotation_System
# (current state, desired state) -> five positions to try before failing
wall_kick_LJSZT = {
    (RotationState.R0, RotationState.R1): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (RotationState.R1, RotationState.R0): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (RotationState.R1, RotationState.R2): ((0, 0), (1, 0), (1, -1), (0, 2), (1, 2)),
    (RotationState.R2, RotationState.R1): ((0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)),
    (RotationState.R2, RotationState.R3): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2)),
    (RotationState.R3, RotationState.R2): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (RotationState.R3, RotationState.R0): ((0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)),
    (RotationState.R0, RotationState.R3): ((0, 0), (1, 0), (1, 1), (0, -2), (1, -2))
}

wall_kick_I = {
    (RotationState.R0, RotationState.R1): ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),
    (RotationState.R1, RotationState.R0): ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
    (RotationState.R1, RotationState.R2): ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)),
    (RotationState.R2, RotationState.R1): ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),
    (RotationState.R2, RotationState.R3): ((0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)),
    (RotationState.R3, RotationState.R2): ((0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)),
    (RotationState.R3, RotationState.R0): ((0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)),
    (RotationState.R0, RotationState.R3): ((0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1))
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
    for rot in RotationState:
        shapes[(sn, rot)] = set(Coord(x, y) for (x, y) in matrix_to_set(sh))
        sh = rot_ccw(sh)


def draw_sq(sf, pos, col):
    xp = pos.x * SQW
    yp = pos.y * SQW
    pygame.draw.rect(sf, col, ((xp, yp), (SQW, SQW)))


class Block:
    def __init__(self, shape, pos, rot=RotationState.R0):
        self.shape = shape
        self.pos = pos  # top-left corner of the shape matrix
        self.rot = rot
        self.col = colors[self.shape]

    def pos_ls(self):
        l = []
        for sq_pos in shapes[(self.shape, self.rot)]:
            npos = self.pos + sq_pos
            l.append(npos)
        return l

    def draw_on(self, sf):
        for p in self.pos_ls():
            draw_sq(sf, p, self.col)


class State:
    def __init__(self):
        self.running = True

        self.dropping = False
        self.prev_drop_t = 0
        self.soft_drop = False
        self.last_move_t = 0  # when last successful shift/rotation was performed

        self.right_pressed = False  # Right arrow pressed
        self.left_pressed = False  # Left arrow pressed
        self.right_last = False   # Check what direction was pressed last
        self.last_side_t = 0  # Time when last side key was pressed or released

        self.matrix = []  # board matrix, value at (x, y) = pygame.Color
        for _ in range(BOARD_Y):
            self.matrix.append([None]*BOARD_X)

        self.spawn_block()

    def spawn_block(self):
        shape = random.choice(list(Shape))
        self.blck = Block(shape, shape_spawn_pos[shape])

    def direction(self):
        if self.right_pressed and (self.right_last or (not self.left_pressed)):
            return 1
        if self.left_pressed and (not self.right_last or (not self.right_pressed)):
            return -1
        return 0

    def pos_overlapping(self, p):
        if p.y < 0:
            return False
        return p.y >= BOARD_Y \
            or p.x < 0 or p.x >= BOARD_X \
            or (self.matrix[p.y][p.x] is not None)

    def pos_on_floor(self, p):
        return self.pos_overlapping(p + Coord(0, 1))

    def block_overlapping(self, blck=None):
        blck = self.blck if not blck else blck
        return any(self.pos_overlapping(pos) for pos in blck.pos_ls())

    def block_on_floor(self):
        return any(self.pos_on_floor(pos) for pos in self.blck.pos_ls())

    def lock_block(self, force=False):
        t = pygame.time.get_ticks()
        if not force and t - self.last_move_t < LOCK_DELAY:
            return

        for pos in self.blck.pos_ls():
            self.matrix[pos.y][pos.x] = self.blck.col

        self.kill_completed_lines()

        self.spawn_block()

    def line_complete(self, y):
        return all(self.matrix[y])

    def kill_completed_lines(self):
        # assumes the pos_ls are both in matrix and block
        lines_complete = {y for pos in self.blck.pos_ls() if self.line_complete(y := pos.y)}
        for i, y in enumerate(sorted(lines_complete)):
            # del from bottom to top
            del self.matrix[y]
            self.matrix.insert(0, [None]*BOARD_X)

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
            self.lock_block()
            return True

        self.last_move_t = pygame.time.get_ticks()
        self.blck.pos += Coord(0, 1)

    def handle_DAS(self):
        t = pygame.time.get_ticks()
        if (t - (self.last_side_t + DAS)) < ARR \
           and self.direction() != 0:
            return

        self.move_side()

    def move_side(self):
        if self.direction() == 0:
            return
        self.blck.pos += Coord(self.direction(), 0)
        if self.block_overlapping():
            self.blck.pos -= Coord(self.direction(), 0)
            return
        self.last_move_t = pygame.time.get_ticks()

    def drop(self):
        while not self.move_down():
            pass
        self.lock_block(force=True)

    def _rotate_block(self, blck, rn):
        wall_kick_data = wall_kick_LJSZT \
            if self.blck.shape in (Shape.L, Shape.J, Shape.S, Shape.Z, Shape.T) \
            else wall_kick_I
        result_rot = blck.rot.rotate(rn)
        for x, y in wall_kick_data[(blck.rot, result_rot)]:
            y = -y  # they used positive Y upwards in the data table, but I used opposite
            pos_offset = Coord(x, y)
            npos = blck.pos + pos_offset
            result_blck = Block(blck.shape, npos, result_rot)

            if self.block_overlapping(result_blck):
                continue
            return result_blck
        return blck

    def rotate(self, rn):
        if self.blck.shape == Shape.O:
            return

        if rn == Rotation.DOUBLE:
            result_blck = self._rotate_block(self.blck, Rotation.CCW)
            if result_blck == self.blck:
                return False
            result_blck = self._rotate_block(result_blck, Rotation.CCW)
        else:
            result_blck = self._rotate_block(self.blck, rn)
        if result_blck == self.blck:
            return False

        self.blck = result_blck
        self.last_move_t = pygame.time.get_ticks()


def draw_board(s):
    board = pygame.Surface((BOARD_W, BOARD_H))
    pygame.draw.rect(board, "gray", ((0, 0), (BOARD_W, BOARD_Y_BUF * SQW)))
    for i in range(BOARD_X):
        x = i * SQW
        pygame.draw.aaline(board, GRID_COLOR, (x, 0), (x, BOARD_H))
    for j in range(BOARD_Y):
        y = j * SQW
        pygame.draw.aaline(board, GRID_COLOR, (0, y), (BOARD_W, y))
    for y, ln in enumerate(s.matrix):
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
                    s.rotate(Rotation.DOUBLE)
                case pygame.K_z if event.type == pygame.KEYDOWN:
                    s.rotate(Rotation.CCW)
                case pygame.K_UP | pygame.K_x if event.type == pygame.KEYDOWN:
                    s.rotate(Rotation.CW)
                case pygame.K_SPACE if event.type == pygame.KEYDOWN:
                    s.drop()
                case pygame.K_DOWN:
                    s.soft_drop = True if event.type == pygame.KEYDOWN else False
                    pass
                case pygame.K_RIGHT:
                    s.last_side_t = pygame.time.get_ticks()
                    if event.type == pygame.KEYDOWN:
                        s.right_pressed = True
                        s.right_last = True
                        s.move_side()
                    else:
                        s.right_pressed = False
                case pygame.K_LEFT:
                    s.last_side_t = pygame.time.get_ticks()
                    if event.type == pygame.KEYDOWN:
                        s.left_pressed = True
                        s.right_last = False
                        s.move_side()
                    else:
                        s.left_pressed = False


def update(s):
    s.fall()
    s.handle_DAS()


if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((600, 720))
    clock = pygame.time.Clock()
    dt = 0
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
