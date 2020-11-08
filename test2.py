import math

import pygame
import random
import pymunk
import numpy as np
from pymunk import Vec2d


def flipy(y):
    """Small hack to convert chipmunk physics to pygame coordinates"""
    return -y + 600


class Player(pygame.sprite.Sprite):
    def __init__(self, space, init_pos=(0, 0)):
        super().__init__()
        self.image = pygame.image.load("nacho_sprite.jpg")
        self.rect = self.image.get_bounding_rect()
        width = self.rect.width / 2
        height = self.rect.height / 2
        self.space = space
        self.pos = pygame.Vector2(init_pos)

        vs = [(-width / 2, -height / 2), (width / 2, -height / 2),
              (width / 2, height / 2), (-width / 2, height / 2)]
        mass = 10
        moment = pymunk.moment_for_poly(mass, vs)
        self.body = pymunk.Body(mass, moment)
        self.body.force = (0, -250)
        self.body.position = self.pos.x, -self.pos.y + 500
        self.shape = pymunk.Poly(self.body, vs)
        self.shape.friction = 0.5
        self.space.add(self.body, self.shape)

    def update(self, events, dt):
        pressed = pygame.key.get_pressed()
        move = pygame.Vector2((0, 0))
        if pressed[pygame.K_w]: move += (0, 1)
        if pressed[pygame.K_a]: move += (-1, 0)
        if pressed[pygame.K_s]: move += (0, -1)
        if pressed[pygame.K_d]: move += (1, 0)
        if move.length() > 0: move.normalize_ip()
        self.body.apply_impulse_at_local_point(move*10)

        # if you used pymunk before, you'll probably already know
        # that you'll have to invert the y-axis to convert between
        # the pymunk and the pygame coordinates.
        self.body.force = (0, -250)
        self.pos = pygame.Vector2(self.body.position[0], -self.body.position[1]+500)
        self.rect.center = self.pos
        self.body.angle = 0

class Satellite(pygame.sprite.Sprite):
    def __init__(self, space, init_pos=(0, 0)):
        super().__init__()
        self.image = pygame.image.load("nacho_sprite.jpg")
        # self.rect = self.image.get_rect()
        self.rect = self.image.get_bounding_rect()
        width = self.rect.width / 2
        height = self.rect.height / 2
        self.space = space
        self.pos = pygame.Vector2(init_pos)
        # self.body = pymunk.Body(1, 1666)

        vs = [(-width / 2, -height / 2), (width / 2, -height / 2),
              (width / 2, height / 2), (-width / 2, height / 2)]
        mass = 10
        moment = pymunk.moment_for_poly(mass, vs)
        self.body = pymunk.Body(mass, moment)
        self.body.position = self.pos.x, -self.pos.y + 500
        self.shape = pymunk.Poly(self.body, vs)
        self.shape.friction = 0.5
        self.body.velocity = 10, 100
        self.space.add(self.body, self.shape)

    def update(self, events, dt):
        self.die()
        self.pos = pygame.Vector2(self.body.position[0], -self.body.position[1]+500)
        self.rect.center = self.pos

    def die(self):
        SCREEN_HEIGHT = 1000
        if self.rect.y > SCREEN_HEIGHT or self.rect.y < -100:
            self.kill()


def main():
    pygame.init()
    screen = pygame.display.set_mode((500, 500))
    clock = pygame.time.Clock()
    dt = 0

    space = pymunk.Space()
    space.gravity = 0, 0

    player = Player(space, (10, -10))
    satellite = Satellite(space, (100, 200))

    sprites = pygame.sprite.Group(player, satellite)

    # the "world" is now bigger than the screen
    # so we actually have anything to move the camera to
    background = pygame.Surface((1500, 1500))
    background.fill((30, 30, 30))

    # a camera is just two values: x and y
    # we use a vector here because it's easier to handle than a tuple
    camera = pygame.Vector2((0, 0))

    for _ in range(3000):
        x, y = random.randint(0, 1000), random.randint(0, 1000)
        pygame.draw.rect(background, pygame.Color('green'), (x, y, 2, 2))
    ticks_to_next_spawn = 10
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return

        ticks_to_next_spawn -= 1
        if ticks_to_next_spawn <= 0:
            ticks_to_next_spawn = 10
            x_pos = np.random.uniform(100, 400)
            satellite = Satellite(space, (x_pos, 500))
            sprites.add(satellite)

        # copy/paste because I'm lazy
        # just move the camera around
        pressed = pygame.key.get_pressed()
        camera_move = pygame.Vector2()
        if pressed[pygame.K_UP]: camera_move += (0, 1)
        if pressed[pygame.K_LEFT]: camera_move += (1, 0)
        if pressed[pygame.K_DOWN]: camera_move += (0, -1)
        if pressed[pygame.K_RIGHT]: camera_move += (-1, 0)
        if camera_move.length() > 0: camera_move.normalize_ip()
        camera += camera_move*(dt / 5)

        sprites.update(events, dt)

        # before drawing, we shift everything by the camera's x and y values
        screen.blit(background, camera)
        for s in sprites:

            p = s.shape.body.position
            p = Vec2d(p.x, flipy(p.y))

            # we need to rotate 180 degrees because of the y coordinate flip
            angle_degrees = math.degrees(s.shape.body.angle) + 180
            rotated_logo_img = pygame.transform.rotate(s.image, angle_degrees)

            offset = Vec2d(rotated_logo_img.get_size()) / 2.
            p = p - offset + s.rect.move(*camera)

            screen.blit(rotated_logo_img, p)

        pygame.display.update()
        dt = clock.tick(60)
        space.step(dt/1000)


if __name__ == '__main__':
    main()
