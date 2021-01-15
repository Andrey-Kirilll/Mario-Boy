import pygame

import pyganim
from CONSTANTS import ALL_BLOCK_WIDTH, ALL_BLOCK_HEIGHT, BLUE, ANIMATION_DELAY


"""Класс блок, является родителем для остальных классов дополнительных элементов. В случае ошибки установится
                                                                            изображение по умолчанию"""


class Block(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super(Block, self).__init__()
        self.image = pygame.Surface((40, 40))
        self.image.fill(BLUE)
        self.image = pygame.image.load('data/images/block_center.png')
        self.image.set_colorkey(BLUE)
        self.rect = pygame.Rect(x, y, ALL_BLOCK_WIDTH, ALL_BLOCK_HEIGHT)


"""Класс смертельных шипов"""


class DieBlock(Block):

    def __init__(self, x, y):
        super(DieBlock, self).__init__(x, y)
        self.image = pygame.image.load('data/images/dieBlock.png')


"""Класс портала (анимирован)"""


PORTAL_ANIMATION = [('data/images/portal1.png', ANIMATION_DELAY),
                    ('data/images/portal2.png', ANIMATION_DELAY)]


class Portal(Block):

    def __init__(self, x, y, go_x, go_y):
        super(Portal, self).__init__(x, y)
        self.go_x = go_x
        self.go_y = go_y
        self.PORTAL_ANIMATION = pyganim.PygAnimation(PORTAL_ANIMATION)
        self.PORTAL_ANIMATION.play()

    def update(self):
        self.image.fill(BLUE)
        self.PORTAL_ANIMATION.blit(self.image, (0, 0))


"""Класс принцессы (анимирован)"""


ANIMATED_PRINCESS = [('data/images/princess_r.png', ANIMATION_DELAY),
                     ('data/images/princess_l.png', ANIMATION_DELAY)]


class Princess(Block):

    def __init__(self, x, y):
        super(Princess, self).__init__(x, y)
        self.ANIMATED_PRINCESS = pyganim.PygAnimation(ANIMATED_PRINCESS)
        self.ANIMATED_PRINCESS.play()

    def update(self):
        self.image.fill(BLUE)
        self.ANIMATED_PRINCESS.blit(self.image, (0, 0))


"""Класс монетки (анимирован)"""


ANIMATED_COIN = [('data/images/gold_1.png', ANIMATION_DELAY),
                 ('data/images/gold_2.png', ANIMATION_DELAY),
                 ('data/images/gold_3.png', ANIMATION_DELAY)]


class Coin(Block):

    def __init__(self, x, y):
        super(Coin, self).__init__(x, y)
        self.ANIMATED_COIN = pyganim.PygAnimation(ANIMATED_COIN)
        self.ANIMATED_COIN.play()

    def update(self):
        self.image.fill(BLUE)
        self.ANIMATED_COIN.blit(self.image, (0, 0))


"""Классы флажковб являются кт в игре"""


class Flag(Block):
    def __init__(self, x, y):
        super(Flag, self).__init__(x, y)
        self.image = pygame.image.load('data/images/flag.png')


class WallFlag(Block):

    def __init__(self, x, y):
        super(WallFlag, self).__init__(x, y)
        self.image = pygame.image.load('data/images/flag1.jpg')
