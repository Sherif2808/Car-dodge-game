import pygame as pg
from pygame import mixer
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import time
import datetime
import os
import math

# ---------- User-uploaded file path (available locally) ----------
UPLOADED_IMAGE_PATH = r"/mnt/data/c1434bc6-85de-4c0a-87cf-1487d18dc83d.png"

# ---------- Configuration ----------
WIN_W, WIN_H = 900, 600
GROUND_Y = -1.5
PLAYER_Y = GROUND_Y + 0.4
PLAYER_Z = 0.0
PLAYER_HALF_WIDTH = 0.9
PLAYER_HALF_DEPTH = 0.6
PLAYER_SPEED = 10.0
OBSTACLE_SIZE = 1.5
OBSTACLE_SPAWN_Z = -60.0
OBSTACLE_END_Z = 4.0

# Default gameplay params (will be overridden by difficulty)
SPAWN_INTERVAL_DEFAULT = 1.0
OBSTACLE_SPEED_START_DEFAULT = 18.0
OBSTACLE_SPEED_INC_DEFAULT = 0.3
MAX_LIVES = 3

# Track appearance
ROAD_WIDTH = 14.0
STRIP_LENGTH = 4.0

# Leaderboard file (absolute path - set to your folder)
LEADERBOARD_PATH = r"CarDodge_Leaderboard.txt"
LEADERBOARD_SHOW_COUNT = 10  # how many recent entries to show

# Ensure leaderboard directory exists
try:
    os.makedirs(os.path.dirname(LEADERBOARD_PATH), exist_ok=True)
except Exception:
    pass

# ---------- OpenGL setup ----------
def init_gl():
    glClearColor(0.2, 0.3, 0.5, 1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glShadeModel(GL_SMOOTH)

    # Enable blending for HUD/text transparency
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    # This makes the cars look 3D instead of flat blocks
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_COLOR_MATERIAL)
    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)

    # Sun position light
    light_pos = [15.0, 15.0, 10.0, 1.0]
    glLightfv(GL_LIGHT0, GL_POSITION, light_pos)

def set_perspective():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, WIN_W / WIN_H, 0.1, 200.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    glTranslatef(0.0, -0.6, -18.0)

def draw_cube(size=1.0):
    s = size / 2.0
    glBegin(GL_QUADS)
    # front
    glNormal3f(0,0,1); glVertex3f( s,  s,  s); glVertex3f(-s,  s,  s); glVertex3f(-s, -s,  s); glVertex3f( s, -s,  s)
    # back
    glNormal3f(0,0,-1); glVertex3f( s, -s, -s); glVertex3f(-s, -s, -s); glVertex3f(-s,  s, -s); glVertex3f( s,  s, -s)
    # top
    glNormal3f(0,1,0); glVertex3f( s,  s, -s); glVertex3f(-s,  s, -s); glVertex3f(-s,  s,  s); glVertex3f( s,  s,  s)
    # bottom
    glNormal3f(0,-1,0); glVertex3f( s, -s,  s); glVertex3f(-s, -s,  s); glVertex3f(-s, -s, -s); glVertex3f( s, -s, -s)
    # left
    glNormal3f(-1,0,0); glVertex3f(-s,  s,  s); glVertex3f(-s,  s, -s); glVertex3f(-s, -s, -s); glVertex3f(-s, -s,  s)
    # right
    glNormal3f(1,0,0); glVertex3f( s,  s, -s); glVertex3f( s,  s,  s); glVertex3f( s, -s,  s); glVertex3f( s, -s, -s)
    glEnd()

# Builds a car using multiple scaled cubes (Body, Cabin, Wheels)
def draw_car(color):
    
    # 1. Car Body
    glPushMatrix()
    glColor3f(*color)
    glScalef(1.0, 0.4, 1.8) # Flatten and stretch
    draw_cube(1.0)
    glPopMatrix()

    # 2. Cabin (Top)
    glPushMatrix()
    glColor3f(0.2, 0.2, 0.2) # Dark grey windows
    glTranslatef(0.0, 0.35, -0.1) 
    glScalef(0.8, 0.35, 0.8)
    draw_cube(1.0)
    glPopMatrix()

    # 3. Wheels
    wheel_color = (0.1, 0.1, 0.1)
    wheel_positions = [(-0.55, -0.2, 0.5), (0.55, -0.2, 0.5), (-0.55, -0.2, -0.6), (0.55, -0.2, -0.6)]
    for wx, wy, wz in wheel_positions:
        glPushMatrix()
        glColor3f(*wheel_color)
        glTranslatef(wx, wy, wz)
        glScalef(0.2, 0.3, 0.3)
        draw_cube(1.0)
        glPopMatrix()

    # 4. Headlights
    glPushMatrix()
    glColor3f(1.0, 1.0, 0.0)
    glTranslatef(0.0, 0.0, 0.91)
    glScalef(0.8, 0.1, 0.05)
    draw_cube(1.0)
    glPopMatrix()


