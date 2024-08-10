import pygame
import broadlink.exceptions
from time import sleep

from bulb import initialize_connection
import xbox360_controller as my_controller


class LightController:
    max_bulb_connection_retries = 3
    bulb_retry_timeout = 10

    def __init__(self, bulb_ip, ssid, wifi_pass):
        self.bulb_ip = bulb_ip
        self.ssid = ssid
        self.wifi_pass = wifi_pass
        self.bulb = None
        self.is_bulb_connected = False
        self.connect_to_bulb()

    def start(self):
        pygame.init()
        clock = pygame.time.Clock()
        while self.is_bulb_connected:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED:
                    joystick = pygame.joystick.Joystick(event.device_index)
                    print("Detected joystick:", joystick.get_name(), joystick.get_guid())
                    joystick.init()
                if event.type == pygame.JOYDEVICEREMOVED:
                    print("Joystick disconnected")
                else:
                    try:
                        self.handle_joystick_controls(event)
                    except broadlink.exceptions.NetworkTimeoutError:
                        print("---------------")
                        print("Bulb connection error, using retry mechanism...")
                        self.connect_to_bulb()

    def handle_joystick_controls(self, event):
        if event.type == pygame.JOYBUTTONDOWN:
            if event.button == my_controller.START:
                bulb_pwr = self.bulb.get_state()['pwr']
                self.bulb.set_state(pwr=int(not bulb_pwr))
            if event.button == my_controller.A:
                self.bulb.set_state(red=0, green=100, blue=0)
            if event.button == my_controller.B:
                self.bulb.set_state(red=100, green=0, blue=0)
            if event.button == my_controller.X:
                self.bulb.set_state(red=0, green=0, blue=100)
            if event.button == my_controller.Y:
                self.bulb.set_state(red=255, green=140, blue=0)
            if event.button == my_controller.BACK:
                bulb_color_mode = self.bulb.get_state()['bulb_colormode']
                self.bulb.set_state(bulb_colormode=int(not bulb_color_mode), brightness=50)

    def connect_to_bulb(self):
        max_retries = self.max_bulb_connection_retries
        while max_retries > 0:
            if max_retries != self.max_bulb_connection_retries:
                print("---------------")
                print(f"Trying to re-connect to smart bulb in {self.bulb_retry_timeout} seconds...")
                sleep(self.bulb_retry_timeout)
            try:
                self.bulb = initialize_connection(self.bulb_ip, self.ssid, self.wifi_pass)
                self.is_bulb_connected = True
                print("---------------")
                print("Smart bulb detected, model:", self.bulb.type)
                return None
            except Exception:
                max_retries -= 1
                print(f"Attempt number {self.max_bulb_connection_retries - max_retries} - error above ^^")

        self.is_bulb_connected = False
        print("---------------")
        print(f"Could not connect to smart bulb after {self.max_bulb_connection_retries} retries, finishing program...")
