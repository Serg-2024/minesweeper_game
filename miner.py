import pygame as pg
import pandas as pd
from pygame.math import Vector2 as V2
from itertools import product
from datetime import datetime
from random import randint
pg.init()
FONT24 = pg.font.Font(None, 24)
FONT24.bold = True
FONT60 = pg.font.Font(None, 60)
FLAP = pg.USEREVENT + 1
pg.time.set_timer(FLAP,50)
# todo: free initial collisions
class Game:
    def __init__(self):
        self.screen = pg.display.set_mode((800, 600))
        self.running = True
        self.clock = pg.time.Clock()
        self.current_level = 1
        self.difficulty = 21
        self.flowers = self.difficulty//3
        self.thorns = self.difficulty - self.flowers
        self.level = Level(self.current_level, self.difficulty)
        self.bee_index = 0
        self.direction = None
        self.max_lives = self.lives = 5
        self.status = 'play'
        self.pause = False
        self.game_duration = 300
        self.start_time = None
        self.stop_time = None
    def run(self):
        self.start_time = datetime.now()
        while self.running:
            self.screen.fill('brown')
            self.level.map.update()
            self.level.check_collision()
            self.level.map.draw(self.screen)
            self.check_status()
            if self.pause: self.show_menu()
            self.event_handler()
            self.timer_handler(self.start_time)
            pg.display.flip()
            self.clock.tick(30)
        pg.quit()
    def event_handler(self):
        for event in pg.event.get():
            if event.type == pg.QUIT: self.running = False
            elif event.type == FLAP: self.bee_index = not self.bee_index
            elif event.type == pg.MOUSEBUTTONDOWN and self.status in ['play', 'win'] and not self.pause:
                self.level.bee.change_direction(event.pos)
            elif event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.pause = True
                self.stop_time = datetime.now()
    def timer_handler(self, start_time):
        if self.pause: text = FONT24.render('- : -', True, 'brown')
        else:
            timer = self.game_duration - (datetime.now() - start_time).seconds
            if timer <= 0: self.status = 'no_time'
            text = FONT24.render('{}:{:02d}'.format(*divmod(timer, 60)), True, 'brown')
        text_rect = text.get_rect(midtop=(400, 570))
        pg.draw.rect(self.screen, 'gold3', (375, 567, 50, 20))
        self.screen.blit(text, text_rect)
    def check_status(self):
        if self.status == 'level_up':
            if not self.level.map:
                self.status = 'play'
                self.new_game(self.current_level, self.difficulty)
        else:
            if self.lives == 0: self.status = 'no_lives'
            if self.flowers == 0:
                self.status = 'win'
                exit_collision = pg.sprite.collide_mask(self.level.bee, self.level.exit)
                if self.thorns == 0 or exit_collision:
                    self.status = 'level_up'
                    self.current_level += 1
                    self.current_level = 1 if self.current_level > self.level.max_level else self.current_level
                    self.difficulty += 1
                    self.level.map.draw(self.screen)
                    text = FONT60.render(f'LEVEL UP! - #{self.current_level}', True, 'gold', 'brown')
                    self.screen.blit(text, text.get_rect(center=(400, 300)))
                    pg.display.flip()
                    pg.time.wait(1000)
        if self.status not in ['play', 'win', 'level_up']: self.pause = True; self.stop_time = datetime.now()
        self.screen.blit(FONT24.render(f'Thorns: {self.thorns}', True, 'grey60'), (50, 570))
        self.screen.blit(FONT24.render(f'Flowers: {self.flowers}', True, 'cyan'), (150, 570))
        self.screen.blit(FONT24.render(f'Level: {self.current_level}', True, 'gold'), (250, 570))
        self.screen.blit(FONT24.render(f'Lives: {self.lives}', True, 'gold'), (700, 570))
    def show_menu(self):
        timer = datetime.now() - self.stop_time
        if self.status in ['no_time', 'no_lives']: text, text2 = 'TRY AGAIN', 'NEW GAME'
        else: text, text2 = 'RESTART', 'RESUME'
        label = {'no_time': 'time is over, try again!',
                 'no_lives': 'no more lives, try again!',
                 'win': 'good job, go to exit!',
                 'play': 'good job, keep going!',
                 'clear': 'excellent, level up!'}.get(self.status)
        rect = pg.draw.rect(self.screen, 'gold', (200, 20, 400, 50), 0, 10)
        pg.draw.rect(self.screen, 'brown', (200, 20, 400, 50), 5, 10)
        label_text = FONT24.render(label, True, 'brown')
        label_rect = label_text.get_rect(center=rect.center)
        self.screen.blit(label_text, label_rect)
        self.restart = Button((250, 100), text)
        self.resume = Button((250, 250), text2)
        self.quit_game = Button((250, 400), 'QUIT')
        if self.restart.draw(self.screen): self.status = 'level_up'; self.pause = False
        if self.resume.draw(self.screen):
            if text2 == 'NEW GAME': self.status = 'level_up'; self.current_level = 1
            else: self.pause = False; self.start_time += timer
        if self.quit_game.draw(self.screen): self.running = False
    def new_game(self, level, difficulty):
        self.level.level = self.level.get_curr_level(level, difficulty)
        self.level.map.empty()
        self.level.collidable.empty()
        self.level.draw()
        self.start_time = datetime.now()
        self.stop_time = None
        self.pause = False
        self.direction = None
        self.lives = self.max_lives
        self.flowers = self.difficulty // 3
        self.thorns = self.difficulty - self.flowers

