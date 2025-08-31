from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import sys
import random
import time
from copy import deepcopy

#window
WIN_W, WIN_H = 1000, 800
fovY = 60
camera_mode = 1

# default values
LANE_LEN = 1800.0
LANE_W   = 300.0
FOUL_LINE_Y = -700.0
PIN_DECK_Y  = 700.0
BALL_START_Y = FOUL_LINE_Y - 50.0
BALL_RADIUS = 12.0
PIN_RADIUS  = 7.0
PIN_HEIGHT  = 35.0

# aim , charge , roll , settle , between_throws , replay(modes of the ball)
state = "aim"  

# HUD (kept to match your helper; not used for logic)
lives = 1


#farhan
def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    
    #the texts above the screen
    glColor3f(1,1,1)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WIN_W, 0, WIN_H)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    

#farhan
def arrange_pins():
    # making of the pins
    global pins
    pins = []
    row_spacing = 28.0
    col_spacing = 20.0
    rows = [(0, 0) , (-col_spacing, row_spacing),   (col_spacing, row_spacing) , (-2*col_spacing, 2*row_spacing), (0,2*row_spacing), (2*col_spacing, 2*row_spacing) , (-3*col_spacing, 3*row_spacing), (-col_spacing,3*row_spacing) , (col_spacing,3*row_spacing), (3*col_spacing,3*row_spacing)]
    
    for dx, dy in rows:
        pins.append({"x": dx , "y" : PIN_DECK_Y + dy , "fallen" : False , "fall_t" : 0.0 , "fall_angle" : 0.0})


def count_standing():
    return sum(1 for p in pins if not p["fallen"])
#farhan
def knock_pin(p):
    #making the state fallen so pins stay fallen
    if not p["fallen"]:
        p["fallen"] = True
        p["fall_t"] = time.time()
#farhan
def score_from_throws(throws):
    # score for strike and spare(pins fallen)
    score = 0
    idx = 0
    for frame in range(10):
        if idx >= len(throws): break
        if throws[idx] == 10:
            bonus = 0
            if idx+1 < len(throws): 
                bonus += throws[idx+1]
            else :
                continue
            if idx+2 < len(throws): 
                bonus += throws[idx+2]
            else :
                continue
            score += 10 + bonus
            idx += 1
        else:
            frame_sum = throws[idx]
            if idx+1 < len(throws): frame_sum += throws[idx+1]
            if frame_sum == 10:
                bonus = throws[idx+2] if idx+2 < len(throws) else 0
                score += 10 + bonus
            else:
                score += frame_sum
            idx += 2
    return score


#all members
def keyboard(key, x, y):
    global spin, camera_mode, state
    key = key.lower()

    #camera angles
    if key == b'1' :
        camera_mode = 1
    if key == b'2' :
        camera_mode = 2
    if key == b'3' :
        camera_mode = 3


#farhan
def collide_ball_with_pins():
    #measuring the distance of ball and pins(collision)
    hit_any = False
    for p in pins:
        if p["fallen"]:
            continue
        dx = ball_x - p["x"]
        dy = ball_y - p["y"]
        dist = math.hypot(dx, dy)
        if dist < (BALL_RADIUS + PIN_RADIUS + 1.5):
            knock_pin(p)
            hit_any = True
            if dist > 0.001:
                nx = dx / dist
                ny = dy / dist
                ball_vx += nx * 20.0
    return hit_any



#farhan
def animate_pins():
    #fall animation
    now = time.time()
    for p in pins:
        if p["fallen"]:
            t = now - p["fall_t"]
            p["fall_angle"] = min(90.0, t * 180.0)  # tip to 90 degrees


#farhan
def draw_lane():
    # floor
    glColor3f(0.75, 0.55, 0.25)
    glBegin(GL_QUADS)
    glVertex3f(-LANE_W*0.5, FOUL_LINE_Y-100.0, 0)
    glVertex3f(+LANE_W*0.5, FOUL_LINE_Y-100.0, 0)
    glVertex3f(+LANE_W*0.5, PIN_DECK_Y+200.0, 0)
    glVertex3f(-LANE_W*0.5, PIN_DECK_Y+200.0, 0)
    glEnd()

    # gutters (walls)
    glColor3f(0.5, 0.5, 0.5)
    
    # left wall
    glBegin(GL_QUADS)
    glVertex3f(-LANE_W*0.5-8, FOUL_LINE_Y-100.0, 0)
    glVertex3f(-LANE_W*0.5-8, PIN_DECK_Y+200.0, 0)
    glVertex3f(-LANE_W*0.5-8, PIN_DECK_Y+200.0, 60)
    glVertex3f(-LANE_W*0.5-8, FOUL_LINE_Y-100.0, 60)
    glEnd()
    
    # right wall
    glBegin(GL_QUADS)
    glVertex3f(+LANE_W*0.5+8, FOUL_LINE_Y-100.0, 0)
    glVertex3f(+LANE_W*0.5+8, PIN_DECK_Y+200.0, 0)
    glVertex3f(+LANE_W*0.5+8, PIN_DECK_Y+200.0, 60)
    glVertex3f(+LANE_W*0.5+8, FOUL_LINE_Y-100.0, 60)
    glEnd()

    # foul line
    glColor3f(0,0,0)
    glBegin(GL_QUADS)
    glVertex3f(-LANE_W*0.5, FOUL_LINE_Y, 0.1)
    glVertex3f(+LANE_W*0.5, FOUL_LINE_Y, 0.1)
    glVertex3f(+LANE_W*0.5, FOUL_LINE_Y+2, 0.1)
    glVertex3f(-LANE_W*0.5, FOUL_LINE_Y+2, 0.1)
    glEnd()


#farhan
def draw_pin(px, py, fallen=False, fall_angle=0.0):
    glPushMatrix()
    glTranslatef(px, py, 0)
    if fallen:
        glRotatef(fall_angle, 0,1,0)
        glTranslatef(0, 0, -PIN_RADIUS*0.2)

    glColor3f(1,1,1)
    body = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, PIN_HEIGHT*0.2)
    gluCylinder(body, PIN_RADIUS, PIN_RADIUS*0.7, PIN_HEIGHT*0.6, 16, 2)
    glPopMatrix()
    # neck
    neck = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, PIN_HEIGHT*0.8)
    gluCylinder(neck, PIN_RADIUS*0.6, PIN_RADIUS*0.4, PIN_HEIGHT*0.15, 16, 2)
    glPopMatrix()
    # head
    head = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, PIN_HEIGHT*0.95)
    gluSphere(head, PIN_RADIUS*0.5, 12, 10)
    glPopMatrix()
    # red stripe
    glColor3f(1,0,0)
    stripe = gluNewQuadric()
    glPushMatrix()
    glTranslatef(0, 0, PIN_HEIGHT*0.65)
    gluCylinder(stripe, PIN_RADIUS*0.8, PIN_RADIUS*0.8, 5.0, 16, 1)
    glPopMatrix()
    glPopMatrix()
    
    
#farhan
def draw_pins(pins_arr=None):
    arr = pins if pins_arr is None else pins_arr
    for p in arr:
        draw_pin(p["x"], p["y"], p.get("fallen", False), p.get("fall_angle", 0.0))


def init_gl():
    glClearColor(0.05, 0.08, 0.12, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"3D Bowling (GLUT + GLU) - Multiplayer + Angle + Replay")
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special)

    glutMainLoop()

if __name__ == "__main__":
    main()