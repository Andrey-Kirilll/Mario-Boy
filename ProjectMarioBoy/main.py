import pygame
import tmxreader
import helperspygame
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QMainWindow, QApplication, QLabel, QPushButton, QDesktopWidget, QLineEdit, QCheckBox, \
    QTableWidget, QTableWidgetItem
from sys import argv, exit
from sqlite3 import connect, IntegrityError
from CONSTANTS import WINDOWS_WIDTH, WINDOWS_HEIGHT, BLUE, FPS, ALL_BLOCK_HEIGHT, ALL_BLOCK_WIDTH, BLACK, WHITE
from ELEMENTS import Block, DieBlock, Portal, Princess, Coin, Flag, WallFlag
from MONSTERS import HellHound
from PLAYER import MarioBoy


pygame.mixer.music.load('data/music/main_menu_sound.mp3')  # загрузка фоновой музыки(меню)
pygame.mixer.music.play(-1)
pygame.mixer.music.pause()
con = connect('data/sources/Mario_Boy_db.db')  # подключаемся к БД
cur = con.cursor()  # создаём объект
name = None
paused = False  # Определяем, нужно ли ставить игру на паузу
full_screen = cur.execute('''SELECT is_full_screen FROM game_information''').fetchall()[0][0]  # определяем
# режим экрана - полный или окно
is_music = cur.execute('''SELECT is_music FROM game_information''').fetchall()[0][0]
# будет ли фоновая музыка в игре?
all_sprites = pygame.sprite.Group()  # Все спрайты
monsters = pygame.sprite.Group()  # Спрайты монстров
animated_blocks = pygame.sprite.Group()  # Спрайты, отнаследованные от Block, но имеющие анимацию
obstacles = []  # то, во что мы будем врезаться или опираться
coins = []  # спрайты монеток
playerX, playerY = 87, 401   # координаты героя, на тот случай, если он не найдётся на карте
total_level_width, total_level_height = 0, 0
sprite_layers, coins_layer = [], []
"""Ниже представлены вспомогательные классы, написанные на PyQt5"""

"""Класс, обрабатывающий имя игрока"""