class Level:
    def __init__(self, curr_level, difficulty):
        self.levels = pd.read_csv('levels.csv', sep=';')
        self.max_level = self.levels.level.max()
        self.level = self.get_curr_level(curr_level, difficulty)
        self.size = 22
        self.start_point = 100, 100
        self.hex_image = self.get_hex_image(self.size, 'gold')
        self.flower_image = self.get_flower_image(self.size)
        self.thorn_image = self.get_thorn_image(self.size)
        self.map = pg.sprite.Group()
        self.collidable = pg.sprite.Group()
        self.bee = None
        self.exit = None
        self.bee_pos = None
        self.draw()
    def get_curr_level(self, level, difficulty):
        level_df = self.levels.query('level==@level').reset_index().drop('index',axis=1)
        level_map_df = level_df['map'].str.split('', expand=True).iloc[:, 1:-1].rename(columns=lambda x: x - 1)
        level_map_df = level_map_df.rename_axis(index='y', columns='x').unstack().reset_index().rename(columns={0: 'hex'})
        tiles_df = level_map_df.query('hex == "1"').sample(difficulty)
        tiles_df['entity'] = 1
        tiles_df.drop(columns=['x', 'y', 'hex'], inplace=True)
        mines = tiles_df.add(tiles_df.sample(difficulty//3), fill_value=0)
        df = pd.concat([level_map_df, mines], axis=1).fillna(0)
        prod = list(product([1, 0, -1], repeat=2))
        odd_row_off = [i for i in prod if i not in [(-1, 1), (-1, -1), (0, 0)]]
        even_row_off = [i for i in prod if i not in [(1, -1), (1, 1), (0, 0)]]
        def adjacent(s):
            row_off = odd_row_off if s.y % 2 else even_row_off
            adjacents = [i[0] for i in [df[(df.x == s.x + x) & (df.y == s.y + y)].entity.values for x, y in row_off] if i]
            adj_num = len(adjacents)
            if adj_num:
                adj_types = set(adjacents)
                color = 'gold' if {1, 2} <= adj_types else 'cyan' if {2} <= adj_types else 'grey10'
            return (adj_num, color) if adj_num else 0
        df['adjacent'] = df.apply(adjacent, axis=1)
        return df
    def draw(self):
        for row in self.level.itertuples(index=False, name='row'):
            if row.hex in '1be':
                image = {0: self.get_number_image(self.size, row.adjacent),
                         2: self.flower_image,
                         1: self.thorn_image}.get(row.entity)
                rect = image.get_rect()
                if row.y % 2: rect.topleft = (rect.w / 2 + 20 + row.x * rect.w, rect.h*.75*row.y + 20)
                else: rect.topleft = (20 + row.x * rect.w, rect.h*.75*row.y+20)
                if row.hex == '1': Hex((self.map, self.collidable), self.hex_image, image, rect, row.adjacent == 0, self.size, row.entity)
                elif row.hex == 'b': self.bee = Bee(rect.topleft, self.map, self.size)
                elif row.hex == 'e':
                    self.exit = Hex((self.map, self.collidable), self.hex_image, self.get_hex_image(self.size, 'green'), rect, row.adjacent == 0, self.size, row.entity)
        self.map.remove(self.bee)
        self.map.add(self.bee)
    def get_hex_image(self, size, color):
        image = pg.Surface(self.get_hex_size(size))
        image.set_colorkey('black')
        rect = image.get_rect()
        self.draw_hex(image, size - 2, f'{color}3', rect.center)
        self.draw_hex(image, size, f'{color}2', rect.center, 1)
        return image.convert_alpha()
    def get_hex_size(self, size):
        dummy_surf = pg.Surface((150, 150))
        hex_ = self.draw_hex(dummy_surf, size, 'gold', self.start_point, 1)
        return hex_.size
    def draw_hex(self, surf, size, color, start_point, width=0):
        vec = V2(0, size)
        polygon = []
        for angle in range(0, 361, 60):
            side = vec.rotate(angle) + start_point
            polygon.append(side)
        return pg.draw.polygon(surf, color, polygon, width)
    def get_flower_image(self, size):
        flower_image = self.get_hex_image(size,'brown')
        flower_rect = flower_image.get_rect()
        pg.draw.circle(flower_image, 'gold', flower_rect.center, size / 3)
        petal_pos = V2(0, size / 2)
        for a in range(0, 361, 40):
            pg.draw.circle(flower_image, 'cyan', petal_pos.rotate(a) + V2(flower_rect.center), size / 5)
        return flower_image.convert_alpha()
    def get_thorn_image(self, size):
        thorn_image = self.get_hex_image(size,'brown')
        thorn_rect = thorn_image.get_rect()
        pg.draw.circle(thorn_image, 'grey1', thorn_rect.center, size / 3)
        petal_pos = V2(0, size / 1.5)
        for a in range(0, 361, 30):
            pg.draw.line(thorn_image, 'grey60', thorn_rect.center, petal_pos.rotate(a) + V2(thorn_rect.center), 3)
            pg.draw.line(thorn_image, 'grey10', thorn_rect.center, petal_pos.rotate(a) + V2(thorn_rect.center), 2)
        return thorn_image.convert_alpha()
    def get_number_image(self, size, adjacent):
        number_image = self.get_hex_image(size, 'brown')
        number_rect = number_image.get_rect()
        if adjacent: number = adjacent[0]; color = adjacent[1]
        else: number = 'o'; color = 'gray'
        text_image = FONT24.render(str(number), True, color)
        text_rect = text_image.get_rect(center=number_rect.center)
        number_image.blit(text_image, text_rect)
        return number_image.convert_alpha()
    def check_collision(self):
        self.check_circle_collisions()
        collisions = pg.sprite.spritecollide(self.bee, self.collidable, False, collided=pg.sprite.collide_mask)
        for collision in collisions:
            if collision.entity == 1:
                game.lives -= 1
                game.thorns -= 1
                self.bee.step_back()
                self.bee.spinning = True
            elif collision.entity == 2:
                game.flowers -= 1
                if game.flowers == 0: self.reveal_exit()
            collision.image = collision.entity_image
            self.collidable.remove(collision)
        if collisions: self.adjacent_collisions()
    def check_circle_collisions(self):
        collisions = pg.sprite.spritecollide(self.bee, self.collidable, False, collided=pg.sprite.collide_circle)
        for collision in collisions:
            if collision.empty and not collision.entity: collision.kill()
    def adjacent_collisions(self):
        for adj in self.collidable.sprites():
            if adj.entity in [1, 2]:
                group = self.collidable.copy()
                self.entity_collision(adj, group)
    def entity_collision(self, adj, group):
        group.remove(adj)
        collisions = pg.sprite.spritecollide(adj, group, False, collided=pg.sprite.collide_circle)
        if not collisions:
            adj.image = adj.entity_image
            self.collidable.remove(adj)
            if adj.entity == 1: game.thorns -= 1
            elif adj.entity == 2:
                game.flowers -= 1
                if game.flowers == 0: self.reveal_exit()
        elif all(collision.entity in [1, 2] for collision in collisions):
            for collision in collisions:
                group.remove(adj)
                self.entity_collision(collision, group)
    def reveal_exit(self):
        self.exit.image = self.exit.entity_image
        self.map.add(self.exit)
        self.collidable.remove(self.exit)
        text = FONT60.render('GO TO GREEN EXIT!', True, 'gold', 'brown')
        surf = pg.display.get_surface()
        self.map.draw(surf)
        surf.blit(text, text.get_rect(center=(400, 300)))
        surf.blit(self.exit.image, self.exit.rect)
        pg.display.flip()
        pg.time.delay(1000)

class Hex(pg.sprite.Sprite):
    def __init__(self, groups, hex_image, entity_image, rect, empty, size, entity):
        super().__init__(*groups)
        self.image = hex_image
        self.rect = rect
        self.empty = empty
        self.entity_image = entity_image
        self.radius = size
        self.entity = entity
        self.mask = pg.mask.from_surface(self.image)
        self.timer = randint(1, 5)
        self.speed = randint(10, 20)
    def update(self):
        if game.status == 'level_up': self.timer -= 1
        if self.timer <= 0:
            self.rect.move_ip(0, self.speed)
            self.speed += 2
            if self.rect.y > 700: self.kill()

class Bee(pg.sprite.Sprite):
    def __init__(self, pos, group, size):
        super().__init__(group)
        self.indx = 0
        self.angle = 0
        self.speed = 6
        self.radius = size * 2
        self.direction = None
        self.pos = pos
        self.end_pos = self.pos
        self.images = [self.get_bee_image(30, 10), self.get_bee_image(30, -10)]
        self.offset = self.images[0].get_rect().center
        self.image = self.turn_bee_image(self.angle, self.indx)
        self.rect = self.image.get_rect(center=V2(self.pos) + self.offset)
        self.mask = self.get_mask()
        self.area = pg.Rect(10, 10, 780, 540)
        self.spinning = False
        self.rotation = 1080
        self.rotation_speed = 60
    def get_bee_image(self, size, angle):
        image = pg.Surface((size, size * 1.5))
        image.set_colorkey('black')
        rect = image.get_rect()
        image.blit(*self.get_wing_image(rect, angle))
        pg.draw.ellipse(image, 'brown', rect.inflate(0, -30))
        pg.draw.ellipse(image, 'yellow', rect.inflate(0, -32))
        for i in range(3): pg.draw.line(image, 'brown', (5 + 6 * i, 17), (5 + 6 * i, 28), 3)
        pg.draw.ellipse(image, 'yellow', rect.inflate(0, -32), 1)
        return image.convert_alpha()
    def get_wing_image(self, rect, angle):
        wing = rect.inflate(-18, -6)
        wing_image = pg.Surface(wing.size)
        wing_image.set_colorkey('black')
        pg.draw.rect(wing_image, 'white', ((0, 0), wing.size), 1, 6)
        wing_image = pg.transform.rotate(wing_image, angle)
        wing_rect = wing_image.get_rect(center=wing.center)
        return wing_image, wing_rect
    def turn_bee_image(self, angle=0, indx=0):
        return pg.transform.rotate(self.images[indx], angle)
    def change_direction(self, mouse_pos):
        self.direction = (V2(mouse_pos) - V2(self.pos) - self.offset).normalize()
        self.angle = self.direction.angle_to(V2(1, 0))
        self.end_pos = mouse_pos
    def update(self):
        if game.status == 'level_up': self.kill()
        self.image = self.turn_bee_image(self.angle, game.bee_index)
        self.rect = self.image.get_rect(center=V2(self.pos) + self.offset)
        self.mask = self.get_mask()
        if self.spinning: self.spin()
        else:
            if self.direction:
                self.pos = self.pos + self.direction * self.speed
                if (V2(self.end_pos) - V2(self.pos) - self.offset).length() <= self.speed: self.direction = None
            self.rect.clamp_ip(self.area)
    def draw(self, surf):
        surf.blit(self.image, self.rect)
    def get_mask(self):
        surf = pg.Surface(self.rect.size)
        surf.set_colorkey('black')
        rect = surf.get_rect()
        pg.draw.circle(surf, 'white', rect.center, 5)
        return pg.mask.from_surface(surf)
    def step_back(self):
        if self.direction:
            self.pos = self.pos - self.direction * self.speed * 4
            self.direction = None
    def spin(self):
        self.angle += self.rotation_speed
        self.rotation -= self.rotation_speed
        if self.rotation <= 0: self.rotation = 1080; self.spinning = False

class Button:
    def __init__(self, pos, text):
        self.rect = pg.Rect(*pos,300,100)
        self.text = FONT60.render(text, True, 'brown')
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.color = 'gold2'
    def draw(self, surf):
        mouse_pos = pg.mouse.get_pos()
        collision = self.rect.collidepoint(mouse_pos)
        color = 'olivedrab1' if collision else self.color
        pg.draw.rect(surf, color, self.rect, 0, 10)
        pg.draw.rect(surf, 'brown', self.rect, 5, 10)
        surf.blit(self.text, self.text_rect)
        return True if collision and pg.mouse.get_pressed()[0] else False

if __name__ == '__main__':
    game = Game()
    game.run()