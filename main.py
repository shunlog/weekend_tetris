#!/usr/bin/env python3
# Example file showing a circle moving on screen
import pygame

pygame.init()
screen = pygame.display.set_mode((1280, 720))

clock = pygame.time.Clock()
dt = 0

player_pos = pygame.Vector2(screen.get_width() / 2, screen.get_height() / 2)

# state
dropping = False
mov_right = False
mov_left = False
last_dir_r = False   # last dir was right


running = True
while running:
    keys = pygame.key.get_pressed()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
            match event.key:
                case pygame.K_RIGHT:
                    if event.type == pygame.KEYDOWN:
                        mov_right = True
                        last_dir_r = True
                    else:
                        mov_right = False
                case pygame.K_LEFT:
                    if event.type == pygame.KEYDOWN:
                        mov_left = True
                        last_dir_r = False
                    else:
                        mov_left = False
                case pygame.K_DOWN:
                    pass


    # fill the screen with a color to wipe away anything from last frame
    screen.fill("gray")

    pygame.draw.circle(screen, "red", player_pos, 40)

    if keys[pygame.K_UP]:
        player_pos.y -= 300 * dt
    if keys[pygame.K_DOWN]:
        player_pos.y += 300 * dt
    if mov_right and (last_dir_r or (not mov_left)):
        player_pos.x += 300 * dt
    if mov_left and ((not last_dir_r) or (not mov_right)):
        player_pos.x -= 300 * dt

    # flip() the display to put your work on screen
    pygame.display.flip()

    # limits FPS to 60
    # dt is delta time in seconds since last frame, used for framerate-
    # independent physics.
    dt = clock.tick(60) / 1000

pygame.quit()
