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
    def __init__(self, space, init_pos=(0, 0), image_shape=None, is_player=True, is_geosynch=False, moon_center=(0, 0),
                 boost_sound=None):
        super().__init__()
        self.game_over = False
        self.rocket_boost_sound = boost_sound
        self.is_geosynch = is_geosynch
        self.is_player = is_player
        self.image = pygame.image.load("catstronaut.png")
        self.moon_center = moon_center
        if image_shape:
            self.image = pygame.transform.scale(self.image, image_shape)
            self.image = pygame.transform.flip(self.image, True, True)
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
        self.can_jump = True

    def update(self, events, dt, other_sprites=None):
        pressed = pygame.key.get_pressed()
        non_player_sprites = other_sprites.copy()
        non_player_sprites.remove(self)
        is_collided = pygame.sprite.spritecollideany(self, non_player_sprites)
        lateral_strength = 20 if is_collided else 5
        if self.game_over is False:
            if is_collided:
                self.can_jump = True
            if self.body.position.x < self.moon_center[0] + 50:
                move = pygame.Vector2((0, 0))
                if pressed[pygame.K_w] and self.body.velocity[1] < 10 and self.can_jump:
                    self.can_jump = False
                    move += pygame.Vector2((0, 1)) * 300
                    pygame.mixer.Channel(1).play(self.rocket_boost_sound)
                if pressed[pygame.K_a] and np.abs(self.body.velocity[1]) < 20:
                    move += pygame.Vector2((-1, 0)) * lateral_strength
                if pressed[pygame.K_d] and np.abs(self.body.velocity[1]) < 20:
                    move += pygame.Vector2((1, 0)) * lateral_strength
                if self.body.position.x > 550:
                    self.body.apply_impulse_at_local_point(move)
                    self.body.force = (0, -250)

                if self.body.position.x < 550:
                    self.body.force = (1000, 200)
                self.pos = pygame.Vector2(self.body.position.x, -self.body.position.y+500)
                self.rect.center = self.pos

                self.body.angle = 0
            else:
                self.game_over = True

                self.body.angle += 0.05

        elif (np.abs(self.body.position.x-self.moon_center[0]) > 20 or
              np.abs((-self.body.position.y+500)-self.moon_center[1]) > 20):
            applied_force = (-15*(self.body.position.x-self.moon_center[0]),
                             15*((-self.body.position.y+500)-self.moon_center[1]))
            self.body.force = applied_force


class Satellite(pygame.sprite.Sprite):
    def __init__(self, space, image_filename=None, init_pos=(0, 0), init_velocity=(0, 0), mass=1, image_shape=None,
                 is_geosynch=False, is_player=False, screen_height=None, init_angular_velocity=0):
        if screen_height is None:
            screen_height = 1500
        self.screen_height = screen_height
        super().__init__()
        self.satellite_images_health = None
        if image_filename is None:
            self.satellite_images_health = {'low': "satellite_large_low_health.png",
                                            'med': "satellite_large_med_health.png",
                                            'high': "satellite_large_high_health.png",
                                            }
            image_filename = self.satellite_images_health['high']

        self.image = pygame.image.load(image_filename)
        self.is_geosynch = is_geosynch
        self.is_player = is_player

        self.health = 6
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
        self.body.angular_velocity = init_angular_velocity
        self.space.add(self.body, self.shape)

    def update(self, events, dt, other_sprites=None):
        self.pos = pygame.Vector2(self.body.position[0], -self.body.position[1]+500)
        self.rect.center = self.pos

        non_player_sprites = other_sprites.copy()
        non_player_sprites.remove(self)
        is_collided = pygame.sprite.spritecollideany(self, non_player_sprites)
        satellite_to_return = None

        if self.satellite_images_health:
            if 3 < self.health <= 5:
                self.image = pygame.image.load(self.satellite_images_health['med'])
            if self.health <= 3:
                self.image = pygame.image.load(self.satellite_images_health['low'])

        if is_collided and self.is_geosynch and is_collided.is_player is False and is_collided.is_geosynch is False:
            self.health -= 1
            is_collided.space.remove(is_collided.body, is_collided.shape)
            is_collided.kill()

        if self.health < 0 and self.is_geosynch is True:
            self.space.remove(self.body, self.shape)
            self.kill()
            new_vect = pygame.Vector2(self.body.position[0], -self.body.position[1] + 500)
            satellite_to_return = Satellite(self.space, "sputnik_custom.png", init_pos=new_vect,
                                            init_velocity=(0, 5), screen_height=self.screen_height)
            # other_sprites.add(satellite)

        self.die(other_sprites)
        return satellite_to_return

    def die(self, other_sprites):
        if self.rect.y > self.screen_height or self.rect.y < -100 or self.rect.x + 500 < other_sprites.sprites()[0].pos.x:
            self.kill()
            self.space.remove(self.body, self.shape)


