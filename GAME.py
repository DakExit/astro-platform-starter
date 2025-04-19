import pygame
import random
import sys
import os
import time

# Проверка рабочей директории (для отладки)
print("Рабочая директория:", os.getcwd())

# Инициализация Pygame
pygame.init()

# Получаем разрешение экрана
screen_width, screen_height = pygame.display.Info().current_w, pygame.display.Info().current_h

# Устанавливаем полноэкранный режим
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Герой против врагов")

# Цвета (используются для текста и некоторых элементов)
light_blue = (173, 216, 230)
red = (255, 0, 0)
black = (0, 0, 0)
yellow = (255, 255, 0)
blue = (0, 0, 255)
white = (255, 255, 255)

# --- ЗАГРУЗКА ИЗОБРАЖЕНИЙ ---
def load_image(path, width, height):
    try:
        image = pygame.image.load(path)
        return pygame.transform.scale(image, (width, height))
    except Exception as e:
        print(f"Ошибка загрузки {path}:", e)
        sys.exit()

background_image = load_image("fon.jpg", screen_width, screen_height)
player_width, player_height = 50, 50
player_image = load_image("gg.png", player_width, player_height)
enemy_width, enemy_height = 50, 50
enemy_image = load_image("bot.png", enemy_width, enemy_height)
bullet_width, bullet_height = 16, 32
bullet_image = load_image("byllet.png", bullet_width, bullet_height)
life_image = load_image("lofe.png", 65, 65)

# Загрузка изображений для анимации взрыва
explosion_images = [load_image(f"взрыв0{i}.png", enemy_width, enemy_height) for i in range(8)]

# --- ПАРАМЕТРЫ ИГРЫ ---
paused = False
shoot_mode = "single"  # Режим стрельбы: "single" или "burst"

# Параметры персонажа
player_x = screen_width // 2 - player_width // 2
player_y = screen_height - player_height - 10
player_speed = 4

# Параметры врагов
enemy_speed_min = 3
enemy_speed_max = 6
enemy_frequency = 15  # Чем меньше число, тем чаще появляются враги
enemies = []

# Параметры пуль
bullet_speed = 7
bullets = []
last_shot_time = 0
shoot_delay = 500  # задержка в миллисекундах между выстрелами
burst_shot_delay = 100  # задержка между выстрелами в очереди

# Параметры взрывов
explosions = []

# Жизни и очки
lives = 3
max_lives = 3  # Максимальное количество жизней
life_size = 65
life_spacing = 10
score = 0
coins = 0  # Добавляем переменную для монет
total_coins = 0  # Общая сумма монет
previous_score = 0  # Переменная для отслеживания предыдущего количества очков

# Параметры падающих сердечек
heart_speed = 3
heart_spawned = False
heart_caught = False
heart_x = screen_width // 2 - 25  # Центрируем сердечко по горизонтали
heart_y = -50

# Таймер для появления сердечка
heart_spawn_time = 0
heart_timer_started = False

# Остальные параметры
clock = pygame.time.Clock()
game_over = False

# Шрифты для текста
font = pygame.font.SysFont("arial", 36)
score_font = pygame.font.SysFont("arial", 36, bold=True)
instructions_font = pygame.font.SysFont("arial", 48, bold=True)

# --- ФУНКЦИИ ---

def show_text(text, x, y, color, font, align_right=False):
    img = font.render(text, True, color)
    if align_right:
        x = screen_width - img.get_width() - 20
    screen.blit(img, (x, y))

def load_high_score():
    try:
        with open("high_score.txt", "r") as f:
            return int(f.read())
    except FileNotFoundError:
        return 0

def save_high_score(score):
    with open("high_score.txt", "w") as f:
        f.write(str(score))

high_score = load_high_score()

def load_total_coins():
    try:
        with open("total_coins.txt", "r") as f:
            return int(f.read())
    except FileNotFoundError:
        return 0

def save_total_coins(coins):
    with open("total_coins.txt", "w") as f:
        f.write(str(coins))

total_coins = load_total_coins()

