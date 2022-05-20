import os
import sys

# os.environ['DISPLAY'] = ":0.0"
# os.environ['KIVY_WINDOW'] = 'egl_rpi'

from kivy.app import App
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from odrive_helpers import digital_read

from pidev.MixPanel import MixPanel
from pidev.kivy.PassCodeScreen import PassCodeScreen
from pidev.kivy.PauseScreen import PauseScreen
from pidev.kivy import DPEAButton
from pidev.kivy import ImageButton

sys.path.append("/home/soft-dev/Documents/dpea-odrive/")
from odrive_helpers import *

MIXPANEL_TOKEN = "x"
MIXPANEL = MixPanel("Project Name", MIXPANEL_TOKEN)

SCREEN_MANAGER = ScreenManager()
MAIN_SCREEN_NAME = 'main'
TRAJ_SCREEN_NAME = 'traj'
GPIO_SCREEN_NAME = 'gpio'
ADMIN_SCREEN_NAME = 'admin'

from odrive_helpers import *
od = find_odrive()
assert od.config.enable_brake_resistor is True, "Check for faulty brake resistor."
# axis0 and axis1 correspond to M0 and M1 on the ODrive
# You can also set the current limit and velocity limit when initializing the axis
ax = ODriveAxis(od.axis0, current_lim=10, vel_lim=10)
#digital_read(od, 2) #od defined after od is defined
# Basic motor tuning, for more precise tuning,
# follow this guide: https://docs.odriverobotics.com/v/latest/control.html#tuning
ax.set_gains()
if not ax.is_calibrated():
    print("calibrating...")
    ax.calibrate_with_current_lim(15)
print("Current Limit: ", ax.get_current_limit())
print("Velocity Limit: ", ax.get_vel_limit())
ax.set_vel(0)
dump_errors(od)
od.clear_errors()
od.axis0.controller.config.enable_overspeed_error = False

class ProjectNameGUI(App):
    """
    Class to handle running the GUI Application
    """

    def build(self):
        """
        Build the application
        :return: Kivy Screen Manager instance
        """
        return SCREEN_MANAGER


Window.clearcolor = (1, 1, 1, 1)  # White


class MainScreen(Screen):
    """
    Class to handle the main screen and its associated touch events
    """
    count = 0

    #self.velocity = root.velocity_slider.value/10

    def velocity_function(self):
        ax.set_vel(self.velocity_slider.value)
        self.velocity_slider.text = str(round(self.velocity_slider.value))
        print('slider activated')

    def acceleration_function(self):
        self.acceleration_slider.text = str(round(self.acceleration_slider.value))
        print('slider activated')

    def switch_to_traj(self):
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = TRAJ_SCREEN_NAME

    def switch_to_gpio(self):
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = GPIO_SCREEN_NAME

    def home_without_endstop(self):
        ax.home_without_endstop(1, .5) # Home with velocity 1 until wall is hit, then offset .5 rotations

    def motor_toggle(self):
        #ax.set_relative_pos(0)
        print(ax.get_vel())
        #dump_errors(od)
        if ax.get_vel() <= 0.2:
            if self.count%2 == 0:
                ax.set_rel_pos_traj(10, self.acceleration_slider.value, 10, self.acceleration_slider.value)
                print('If vel = 0 and count% = 0 : ax.set_rel_pos_traj(-5, .5, 1, .5)')
                self.count += 1
            elif self.count%2 == 1:
                ax.set_rel_pos_traj(-10, self.acceleration_slider.value, 10, self.acceleration_slider.value)
                print('If vel = 0 and count% = 1 : ax.set_rel_pos_traj(5, .5, 1, .5)')
                self.count += 1
            else:
                print("motor_toggle command malfunction")
        else:
            if self.count%2 == 0:
                ax.set_rel_pos_traj(5, self.acceleration_slider.value, self.velocity_slider.value, self.acceleration_slider.value)
                print('If vel = moving and count% = 0 : ax.set_rel_pos_traj(5, .5, var, .5)')
                #ax.set_vel_limit(self.velocity_slider.value)
                #ax.set_relative_pos(-5)
                self.count += 1
            elif self.count%2 == 1:
                ax.set_rel_pos_traj(-5, self.acceleration_slider.value, self.velocity_slider.value, self.acceleration_slider.value)
                print('If vel = moving and count% = 1 : ax.set_rel_pos_traj(-5, .5, var, .5)')
                #ax.set_vel_limit(self.velocity_slider.value)
                #ax.set_relative_pos(5)
                self.count += 1
            else:
                print("motor_toggle command malfunction")


    def admin_action(self):
        """
        Hidden admin button touch event. Transitions to passCodeScreen.
        This method is called from pidev/kivy/PassCodeScreen.kv
        :return: None
        """
        SCREEN_MANAGER.current = 'passCode'


