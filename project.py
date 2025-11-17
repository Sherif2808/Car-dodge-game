import pygame as pg
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import random
import time

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
SPAWN_INTERVAL = 1.0
OBSTACLE_SPEED_START = 18.0
OBSTACLE_SPEED_INC = 0.3
MAX_LIVES = 3

# ---------- OpenGL setup ----------
def init_gl():
    glClearColor(0.15, 0.18, 0.22, 1.0)
    glEnable(GL_DEPTH_TEST)
    glDepthFunc(GL_LEQUAL)
    glShadeModel(GL_SMOOTH)

    # Enable blending for text transparency (important for HUD visibility)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

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
    glNormal3f(0,0,1)
    glVertex3f( s,  s,  s); glVertex3f(-s,  s,  s)
    glVertex3f(-s, -s,  s); glVertex3f( s, -s,  s)
    # back
    glNormal3f(0,0,-1)
    glVertex3f( s, -s, -s); glVertex3f(-s, -s, -s)
    glVertex3f(-s,  s, -s); glVertex3f( s,  s, -s)
    # top
    glNormal3f(0,1,0)
    glVertex3f( s,  s, -s); glVertex3f(-s,  s, -s)
    glVertex3f(-s,  s,  s); glVertex3f( s,  s,  s)
    # bottom
    glNormal3f(0,-1,0)
    glVertex3f( s, -s,  s); glVertex3f(-s, -s,  s)
    glVertex3f(-s, -s, -s); glVertex3f( s, -s, -s)
    # left
    glNormal3f(-1,0,0)
    glVertex3f(-s,  s,  s); glVertex3f(-s,  s, -s)
    glVertex3f(-s, -s, -s); glVertex3f(-s, -s,  s)
    # right
    glNormal3f(1,0,0)
    glVertex3f( s,  s, -s); glVertex3f( s,  s,  s)
    glVertex3f( s, -s,  s); glVertex3f( s, -s, -s)
    glEnd()

