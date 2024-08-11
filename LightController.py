import pygame
import broadlink.exceptions
from time import time, sleep
import math

import xbox360_controller
from bulb import initialize_connection


class LightController:
    max_bulb_connection_retries = 3
    bulb_retry_timeout = 10
    my_controller = None
    last_timestamp = time()

    def __init__(self, bulb_ip, ssid, wifi_pass):
        self.bulb_ip = bulb_ip
        self.ssid = ssid
        self.wifi_pass = wifi_pass
        self.bulb = None
        self.is_bulb_connected = False
        self.connect_to_bulb()

    def start(self):
        pygame.init()

        while self.is_bulb_connected:
            sleep(0.1)
            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED:
                    self.my_controller = xbox360_controller.Controller(device_id=event.device_index)
                    print("Detected joystick:", self.my_controller.joystick.get_name(), self.my_controller.joystick.get_guid())
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
        if event.type == pygame.JOYBUTTONUP:
            if event.button == xbox360_controller.START:
                bulb_pwr = self.bulb.get_state()['pwr']
                self.bulb.set_state(pwr=int(not bulb_pwr))
            if event.button == xbox360_controller.BACK:
                bulb_color_mode = self.bulb.get_state()['bulb_colormode']
                self.bulb.set_state(bulb_colormode=int(not bulb_color_mode), brightness=50)
            if event.button == xbox360_controller.A:
                self.bulb.set_state(red=0, green=100, blue=0)
            if event.button == xbox360_controller.B:
                self.bulb.set_state(red=100, green=0, blue=0)
            if event.button == xbox360_controller.X:
                self.bulb.set_state(red=0, green=0, blue=100)
            if event.button == xbox360_controller.Y:
                self.bulb.set_state(red=255, green=140, blue=0)
        elif event.type == pygame.JOYAXISMOTION:
            now = time()
            # sort of throttling to prevent from the bulb to be flooded
            if (now - self.last_timestamp) < 0.25:
                return
            left_x, left_y = self.my_controller.get_left_stick()
            red = (left_x + 1) * 127.5
            green = (left_y + 1) * 127.5
            # the distance between the center of the joystick to the current point will be the blue
            blue = math.sqrt((left_x ** 2) + (left_y ** 2)) * 255
            if blue > 255:
                blue = 255
            self.bulb.set_state(red=red, green=green, blue=blue)
            self.last_timestamp = now
            print(red, green, blue)

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