def draw_button(text, x, y, width, height, color, font):
    pygame.draw.rect(screen, color, (x, y, width, height))
    show_text(text, x + (width - font.render(text, True, white).get_width()) // 2,
              y + (height - font.get_height()) // 2, white, font)

def new_game():
    global player_x, player_y, lives, score, enemies, bullets, game_over, paused, shoot_mode, coins, previous_score, heart_spawned, heart_caught, heart_spawn_time, heart_timer_started
    player_x = screen_width // 2 - player_width // 2
    player_y = screen_height - player_height - 10
    lives = 3
    score = 0
    coins = 0  # Сбрасываем количество монет при новой игре
    previous_score = 0  # Сбрасываем предыдущий счет при новой игре
    enemies = []
    bullets = []
    heart_spawned = False  # Сбрасываем флаг появления сердечка
    heart_caught = False  # Сбрасываем флаг пойманного сердечка
    heart_spawn_time = 0  # Сбрасываем таймер появления сердечка
    heart_timer_started = False
    game_over = False
    paused = False
    shoot_mode = "single"

# --- ГЛАВНЫЙ ЦИКЛ ---

# Функция для отображения экрана с инструкциями
def show_instructions():
    instructions_text = [
        "Управление:",
        "W - Вверх",
        "A - Влево",
        "S - Вниз",
        "D - Вправо",
        "Левая кнопка мыши - Стрелять",
        "1 - Пауза"
    ]
    screen.fill(black)
    for i, line in enumerate(instructions_text):
        text_surface = instructions_font.render(line, True, white)
        text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2 - 100 + i * 60))
        screen.blit(text_surface, text_rect)
    show_text("Пробел - пропустить", screen_width // 2, screen_height - 100, white, instructions_font, align_right=True)
    pygame.display.flip()

# Функция для отображения меню
def show_menu():
    menu_text = [
        "Меню паузы:",
        "1. Продолжить",
        "2. Новая игра",
        "3. Выйти"
    ]
    screen.fill(black)
    for i, line in enumerate(menu_text):
        text_surface = instructions_font.render(line, True, white)
        text_rect = text_surface.get_rect(center=(screen_width // 2, screen_height // 2 - 100 + i * 60))
        screen.blit(text_surface, text_rect)
    pygame.display.flip()

# Показать экран с инструкциями перед началом игры
show_instructions()

# Флаг для экрана инструкций
instructions_shown = True

while True:
    if instructions_shown:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    instructions_shown = False
        continue

    # Рисуем фон
    screen.blit(background_image, (0, 0))

    if game_over:
        game_over_font = pygame.font.SysFont("arial", 72, bold=True)
        button_font = pygame.font.SysFont("arial", 36, bold=True)  # Уменьшенный размер шрифта для кнопки
        game_over_text = "Game Over"
        game_over_x = (screen_width - game_over_font.size(game_over_text)[0]) // 2
        game_over_y = (screen_height - game_over_font.size(game_over_text)[1]) // 2
        show_text(game_over_text, game_over_x, game_over_y, red, game_over_font)
        
        # Отображаем кнопку "Новая игра"
        draw_button("Новая игра", screen_width // 2 - 100, screen_height // 2 + 100, 200, 50, (0, 255, 255), button_font)
        
        # Обновляем общую сумму монет
        total_coins += coins
        save_total_coins(total_coins)
        
        # Определяем текст для отображения количества монет
        coins_text = f"Монеты: {coins}"
        
        # Отображаем рекорд, количество очков и монет
        high_score_text = f"Рекорд: {high_score}"
        score_text = f"Очки: {score}"
        high_score_x = (screen_width - game_over_font.size(high_score_text)[0]) // 2
        score_x = (screen_width - game_over_font.size(score_text)[0]) // 2
        show_text(high_score_text, high_score_x, screen_height // 2 + 160, (0, 255, 255), game_over_font)
        show_text(score_text, score_x, screen_height // 2 + 220, (0, 255, 255), game_over_font)
        show_text(coins_text, screen_width - game_over_font.size(coins_text)[0] - 20, 10, (0, 255, 255), game_over_font)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if (screen_width // 2 - 100 <= mouse_x <= screen_width // 2 + 100 and
                    screen_height // 2 + 100 <= mouse_y <= screen_height // 2 + 150):
                    new_game()
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    paused = not paused
                    if paused:
                        show_menu()
                if event.key == pygame.K_2 and paused:
                    new_game()
                    paused = False
                if event.key == pygame.K_3 and paused:
                    pygame.quit()
                    sys.exit()
                if event.key == pygame.K_0:  # Чит-код: создать сердечко
                    heart_spawned = True
                    heart_caught = False
                    heart_x = random.randint(0, screen_width - 50)  # Случайная позиция сердечка по горизонтали
                    heart_y = -50
                if event.key == pygame.K_9:  # Чит-код: удалить всех врагов
                    enemies.clear()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Левая кнопка мыши
                    current_time = pygame.time.get_ticks()
                    if current_time - last_shot_time > shoot_delay:
                        bullet_x = player_x + player_width // 2 - bullet_width // 2
                        bullet_y = player_y
                        bullets.append([bullet_x, bullet_y])
                        last_shot_time = current_time
                if event.button == 3:  # Правая кнопка мыши
                    shoot_mode = "burst" if shoot_mode == "single" else "single"

        if paused:
            continue

        if not paused:
            # Движение игрока
            keys = pygame.key.get_pressed()
            if keys[pygame.K_a] and player_x > 0:
                player_x -= player_speed
            if keys[pygame.K_d] and player_x < screen_width - player_width:
                player_x += player_speed
            if keys[pygame.K_w] and player_y > 0:
                player_y -= player_speed
            if keys[pygame.K_s] and player_y < screen_height - player_height:
                player_y += player_speed

            # Появление врагов
            for _ in range(2):  # Попытка создать 2 врагов за кадр
                if random.randint(1, enemy_frequency) == 1:
                    enemy_x = random.randint(0, screen_width - enemy_width)
                    enemy_speed = random.randint(enemy_speed_min, enemy_speed_max)
                    enemy_direction = random.choice([-1, 1])
                    enemies.append([enemy_x, -enemy_height, enemy_speed, enemy_direction])

            # Обновление и отрисовка врагов
            for enemy in enemies[:]:
                enemy[1] += enemy[2]  # вертикальное движение
                enemy[0] += enemy[3]  # горизонтальное движение
                if enemy[1] > screen_height:
                    enemies.remove(enemy)
                    continue
                screen.blit(enemy_image, (enemy[0], enemy[1]))

            # Обновление и отрисовка пуль
            for bullet in bullets[:]:
                bullet[1] -= bullet_speed
                if bullet[1] < 0:
                    bullets.remove(bullet)
                    continue
                screen.blit(bullet_image, (bullet[0], bullet[1]))

            # Проверка столкновений пули и врага
            for enemy in enemies[:]:
                for bullet in bullets[:]:
                    if (bullet[0] < enemy[0] + enemy_width and
                        bullet[0] + bullet_width > enemy[0] and
                        bullet[1] < enemy[1] + enemy_height and
                        bullet[1] + bullet_height > enemy[1]):
                        enemies.remove(enemy)
                        bullets.remove(bullet)
                        score += 10
                        if score > high_score:
                            high_score = score
                            save_high_score(high_score)
                        # Добавляем взрыв
                        explosions.append([enemy[0], enemy[1], 0])
                        # Обновляем количество монет
                        if score // 100 > previous_score // 100:
                            coins += 10
                            previous_score = (score // 100) * 100  # Обновляем previous_score до ближайших 100
                        break

            # Проверка столкновений игрока и врагов
            for enemy in enemies[:]:
                if (player_x < enemy[0] + enemy_width and
                    player_x + player_width > enemy[0] and
                    player_y < enemy[1] + enemy_height and
                    player_y + player_height > enemy[1]):
                    enemies.remove(enemy)
                    lives -= 1
                    # Добавляем взрыв для игрока
                    explosions.append([player_x, player_y, 0])
                    if lives == 1 and not heart_timer_started:
                        heart_spawn_time = pygame.time.get_ticks() + 30000  # Устанавливаем время появления через 30 секунд
                        heart_timer_started = True
                    if lives <= 0:
                        game_over = True
                    break

            # Появление сердечек
            if lives == 1 and not heart_spawned and not heart_caught and heart_timer_started:
                if pygame.time.get_ticks() >= heart_spawn_time:
                    heart_x = random.randint(0, screen_width - 50)  # Случайная позиция сердечка по горизонтали
                    heart_y = -50
                    heart_spawned = True
                    heart_timer_started = False

            # Обновление и отрисовка сердечек
            if heart_spawned and not heart_caught:
                heart_y += heart_speed  # движение вниз
                if heart_y > screen_height:
                    heart_spawned = False
                else:
                    screen.blit(life_image, (heart_x, heart_y))

                # Проверка столкновений игрока и сердечка
                if (player_x < heart_x + 50 and
                    player_x + player_width > heart_x and
                    player_y < heart_y + 50 and
                    player_y + player_height > heart_y):
                    heart_caught = True
                    heart_spawned = False
                    if lives < max_lives:  # Проверка на максимальное количество жизней
                        lives += 1
            else:
                heart_caught = False  # Сбрасываем флаг пойманного сердечка, чтобы позволить появляться новым сердечкам

            # Отображаем жизни по центру экрана
            life_total_width = lives * life_size + (lives - 1) * life_spacing
            start_x = (screen_width - life_total_width) // 2
            for i in range(lives):
                screen.blit(life_image, (start_x + i * (life_spacing + life_size), 10))

            # Отображаем очки и рекорд
            show_text(f"Очки: {score}", 10, 10, yellow, score_font)
            show_text(f"Рекорд: {high_score}", screen_width - 200, 10, yellow, score_font)

            # Отображаем игрока (ГГ)
            screen.blit(player_image, (player_x, player_y))

            # Обновление и отрисовка взрывов
            for explosion in explosions[:]:
                x, y, frame = explosion
                screen.blit(explosion_images[frame], (x, y))
                explosion[2] += 1
                if explosion[2] >= len(explosion_images):
                    explosions.remove(explosion)

    # Обновление экрана
    pygame.display.flip()

    # Частота обновления
    clock.tick(60)