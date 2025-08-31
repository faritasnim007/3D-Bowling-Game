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

# Two players
player_count = 2
players = []
active_player = 0  # index of current player

#khadiza
def init_players():
    #making of players
    global players, active_player
    players = []
    for i in range(player_count):
        players.append({"name": f"Player : {i+1}" , "frame_idx" : 1 , "throw_in_frame" : 1 , "pins_down_this_frame" : 0 , "throws_list" : [] , "score_total" : 0})
    
    active_player = 0

# HUD (kept to match your helper; not used for logic)
lives = 1

#for reply features
current_throw_record = []
last_replay = []
replay_active = False
replay_index = 0
vis_ball_x = 0.0
vis_ball_y = 0.0

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
    
#khadiza
def setup_camera():
    #camera angle setup
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(fovY, WIN_W/float(WIN_H), 0.1, 5000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    global camera_mode, ball_x, ball_y, vis_ball_x, vis_ball_y, replay_active

    if replay_active :
        bx = vis_ball_x 
        by = vis_ball_y 
    else :
        bx = ball_x
        by = ball_y
        
    if replay_active :
        eye = (bx, by - 320.0, 180.0)
        at  = (bx, by + 240.0, 40.0)
        up  = (0 , 0 , 1)
    elif camera_mode == 1:
        # behind ball
        eye = (ball_x , ball_y - 250.0 , 120.0)
        at  = (ball_x , ball_y + 200.0 , 40.0)
        up  = (0 , 0 , 1)
    elif camera_mode == 2:
        # top down
        eye = (0.0 , -550.0 , 500.0)
        at  = (0.0 , -100.0 , 0.0)
        up  = (0 , 1 , 0)
    else:
        # side
        eye = (-(LANE_W + 50.0) , -150.0 , 200.0)
        at  = (0.0 , 200.0 , 0.0)
        up  = (0 , 0 , 1)
        
        
    gluLookAt(*eye, *at, *up)
    

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

#khadiza
def reset_frame(full_reset = True) :
    # resetting the frame and the pins
    if full_reset:
        arrange_pins()
    else:
        pass
    reset_ball()

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

    #reply the last throw
    if key == b'p':
        toggle_replay()

    #restart game
    if key == b'r':
        full_game_reset()

#khadiza
def update_charge():
    #charging the ball power from 0-100-0
    global power_value, power_dir
    speed = 2.0
    power_value += power_dir * speed * DT
    if power_value > 1.0:
        power_value = 1.0
        power_dir = -1
    if power_value < 0.0:
        power_value = 0.0
        power_dir = +1
        
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

#khadiza
def end_throw_and_advance():
    #next round or play
    global state, last_replay, replay_active, replay_index, active_player

    pl = players[active_player]

    if len(current_throw_record) > 0:
        last = []
        for fr in current_throw_record:
            last.append({"ball_x": fr["ball_x"],"ball_y": fr["ball_y"],"pins": deepcopy(fr["pins"])})
            
        set_last_replay(last)

    standing = count_standing()
    knocked_now = 10 - standing - pl["pins_down_this_frame"]
    if knocked_now < 0: knocked_now = 0
    pl["pins_down_this_frame"] += knocked_now
    pl["throws_list"].append(knocked_now)
    update_score(active_player)


    def frame_over_and_switch():
        #only call when a player's frame is over and reset pins and switch to next player
        reset_frame(full_reset=True)
        pl["throw_in_frame"] = 1
        pl["pins_down_this_frame"] = 0
        switch_to_next_player()

    if pl["frame_idx"] < 10:
        if pl["throw_in_frame"] == 1:
            if pl["pins_down_this_frame"] == 10:
                # strike -> frame over
                pl["frame_idx"] += 1
                frame_over_and_switch()
            else:
                # go to throw 2 with remaining pins
                pl["throw_in_frame"] = 2
                state = "between_throws"
        else:
            # second throw ends frame
            pl["frame_idx"] += 1
            frame_over_and_switch()
            
    else:
        # 10th frame handling
        tenth_throws = get_10th_frame_throws(active_player)
        if len(tenth_throws) == 1:
            if tenth_throws[0] == 10:
                # strike -> reset pins for next throw
                reset_frame(full_reset=True)
                state = "aim"
                pl["throw_in_frame"] = 2
            else:
                # go to throw 2 with remaining pins
                state = "between_throws"
                pl["throw_in_frame"] = 2
        elif len(tenth_throws) == 2:
            if sum(tenth_throws) >= 10:
                # spare or strike+something -> one bonus ball, fresh pins
                reset_frame(full_reset=True)
                state = "aim"
                pl["throw_in_frame"] = 3
            else:
                # game over (no spare/strike) -> switch player and leave frame 10 complete
                state = "aim"
                reset_frame(full_reset=True)
                frame_over_and_switch()
        else:
            # end of game after 3rd throw -> switch player
            state = "aim"
            reset_frame(full_reset=True)
            frame_over_and_switch()

#khadiza
def switch_to_next_player():
    global active_player
    active_player = (active_player + 1) % player_count

#khadiza
def get_10th_frame_throws(player_idx):
    # derive which throws belong to the 10th from that player's throws_list
    tlist = players[player_idx]["throws_list"]
    frames = []
    i = 0
    while len(frames) < 9 and i < len(tlist):
        if tlist[i] == 10:
            frames.append([10])
            i += 1
        else:
            if i+1 < len(tlist):
                frames.append([tlist[i], tlist[i+1]])
            else:
                frames.append([tlist[i]])
            i += 2
    # Remaining belong to 10th
    return tlist[i:]

#khadiza
def update_score(player_idx):
    players[player_idx]["score_total"] = score_from_throws(players[player_idx]["throws_list"])

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
def draw_ball(x=None, y=None):
    bx = ball_x if x is None else x
    by = ball_y if y is None else y
    glPushMatrix()
    glTranslatef(bx, by, BALL_RADIUS)
    glColor3f(0.4, 0.15, 0.05)
    quad = gluNewQuadric()
    gluSphere(quad, BALL_RADIUS, 20, 16)
    glPopMatrix()
    
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

#farhan
def draw_hud():
    #calling to draw informations
    pl = players[active_player]
    draw_text(10, WIN_H-30, f"Player: {pl['name']}   Frame: {pl['frame_idx']}   Throw: {pl['throw_in_frame']}   Score: {pl['score_total']}")
    draw_text(10, WIN_H-60, f"Spin (A/D): {spin:+.1f}     Angle (W/S): {throw_angle_deg:+.1f}°     Power (SPACE twice): {int(power_value*100)}%")
    draw_text(10, WIN_H-90, "Views: 1=Behind  2=Top  3=Side   Reset: R   Replay: P")
    draw_text(10, WIN_H-120, f"Pins standing: {count_standing()}")

    y = WIN_H - 150
    for i, pp in enumerate(players):
        draw_text(10, y, f"{pp['name']}: Score {pp['score_total']}  Frame {pp['frame_idx']}")
        y -= 24
    if replay_active:
        draw_text(WIN_W-240, WIN_H-30, "REPLAY", GLUT_BITMAP_HELVETICA_18)

#khadiza
def show():
    global vis_ball_x, vis_ball_y
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glViewport(0, 0, WIN_W, WIN_H)

    # Determine visual ball/pins (live vs replay)
    if replay_active and last_replay:
        idx = max(0, min(len(last_replay)-1, replay_index))
        frame = last_replay[idx]
        vis_ball_x = frame["ball_x"]
        vis_ball_y = frame["ball_y"]
    else:
        vis_ball_x = ball_x
        vis_ball_y = ball_y

    setup_camera()
    draw_lane()

    if replay_active and last_replay:
        idx = max(0, min(len(last_replay)-1, replay_index))
        draw_pins(last_replay[idx]["pins"])
        draw_ball(x=vis_ball_x, y=vis_ball_y)
    else:
        draw_pins()
        draw_ball()

    draw_hud()

    glutSwapBuffers()


last_settle_time = 0.0
replay_timer_accum = 0.0

#khadiza
def idle():
    global state, last_settle_time, replay_index, replay_timer_accum

    if replay_active:
        # advance replay at ~60 fps based on DT
        replay_timer_accum += DT
        if last_replay:
            # step one recorded frame per idle tick (can be improved to time-based)
            replay_index += 1
            if replay_index >= len(last_replay):
                stop_replay()
    else:
        if state == "charge":
            update_charge()
        elif state == "roll":
            update_roll()
        elif state == "settle":
            animate_pins()
            # wait briefly so pins can finish falling, then advance
            if last_settle_time == 0.0:
                last_settle_time = time.time()
            if time.time() - last_settle_time > 0.6:
                last_settle_time = 0.0
                end_throw_and_advance()
        elif state == "between_throws":
            # prepare second throw: keep standing pins only
            reset_ball()
            # keep remaining pins; do not full reset
            state = "aim"
        # always animate pins slightly
        animate_pins()

    glutPostRedisplay()

#khadiza
def set_last_replay(frames):
    global last_replay
    last_replay = frames
    
#khadiza
def toggle_replay():
    if not replay_active:
        start_replay()
    else:
        stop_replay()
        
#khadiza
def start_replay():
    global replay_active, replay_index, replay_timer_accum
    if last_replay:
        replay_active = True
        replay_index = 0
        replay_timer_accum = 0.0
        
#khadiza
def stop_replay():
    global replay_active
    replay_active = False


def init_gl():
    glClearColor(0.05, 0.08, 0.12, 1.0)
    glEnable(GL_DEPTH_TEST)
    glShadeModel(GL_SMOOTH)
    
#khadiza
def full_game_reset():
    init_players()
    arrange_pins()

    for i in range(player_count):
        update_score(i)

def main():
    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WIN_W, WIN_H)
    glutInitWindowPosition(50, 50)
    glutCreateWindow(b"3D Bowling (GLUT + GLU) - Multiplayer + Angle + Replay")

    init_gl()
    init_players()
    arrange_pins()

    for i in range(player_count):
        update_score(i)

    glutDisplayFunc(show)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special)
    glutIdleFunc(idle)

    glutMainLoop()

if __name__ == "__main__":
    main()