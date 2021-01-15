from sqlite3 import connect
import pygame
import pyganim
from MONSTERS import HellHound
from ELEMENTS import DieBlock, Portal, Princess, Coin, Flag, WallFlag
from CONSTANTS import BLUE, MOVE_SPEED, JUMP_POWER, GRAVITY, ANIMATION_STAY, \
    ANIMATION_RIGHT, ANIMATION_LEFT, ANIMATION_JUMP_LEFT, ANIMATION_JUMP_RIGHT, ANIMATION_JUMP

pygame.mixer.pre_init(22100, -16, 2, 64)  # пред-инициализация микшера для исключения
pygame.init()

princess_caught = pygame.mixer.Sound('data/music/win.mp3')
coin_collected = pygame.mixer.Sound('data/music/coin1.wav')
death = pygame.mixer.Sound('data/music/gameover5.wav')
teleported = pygame.mixer.Sound('data/music/teleported.wav')
jump = pygame.mixer.Sound('data/music/jump1.wav')
con = connect('data/sources/Mario_Boy_db.db')
cur = con.cursor()


class MarioBoy(pygame.sprite.Sprite):

    def __init__(self, x, y):
        super(MarioBoy, self).__init__()
        self.image = pygame.Surface((32, 40))
        self.image.fill(BLUE)
        self.image.set_colorkey(BLUE)
        self.rect = pygame.Rect(x, y, 32, 40)
        self.x_velocity = self.y_velocity = 0
        self.isFly = False
        self.on_ground = False
        self.win = False
        self.score = 0
        self.start_x = x
        self.start_y = y

        # инициализация анимаций
        self.ANIMATION_STAY = pyganim.PygAnimation(ANIMATION_STAY)
        self.ANIMATION_STAY.play()
        self.ANIMATION_STAY.blit(self.image, (0, 0))

        self.ANIMATION_RIGHT = pyganim.PygAnimation(ANIMATION_RIGHT)
        self.ANIMATION_RIGHT.play()

        self.ANIMATION_LEFT = pyganim.PygAnimation(ANIMATION_LEFT)
        self.ANIMATION_LEFT.play()

        self.ANIMATION_JUMP_LEFT = pyganim.PygAnimation(ANIMATION_JUMP_LEFT)
        self.ANIMATION_JUMP_LEFT.play()

        self.ANIMATION_JUMP_RIGHT = pyganim.PygAnimation(ANIMATION_JUMP_RIGHT)
        self.ANIMATION_JUMP_RIGHT.play()

        self.ANIMATION_JUMP = pyganim.PygAnimation(ANIMATION_JUMP)
        self.ANIMATION_JUMP.play()

    def update(self, left, right, top, blocks, max_width, max_height, coins):
        if top:  # если движется вверх
            if self.on_ground:  # прыгаем только когда на земле
                self.y_velocity = - JUMP_POWER
                if cur.execute('''SELECT is_effects FROM game_information''').fetchall()[0][0] == 'True':
                    jump.play()  # включены ли эффекты?
        if left:  # если движемся влево
            self.x_velocity = -MOVE_SPEED
            self.image.fill(BLUE)
            self.ANIMATION_LEFT.blit(self.image, (0, 0))  # то меняем анимацию

        if right:  # если движемся вправо
            self.x_velocity = MOVE_SPEED
            self.image.fill(BLUE)
            self.ANIMATION_RIGHT.blit(self.image, (0, 0))  # то меняем анимацию

        if self.isFly:  # если марио в 'невесомости'
            self.image.fill(BLUE)
            if self.x_velocity < 0:  # если движемся влево
                self.ANIMATION_JUMP_LEFT.blit(self.image, (0, 0))
            elif self.x_velocity > 0:  # если движемся вправо
                self.ANIMATION_JUMP_RIGHT.blit(self.image, (0, 0))
            else:  # если просто падаем или поднимаемся вверх
                self.ANIMATION_JUMP.blit(self.image, (0, 0))

        if not (right or left) and not self.isFly:  # стоим
            self.x_velocity = 0
            if not top:
                self.image.fill(BLUE)
                self.ANIMATION_STAY.blit(self.image, (0, 0))

        if not self.on_ground:  # если не на земле
            self.y_velocity += GRAVITY  # учитываем гравитацию

        if abs(round(self.y_velocity)) > 2:  # если в воздухе
            self.isFly = True
        elif self.on_ground:  # если на земле
            self.isFly = False

        self.on_ground = False  # мы не знаем, на земле ли

        self.rect.x += self.x_velocity
        self.collide(self.x_velocity, 0, blocks, coins)

        self.rect.y += self.y_velocity
        self.collide(0, self.y_velocity, blocks, coins)

    def collide(self, x_vel, y_vel, blocks, coins):
        for obstacle in blocks:  # проверяем столкновение марио с объектами в игре
            if pygame.sprite.collide_rect(self, obstacle):
                if isinstance(obstacle, HellHound) or isinstance(obstacle, DieBlock):  # если это огонь или смертельный
                    # блок
                    if cur.execute('''SELECT is_effects FROM game_information''').fetchall()[0][0] == 'True':
                        death.play()
                    self.die()  # значит смерть
                elif isinstance(obstacle, Portal):  # столкновение с порталом
                    if cur.execute('''SELECT is_effects FROM game_information''').fetchall()[0][0] == 'True':
                        teleported.play()
                    self.teleporting(obstacle.go_x, obstacle.go_y)  # перемещаемся на новое место
                elif isinstance(obstacle, Princess):  # принцесса
                    if cur.execute('''SELECT is_effects FROM game_information''').fetchall()[0][0] == 'True':
                        princess_caught.play()
                    blocks.pop(blocks.index(obstacle))
                    self.score += 500  # если поймали, то начисляем ещё 500 очков
                    self.win = True   # и игра пройдена
                elif isinstance(obstacle, Flag) or isinstance(obstacle, WallFlag):
                    self.start_x = obstacle.rect.x  # устанавливаем новые
                    self.start_y = obstacle.rect.y  # координаты начала(респауна)
                    blocks.pop(blocks.index(obstacle))  # убираем флаг из списка, т.к кт можно пройти единожды
                else:  # все остальные блоки (кроме монеток)
                    if x_vel > 0:  # если движется вправо
                        self.rect.right = obstacle.rect.left
                        self.x_velocity = 0  # то не движется вправо
                    elif x_vel < 0:  # если движется влево
                        self.rect.left = obstacle.rect.right
                        self.x_velocity = 0  # то не движется влево
                    if y_vel > 0:  # если падает
                        self.rect.bottom = obstacle.rect.top
                        self.on_ground = True
                        self.y_velocity = 0  # то стоит твёрдо на земле
                    elif y_vel < 0:  # если поднимается
                        self.rect.top = obstacle.rect.bottom
                        self.y_velocity = 0  # то не поднимается

        for coin in coins:  # проверка столкновения с монеткой
            if pygame.sprite.collide_rect(self, coin):  # если столкнулись
                if cur.execute('''SELECT is_effects FROM game_information''').fetchall()[0][0] == 'True':
                    coin_collected.play()
                self.score += 20  # то начисляем очки
                Coin.kill(coin)  # и убиваем монетку, так, чтобы не было ни на экране, ни в памяти
                coins.pop(coins.index(coin))

    def die(self):  # если умерли
        self.x_velocity = 0  # то скорость движения
        self.y_velocity = 0  # пропадает
        self.teleporting(self.start_x, self.start_y)  # респавнимся на кт

    def teleporting(self, go_x, go_y):
        self.rect.x = go_x
        self.rect.y = go_y
