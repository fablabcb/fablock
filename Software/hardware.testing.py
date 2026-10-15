from enum import Enum, auto

import config

sim_motor = False
sim_motor_dir = -1
sim_position = 1
sim_timer_unlocked = 0


def do_sim_motor():
    global sim_motor, sim_motor_dir, sim_position, sim_timer_unlocked

    if sim_motor:
        sim_position += sim_motor_dir
        print(f"motor turning {sim_motor_dir:+}, now at {sim_position}")
    else:
        print("motor is still")


def endstop_unlocked_reached():
    global sim_motor, sim_motor_dir, sim_position, sim_timer_unlocked
    do_sim_motor()
    return sim_position >= 100


def endstop_locked_reached():
    global sim_motor, sim_motor_dir, sim_position, sim_timer_unlocked
    do_sim_motor()
    return sim_position <= 0


def window_open():
    global sim_motor, sim_motor_dir, sim_position, sim_timer_unlocked
    if endstop_unlocked_reached():
        if sim_timer_unlocked == 3:
            sim_timer_unlocked = 0
            print("window open")
            return True
        else:
            sim_timer_unlocked += 1
    print("window closed")
    return False


def setup():
    pass


# enable Polulu driver (pass false, to disable)
def enable_motor(state: bool = True):
    global sim_motor, sim_motor_dir, sim_position, sim_timer_unlocked

    print("enable motor", state)
    sim_motor = state
    do_sim_motor()


def set_direction(direction: bool):
    global sim_motor, sim_motor_dir, sim_position, sim_timer_unlocked
    sim_motor_dir = -1 if direction == config.CLOSING else +1
    print("set direction", sim_motor_dir)


class LedStatus(Enum):
    LOCKED = auto()
    MOVING = auto()
    OPEN = auto()
    OFF = auto()


def show_status(status: LedStatus):
    print(f"led showing {status}")


def stop():
    enable_motor(False)
    show_status(LedStatus.OFF)