def draw_ground():
    glColor3f(0.12, 0.12, 0.12)
    glBegin(GL_QUADS)
    width, depth, y = 20.0, 120.0, GROUND_Y
    glVertex3f(-width, y, -depth)
    glVertex3f(width, y, -depth)
    glVertex3f(width, y, 20.0)
    glVertex3f(-width, y, 20.0)
    glEnd()

    # center road line
    glColor3f(0.9, 0.85, 0.2)
    glLineWidth(4.0)
    glBegin(GL_LINES)
    glVertex3f(0, y + 0.01, -depth)
    glVertex3f(0, y + 0.01, 20.0)
    glEnd()

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

    def draw(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glColor3f(*self.color)
        draw_cube(self.size)
        glPopMatrix()

# ---------- Collision ----------
def check_collision(player_x, obstacle):
    dx = abs(player_x - obstacle.x)
    dz = abs(PLAYER_Z - obstacle.z)
    collide_x = dx <= (PLAYER_HALF_WIDTH + obstacle.size / 2.0)
    collide_z = dz <= (PLAYER_HALF_DEPTH + obstacle.size / 2.0)
    return collide_x and collide_z

# ---------- Main game ----------
def main():
    pg.init()
    pg.font.init()
    screen = pg.display.set_mode((WIN_W, WIN_H), DOUBLEBUF | OPENGL)
    pg.display.set_caption("Car Dodge 3D Game")
    clock = pg.time.Clock()
    font = pg.font.Font(None, 48)  # larger font for big GAME OVER
    small_font = pg.font.Font(None, 30)

    init_gl()
    set_perspective()

    player_x = 0.0
    lives = MAX_LIVES
    score = 0
    obstacles = []
    last_spawn = time.time()
    obstacle_speed = OBSTACLE_SPEED_START
    running = True
    game_over = False

    while running:
        dt = clock.tick(60) / 1000.0

        # Input events
        for event in pg.event.get():
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False

            # Restart logic (press R when game_over)
            if game_over and event.type == KEYDOWN and event.key == K_r:
                player_x = 0.0
                lives = MAX_LIVES
                score = 0
                obstacles.clear()
                last_spawn = time.time()
                obstacle_speed = OBSTACLE_SPEED_START
                game_over = False

        # Gameplay updates
        if not game_over:
            keys = pg.key.get_pressed()
            move = 0.0
            if keys[K_LEFT] or keys[K_a]:
                move -= 1.0
            if keys[K_RIGHT] or keys[K_d]:
                move += 1.0

            player_x += move * PLAYER_SPEED * dt
            player_x = max(-8.0 + PLAYER_HALF_WIDTH, min(8.0 - PLAYER_HALF_WIDTH, player_x))

            now = time.time()
            if now - last_spawn > SPAWN_INTERVAL:
                last_spawn = now
                x = random.uniform(-8.0 + OBSTACLE_SIZE, 8.0 - OBSTACLE_SIZE)
                y = GROUND_Y + OBSTACLE_SIZE / 2.0
                z = OBSTACLE_SPAWN_Z
                color = (
                    random.random() * 0.7 + 0.3,
                    random.random() * 0.7 + 0.3,
                    random.random() * 0.7 + 0.3
                )
                obstacles.append(Obstacle(x, y, z, OBSTACLE_SIZE, color))

            dz = obstacle_speed * dt
            obstacle_speed += OBSTACLE_SPEED_INC * dt

            remove_list = []
            for ob in obstacles:
                ob.update(dz)

                if check_collision(player_x, ob):
                    lives -= 1
                    remove_list.append(ob)
                    if lives <= 0:
                        game_over = True

                elif ob.z > OBSTACLE_END_Z:
                    score += 10
                    remove_list.append(ob)

            for r in remove_list:
                if r in obstacles:
                    obstacles.remove(r)

        # ---------- Rendering ----------
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # 3D scene
        glPushMatrix()
        draw_ground()

        for ob in obstacles:
            ob.draw()

        # Player car
        glPushMatrix()
        glTranslatef(player_x, PLAYER_Y, PLAYER_Z)
        glScalef(PLAYER_HALF_WIDTH * 2.0, 0.6, PLAYER_HALF_DEPTH * 2.0)
        glColor3f(0.1, 0.6, 0.9)
        draw_cube(1.0)
        glPopMatrix()

        glPopMatrix()

        # ---------- HUD (2D on top of 3D) ----------
        # Ensure HUD renders on top: disable depth test & prevent depth writes, enable blending
        glDisable(GL_DEPTH_TEST)
        glDepthMask(GL_FALSE)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Score and lives (small)
        score_tex, sw, sh = create_text_texture(small_font, f"Score: {score}", (255, 255, 255))
        lives_tex, lw, lh = create_text_texture(small_font, f"Lives: {lives}", (255,200,80))
        draw_text_ortho(score_tex, sw, sh, 12, 12)
        draw_text_ortho(lives_tex, lw, lh, WIN_W - (lw + 12), 12)

        # GAME OVER big centered (Option A)
        if game_over:
            msg1_tex, mw1, mh1 = create_text_texture(font, "GAME OVER", (255, 40, 40))   # big red
            msg2_tex, mw2, mh2 = create_text_texture(small_font, "Press R to Restart", (255,255,255))  # white

            draw_text_ortho(msg1_tex, mw1, mh1, WIN_W//2 - mw1//2, WIN_H//2 - 50)
            draw_text_ortho(msg2_tex, mw2, mh2, WIN_W//2 - mw2//2, WIN_H//2 + 10)

            # delete game over textures (safe after drawing this frame)
            glDeleteTextures([msg1_tex, msg2_tex])

        # restore depth writes and depth test for 3D
        glDepthMask(GL_TRUE)
        glEnable(GL_DEPTH_TEST)

        # delete small hud textures
        glDeleteTextures([score_tex, lives_tex])

        pg.display.flip()

    pg.quit()


if __name__ == "__main__":
    main()
