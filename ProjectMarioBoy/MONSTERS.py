import pygame

import pyganim
from CONSTANTS import BLUE, ANIMATION_DELAY

ANIMATED_HELL_HOUND = [('data/images/fire1.png', ANIMATION_DELAY),
                       ('data/images/fire2.png', ANIMATION_DELAY)]

"""Класс смертельно опасного огонька"""


class HellHound(pygame.sprite.Sprite):

    def __init__(self, x, y, move_speed_x, move_speed_y, max_left, max_up):
        super(HellHound, self).__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(BLUE)
        self.rect = pygame.Rect(x, y, 40, 40)
        self.image.set_colorkey(BLUE)
        self.x_velocity = self.y_velocity = 0

        # устанавливаем параметры
        self.start_x = x  # начальные
        self.start_y = y  # координаты
        self.move_speed_horizontal = move_speed_x  # скорость по х
        self.move_speed_vertical = move_speed_y  # скорость по у
        self.max_left_direction = max_left  # максимальная величина ухода от начальных координат по х
        self.max_up_direction = max_up  # по у

        self.ANIMATED_HELL_HOUND = pyganim.PygAnimation(ANIMATED_HELL_HOUND)
        self.ANIMATED_HELL_HOUND.play()
        self.ANIMATED_HELL_HOUND.blit(self.image, (0, 0))

    def update(self, obstacles):

        self.image.fill(BLUE)
        self.ANIMATED_HELL_HOUND.blit(self.image, (0, 0))

        self.rect.x += self.move_speed_horizontal
        self.rect.y += self.move_speed_vertical

        self.collide(obstacles)

        if abs(self.start_x - self.rect.x) > self.max_left_direction:  # проверяем не превысило ли расстояние от
            self.move_speed_horizontal = -self.move_speed_horizontal  # текущих максимального значения
            # если да то меняем направление движения
        if abs(self.start_y - self.rect.y) > self.max_up_direction:
            self.move_speed_vertical = -self.move_speed_vertical

    def collide(self, obstacles):  # проверка столкновений с блоками или другими монстрами
        for obstacle in obstacles:
            if pygame.sprite.collide_rect(self, obstacle) and self != obstacle:
                self.move_speed_horizontal = -self.move_speed_horizontal  # если да то меняем направление движения
                self.move_speed_vertical = -self.move_speed_vertical