class PlayerNameForm(QMainWindow):

    def __init__(self):
        super(PlayerNameForm, self).__init__()
        self.setGeometry(0, 0, WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 3)
        self.setFixedHeight(WINDOWS_HEIGHT // 3)
        self.setFixedWidth(WINDOWS_WIDTH // 2)
        self.setWindowTitle('Enter your name')
        self.setWindowFlags(Qt.FramelessWindowHint)
        center(self)

        self.background = QLabel('', self)
        self.background.setGeometry(0, 0, WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 3)
        self.background.setAlignment(Qt.AlignCenter)
        self.pixmap = QPixmap('data/images/fon.png')
        self.pixmap = self.pixmap.scaled(WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 3)
        self.background.setPixmap(self.pixmap)

        self.ok_btn = QPushButton('Подтвердить', self)
        self.ok_btn.resize(210, 30)
        self.ok_btn.setFlat(True)
        self.ok_btn.setStyleSheet('font: 16pt "MS Shell Dlg 2";')
        self.ok_btn.move(400 // 2, 200 - 50)

        self.input_form = QLineEdit(self)
        self.input_form.resize(200, 50)
        self.input_form.setStyleSheet('font: 14pt "MS Shell Dlg 2";'
                                      'background-image: rgb(154, 154, 154);'
                                      'background-color: rgb(154, 154, 154)')
        self.input_form.setPlaceholderText('Введите ваше имя')
        self.input_form.move(100, 50)

        background_lbl_image = QPixmap('data/images/btn_image2.png')
        self.error_lbl = QLabel('', self)
        self.error_lbl.resize(260, 30)
        self.error_lbl.setPixmap(background_lbl_image)
        self.error_lbl.setStyleSheet('font: 16pt;'
                                     'color: rgb(255, 0, 0)')
        self.error_lbl.move(100, 120)

        self.initUI()

    def initUI(self):
        self.ok_btn.clicked.connect(self.start_game)

    def start_game(self):
        try:
            global name
            name = self.input_form.text()
            assert name != ''
            assert not name.isdigit()
            cur.execute('''INSERT INTO players(player_name, score) VALUES("{}", {})'''.format(name, 0))
            con.commit()
            self.close()
            global ex, full_screen
            ex.close()
            main(full_screen)
        except IntegrityError:
            self.error_lbl.setText('Такой игрок уже есть')
        except AssertionError:
            self.error_lbl.setText('Недопустимое имя игрока')


""""Класс настроек игры. Открывается как главного меню. Перезагружает главное меню"""


class Setups(QMainWindow):

    def __init__(self):
        super(Setups, self).__init__()
        self.anything_was_changed = False

        self.setGeometry(0, 0, WINDOWS_WIDTH * 0.8, WINDOWS_HEIGHT * 0.9)
        self.setFixedWidth(WINDOWS_WIDTH * 0.8)
        self.setFixedHeight(WINDOWS_HEIGHT * 0.9)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: rgb(50, 50, 50);'
                           'font: 16pt "MS Shell Dlg 2";'
                           'color: rgb(180, 180, 180);')
        center(self)

        self.screen_lbl = QLabel('Полноэкранный режим', self)
        self.screen_lbl.resize(230, 30)
        self.screen_lbl.move(50, 50)

        self.music_lbl = QLabel('Музыка', self)
        self.music_lbl.resize(80, 30)
        self.music_lbl.move(50, 90)

        self.sounds_lbl = QLabel('Эффекты', self)
        self.sounds_lbl.resize(90, 30)
        self.sounds_lbl.move(50, 130)

        self.type_screen = QCheckBox('', self)
        if cur.execute("""SELECT is_full_screen FROM game_information""").fetchall()[0][0] == 'True':
            self.type_screen.toggle()
        self.type_screen.resize(30, 30)
        self.type_screen.setStyleSheet("""QCheckBox::indicator {width: 30px;height: 30px;}""")
        self.type_screen.move(300, 50)

        self.music_box = QCheckBox('', self)
        if cur.execute("""SELECT is_music FROM game_information""").fetchall()[0][0] == 'True':
            self.music_box.toggle()
        self.music_box.setStyleSheet("""QCheckBox::indicator {width: 30px;height: 30px;}""")
        self.music_box.resize(30, 30)
        self.music_box.move(300, 90)

        self.sounds_box = QCheckBox('', self)
        if cur.execute("""SELECT is_effects FROM game_information""").fetchall()[0][0] == 'True':
            self.sounds_box.toggle()
        self.sounds_box.setStyleSheet("""QCheckBox::indicator {width: 30px;height: 30px;}""")
        self.sounds_box.resize(30, 30)
        self.sounds_box.move(300, 130)

        self.ok_btn = QPushButton('Вернуться в меню', self)
        self.ok_btn.resize(200, 30)
        self.ok_btn.setStyleSheet('background-color: rgb(80, 80, 80)')
        self.ok_btn.move(WINDOWS_WIDTH // 2 - 200, 300)

        self.initUI()

    def initUI(self):
        self.ok_btn.clicked.connect(self.close_window)
        self.type_screen.stateChanged.connect(self.screen_)
        self.music_box.stateChanged.connect(self.music_)
        self.sounds_box.stateChanged.connect(self.sounds_)

    def close_window(self):
        self.close()
        if self.anything_was_changed:
            global ex, full_screen
            ex.close()
            full_screen = cur.execute('''SELECT is_full_screen from game_information''').fetchall()[0][0]
            mus = cur.execute('''SELECT is_music FROM game_information''').fetchall()[0][0]
            ex = MainMenuQT(full_screen, mus)
            if full_screen == 'True':
                ex.showFullScreen()
            else:
                ex.show()

    def screen_(self):
        if self.type_screen.isChecked():
            cur.execute("""UPDATE game_information SET is_full_screen = 'True'""")
        else:
            cur.execute("""UPDATE game_information SET is_full_screen = 'False'""")
        self.anything_was_changed = True
        con.commit()

    def music_(self):
        if self.music_box.isChecked():
            pygame.mixer.music.load('data/music/main_menu_sound.mp3')
            pygame.mixer.music.play()
            cur.execute('''UPDATE game_information SET is_music = "True"''')
        else:
            cur.execute("""UPDATE game_information SET is_music = 'False'""")
            pygame.mixer.music.stop()
        con.commit()

    def sounds_(self):
        if self.sounds_box.isChecked():
            cur.execute('''UPDATE game_information SET is_effects = "True"''')
        else:
            cur.execute('''UPDATE game_information SET is_effects = "False"''')
        con.commit()


"""Класс, показывающий управление в игре. Открывается из главного меню и из самой игры"""


class Instruction(QMainWindow):

    def __init__(self):
        super(Instruction, self).__init__()

        self.setGeometry(0, 0, WINDOWS_WIDTH * 0.8, WINDOWS_HEIGHT * 0.9)
        self.setFixedWidth(WINDOWS_WIDTH * 0.8)
        self.setFixedHeight(WINDOWS_HEIGHT * 0.9)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: rgb(50, 50, 50);'
                           'font: 16pt "MS Shell Dlg 2";'
                           'color: rgb(180, 180, 180)')
        center(self)

        self.pause_label = QLabel('Поставить игру на паузу --- клавиша Esc', self)
        self.pause_label.resize(WINDOWS_WIDTH * 0.8, 30)
        self.pause_label.move(10, 10)

        self.jump_label = QLabel('Прыжок --- клавиша W, стрелочка вверх', self)
        self.jump_label.resize(WINDOWS_WIDTH * 0.8, 30)
        self.jump_label.move(10, 50)

        self.move_left_lbl = QLabel('Двигаться влево --- клавиша A, стрелочка влево', self)
        self.move_left_lbl.resize(WINDOWS_WIDTH * 0.8, 30)
        self.move_left_lbl.move(10, 90)

        self.move_right_lbl = QLabel('Двигаться вправо --- клавиша D, стрелочка вправо', self)
        self.move_right_lbl.resize(WINDOWS_WIDTH * 0.8, 30)
        self.move_right_lbl.move(10, 130)

        self.ok_button = QPushButton('Вернуться в меню', self)
        self.ok_button.resize(200, 30)
        self.ok_button.setStyleSheet('background-color: rgb(80, 80, 80)')
        self.ok_button.move(int(WINDOWS_WIDTH * 0.8 - 220), int(WINDOWS_HEIGHT * 0.8 + 20))

        self.initUi()

    def initUi(self):
        self.ok_button.clicked.connect(self.close_window)

    def close_window(self):
        self.close()


"""Класс, показывающий таблицу лучших результатов среди всех игроков, которые когда-либо были. Открывается только
                                                                                                    из главного меню"""


class TableOfPlayers(QMainWindow):

    def __init__(self):
        super(TableOfPlayers, self).__init__()
        self.players = cur.execute('''SELECT * FROM players''').fetchall()
        self.players.sort(key=lambda x: x[1], reverse=True)
        self.setGeometry(0, 0, WINDOWS_WIDTH * 0.8, WINDOWS_HEIGHT * 0.9)
        self.setFixedWidth(WINDOWS_WIDTH * 0.8)
        self.setFixedHeight(WINDOWS_HEIGHT * 0.9)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet('background-color: rgb(50, 50, 50);')
        center(self)

        self.ok_button = QPushButton('Вернуться в меню', self)
        self.ok_button.resize(200, 30)
        self.ok_button.setStyleSheet('background-color: rgb(80, 80, 80);'
                                     'font: 16pt "MS Shell Dlg 2";'
                                     'color: rgb(180, 180, 180)')
        self.ok_button.move(int(WINDOWS_WIDTH * 0.8 // 2 - 100), int(WINDOWS_HEIGHT * 0.8 + 20))

        self.table = QTableWidget(self)
        self.table.setGeometry(0, 0, WINDOWS_WIDTH * 0.8 + 10, WINDOWS_HEIGHT * 0.9 - 50)
        self.table.setStyleSheet('background-color: rgb(120, 120, 120);'
                                 'color: rgb(180, 180, 180);'
                                 'font: 12pt "MS Shell Dlg 2"')
        self.table.setRowCount(0)
        self.table.setColumnCount(2)
        self.table.setColumnWidth(0, WINDOWS_WIDTH * 0.8 // 2)
        self.table.setColumnWidth(1, WINDOWS_WIDTH * 0.8 // 2 - 20)

        self.initUi()

    def initUi(self):
        self.table.setRowCount(len(self.players))
        for player in self.players:
            for j in range(2):
                index = self.players.index(player)
                self.table.setItem(index, j, QTableWidgetItem(self.players[index][j]))
                self.table.setItem(index, j, QTableWidgetItem(str(self.players[index][j])))
        self.table.setHorizontalHeaderLabels(['Имя игрока', 'Набрано очков'])
        self.ok_button.clicked.connect(self.close_window)

    def close_window(self):
        self.close()


"""Класс, открывающий меню паузы во время игры. Запускается нажатием клавишы Esc в окне pygame"""


class PauseMenu(QMainWindow):

    def __init__(self):
        super(PauseMenu, self).__init__()
        self.instruction = None

        self.setGeometry(0, 0, WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 1.5)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setFixedWidth(WINDOWS_WIDTH // 2)
        self.setFixedHeight(WINDOWS_HEIGHT // 1.5)
        self.setWindowTitle('Игра на паузе')
        center(self)

        self.background = QLabel('', self)
        self.background.setGeometry(0, 0, WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 1.5)
        self.background.setAlignment(Qt.AlignCenter)
        self.pixmap = QPixmap('data/images/fon3.png')
        self.pixmap = self.pixmap.scaled(WINDOWS_WIDTH // 2, WINDOWS_HEIGHT // 1.5)
        self.background.setPixmap(self.pixmap)

        self.label = QLabel('Пауза', self)
        self.label.resize(180, 30)
        self.label.setStyleSheet('font: 20pt "MS Shell Dlg 2";'
                                 'color: rgb(240, 240, 240);')
        self.label.move(170, 50)

        self.continue_game = QPushButton('Продолжить игру', self)
        self.continue_game.resize(180, 30)
        self.continue_game.setFlat(True)
        self.continue_game.setStyleSheet('font: 16pt "MS Shell Dlg 2";')
        self.continue_game.move(120, 140)

        self.exit_game_btn = QPushButton('Выйти из игры', self)
        self.exit_game_btn.resize(180, 30)
        self.exit_game_btn.setFlat(True)
        self.exit_game_btn.setStyleSheet('font: 16pt "MS Shell Dlg 2";')
        self.exit_game_btn.move(120, 220)

        self.instruction_btn = QPushButton('Управление', self)
        self.instruction_btn.resize(180, 30)
        self.instruction_btn.setFlat(True)
        self.instruction_btn.setStyleSheet('font: 16pt "MS Shell Dlg 2";')
        self.instruction_btn.move(120, 180)

        self.initUI()

    def initUI(self):
        self.continue_game.clicked.connect(self.continue_method)
        self.instruction_btn.clicked.connect(self.show_instruction)
        self.exit_game_btn.clicked.connect(self.exit_game)

    def continue_method(self):
        global paused
        paused = False
        self.close()
        pygame.mixer.music.unpause()

    def show_instruction(self):
        self.instruction = Instruction()
        self.instruction.close()
        self.instruction.show()

    def exit_game(self):
        exit()


"""Ниже представлен класс, открывающий главное меню игры"""


class MainMenuQT(QMainWindow):

    def __init__(self, screen_mod, is_mus):
        super(MainMenuQT, self).__init__()
        self.player_name = None
        self.instruction = None
        self.setups = None
        self.table = None

        self.setGeometry(0, 0, WINDOWS_WIDTH, WINDOWS_HEIGHT)
        self.setWindowTitle('Super Mario Boy')

        if is_mus == 'True':
            pygame.mixer.music.unpause()
        else:
            pygame.mixer.music.pause()

        if screen_mod == 'True':
            self.width_ = QApplication.desktop().width()
            self.height_ = QApplication.desktop().height()
        else:
            self.width_ = WINDOWS_WIDTH
            self.height_ = WINDOWS_HEIGHT
            self.setFixedWidth(self.width_)
            self.setFixedHeight(self.height_)
            center(self)

        self.background = QLabel('', self)
        self.background.setGeometry(0, 0, self.width_, self.height_)
        self.background.setAlignment(Qt.AlignCenter)
        self.pixmap = QPixmap('data/images/fon1.png')
        self.pixmap = self.pixmap.scaled(self.width_, self.height_)
        self.background.setPixmap(self.pixmap)

        self.version = QLabel('Beta Version', self)
        self.version.resize(210, 30)
        self.version.setStyleSheet('font: 20pt "MS Shell Dlg 2";'
                                   'color: rgb(240, 240, 240);')
        self.version.move(int(self.width_ - 230), int(self.height_ - 50))

        self.game_name = QLabel('Super Mario Boy\n'
                                'Reinterpretation', self)
        self.game_name.resize(210, 80)
        self.game_name.setStyleSheet('font: 20pt "MS Shell Dlg 2";'
                                     'color: rgb(240, 240, 240);')
        self.game_name.move(self.width_ - 230, int(self.height_ * 0.05))

        self.start_new_game = QPushButton('Начать новую игру', self)
        self.start_new_game.resize(200, 30)
        self.start_new_game.setFlat(True)
        self.start_new_game.setStyleSheet('font: 16pt "MS Shell Dlg 2";'
                                          'color: rgb(240, 240, 240);'
                                          'background-color: rgb(150, 150, 150)')
        self.start_new_game.move(self.width_ // 2 - 100, int(self.height_ * 0.3))

        self.records_table_btn = QPushButton('Таблица рекордов', self)
        self.records_table_btn.resize(200, 30)
        self.records_table_btn.setFlat(True)
        self.records_table_btn.setStyleSheet('font: 16pt "MS Shell Dlg 2";'
                                             'color: rgb(240, 240, 240);'
                                             'background-color: rgb(150, 150, 150)')
        self.records_table_btn.move(self.width_ // 2 - 100, int(self.height_ * 0.35))

        self.instruction_btn = QPushButton('Управление', self)
        self.instruction_btn.resize(200, 30)
        self.instruction_btn.setFlat(True)
        self.instruction_btn.setStyleSheet('font: 16pt "MS Shell Dlg 2";'
                                           'color: rgb(240, 240, 240);'
                                           'background-color: rgb(150, 150, 150)')
        self.instruction_btn.move(self.width_ // 2 - 100, int(self.height_ * 0.4))

        self.setups_btn = QPushButton('Настройки', self)
        self.setups_btn.resize(200, 30)
        self.setups_btn.setFlat(True)
        self.setups_btn.setStyleSheet('font: 16pt "MS Shell Dlg 2";'
                                      'color: rgb(240, 240, 240);'
                                      'background-color: rgb(150, 150, 150)')
        self.setups_btn.move(self.width_ // 2 - 100, int(self.height_ * 0.45))

        self.exit_btn = QPushButton('Выйти из игры', self)
        self.exit_btn.resize(200, 30)
        self.exit_btn.setFlat(True)
        self.exit_btn.setStyleSheet('font: 16pt "MS Shell Dlg 2";'
                                    'color: rgb(240, 240, 240);'
                                    'background-color: rgb(150, 150, 150)')
        self.exit_btn.move(self.width_ // 2 - 100, int(self.height_ * 0.5))

        self.initUI()

    def initUI(self):
        self.start_new_game.clicked.connect(self.start_game)
        self.records_table_btn.clicked.connect(self.show_records_table)
        self.instruction_btn.clicked.connect(self.show_instructions)
        self.setups_btn.clicked.connect(self.setups_)
        self.exit_btn.clicked.connect(self.exit_game)

    def start_game(self):
        self.player_name = PlayerNameForm()
        self.player_name.close()
        self.player_name.show()

    def show_records_table(self):
        self.table = TableOfPlayers()
        self.table.close()
        self.table.show()

    def show_instructions(self):
        self.instruction = Instruction()
        self.instruction.close()
        self.instruction.show()

    def setups_(self):
        self.setups = Setups()
        self.setups.close()
        self.setups.show()

    def exit_game(self):
        exit()


""""Функция, которая центрирует окна PyQt5 относительно экрана. Принимает на вход само окно"""


def center(self):
    qr = self.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    self.move(qr.topLeft())


"""Класс камеры в игре. Следит за главным персонажем - скроллит карту"""


class Camera(object):
    def __init__(self, camera_func, width, height, width1, height1):
        self.win_width = width1
        self.win_height = height1
        self.camera_func = camera_func
        self.state = pygame.Rect(0, 0, width, height)

    def apply(self, target):
        return target.rect.move(self.state.topleft)

    def update(self, target):
        self.state = self.camera_func(self.state, target.rect, self.win_width, self.win_height)

    def reverse(self, pos):  # получение внутренних координат из глобальных
        return pos[0] - self.state.left, pos[1] - self.state.top


"""Вспомогательная функция для камеры, принимает на вход объект - камеру, объект - героя, максимальные ширину и высоту
                                                                                                            уровня.
                                                                Задает начальную конфигурацию камеры"""


def camera_configure(camera, target_rect, win_width, win_height):
    left, top, _, _ = target_rect
    _, _, camera_width, camera_height = camera
    left, top = -left + win_width / 2, -top + win_height / 2

    left = min(0, left)  # Не движемся дальше левой границы
    left = max(-(camera.width - win_width), left)  # Не движемся дальше правой границы
    top = max(-(camera.height - win_height), top)  # Не движемся дальше нижней границы
    top = min(0, top)  # Не движемся дальше верхней границы

    return pygame.Rect(left, top, camera_width, camera_height)


"""Функция, открывающая файл с картой уровня"""


def load_level(filename):
    global playerX, playerY  # объявляем глобальные переменные, это координаты героя
    global total_level_height, total_level_width
    global sprite_layers  # все слои карты
    global coins_layer  # слои монеток
    world_map = tmxreader.TileMapParser().parse_decode('%s.tmx' % filename)  # загружаем карту
    resources = helperspygame.ResourceLoaderPygame()  # инициируем преобразователь карты
    resources.load(world_map)  # и преобразуем карту в понятный pygame формат

    sprite_layers = helperspygame.get_layers_from_map(resources)  # получаем все слои карты

    platforms_layer = sprite_layers[1]
    die_blocks_layer = sprite_layers[2]

    for row in range(0, platforms_layer.num_tiles_x):  # перебираем все координаты тайлов
        for col in range(0, platforms_layer.num_tiles_y):
            if platforms_layer.content2D[col][row] is not None:
                block = Block(row * ALL_BLOCK_WIDTH, col * ALL_BLOCK_HEIGHT)
                obstacles.append(block)
            if die_blocks_layer.content2D[col][row] is not None:
                die_block = DieBlock(row * ALL_BLOCK_WIDTH, col * ALL_BLOCK_HEIGHT)
                obstacles.append(die_block)
    monsters_layer = sprite_layers[4]
    for monster in monsters_layer.objects:
        x = monster.x
        y = monster.y
        if monster.name == 'MarioBoy':
            playerX = x
            playerY = y - ALL_BLOCK_HEIGHT
        elif monster.name == 'HellHound':
            speed_y = int(monster.properties["move_speed_y"])
            max_y_direction = int(monster.properties["max_up"])
            speed_x = int(monster.properties["move_speed_x"])
            max_x_direction = int(monster.properties["max_left"])
            mn = HellHound(x, y - ALL_BLOCK_HEIGHT, speed_x, speed_y, max_x_direction, max_y_direction)
            all_sprites.add(mn)
            obstacles.append(mn)
            monsters.add(mn)
        elif monster.name == 'Princess':
            princess = Princess(x, y - ALL_BLOCK_HEIGHT)
            all_sprites.add(princess)
            animated_blocks.add(princess)
            obstacles.append(princess)

    coins_layer = sprite_layers[5]
    for coin in coins_layer.objects:
        x = coin.x
        y = coin.y
        coin = Coin(x, y - ALL_BLOCK_HEIGHT)
        all_sprites.add(coin)
        coins.append(coin)
        animated_blocks.add(coin)

    portal_layer = sprite_layers[6]
    for portal in portal_layer.objects:
        x = portal.x
        y = portal.y - ALL_BLOCK_HEIGHT
        if portal.name == 'Portal':
            go_x = int(portal.properties['go_x'])
            go_y = int(portal.properties['go_y'])
            portal = Portal(x, y, go_x * ALL_BLOCK_WIDTH, go_y * ALL_BLOCK_HEIGHT)
            all_sprites.add(portal)
            animated_blocks.add(portal)
            obstacles.append(portal)
        else:
            flag = Flag(x, y)
            all_sprites.add(flag)
            obstacles.append(flag)

    wall_flag = sprite_layers[7]
    for flag in wall_flag.objects:
        flag = WallFlag(flag.x, flag.y - ALL_BLOCK_HEIGHT)
        all_sprites.add(flag)
        obstacles.append(flag)
    total_level_width = platforms_layer.num_tiles_x * ALL_BLOCK_WIDTH  # Высчитываем фактическую ширину уровня
    total_level_height = platforms_layer.num_tiles_y * ALL_BLOCK_HEIGHT  # высоту


""""Основная функция main() проекта - игра. Принимает на вход строку full_screen, чтобы понять, какой режим экрана
                                                                            отобразить - полноэкранный или оконный"""


def main(screen_mod):
    pygame.mixer.music.stop()  # выключили музыку из меню
    is_mus = cur.execute("""SELECT is_music FROM game_information""").fetchall()[0][0]
    if is_mus == 'True':   # удостоверились, что музыка включена в настройках
        pygame.mixer.music.load('data/music/game_music.mp3')
        pygame.mixer.music.play(-1)
    if screen_mod == 'True':   # удостоверились, что в настройках выбран полноэкранный режим
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Создаем окошко
    else:
        screen = pygame.display.set_mode((800, 600))
    width, height = screen.get_width(), screen.get_height()
    pygame.display.set_caption("Super Mario Boy")  # Пишем в шапку
    clock = pygame.time.Clock()
    center_of_screen = width // 2, height // 2

    renderer = helperspygame.RendererPygame()  # визуализатор
    for lvl in range(1, 2):
        load_level('data/levels/lvl')

        left = right = False
        top = False

        hero = MarioBoy(playerX, playerY)
        all_sprites.add(hero)

        camera = Camera(camera_configure, total_level_width, total_level_height, width, height)

        global paused
        paused = False
        running = True
        while running:  # Основной цикл программы
            clock.tick(FPS)
            for event in pygame.event.get():  # Обрабатываем события
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    key = pygame.key.get_pressed()
                    if key[pygame.K_w] or key[pygame.K_UP]:
                        top = True
                    if key[pygame.K_a] or key[pygame.K_LEFT]:
                        left = True
                    if key[pygame.K_d] or key[pygame.K_RIGHT]:
                        right = True
                    if key[pygame.K_ESCAPE]:
                        paused = True
                        pygame.mixer.music.pause()
                        x = PauseMenu()
                        x.show()

                if event.type == pygame.KEYUP and (event.key == pygame.K_w or event.key == pygame.K_UP):
                    top = False
                if event.type == pygame.KEYUP and (event.key == pygame.K_a or event.key == pygame.K_LEFT):
                    left = False
                if event.type == pygame.KEYUP and (event.key == pygame.K_d or event.key == pygame.K_RIGHT):
                    right = False
            if not paused:

                for sprite_layer in sprite_layers:  # перебираем все слои
                    if not sprite_layer.is_object_group:  # и если это не слой объектов
                        renderer.render_layer(screen, sprite_layer)  # отображаем его

                for sprite in all_sprites:
                    screen.blit(sprite.image, camera.apply(sprite))

                monsters.update(obstacles)  # показываем анимацию у блоков
                animated_blocks.update()  # передвигаем всех монстров
                camera.update(hero)  # центризируем камеру относительно персонажа
                center_offset = camera.reverse(center_of_screen)  # получаем координаты внутри длинного уровня
                renderer.set_camera_position_and_size(center_offset[0], center_offset[1],
                                                      width, height, "center")

                hero.update(left, right, top, obstacles, total_level_width, total_level_height, coins)  # передвижение
                pygame.display.update()  # обновление и вывод всех изменений на экран
                screen.fill(BLUE)
                if hero.win:  # выводим на экран сообщение о победе и останавливаем игру
                    pygame.mixer.music.stop()
                    pygame.time.wait(500)
                    font1 = pygame.font.SysFont('arial', 36)
                    font2 = pygame.font.SysFont('arial', 26)
                    text1 = font1.render('Поздравялем,', True, WHITE)
                    text2 = font1.render('Вы выиграли!', True, WHITE)
                    text3 = font2.render('Вы набрали {} очков'.format(hero.score), False, WHITE)
                    text4 = font2.render('Чтобы выйти из игры, нажмите правую кнопку мыши', False, WHITE)
                    screen.fill(BLACK)
                    screen.blit(text1, (width // 2 - 100, 150))
                    screen.blit(text2, (width // 2 - 100, 250))
                    screen.blit(text3, (width // 2 - 120, 350))
                    screen.blit(text4, (width // 2 - 250, 450))
                    pygame.display.flip()
                    run = True
                    cur.execute('''UPDATE players SET score = {} WHERE player_name = "{}"'''.format(hero.score, name))
                    con.commit()
                    while run:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                exit()
                            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                                exit()


if __name__ == '__main__':
    app = QApplication(argv)
    ex = MainMenuQT(full_screen, is_music)
    if full_screen == 'True':
        ex.showFullScreen()
    else:
        ex.show()
    exit(app.exec())
