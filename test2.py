import math

import pygame
import random
import pymunk
from pygame.color import *
import numpy as np
from pymunk import Vec2d


def flipy(y):
    """Small hack to convert chipmunk physics to pygame coordinates"""
    return -y + 600


class Player(pygame.sprite.Sprite):
    def __init__(self, space, init_pos=(0, 0), image_shape=None):
        super().__init__()
        self.image = pygame.image.load("nacho_sprite.png")
        if image_shape:
            self.image = pygame.transform.scale(self.image, image_shape)
        self.rect = self.image.get_bounding_rect()
        width = self.rect.width
        height = self.rect.height
        self.space = space
        self.pos = pygame.Vector2(init_pos)

        vs = [(-width / 2, -height / 2), (width / 2, -height / 2),
              (width / 2, height / 2), (-width / 2, height / 2)]
        mass = 5
        moment = pymunk.moment_for_poly(mass, vs)
        self.body = pymunk.Body(mass, moment)
        self.body.force = (0, -250)
        self.body.position = self.pos.x, -self.pos.y + 500
        self.shape = pymunk.Poly(self.body, vs)
        self.shape.friction = 0.5
        self.space.add(self.body, self.shape)

    def update(self, events, dt, other_sprites=None):
        pressed = pygame.key.get_pressed()
        move = pygame.Vector2((0, 0))
        non_player_sprites = other_sprites.copy()
        non_player_sprites.remove(self)
        is_collided = pygame.sprite.spritecollideany(self, non_player_sprites)

        if pressed[pygame.K_w] and is_collided:
            move += (0, 1)
            move.normalize_ip()
            self.body.apply_impulse_at_local_point(move * 100)
        if pressed[pygame.K_a] and is_collided:
            move += (-1, 0)
            move.normalize_ip()
            self.body.apply_impulse_at_local_point(move * 20)
        if pressed[pygame.K_d] and is_collided:
            move += (1, 0)
            move.normalize_ip()
            self.body.apply_impulse_at_local_point(move * 20)

        # if you used pymunk before, you'll probably already know
        # that you'll have to invert the y-axis to convert between
        # the pymunk and the pygame coordinates.
        self.body.force = (0, -250)
        self.pos = pygame.Vector2(self.body.position[0], -self.body.position[1]+500)
        self.rect.center = self.pos
        self.body.angle = 0

class Satellite(pygame.sprite.Sprite):
    def __init__(self, space, image_filename, init_pos=(0, 0), init_velocity=(0, 0), mass=1, image_shape=None):
        super().__init__()
        self.image = pygame.image.load(image_filename)
        if image_shape:
            self.image = pygame.transform.scale(self.image, image_shape)
        self.rect = self.image.get_bounding_rect()
        width = self.rect.width
        height = self.rect.height
        self.space = space
        self.pos = pygame.Vector2(init_pos)

        vs = [(-width / 2, -height / 2), (width / 2, -height / 2),
              (width / 2, height / 2), (-width / 2, height / 2)]
        moment = pymunk.moment_for_poly(mass, vs)
        self.body = pymunk.Body(mass, moment)
        self.body.position = self.pos.x, -self.pos.y + 500
        self.shape = pymunk.Poly(self.body, vs)
        self.shape.friction = 0.5
        self.body.velocity = init_velocity
        self.space.add(self.body, self.shape)

    def update(self, events, dt, other_sprites=None):
        self.die()
        self.pos = pygame.Vector2(self.body.position[0], -self.body.position[1]+500)
        self.rect.center = self.pos

    def die(self):
        SCREEN_HEIGHT = 1000
        if self.rect.y > SCREEN_HEIGHT or self.rect.y < -100:
            self.kill()

def create_geosynch_satellites(space):
    geosynch_satellite_sprites = []

    mass = 200
    image_filename = "satellite_large_img_transparent.png"
    satellite = Satellite(space, image_filename, init_pos=(100, 30), mass=mass, image_shape=(100, 50))
    geosynch_satellite_sprites.append(satellite)

    satellite = Satellite(space, image_filename, init_pos=(250, 50), mass=mass, image_shape=(100, 50))
    geosynch_satellite_sprites.append(satellite)

    satellite = Satellite(space, image_filename, init_pos=(400, 70), mass=mass, image_shape=(100, 50))
    geosynch_satellite_sprites.append(satellite)

    satellite = Satellite(space, image_filename, init_pos=(550, 90), mass=mass, image_shape=(100, 50))
    geosynch_satellite_sprites.append(satellite)

    satellite = Satellite(space, image_filename, init_pos=(700, 110), mass=mass, image_shape=(100, 50))
    geosynch_satellite_sprites.append(satellite)

    return geosynch_satellite_sprites


def main():
    debug = True
    pygame.init()
    screen = pygame.display.set_mode((500, 500))
    clock = pygame.time.Clock()
    dt = 0

    space = pymunk.Space()
    space.gravity = 0, 0

    player = Player(space, (55, -10))

    sprites = pygame.sprite.Group(player)
    level_sprite_list = create_geosynch_satellites(space)
    sprites.add(*level_sprite_list)

    # the "world" is now bigger than the screen
    # so we actually have anything to move the camera to

    background_width = 15000
    background_height = 1500

    background = pygame.Surface((background_width, background_height))
    background.fill((30, 30, 30))

    # a camera is just two values: x and y
    # we use a vector here because it's easier to handle than a tuple

    for _ in range(80000):
        x, y = random.randint(0, background_width), random.randint(0, background_height)
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
            satellite = Satellite(space, "nacho_sprite.png", init_pos=(x_pos, 500), init_velocity=(10, 100))
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
        # camera += camera_move*(dt / 5)
        camera = pygame.Vector2(-player.pos[0] + 210, -player.pos[1] + 210)

        sprites.update(events, dt, sprites)

        # before drawing, we shift everything by the camera's x and y values
        screen.blit(background, camera)
        for s in sprites:

            p = s.shape.body.position
            p = Vec2d(p.x, flipy(p.y))

            # we need to rotate 180 degrees because of the y coordinate flip
            angle_degrees = math.degrees(s.shape.body.angle) + 180
            rotated_logo_img = pygame.transform.rotate(s.image, angle_degrees)

            offset = Vec2d(rotated_logo_img.get_size()) / 2
            p = p + camera - offset

            screen.blit(rotated_logo_img, p)

            if debug:
                ps = [p_tmp.rotated(s.shape.body.angle) + s.shape.body.position for p_tmp in s.shape.get_vertices()]
                ps = [(p_tmp.x, flipy(p_tmp.y)) + camera for p_tmp in ps]
                ps += [ps[0]]
                pygame.draw.lines(screen, THECOLORS["red"], False, ps, 1)

        pygame.display.update()
        dt = clock.tick(60)
        space.step(dt/1000)


if __name__ == '__main__':
    main()
