import pygame
import pymunk
import numpy as np


class Player(pygame.sprite.Sprite):
    def __init__(self, space, init_pos=(0, 0), image_shape=None, is_player=True, is_geosynch=False, moon_center=(0, 0),
                 boost_sound=None):
        super().__init__()
        self.game_over = False
        self.rocket_boost_sound = boost_sound
        self.is_geosynch = is_geosynch
        self.is_player = is_player
        self.image = pygame.image.load("images/catstronaut.png")
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
            self.satellite_images_health = {'low': "images/satellite_large_low_health.png",
                                            'med': "images/satellite_large_med_health.png",
                                            'high': "images/satellite_large_high_health.png",
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
            satellite_to_return = Satellite(self.space, "images/sputnik_custom.png", init_pos=new_vect,
                                            init_velocity=(0, 5), screen_height=self.screen_height)
            # other_sprites.add(satellite)

        self.die(other_sprites)
        return satellite_to_return

    def die(self, other_sprites):
        if self.rect.y > self.screen_height or self.rect.y < -100 or self.rect.x + 500 < other_sprites.sprites()[0].pos.x:
            self.kill()
            self.space.remove(self.body, self.shape)