# ---------- Racing Track ----------
def draw_racing_track(track_offset):
    y = GROUND_Y
    
    glDisable(GL_LIGHTING) # Disable lighting so ground colors pop
    
    # 1. Grass
    glColor3f(0.1, 0.5, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(-100, y, -100); glVertex3f(-ROAD_WIDTH/2, y, -100)
    glVertex3f(-ROAD_WIDTH/2, y, 20); glVertex3f(-100, y, 20)
    glVertex3f(ROAD_WIDTH/2, y, -100); glVertex3f(100, y, -100)
    glVertex3f(100, y, 20); glVertex3f(ROAD_WIDTH/2, y, 20)
    glEnd()

    # 2. Road
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex3f(-ROAD_WIDTH/2, y, -100); glVertex3f(ROAD_WIDTH/2, y, -100)
    glVertex3f(ROAD_WIDTH/2, y, 20); glVertex3f(-ROAD_WIDTH/2, y, 20)
    glEnd()

    # 3. Moving Rumble Strips
    z_start = -100.0 + (track_offset % STRIP_LENGTH)
    z = z_start
    count = 0
    while z < 20:
        if count % 2 == 0: glColor3f(0.9, 0.1, 0.1) # Red
        else: glColor3f(1.0, 1.0, 1.0) # White
        
        # Left & Right Strips
        glBegin(GL_QUADS)
        glVertex3f(-ROAD_WIDTH/2 - 1.0, y+0.02, z); glVertex3f(-ROAD_WIDTH/2, y+0.02, z)
        glVertex3f(-ROAD_WIDTH/2, y+0.02, z + STRIP_LENGTH); glVertex3f(-ROAD_WIDTH/2 - 1.0, y+0.02, z + STRIP_LENGTH)
        
        glVertex3f(ROAD_WIDTH/2, y+0.02, z); glVertex3f(ROAD_WIDTH/2 + 1.0, y+0.02, z)
        glVertex3f(ROAD_WIDTH/2 + 1.0, y+0.02, z + STRIP_LENGTH); glVertex3f(ROAD_WIDTH/2, y+0.02, z + STRIP_LENGTH)
        glEnd()
        z += STRIP_LENGTH
        count += 1
    
    # 4. Center Line
    glColor3f(1.0, 0.8, 0.0)
    z = z_start
    count = 0
    while z < 20:
        if count % 2 == 0:
            glBegin(GL_QUADS)
            glVertex3f(-0.2, y+0.02, z + 1.0); glVertex3f( 0.2, y+0.02, z + 1.0)
            glVertex3f( 0.2, y+0.02, z + 3.0); glVertex3f(-0.2, y+0.02, z + 3.0)
            glEnd()
        z += STRIP_LENGTH
        count += 1

    glEnable(GL_LIGHTING)

def draw_3d_sun():
    # We keep lighting ENABLED here so the sphere reacts to light and looks 3D
    # Or we can disable it and use just color.
    # To make it look like a 3D ball, we use gluSphere.
    
    glPushMatrix()
    glTranslatef(15.0, 15.0, -80.0) 
    
    # Sun Color
    glColor3f(1.0, 0.9, 0.0) 
    
    # Create a Quadric object for the sphere
    quadric = gluNewQuadric()
    
    # ### --- NEW: Draw a 3D Sphere instead of a flat disk ---
    # Radius 8.0, 20 slices, 20 stacks
    gluSphere(quadric, 8.0, 20, 20)
    
    gluDeleteQuadric(quadric)
    glPopMatrix()

# ---------- HUD text ----------
def create_text_texture(font, text, color=(255,255,255)):
    surface = font.render(text, True, color)
    data = pg.image.tostring(surface, "RGBA", True)
    w, h = surface.get_size()
    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glPixelStorei(GL_UNPACK_ALIGNMENT,1)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
    glBindTexture(GL_TEXTURE_2D, 0)
    return tex_id, w, h


def draw_text_ortho(tex_id, w, h, x, y):
    glDisable(GL_LIGHTING)
    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glColor3f(1,1,1)

    glMatrixMode(GL_PROJECTION)
    glPushMatrix(); glLoadIdentity()
    glOrtho(0, WIN_W, 0, WIN_H, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glPushMatrix(); glLoadIdentity()

    glBegin(GL_QUADS)
    glTexCoord2f(0,1); glVertex2f(x, WIN_H - y)
    glTexCoord2f(1,1); glVertex2f(x + w, WIN_H - y)
    glTexCoord2f(1,0); glVertex2f(x + w, WIN_H - (y + h))
    glTexCoord2f(0,0); glVertex2f(x, WIN_H - (y + h))
    glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION); glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

    glBindTexture(GL_TEXTURE_2D, 0)
    glDisable(GL_TEXTURE_2D)

# ---------- Game objects ----------
class Obstacle:
    def __init__(self, x, y, z, size, color):
        self.x, self.y, self.z = x, y, z
        self.size, self.color = size, color

    def update(self, dz):
        self.z += dz
   

# ---------- Collision ----------
def check_collision(player_x, obstacle):
    dx = abs(player_x - obstacle.x)
    dz = abs(PLAYER_Z - obstacle.z)
    collide_x = dx <= (PLAYER_HALF_WIDTH + obstacle.size / 2.0)
    collide_z = dz <= (PLAYER_HALF_DEPTH + obstacle.size / 2.0)
    return collide_x and collide_z

# ---------- Leaderboard helpers ----------
def append_score_to_leaderboard(name, score):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_name = name.strip() if name and name.strip() else "Player"
    line = f"{ts} | {safe_name} | {score}\n"
    try:
        with open(LEADERBOARD_PATH, "a", encoding="utf-8") as f:
            f.write(line)
        print("Score saved:", line.strip())
    except Exception as e:
        print("Failed to write leaderboard:", e)

def read_leaderboard_lines():
    try:
        with open(LEADERBOARD_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = []
    return [l.strip() for l in lines if l.strip()]

# ---------- Main game ----------
def main():
    pg.init()
    pg.mixer.init()
    pg.font.init()
    screen = pg.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | OPENGL)
    pg.display.set_caption("CAR DODGE 3D")
    clock = pg.time.Clock()

    # Fonts
    title_font = pg.font.Font(None, 72)
    menu_font = pg.font.Font(None, 40)
    hud_font = pg.font.Font(None, 28)
    big_font = pg.font.Font(None, 56)
    input_font = pg.font.Font(None, 36)

    # Channels For Sound and Music
    channel1 = pg.mixer.Channel(0)
    channel2 = pg.mixer.Channel(1)
    channel3 = pg.mixer.Channel(2)
    songmenu = pg.mixer.Sound("Animal Crossing Population Growing 7 P.M.ogg")
    songgameover = pg.mixer.Sound("AudioCutter_Hades II - Time Cannot Be Stopped.ogg")


    init_gl()
    set_perspective()

    # Game states
    state = 'menu'  # 'menu', 'enter_name', 'difficulty', 'playing', 'leaderboard', 'game_over'
    menu_index = 0            # for main menu (Play, Leaderboard)
    difficulty_index = 1      # 0=Easy,1=Normal,2=Hard
    difficulties = ['Easy', 'Normal', 'Hard']

    # difficulty presets
    difficulty_params = [
        {"spawn_interval": 1.4, "obstacle_speed_start": 12.0, "obstacle_speed_inc": 0.18, "music": "Hotel.ogg"},  # easy
        {"spawn_interval": 1.0, "obstacle_speed_start": 18.0, "obstacle_speed_inc": 0.3, "music": "Godspeed - Grace CST.ogg"},   # normal
        {"spawn_interval": 0.6, "obstacle_speed_start": 24.0, "obstacle_speed_inc": 0.45, "music": "Death By Glamour.ogg"},  # hard
    ]

    # playing variables
    player_x = 0.0
    lives = MAX_LIVES
    score = 0
    obstacles = []
    spawn_timer = 0.0
    obstacle_speed = OBSTACLE_SPEED_START_DEFAULT
    spawn_interval = SPAWN_INTERVAL_DEFAULT
    obstacle_speed_inc = OBSTACLE_SPEED_INC_DEFAULT
    track_offset = 0.0
    hit_flash_timer = 0.0
    running = True
    paused = False
    game_over = False

    # input name variables
    current_player_name = ""
    name_max_len = 12

    def start_game_with_difficulty(idx):
        nonlocal player_x, lives, score, obstacles, spawn_timer, obstacle_speed, spawn_interval, obstacle_speed_inc, game_over, paused
        params = difficulty_params[idx]
        player_x = 0.0
        lives = MAX_LIVES
        score = 0
        obstacles = []
        spawn_timer = 0.0
        obstacle_speed = params["obstacle_speed_start"]
        spawn_interval = params["spawn_interval"]
        obstacle_speed_inc = params["obstacle_speed_inc"]
        track_offset = 0.0
        hit_flash_timer = 0.0
        song1 = pg.mixer.Sound(params["music"])
        channel1.play(song1, loops=-1)
        game_over = False
        paused = False
        return player_x, lives, score, obstacles, spawn_timer, obstacle_speed, spawn_interval, obstacle_speed_inc, game_over, paused

    while running:
        dt = clock.tick(60) / 1000.0

        # events
        for event in pg.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if state == 'menu':
                        running = False
                    else:
                        state = 'menu'

                # menu navigation
                if state == 'menu':
                    if event.key in (K_UP, K_w):
                        menu_index = max(0, menu_index - 1)
                    elif event.key in (K_DOWN, K_s):
                        menu_index = min(1, menu_index + 1)
                    elif event.key in (K_RETURN, K_KP_ENTER):
                        if menu_index == 0:  # Play -> ask for name first
                            current_player_name = ""
                            state = 'enter_name'
                        else:
                            state = 'leaderboard'

                # Name input screen
                elif state == 'enter_name':
                    if event.key == K_RETURN:
                        # confirm name and go to difficulty selection
                        state = 'difficulty'
                        difficulty_index = 1
                    elif event.key == K_BACKSPACE:
                        current_player_name = current_player_name[:-1]
                    else:
                        # allow letters, numbers, spaces, dash, underscore
                        ch = event.unicode
                        if ch and len(current_player_name) < name_max_len:
                            # basic filter: printable
                            if ch.isprintable():
                                current_player_name += ch

                elif state == 'difficulty':
                    if event.key in (K_UP, K_w):
                        difficulty_index = max(0, difficulty_index - 1)
                    elif event.key in (K_DOWN, K_s):
                        difficulty_index = min(2, difficulty_index + 1)
                    elif event.key in (K_RETURN, K_KP_ENTER):
                        (player_x, lives, score, obstacles, spawn_timer, obstacle_speed,
                         spawn_interval, obstacle_speed_inc, game_over, paused) = start_game_with_difficulty(difficulty_index)
                        state = 'playing'
                    elif event.key == K_ESCAPE:
                        state = 'menu'

                elif state == 'leaderboard':
                    if event.key in (K_ESCAPE, K_RETURN):
                        state = 'menu'

                elif state == 'playing':
                    if event.key == K_p:
                        paused = not paused

                elif state == 'game_over':
                    if event.key == K_r:
                        # restart with same difficulty
                        (player_x, lives, score, obstacles, spawn_timer, obstacle_speed,
                         spawn_interval, obstacle_speed_inc, game_over, paused) = start_game_with_difficulty(difficulty_index)
                        state = 'playing'
                    elif event.key in (K_ESCAPE, K_RETURN):
                        state = 'menu'

        # updates when playing
        if state == 'playing' and not paused and not game_over:
            keys = pg.key.get_pressed()
            move = 0.0
            if keys[K_LEFT] or keys[K_a]:
                move -= 1.0
            if keys[K_RIGHT] or keys[K_d]:
                move += 1.0
            player_x += move * PLAYER_SPEED * dt
            limit = ROAD_WIDTH/2.0 - PLAYER_HALF_WIDTH
            player_x = max(-limit, min(limit, player_x))
            if hit_flash_timer > 0:
                hit_flash_timer -= dt
            spawn_timer += dt
            if spawn_timer > spawn_interval:
                spawn_timer = 0.0
                road_edge = ROAD_WIDTH/2.0 - OBSTACLE_SIZE
                x = random.uniform(-road_edge, road_edge)
                y = GROUND_Y + OBSTACLE_SIZE / 2.0
                z = OBSTACLE_SPAWN_Z
                color = (random.random()*0.7 + 0.3, random.random()*0.7 + 0.3, random.random()*0.7 + 0.3)
                obstacles.append(Obstacle(x, y, z, OBSTACLE_SIZE, color))

            dz = obstacle_speed * dt
            obstacle_speed += obstacle_speed_inc * dt
            track_offset += dz
            remove_list = []
            for ob in obstacles:
                ob.update(dz)
                if check_collision(player_x, ob):
                    channel2.play(pg.mixer.Sound("car-crash-sound-376882.mp3"))
                    lives -= 1
                    remove_list.append(ob)
                    hit_flash_timer = 1.0
                    if lives <= 0:
                        channel3.play(songgameover)
                        game_over = True
                elif ob.z > OBSTACLE_END_Z:
                    channel2.play(pg.mixer.Sound("coin-recieved-230517.mp3"))
                    score += 10
                    remove_list.append(ob)
            for r in remove_list:
                if r in obstacles:
                    obstacles.remove(r)

            if game_over:
                # save score with the name provided earlier (Option A)
                append_score_to_leaderboard(current_player_name, score)
                state = 'game_over'

        # ---------- Rendering ----------
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_3d_sun()
        glPushMatrix()
        draw_racing_track(track_offset)
        if state in ('playing', 'game_over'):
            for ob in obstacles:
                glPushMatrix()
                glTranslatef(ob.x, ob.y, ob.z)
                glScalef(1.3, 1.3, 1.3) # Make car slightly bigger than box
                draw_car(ob.color)
                glPopMatrix()
            glPushMatrix()
            glTranslatef(player_x, PLAYER_Y, PLAYER_Z)
            glScalef(1.3, 1.3, 1.3)
            
            # ### --- NEW: Color Flash Logic ---
            player_color = (0.1, 0.6, 0.9) # Normal Blue
            if hit_flash_timer > 0:
                # Toggle color every 0.1 seconds
                if int(hit_flash_timer * 10) % 2 == 0:
                    player_color = (1.0, 0.0, 0.0) # Flash Red
            
            draw_car(player_color)
            glPopMatrix()
        glPopMatrix()

        # HUD & Menus
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # MENU
        if state == 'menu':
            title_tex, tw, th = create_text_texture(title_font, "CAR DODGE 3D", (255,255,255))
            draw_text_ortho(title_tex, tw, th, WIN_W//2 - tw//2, WIN_H//2 - 120)
            glDeleteTextures([title_tex])

            opts = ["Play", "Leaderboard"]
            for i, opt in enumerate(opts):
                color = (255, 220, 40) if i == menu_index else (255,255,255)
                tex, w, h = create_text_texture(menu_font, opt, color)
                draw_text_ortho(tex, w, h, WIN_W//2 - w//2, WIN_H//2 - 30 + i*50)
                glDeleteTextures([tex])

            hint_tex, hw, hh = create_text_texture(hud_font, "Use Up/Down and Enter. Esc to Quit.", (200,200,200))
            draw_text_ortho(hint_tex, hw, hh, WIN_W//2 - hw//2, WIN_H - 60)
            glDeleteTextures([hint_tex])

        # ENTER NAME (Option A)
        elif state == 'enter_name':
            msg_tex, mw, mh = create_text_texture(title_font, "ENTER YOUR NAME", (255,255,255))
            draw_text_ortho(msg_tex, mw, mh, WIN_W//2 - mw//2, WIN_H//2 - 120)
            glDeleteTextures([msg_tex])

            # show current typed name with cursor
            display_name = current_player_name + ("_" if (time.time() % 1.0) < 0.6 else "")
            name_tex, nw, nh = create_text_texture(input_font, display_name, (255, 220, 40))
            draw_text_ortho(name_tex, nw, nh, WIN_W//2 - nw//2, WIN_H//2 - 20)
            glDeleteTextures([name_tex])

            hint_tex, hw, hh = create_text_texture(hud_font, "Type name (max 12 chars). Press Enter to continue.", (200,200,200))
            draw_text_ortho(hint_tex, hw, hh, WIN_W//2 - hw//2, WIN_H - 60)
            glDeleteTextures([hint_tex])

        # DIFFICULTY
        elif state == 'difficulty':
            title_tex, tw, th = create_text_texture(title_font, "Select Difficulty", (255,255,255))
            draw_text_ortho(title_tex, tw, th, WIN_W//2 - tw//2, WIN_H//2 - 130)
            glDeleteTextures([title_tex])

            for i, d in enumerate(difficulties):
                color = (255,220,40) if i == difficulty_index else (255,255,255)
                tex, w, h = create_text_texture(menu_font, d, color)
                draw_text_ortho(tex, w, h, WIN_W//2 - w//2, WIN_H//2 - 20 + i*50)
                glDeleteTextures([tex])

            info_tex, iw, ih = create_text_texture(hud_font, "Esc to go back", (200,200,200))
            draw_text_ortho(info_tex, iw, ih, WIN_W//2 - iw//2, WIN_H - 60)
            glDeleteTextures([info_tex])

        # LEADERBOARD
        elif state == 'leaderboard':
            title_tex, tw, th = create_text_texture(title_font, "LEADERBOARD", (255,255,255))
            draw_text_ortho(title_tex, tw, th, WIN_W//2 - tw//2, 40)
            glDeleteTextures([title_tex])

            lines = read_leaderboard_lines()
            show_lines = list(reversed(lines))[:LEADERBOARD_SHOW_COUNT]
            if not show_lines:
                empty_tex, ew, eh = create_text_texture(menu_font, "No scores yet", (200,200,200))
                draw_text_ortho(empty_tex, ew, eh, WIN_W//2 - ew//2, WIN_H//2 - 20)
                glDeleteTextures([empty_tex])
            else:
                start_y = 120
                for i, ln in enumerate(show_lines):
                    tex, w, h = create_text_texture(hud_font, f"{i+1}. {ln}", (230,230,230))
                    draw_text_ortho(tex, w, h, 60, start_y + i*30)
                    glDeleteTextures([tex])

            hint_tex, hw, hh = create_text_texture(hud_font, "Esc or Enter to return to menu", (200,200,200))
            draw_text_ortho(hint_tex, hw, hh, WIN_W//2 - hw//2, WIN_H - 60)
            glDeleteTextures([hint_tex])

        # PLAYING HUD
        elif state == 'playing':
            score_tex, sw, sh = create_text_texture(hud_font, f"Score: {score}", (255,255,255))
            lives_tex, lw, lh = create_text_texture(hud_font, f"Lives: {lives}", (255,200,80))
            draw_text_ortho(score_tex, sw, sh, 12, 12)
            draw_text_ortho(lives_tex, lw, lh, WIN_W - (lw + 12), 12)
            glDeleteTextures([score_tex, lives_tex])

            if paused:
                channel1.pause()
                ptex, pw, ph = create_text_texture(big_font, "PAUSED", (255,255,255))
                draw_text_ortho(ptex, pw, ph, WIN_W//2 - pw//2, WIN_H//2 - ph//2)
                glDeleteTextures([ptex])

        # GAME OVER
        elif state == 'game_over':
            channel1.pause()
            score_tex, sw, sh = create_text_texture(hud_font, f"Final Score: {score}", (255,255,255))
            draw_text_ortho(score_tex, sw, sh, WIN_W//2 - sw//2, WIN_H//2 + 40)
            glDeleteTextures([score_tex])

            msg1_tex, mw1, mh1 = create_text_texture(big_font, "GAME OVER", (255,40,40))
            msg2_tex, mw2, mh2 = create_text_texture(menu_font, "Press R to Restart or Esc to Menu", (255,255,255))
            draw_text_ortho(msg1_tex, mw1, mh1, WIN_W//2 - mw1//2, WIN_H//2 - 90)
            draw_text_ortho(msg2_tex, mw2, mh2, WIN_W//2 - mw2//2, WIN_H//2 - 20)
            glDeleteTextures([msg1_tex, msg2_tex])

        # restore 3D state
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)

        pg.display.flip()

    pg.quit()

if __name__ == "__main__":
    main()
