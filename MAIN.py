import pygame
import sys
from math import sin, pi

pygame.init()

WIDTH, HEIGHT = 1000, 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))

block_textures = pygame.image.load('текстуры_увелич.png').convert_alpha()
background = pygame.image.load('фон_увелич.png').convert()
spikes = pygame.image.load('шипы_увелич.png').convert_alpha()
outline_dashable = pygame.image.load('outline1.png').convert_alpha()
outline_dashless = pygame.image.load('outline2.png').convert_alpha()
rendering = pygame.image.load('rendering.png').convert_alpha()
main_screen = pygame.image.load('главный_экран_увелич.png').convert_alpha()
main_buttons = pygame.image.load('кнопки.png').convert_alpha()
main_button_texts = pygame.image.load('надписи.png').convert_alpha()
checkpoints = pygame.image.load('чекпоинт_увелич.png').convert_alpha()
player_sprites = pygame.image.load('персонаж_увелич.png').convert_alpha()

pygame.display.set_caption("Селестия")

player_x, player_y = 100, 300
const_x, const_y = 0, 0
momentum_x, momentum_y = 0, 0
const_decreasing_x, const_decreasing_y = 0, 0
player_speed = 5

friction_left_n = 1
friction_right_n = 1
friction_max = 10
friction_last_frame = 1

grounded = False
gravity_mult = 0
buffer_frames_y = 4

dashable = True
dash_duraion = 10
dash_in_motion = False
dash_initialized = False
dash_cooldown = 10
dash_x, dash_y = 0, 0
dash_speed = 14
dash_ratio = 1
dash_held = False

last_orient_x = 0
last_orient_y = 0
last_player_x = player_x
last_player_y = player_y
player_x_pending = 0
player_y_pending = 0

block_coords = []
agreed_grounded = False
coyote_timer = 0
coyote_jump = False
grounded_frame_off = False
coyote_off = False
coyote_global_off = False
jump_held = False
jump_held_timer = 5
dash_renewed = False

game_on = False
title_on = True
game_fps = 60
programm_exit = False

camera_offset_x = 0
camera_offset_y = 0
last_camera_offset_x = 0
last_camera_offset_y = 0
ceiling_col_crutch = 0

held_key_w = False
held_key_s = False
key_pending = 3
no_active_game = 0
default_checkpoint = '480 2055'
current_checkpoint = tuple(default_checkpoint.split(' '))
game_check = True
transition_time_in = 0
transition_time_out = 0
button1_selected = 1
button2_selected = 1
button3_selected = 1
just_started = False
game_reset = False
paused_x, paused_y = False, False
death_timer = 0
player_sprite_offset = 0
walk_timer = 0
dead_timer = 0
dead_check = (0, 0)
fling_check = (0, 0, '')


def get_block_coords():
    level_file = open("map.txt", "r", encoding='utf-8')
    level_data = level_file.readlines()
    block_coords.clear()

    for y in range(camera_offset_y * 15 - 1, (camera_offset_y + 1) * 15):
        for x in range(camera_offset_x * 25 - 1, (camera_offset_x + 1) * 25):
            block_symb = level_data[y][x]
            if block_symb != '-':
                if block_symb in 'ij':
                    block_coords.append((x, y, 'passable', block_symb))
                elif block_symb in 'RST':
                    block_coords.append((x, y, 'platform', block_symb))
                elif block_symb in 'абвгдежзи':
                    block_coords.append((x, y, 'spike', block_symb))
                elif block_symb == 'ё':
                    block_coords.append((x, y, 'checkpoint', block_symb))
                elif block_symb in 'abc':
                    block_coords.append((x, y, 'fling', block_symb))
                else:
                    block_coords.append((x, y, 'solid', block_symb))
    level_file.close()