def create_geosynch_satellites(space, background_height: float, screen_height, start_x: int = 750, end_x: int = 8000,
                               diff_x: int = 150):
    geosynch_satellite_sprites = []

    mass = 500
    for x_pos in np.arange(start_x, end_x, diff_x):
        y_pos = np.random.uniform(0.9 * background_height / 2, 1.1 * background_height / 2)
        satellite = Satellite(space, init_pos=(x_pos, y_pos), mass=mass, image_shape=(100, 50),
                              is_geosynch=True, screen_height=screen_height)
        geosynch_satellite_sprites.append(satellite)

    return geosynch_satellite_sprites


def main():
    debug = False
    pygame.init()
    screen = pygame.display.set_mode((500, 500))
    clock = pygame.time.Clock()
    dt = 0

    x_offset = 500
    pygame.mixer.init(frequency=192000)
    rocket_boost_sound = pygame.mixer.Sound("rocket_boost.wav")
    pygame.mixer.Channel(0).set_volume(50)
    pygame.mixer.Channel(0).play(pygame.mixer.Sound("space_theme.wav"), loops=-1)

    image_filename = "satellite_large_img_transparent.png"

    background_width = 15000
    background_height = 1500
    level_end = 3000

    space = pymunk.Space()
    space.gravity = 0, 0
    earth_image = pygame.image.load('earth.png')
    earth_image = pygame.transform.scale(earth_image, (background_height//2, background_height//2))
    earth_center = (x_offset - 650, background_height / 2 - 300)

    moon_image = pygame.image.load('moon.png')
    moon_image = pygame.transform.scale(moon_image, (200, 200))
    moon_center = (x_offset + level_end + 400, background_height / 2)

    player = Player(space, init_pos=(90 + x_offset, background_height / 2 - 10), image_shape=[50, 30],
                    moon_center=moon_center, boost_sound=rocket_boost_sound)

    sprites = pygame.sprite.Group(player)
    level_sprite_list = create_geosynch_satellites(space, background_height, screen_height=background_height,
                                                   end_x=x_offset + level_end)

    start_satellite = Satellite(space, init_pos=(100 + x_offset, 50 + background_height / 2), mass=500,
                                image_shape=(100, 50), is_geosynch=True, screen_height=background_height)
    level_sprite_list.append(start_satellite)
    sprites.add(*level_sprite_list)

    background = pygame.Surface((background_width, background_height))
    background.fill((30, 30, 30))

    # a camera is just two values: x and y
    # we use a vector here because it's easier to handle than a tuple

    for _ in range(80000):
        x, y = random.randint(0, background_width), random.randint(0, background_height)
        pygame.draw.rect(background, (200, 200, 200), (x, y, 2, 2))
    ticks_to_next_spawn = 10
    while True:
        events = pygame.event.get()
        for e in events:
            if e.type == pygame.QUIT:
                return

        ticks_to_next_spawn -= 1
        if ticks_to_next_spawn <= 0 and player.pos.x < x_offset + level_end:
            ticks_to_next_spawn_init = 20
            ticks_to_next_spawn = np.max([2, ticks_to_next_spawn_init - player.pos.x/1000])

            x_pos_max = player.pos.x + 750
            if x_pos_max > x_offset + level_end:
                x_pos_max = x_offset + level_end - 100
            x_pos = np.random.uniform(player.pos.x - 10, x_pos_max)
            init_velocity_x = np.random.uniform(-5, 5)
            init_velocity_y = -100 - np.random.lognormal(1, 3 + player.pos.x/500.)
            init_velocity = (init_velocity_x, init_velocity_y)

            if random.random() <= 0.8:
                init_size = np.random.uniform(15, 25)
                satellite = Satellite(space, "sputnik_custom.png", init_pos=(x_pos, -10), init_velocity=init_velocity,
                                      screen_height=background_height, image_shape=(int(init_size), int(init_size)),
                                      init_angular_velocity=np.random.uniform(-10, 10))
            else:
                init_size = np.random.uniform(35, 55)
                satellite = Satellite(space, "gold_satellite.png", init_pos=(x_pos, -10), init_velocity=init_velocity,
                                      screen_height=background_height, image_shape=(int(3*init_size), int(init_size)),
                                      init_angular_velocity=np.random.uniform(-10, 10), mass=5)
            sprites.add(satellite)

        # copy/paste because I'm lazy
        # just move the camera around
        pressed = pygame.key.get_pressed()
        camera_move = pygame.Vector2()
        if pressed[pygame.K_UP]:
            camera_move += (0, 1)
        if pressed[pygame.K_LEFT]:
            camera_move += (1, 0)
        if pressed[pygame.K_DOWN]:
            camera_move += (0, -1)
        if pressed[pygame.K_RIGHT]:
            camera_move += (-1, 0)
        if camera_move.length() > 0:
            camera_move.normalize_ip()
        camera = pygame.Vector2(-player.pos[0] + 210, -player.pos[1] + 210)

        sprite_to_add = sprites.update(events, dt, sprites)
        if sprite_to_add:
            sprites.add(sprite_to_add)

        # before drawing, we shift everything by the camera's x and y values
        screen.blit(background, camera)
        screen.blit(earth_image, earth_center + camera)
        screen.blit(moon_image, moon_center + camera)

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
