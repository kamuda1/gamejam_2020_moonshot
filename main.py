import pygame as pg
import math
import pygame
import random
import pymunk
import numpy as np
from pymunk import Vec2d
from game_objects import Satellite, Player, resource_path
import sys


class Control:
    def __init__(self):
        self.done = False
        self.fps = 60
        self.screen = pg.display.set_mode((500, 500))
        self.screen_rect = self.screen.get_rect()
        self.clock = pg.time.Clock()

    def setup_states(self, state_dict, start_state):
        self.state_dict = state_dict
        self.state_name = start_state
        self.state = self.state_dict[self.state_name]

    def flip_state(self):
        self.state.done = False
        previous, self.state_name = self.state_name, self.state.next
        self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        self.state.startup()
        self.state.previous = previous

    def update(self, dt):
        if self.state.quit:
            self.done = True
        elif self.state.done:
            self.flip_state()
        self.state.update(self.screen, dt)

    def event_loop(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            self.state.get_event(event)

    def main_game_loop(self):
        while not self.done:
            delta_time = self.clock.tick(self.fps) / 1000.0
            self.event_loop()
            self.update(delta_time)
            pg.display.update()


class MenuManager:
    def __init__(self):
        self.selected_index = 0
        self.last_option = None
        self.selected_color = (255, 255, 0)
        self.deselected_color = (255, 255, 255)

    def draw_menu(self, screen):
        '''handle drawing of the menu options'''
        for i, opt in enumerate(self.rendered["des"]):
            opt[1].center = (self.screen_rect.centerx, self.from_bottom + i * self.spacer)
            if i == self.selected_index:
                rend_img, rend_rect = self.rendered["sel"][i]
                rend_rect.center = opt[1].center
                screen.blit(rend_img, rend_rect)
            else:
                screen.blit(opt[0], opt[1])

    def update_menu(self):
        self.mouse_hover_sound()
        self.change_selected_option()

    def get_event_menu(self, event):
        if event.type == pg.KEYDOWN:
            '''select new index'''
            if event.key in [pg.K_UP, pg.K_w]:
                self.change_selected_option(-1)
            elif event.key in [pg.K_DOWN, pg.K_s]:
                self.change_selected_option(1)

            elif event.key == pg.K_RETURN:
                self.select_option(self.selected_index)
        self.mouse_menu_click(event)

    def mouse_hover_sound(self):
        '''play sound when selected option changes'''
        for i, opt in enumerate(self.rendered["des"]):
            if opt[1].collidepoint(pg.mouse.get_pos()):
                if self.last_option != opt:
                    self.last_option = opt

    def mouse_menu_click(self, event):
        '''select menu option '''
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            for i, opt in enumerate(self.rendered["des"]):
                if opt[1].collidepoint(pg.mouse.get_pos()):
                    self.selected_index = i
                    self.select_option(i)
                    break

    def pre_render_options(self):
        '''setup render menu options based on selected or deselected'''
        font_deselect = pg.font.SysFont("arial", 50)
        font_selected = pg.font.SysFont("arial", 70)

        rendered_msg = {"des": [], "sel": []}
        for option in self.options:
            d_rend = font_deselect.render(option, 1, self.deselected_color)
            d_rect = d_rend.get_rect()
            s_rend = font_selected.render(option, 1, self.selected_color)
            s_rect = s_rend.get_rect()
            rendered_msg["des"].append((d_rend, d_rect))
            rendered_msg["sel"].append((s_rend, s_rect))
        self.rendered = rendered_msg

    def select_option(self, i):
        '''select menu option via keys or mouse'''
        if i == len(self.next_list):
            self.quit = True
        else:
            self.next = self.next_list[i]
            self.done = True
            self.selected_index = 0

    def change_selected_option(self, op=0):
        '''change highlighted menu option'''
        for i, opt in enumerate(self.rendered["des"]):
            if opt[1].collidepoint(pg.mouse.get_pos()):
                self.selected_index = i
        if op:
            self.selected_index += op
            max_ind = len(self.rendered['des']) - 1
            if self.selected_index < 0:
                self.selected_index = max_ind
            elif self.selected_index > max_ind:
                self.selected_index = 0


class States(Control):
    def __init__(self):
        Control.__init__(self)
        self.done = False
        self.next = None
        self.quit = False
        self.previous = None


class Menu(States, MenuManager):
    def __init__(self):
        States.__init__(self)
        MenuManager.__init__(self)
        self.next = 'game'
        self.options = ['Play', 'Quit']
        self.next_list = ['game']
        self.pre_render_options()
        self.from_bottom = 200
        self.spacer = 75

    def cleanup(self):
        print('cleaning up Main Menu state stuff')

    def startup(self):
        print('starting Main Menu state stuff')

    def get_event(self, event):
        if event.type == pg.QUIT:
            self.quit = True
        self.get_event_menu(event)

    def update(self, screen, dt):
        self.update_menu()
        self.draw(screen)

    def draw(self, screen):
        screen.fill((255, 0, 0))
        self.draw_menu(screen)


class Game(States):
    def __init__(self):
        States.__init__(self)
        self.next = 'menu'
        self.startup()

    def cleanup(self):
        print('cleaning up Game state stuff')
        self.space = None
        self.player = None
        self.sprites = None

    def startup(self):
        pg.mixer.init(frequency=192000)
        rocket_boost_sound = pg.mixer.Sound(resource_path("sounds/rocket_boost.wav"))
        pg.mixer.Channel(0).set_volume(50)
        pg.mixer.Channel(0).play(pygame.mixer.Sound(resource_path("sounds/space_theme.wav")), loops=-1)

        x_offset = 500
        self.background_width = 15000
        self.background_height = 1500
        self.level_end = 3000

        self.space = pymunk.Space()
        self.space.gravity = 0, 0
        earth_image = pg.image.load(resource_path('images/earth.png'))
        self.earth_image = pg.transform.scale(earth_image, (self.background_height // 2, self.background_height // 2))
        self.earth_center = (x_offset - 650, self.background_height / 2 - 300)

        self.moon_image = pg.image.load(resource_path('images/moon.png'))
        self.moon_image = pg.transform.scale(self.moon_image, (200, 200))
        self.moon_center = (x_offset + self.level_end + 400, self.background_height / 2)

        self.player = Player(self.space, init_pos=(90 + x_offset, self.background_height / 2 - 10),
                             image_shape=[50, 30], moon_center=self.moon_center, boost_sound=rocket_boost_sound)

        self.sprites = pg.sprite.Group(self.player)
        level_sprite_list = self.create_geosynch_satellites(self.space, self.background_height,
                                                            screen_height=self.background_height,
                                                            end_x=x_offset + self.level_end)

        start_satellite = Satellite(self.space, init_pos=(100 + x_offset, 50 + self.background_height / 2), mass=500,
                                    image_shape=(100, 50), is_geosynch=True, screen_height=self.background_height)
        level_sprite_list.append(start_satellite)
        self.sprites.add(*level_sprite_list)

        self.background = pg.Surface((self.background_width, self.background_height))
        self.background.fill((30, 30, 30))

        for _ in range(80000):
            x, y = random.randint(0, self.background_width), random.randint(0, self.background_height)
            pg.draw.rect(self.background, (200, 200, 200), (x, y, 2, 2))

    def get_event(self, event):
        if event.type == pg.QUIT:
            self.done = True

    def flipy(self, y):
        """Small hack to convert chipmunk physics to pygame coordinates"""
        return -y + 600

    def create_geosynch_satellites(self, space, background_height: float, screen_height: float, start_x: int = 750,
                                   end_x: int = 8000, diff_x: int = 150):
        geosynch_satellite_sprites = []

        mass = 500
        for x_pos in np.arange(start_x, end_x, diff_x):
            y_pos = np.random.uniform(0.9 * background_height / 2, 1.1 * background_height / 2)
            satellite = Satellite(space, init_pos=(x_pos, y_pos), mass=mass, image_shape=(100, 50),
                                  is_geosynch=True, screen_height=screen_height)
            geosynch_satellite_sprites.append(satellite)

        return geosynch_satellite_sprites

    def update(self, screen, dt):
        moon_center = self.moon_center
        moon_image = self.moon_image
        earth_center = self.earth_center
        earth_image = self.earth_image
        level_end = self.level_end
        player = self.player
        background_height = self.background_height
        space = self.space
        sprites = self.sprites
        x_offset = 500
        events = pg.event.get()
        if random.random() < 0.05 and player.pos.x < x_offset + level_end:
            x_pos_max = player.pos.x + 750
            if x_pos_max > x_offset + level_end:
                x_pos_max = x_offset + level_end - 100
            x_pos = np.random.uniform(player.pos.x - 10, x_pos_max)
            init_velocity_x = np.random.uniform(-5, 5)
            init_velocity_y = -100 - np.random.lognormal(1, 3 + player.pos.x / 500.)
            init_velocity = (init_velocity_x, init_velocity_y)

            if random.random() <= 0.8:
                init_size = np.random.uniform(15, 25)
                satellite = Satellite(space, resource_path("images/sputnik_custom.png"), init_pos=(x_pos, -10),
                                      init_velocity=init_velocity,
                                      screen_height=background_height, image_shape=(int(init_size), int(init_size)),
                                      init_angular_velocity=np.random.uniform(-10, 10))
            else:
                init_size = np.random.uniform(35, 55)
                satellite = Satellite(space, resource_path("images/gold_satellite.png"), init_pos=(x_pos, -10),
                                      init_velocity=init_velocity,
                                      screen_height=background_height,
                                      image_shape=(int(3 * init_size), int(init_size)),
                                      init_angular_velocity=np.random.uniform(-10, 10), mass=5)
            sprites.add(satellite)

        pressed = pg.key.get_pressed()
        camera_move = pg.Vector2()
        if pressed[pg.K_UP]:
            camera_move += (0, 1)
        if pressed[pg.K_LEFT]:
            camera_move += (1, 0)
        if pressed[pg.K_DOWN]:
            camera_move += (0, -1)
        if pressed[pg.K_RIGHT]:
            camera_move += (-1, 0)
        if camera_move.length() > 0:
            camera_move.normalize_ip()
        camera = pg.Vector2(-player.pos[0] + 210, -player.pos[1] + 210)

        sprite_to_add = sprites.update(events, dt, sprites)
        if sprite_to_add:
            sprites.add(sprite_to_add)

        screen.blit(self.background, camera)
        screen.blit(earth_image, earth_center + camera)
        screen.blit(moon_image, moon_center + camera)

        for s in sprites:
            p = s.shape.body.position
            p = Vec2d(p.x, self.flipy(p.y))
            angle_degrees = math.degrees(s.shape.body.angle) + 180
            rotated_logo_img = pg.transform.rotate(s.image, angle_degrees)
            offset = Vec2d(rotated_logo_img.get_size()) / 2
            p = p + camera - offset

            screen.blit(rotated_logo_img, p)

        pg.display.update()
        dt = self.clock.tick(60)
        space.step(dt / 1000)

        if player.pos[1] > 0.8 * self.background_height:
            self.cleanup()
            self.done = True

    def draw(self, screen):
        screen.fill((0, 0, 255))


pg.init()
app = Control()
state_dict = {
    'menu': Menu(),
    'game': Game(),
}
app.setup_states(state_dict, 'menu')
app.main_game_loop()
pg.quit()
sys.exit()