def draw_level():
    for block_x_n, block_y_n, block_type_n, block_symb_n in block_coords:
        block_sprite_offs_x = (ord(block_symb_n) - 65) % 7
        block_sprite_offs_y = (ord(block_symb_n) - 65) // 7
        spike_sprite_offs_x = (ord(block_symb_n) - 1072)

        if block_symb_n != '-' and block_symb_n != ' ':
            if block_type_n == 'spike':
                screen.blit(spikes,
                            ((block_x_n * 40) - (1000 * camera_offset_x), (block_y_n * 40) - (600 * camera_offset_y)),
                            area=((spike_sprite_offs_x * 40), 0, 40, 40))
            if block_type_n == 'checkpoint':
                if (block_x_n * 40) == current_checkpoint[0] and (block_y_n * 40) - 20 == current_checkpoint[1]:
                    screen.blit(checkpoints,
                                ((block_x_n * 40) - (1000 * camera_offset_x),
                                 (block_y_n * 40) - (600 * camera_offset_y)),
                                area=(0, 0, 40, 40))
                else:
                    screen.blit(checkpoints,
                                ((block_x_n * 40) - (1000 * camera_offset_x),
                                 (block_y_n * 40) - (600 * camera_offset_y)),
                                area=(40, 0, 40, 40))
            else:
                screen.blit(block_textures,
                            [(block_x_n * 40) - (1000 * camera_offset_x), (block_y_n * 40) - (600 * camera_offset_y)],
                            area=((block_sprite_offs_x * 40), (block_sprite_offs_y * 40), 40, 40))