class TrajectoryScreen(Screen):
    """
    Class to handle the trajectory control screen and its associated touch events
    """

    def switch_screen(self):
        SCREEN_MANAGER.transition.direction = "right"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    def submit_trapezoidal_traj(self):
        ax.set_vel_limit(10)
        ax.set_pos_traj(int(self.target_position.text), int(self.acceleration.text), int(self.target_speed.text), int(self.deceleration.text))  # position 5, acceleration 1 turn/s^2, target velocity 10 turns/s, deceleration 1 turns/s^2

class GPIOScreen(Screen):
    """
    Class to handle the GPIO screen and its associated touch/listening events
    """

    #ax.home_with_endstop(self, vel, offset, min_gpio_num):

    def homing_switch(self):
        ax.home_with_endstop(1, 1, 2)

    def switch_screen(self):
        SCREEN_MANAGER.transition.direction = "left"
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME


class AdminScreen(Screen):
    """
    Class to handle the AdminScreen and its functionality
    """

    def __init__(self, **kwargs):
        """
        Load the AdminScreen.kv file. Set the necessary names of the screens for the PassCodeScreen to transition to.
        Lastly super Screen's __init__
        :param kwargs: Normal kivy.uix.screenmanager.Screen attributes
        """
        Builder.load_file('AdminScreen.kv')

        PassCodeScreen.set_admin_events_screen(
            ADMIN_SCREEN_NAME)  # Specify screen name to transition to after correct password
        PassCodeScreen.set_transition_back_screen(
            MAIN_SCREEN_NAME)  # set screen name to transition to if "Back to Game is pressed"

        super(AdminScreen, self).__init__(**kwargs)

    @staticmethod
    def transition_back():
        """
        Transition back to the main screen
        :return:
        """
        SCREEN_MANAGER.current = MAIN_SCREEN_NAME

    @staticmethod
    def shutdown():
        """
        Shutdown the system. This should free all steppers and do any cleanup necessary
        :return: None
        """
        os.system("sudo shutdown now")

    @staticmethod
    def exit_program():
        """
        Quit the program. This should free all steppers and do any cleanup necessary
        :return: None
        """
        quit()


"""
Widget additions
"""

Builder.load_file('main.kv')
SCREEN_MANAGER.add_widget(MainScreen(name=MAIN_SCREEN_NAME))
SCREEN_MANAGER.add_widget(TrajectoryScreen(name=TRAJ_SCREEN_NAME))
SCREEN_MANAGER.add_widget(GPIOScreen(name=GPIO_SCREEN_NAME))
SCREEN_MANAGER.add_widget(PassCodeScreen(name='passCode'))
SCREEN_MANAGER.add_widget(PauseScreen(name='pauseScene'))
SCREEN_MANAGER.add_widget(AdminScreen(name=ADMIN_SCREEN_NAME))

"""
MixPanel
"""


def send_event(event_name):
    """
    Send an event to MixPanel without properties
    :param event_name: Name of the event
    :return: None
    """
    global MIXPANEL

    MIXPANEL.set_event_name(event_name)
    MIXPANEL.send_event()


if __name__ == "__main__":
    # send_event("Project Initialized")
    # Window.fullscreen = 'auto'
    ProjectNameGUI().run()