while not programm_exit:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    keys = pygame.key.get_pressed()

    if game_on:

        # ----------------------------------------------------------------------
        # --- GAME START ---
        # ----------------------------------------------------------------------

        if ceiling_col_crutch:
            player_y += ceiling_col_crutch
            ceiling_col_crutch = 0

        camera_offset_x = int(player_x) // 1000
        camera_offset_y = int(player_y) // 600

        if camera_offset_x != last_camera_offset_x or camera_offset_y != last_camera_offset_y:
            player_y -= 3
            get_block_coords()
            if grounded_frame_off or just_started or game_reset:
                grounded = True
            print('updated coords')
        if just_started:
            player_x, player_y = [int(n) for n in current_checkpoint]
            just_started = False
        if game_reset:
            current_checkpoint = [int(n) for n in tuple(default_checkpoint.split(' '))]
            player_x, player_y = current_checkpoint
            game_reset = False

        # -- X MOVEMENT --
        # \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

        if not paused_x:
            # ---- setting friction
            if not grounded:
                friction_max = 10
            else:
                friction_max = 3

            # ---- friction preservation
            if friction_last_frame != friction_max:
                friction_left_n = int(friction_left_n * (friction_max // friction_last_frame))
                friction_right_n = int(friction_right_n * (friction_max // friction_last_frame))

            # --- LEFT MOVEMENT
            if keys[pygame.K_a]:
                last_orient_x = -1

                # failsafe for friction change
                if friction_left_n > friction_max:
                    friction_left_n = friction_max

                # ---- \/ friction start left
                if friction_left_n <= friction_max:
                    player_x_pending -= int(
                        player_speed * round(sin(((90 * friction_left_n) / friction_max) * (pi / 180)), 2))
                    friction_left_n += 1
                else:
                    # ---- \/ left friction off
                    player_x_pending -= int(player_speed - momentum_x)

            else:
                if friction_left_n > friction_max:
                    friction_left_n = friction_max
                if friction_left_n > 1:
                    # ---- \/ friction end left
                    player_x_pending -= int(
                        player_speed * round(sin(90 * friction_left_n / friction_max * (pi / 180)), 2))
                    friction_left_n -= 1

            # --- RIGHT MOVEMENT
            if keys[pygame.K_d]:
                if last_orient_x != -1 and not last_orient_x:
                    last_orient_x = 1

                # failsafe for friction change
                if friction_right_n > friction_max:
                    friction_right_n = friction_max

                # ---- \/ friction start right
                if friction_right_n <= friction_max:
                    player_x_pending += int(
                        player_speed * round(sin(((90 * friction_right_n) / friction_max) * (pi / 180)), 2))
                    friction_right_n += 1
                else:
                    # ---- \/ right friction off
                    player_x_pending += int(player_speed - momentum_x)

            else:
                if friction_right_n > friction_max:
                    friction_right_n = friction_max
                if friction_right_n > 1:
                    # ---- \/ friction end right
                    player_x_pending += int(
                        player_speed * round(sin(90 * friction_right_n / friction_max * (pi / 180)), 2))
                    friction_right_n -= 1

            friction_last_frame = friction_max

            if keys[pygame.K_a] and keys[pygame.K_d]:
                last_orient_x = 1

            player_x_pending += const_decreasing_x
            if const_decreasing_x > 0:
                const_decreasing_x -= 1
            elif const_decreasing_x < 0:
                const_decreasing_x += 1

        # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

        # -----------------------------------------------------------------

        # -- Y MOVEMENT --
        # \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/
        if not paused_y:
            if not keys[pygame.K_SPACE]:
                jump_held = False

            if jump_held and jump_held_timer:
                gravity_mult = 0

            if ((keys[pygame.K_SPACE] and grounded and buffer_frames_y) or
                    (keys[pygame.K_SPACE] and coyote_jump and buffer_frames_y)):
                jump_held = True
                dash_renewed = True
                jump_held_timer = 8
                coyote_jump = False
                gravity_mult = 0
                grounded = False
                const_y = 9
                coyote_global_off = True

            if not grounded:
                gravity_mult += 1

                falling = const_y - ((gravity_mult * 0.25) ** 2)
                if falling < -15:
                    falling = -15

                player_y_pending -= falling
            else:
                gravity_mult = 0
                const_y = 0

            if keys[pygame.K_SPACE] and not grounded:
                if buffer_frames_y > 0:
                    buffer_frames_y -= 1

            if not keys[pygame.K_SPACE]:
                buffer_frames_y = 4

            if keys[pygame.K_s]:
                last_orient_y = 1
            if keys[pygame.K_w]:
                last_orient_y = -1

            player_y_pending += const_decreasing_y
            if const_decreasing_y > 0:
                const_decreasing_y -= 1
            elif const_decreasing_y < 0:
                const_decreasing_y += 1

            if jump_held_timer:
                jump_held_timer -= 1

        # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

        # -----------------------------------------------------------------

        # -- DASHING MECHANIC --
        # \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

        if keys[pygame.K_k] and dashable and not dash_held:
            dash_initialized = True
            dash_in_motion = True
            dashable = False
            dash_x, dash_y = last_orient_x, last_orient_y
            const_y, const_x = 0, 0
            gravity_mult = 0
            friction_right_n, friction_left_n = 0, 0

            if dash_x == dash_y == 0:
                dash_x = 1
            if dash_x and dash_y:
                dash_ratio = 0.7

        if dash_in_motion and dash_duraion:
            coyote_global_off = True
            player_x += int(dash_speed * dash_x * dash_ratio)
            player_y += int(dash_speed * dash_y * dash_ratio)
            dash_duraion -= 1
        elif dash_initialized:
            coyote_global_off = True
            player_x += int(dash_speed * dash_x * dash_ratio)
            player_y += int(dash_speed * dash_y * dash_ratio)

            gravity_mult = 0
            player_x_pending, player_y_pending = 0, 0
            const_decreasing_x = int(player_speed * dash_x * dash_ratio)
            const_decreasing_y = int(player_speed * dash_y * dash_ratio)
            if dash_x == 1:
                friction_right_n = friction_max
            elif dash_x == -1:
                friction_left_n = friction_max
            if dash_y == 1:
                grounded = False
                gravity_mult = 15
            elif dash_y == -1:
                grounded = False
            dashable = False
            dash_initialized = False
            dash_in_motion = False
            dash_duraion = 10
            dash_cooldown = 10
            dash_ratio = 1
            coyote_off = True

        if (grounded or dash_renewed) and not dash_in_motion and not dash_cooldown:
            dash_renewed = False
            dashable = True

        if dash_cooldown > 0:
            dash_cooldown -= 1

        if keys[pygame.K_k]:
            dash_held = True
        else:
            dash_held = False

        if not dash_in_motion and not dash_initialized:
            player_x += player_x_pending
            player_y += player_y_pending
        player_x_pending, player_y_pending = 0, 0

        # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

        # -----------------------------------------------------------------

        # -- COLLISION --
        # \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

        block_current_x = tuple({int((player_x - 5) // 40), int(player_x // 40),
                                 int((player_x + 40) // 40), int((player_x + 45) // 40)})
        block_current_y = tuple({int((player_y - 5) // 40), int(player_y // 40), int((player_y + 20) // 40),
                                 int((player_y + 60) // 40), int((player_y + 65) // 40)})

        # Берём переменные
        agreed_grounded = False
        player_dir_x = int(player_x - last_player_x)
        player_dir_y = int(last_player_y - player_y)
        player_dir_x_pend, player_dir_y_pend = (0, 0, 0), (0, 0, 0)
        block_offset_x, block_offset_y = 0, 0
        player_offset_x, player_offset_y = 0, 0
        player_dir_x_contr, player_dir_y_contr = (0, 0, 0), (0, 0, 0)
        collision_happened = False

        if player_dir_x > 0 and player_dir_y > 0:
            player_offset_x = 1
            block_offset_y = 1
        if player_dir_x < 0 < player_dir_y:
            block_offset_y = 1
            block_offset_x = 1
        if player_dir_x > 0 > player_dir_y:
            player_offset_x = 1
            player_offset_y = 1
        if player_dir_x < 0 and player_dir_y < 0:
            player_offset_y = 1
            block_offset_x = 1

        for block_x, block_y, block_type, block_symb in block_coords:
            if block_x in block_current_x and block_y in block_current_y:
                if -40 < player_x - (block_x * 40) < 40 and -60 < (block_y * 40) - player_y < 60:
                    collision_happened = True

                    if block_type == 'solid' or block_type == 'platform':
                        # 1 Случай
                        if player_dir_y and not player_dir_x:
                            player_dir_y_pend = (player_dir_y, block_x, block_y, block_type)
                        elif not player_dir_y and player_dir_x:
                            player_dir_x_pend = (player_dir_x, block_x, block_y, block_type)

                        # 2 Случай
                        if player_dir_x and player_dir_y:
                            if ((0 < player_x - (block_x * 40) < 40 and player_dir_x > 0) or
                                    (-40 < player_x - (block_x * 40) < 0 and player_dir_x < 0)):
                                player_dir_y_pend = (player_dir_y, block_x, block_y, block_type)
                            elif ((-60 < player_y - (block_y * 40) < 0 < player_dir_y) or
                                  (-20 < player_y - (block_y * 40) < 40 and player_dir_y < 0)):
                                player_dir_x_pend = (player_dir_x, block_x, block_y, block_type)

                            # 3 Случай
                            elif player_dir_x and player_dir_y:
                                if abs(((block_y * 40) + (40 * block_offset_y)) - (
                                        player_y + (60 * player_offset_y))) != 0:
                                    if ((abs(player_dir_x) / abs(player_dir_y)) >=
                                            (abs(((block_x * 40) + (40 * block_offset_x)) - (
                                                    player_x + (40 * player_offset_x))) /
                                             abs(((block_y * 40) + (40 * block_offset_y)) - (
                                                     player_y + (60 * player_offset_y))))):
                                        player_dir_x_contr = (player_dir_x, block_x, block_y, block_type)
                                    else:
                                        player_dir_y_contr = (player_dir_y, block_x, block_y, block_type)
                                else:
                                    player_x, player_y = last_player_x, last_player_y

                    if block_type == 'checkpoint':
                        if current_checkpoint != (block_x * 40, block_y * 40 - 20):
                            current_checkpoint = (block_x * 40, block_y * 40 - 20)
                            with open('checkpoint_data.txt', 'w') as overwrite:
                                text = ' '.join([str(n) for n in current_checkpoint])
                                overwrite.write(text)
                            overwrite.close()

                    if block_type == 'spike':
                        dead_check = ((block_x * 40), (block_y * 40))

                    if block_type == 'fling':
                        fling_check = ((block_x * 40), (block_y * 40), block_symb)

                if block_type == 'solid' or block_type == 'platform':
                    if (player_y + 60) - (block_y * 40) == 0 and -40 < player_x - (block_x * 40) < 40:
                        agreed_grounded = True

        # Последствия
        if collision_happened:
            if (player_dir_x_pend == player_dir_y_pend == (0, 0, 0)) and (
                    player_dir_x_contr != (0, 0, 0) or player_dir_y_contr != (0, 0, 0)):
                player_dir_x_pend = player_dir_x_contr
                player_dir_y_pend = player_dir_y_contr

            if player_dir_x_pend[0] > 0 and player_dir_x_pend[3] != 'platform':
                print('sent left')
                player_x = (player_dir_x_pend[1] * 40) - 40
                dash_x, dash_ratio = 0, 1
                friction_right_n = 0
            if player_dir_x_pend[0] < 0 and player_dir_x_pend[3] != 'platform':
                print('sent right')
                player_x = (player_dir_x_pend[1] * 40) + 40
                dash_x, dash_ratio = 0, 1
                friction_left_n = 0
            if player_dir_y_pend[0] > 0 and player_dir_y_pend[3] != 'platform':
                print(player_dir_y_pend[3])
                print('sent donw :)')
                player_y = (player_dir_y_pend[2] * 40) + 40
                const_y, const_decreasing_y = 0, 0
                jump_held = False
                dash_in_motion = False
                ceiling_col_crutch = 5
            if player_dir_y_pend[0] < 0 and last_player_y <= (player_dir_y_pend[2] * 40) - 50:
                print('sent up')
                agreed_grounded = True
                player_y = (player_dir_y_pend[2] * 40) - 60
                dash_in_motion = False
                const_y, const_decreasing_y = 0, 0

        if -40 < player_x - dead_check[0] < 40 and -60 < dead_check[1] - player_y < 60:
            if not death_timer:
                const_x, const_y = 0, 0
                dash_in_motion = False
                death_timer = 30

        if -40 < player_x - fling_check[0] < 40 and -60 < fling_check[1] - player_y < 60:
            grounded = False
            dash_in_motion = False
            if fling_check[2] == 'a':
                player_y -= 1
                const_y = 20
                gravity_mult = 0
                dashable = True
            elif fling_check[2] == 'b':
                player_x += 1
                const_decreasing_x = 20
                gravity_mult = 0
                const_y = 7
                dashable = True
            elif fling_check[2] == 'c':
                player_x -= 1
                const_decreasing_x = -20
                gravity_mult = 0
                const_y = 7
                dashable = True
        print(grounded_frame_off)
        if agreed_grounded:
            grounded = True
            coyote_off = True
            coyote_global_off = False
        else:
            grounded = False
            coyote_off = False
        if not grounded and grounded_frame_off and not coyote_off:
            coyote_timer = 4
            coyote_off = True

        if coyote_timer and not coyote_global_off:
            coyote_jump = True
            coyote_timer -= 1
        else:
            coyote_jump = False


        # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

        # -----------------------------------------------------------------

        # -- OUTPUT --
        # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

        # Clear last keys
        last_orient_x = 0
        last_orient_y = 0

        if keys[pygame.K_ESCAPE]:
            game_on = False
            title_on = True
            game_check = True

        # Прорисовка
        screen.blit(background, (0, 0), )

        if not death_timer:
            if dashable:
                screen.blit(outline_dashable, (player_x - 20 - (1000 * camera_offset_x), player_y - 20 - (600 * camera_offset_y)))
            else:
                screen.blit(outline_dashless, (player_x - 20 - (1000 * camera_offset_x), player_y - 20 - (600 * camera_offset_y)))

        draw_level()

        if not death_timer:
            dead_timer = 0
            paused_x, paused_y = False, False
            # pygame.draw.rect(screen, 'blue',
            #                  (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y), 40, 60))
            if player_dir_x < 0:
                player_sprite_offset = 200
            elif player_dir_x > 0:
                player_sprite_offset = 0

            # print(dash_x, dash_y)
            if dash_in_motion and dash_x and not dash_y:
                screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                            area=(80 + player_sprite_offset, 180, 40, 60))
            elif dash_in_motion and not dash_x and dash_y < 0:
                screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                            area=(0 + player_sprite_offset, 180, 40, 60))
            elif dash_in_motion and not dash_x and dash_y > 0:
                screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                            area=(40 + player_sprite_offset, 180, 40, 60))
            elif dash_in_motion and dash_x and dash_y < 0:
                screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                            area=(120 + player_sprite_offset, 180, 40, 60))
            elif dash_in_motion and dash_x and dash_y > 0:
                screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                            area=(160 + player_sprite_offset, 180, 40, 60))
            elif not grounded and player_dir_y > 0:
                screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                            area=(0 + player_sprite_offset, 120, 40, 60))
            elif not grounded and player_dir_y <= 0:
                screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                            area=(80 + player_sprite_offset, 120, 40, 60))
            elif player_dir_x and grounded and player_dir_x_pend == (0, 0, 0):
                walk_timer += 1
                screen.blit(player_sprites,
                            (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                            area=((40 * (walk_timer // 7 % 3)) + player_sprite_offset, 60, 40, 60))

            else:
                walk_timer = 0
                screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                        area=(0 + player_sprite_offset, 0, 40, 60))

        elif death_timer == 2:
            player_x, player_y = current_checkpoint
            death_timer -= 1

        elif death_timer > 0:
            dead_timer += 1
            screen.blit(player_sprites, (player_x - (1000 * camera_offset_x), player_y - (600 * camera_offset_y)),
                        area=(40 * (dead_timer // 3), 240, 40, 60))
            death_timer -= 1
            paused_x, paused_y = True, True
        print(death_timer)

        screen.blit(rendering, (0, 0), )
        last_player_x = player_x
        last_player_y = player_y
        if not block_coords:
            get_block_coords()
            pass
        last_camera_offset_x = camera_offset_x
        last_camera_offset_y = camera_offset_y
        grounded_frame_off = grounded

    # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

    # -----------------------------------------------------------------

    # -- MAIN SCREEN --
    # \/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/

    if title_on:
        if game_check:

            data_checkpoint = open('checkpoint_data.txt', 'r', encoding='utf-8')
            checkpoint = data_checkpoint.readlines()
            print(checkpoint, default_checkpoint)
            if not checkpoint or ' '.join(checkpoint) == default_checkpoint:
                key_pending = 2
                no_active_game = 1
            else:
                key_pending = 3
                no_active_game = 0
            data_checkpoint.close()
            game_check = False

        screen.blit(main_screen, (0, 0))

        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            if not held_key_s:
                if 2 <= key_pending <= 3 - no_active_game:
                    key_pending -= 1
            held_key_s = True
        else:
            held_key_s = False

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            if not held_key_w:
                if 1 <= key_pending <= 2 - no_active_game:
                    key_pending += 1
            held_key_w = True
        else:
            held_key_w = False

        if key_pending == 3:
            button1_selected = 0
        else:
            button1_selected = 1
        if key_pending == 2:
            button2_selected = 0
        else:
            button2_selected = 1
        if key_pending == 1:
            button3_selected = 0
        else:
            button3_selected = 1

        if keys[pygame.K_SPACE]:
            if key_pending == 3:
                if not no_active_game:
                    with open('checkpoint_data.txt', 'r', encoding='utf-8') as reading:
                        coords = tuple(' '.join(reading.readlines()).split(' '))
                        current_checkpoint = coords

                    reading.close()
                    title_on = False
                    game_on = True
                    get_block_coords()
                    buffer_frames_y = 0
                    just_started = True
                    grounded = True

            if key_pending == 2:
                with open('checkpoint_data.txt', 'w') as overwrite:
                    overwrite.write(default_checkpoint)
                    current_checkpoint = tuple(default_checkpoint.split(' '))
                overwrite.close()
                title_on = False
                game_on = True
                get_block_coords()
                buffer_frames_y = 0
                game_reset = True
                grounded = True

            if key_pending == 1:
                programm_exit = True

        if not no_active_game:
            screen.blit(main_buttons, (335, 250), area=(0, 76 * button1_selected, 332, 78))
        else:
            screen.blit(main_buttons, (335, 250), area=(0, 156, 332, 78))

        screen.blit(main_buttons, (335, 327), area=(0, 76 * button2_selected, 332, 78))
        screen.blit(main_buttons, (335, 404), area=(0, 76 * button3_selected, 332, 78))
        screen.blit(main_button_texts, (335, 250))

    # /\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\/\

    # -----------------------------------------------------------------

    # Обновление экрана
    pygame.display.flip()

    # Задержка для контроля частоты кадров
    pygame.time.Clock().tick(game_fps)
