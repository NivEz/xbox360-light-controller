import pygame
import broadlink.exceptions
from time import time, sleep
import asyncio

import xbox360_controller
from bulb import initialize_connection
from colors import lamp_colors


class LightController:
    max_bulb_connection_retries = 3
    bulb_retry_timeout = 10

    def __init__(self, bulb_ip, ssid, wifi_pass):
        self.bulb_ip = bulb_ip
        self.ssid = ssid
        self.wifi_pass = wifi_pass
        self.bulb = None
        self.is_bulb_connected = False
        self.my_controller = None
        self.last_timestamp = time()
        self.currently_held_button = None
        self.currently_held_button_press_timestamp = None
        self.wheel_color_loop = None
        self.is_wheel_color_mode = False
        self.additive_y = 0
        self.is_brightness_loop_running = False
        self.bulb_pwr = None
        self.is_colors_scene_loop_running = False
        self.connect_to_bulb()

    async def start(self):
        pygame.init()

        while self.is_bulb_connected:
            await asyncio.sleep(0.1)
            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED:
                    self.my_controller = xbox360_controller.Controller(device_id=event.device_index)
                    print("Detected joystick:", self.my_controller.joystick.get_name(), self.my_controller.joystick.get_guid())
                if event.type == pygame.JOYDEVICEREMOVED:
                    print("Joystick disconnected")
                else:
                    try:
                        await self.handle_joystick_controls(event)
                    except broadlink.exceptions.NetworkTimeoutError:
                        print("---------------")
                        print("Bulb connection error, using retry mechanism...")
                        self.connect_to_bulb()

    async def handle_joystick_controls(self, event):
        if event.type == pygame.JOYBUTTONUP:
            if event.button == self.currently_held_button:
                # use timestamp difference to distinguish between holding and a normal press
                self.currently_held_button = None
                if self.is_wheel_color_mode:
                    print("Stopping wheel color loop")
                    self.wheel_color_loop.cancel()
                    self.is_wheel_color_mode = False
                    return
            bulb_pwr = self.bulb.get_state()['pwr']
            self.bulb_pwr = bulb_pwr
            if event.button == xbox360_controller.START:
                new_pwr = not bulb_pwr
                self.bulb_pwr = new_pwr
                self.bulb.set_state(pwr=int(new_pwr))
            if not self.bulb_pwr:
                return
            match event.button:
                case xbox360_controller.BACK:
                    bulb_color_mode = self.bulb.get_state()['bulb_colormode']
                    self.bulb.set_state(bulb_colormode=int(not bulb_color_mode), brightness=50)
                case xbox360_controller.A:
                    self.bulb.set_state(red=0, green=100, blue=0)
                case xbox360_controller.B:
                    self.bulb.set_state(red=100, green=0, blue=0)
                case xbox360_controller.X:
                    self.bulb.set_state(red=0, green=0, blue=100)
                case xbox360_controller.Y:
                    self.bulb.set_state(red=255, green=140, blue=0)
                case xbox360_controller.LEFT_BUMP:
                    bulb_state = self.bulb.get_state()
                    state = " - ".join([f"{k}: {bulb_state.get(k)}" for k in ["pwr", "red", "green", "blue", "brightness"]])
                    print(state)
                case xbox360_controller.RIGHT_BUMP:
                    if self.is_colors_scene_loop_running:
                        print("Stopping colors scene loop")
                        self.is_colors_scene_loop_running = False
                    else:
                        self.is_colors_scene_loop_running = True
                        asyncio.create_task(self.colors_scene_loop())
        elif event.type == pygame.JOYBUTTONDOWN:
            if event.button in [xbox360_controller.B, xbox360_controller.A, xbox360_controller.X]:
                self.currently_held_button = event.button
                self.currently_held_button_press_timestamp = time()
        elif event.type == pygame.JOYAXISMOTION:
            if not self.bulb_pwr:
                return
            now = time()
            # sort of throttling to prevent too much tasks / calculations on short time
            if (now - self.last_timestamp) < 0.05:
                return
            if event.axis in (xbox360_controller.LEFT_STICK_X, xbox360_controller.LEFT_STICK_Y):
                self.handle_left_joystick(now)
            elif event.axis in (xbox360_controller.RIGHT_STICK_X, xbox360_controller.RIGHT_STICK_Y):
                self.handle_right_joystick()
        elif event.type == pygame.JOYHATMOTION:
            up, right, down, left = self.my_controller.get_pad()
            if up:
                self.bulb.set_state(red=255, green=0, blue=255)
            if right:
                self.bulb.set_state(red=75, green=0, blue=130)
            if down:
                self.bulb.set_state(red=210, green=105, blue=30)
            if left:
                self.bulb.set_state(red=0, green=255, blue=255)

    def handle_left_joystick(self, now):
        if self.currently_held_button is None:
            return
        # check if the button is held enough time (0.2s) and then execute the wheel color task loop
        if now - self.currently_held_button_press_timestamp > 0.2 and not self.is_wheel_color_mode:
            self.wheel_color_loop = asyncio.create_task(self.create_wheel_color_loop())
            self.is_wheel_color_mode = True
        if not self.is_wheel_color_mode:
            return
        # only if got here calculate the new value
        _, left_y = self.my_controller.get_left_stick()
        self.additive_y = (-1 * left_y) * 15
        self.last_timestamp = now

    def handle_right_joystick(self):
        if not self.is_brightness_loop_running:
            asyncio.create_task(self.create_brightness_loop())
            self.is_brightness_loop_running = True
        _, right_y = self.my_controller.get_right_stick()
        self.additive_y = (-1 * right_y) * 10

    async def create_wheel_color_loop(self):
        print("Starting wheel color loop")
        while True:
            await asyncio.sleep(0.1)
            bulb_state = self.bulb.get_state()
            if self.currently_held_button == xbox360_controller.B:
                red = int(bulb_state['red'] + self.additive_y)
                if red > 255:
                    red = 255
                if red < 1:
                    red = 1
                self.bulb.set_state(red=red)
            if self.currently_held_button == xbox360_controller.A:
                green = int(bulb_state['green'] + self.additive_y)
                if green > 255:
                    green = 255
                if green < 1:
                    green = 1
                self.bulb.set_state(green=green)
            if self.currently_held_button == xbox360_controller.X:
                blue = int(bulb_state['blue'] + self.additive_y)
                if blue > 255:
                    blue = 255
                if blue < 1:
                    blue = 1
                self.bulb.set_state(blue=blue)

    async def create_brightness_loop(self):
        print("Starting brightness loop")
        executed_at = time()
        # loop for 15 seconds
        while time() - executed_at < 15 and self.bulb_pwr:
            await asyncio.sleep(0.1)
            brightness = int(self.bulb.get_state()['brightness'] + self.additive_y)
            if brightness > 100:
                brightness = 100
            if brightness < 1:
                brightness = 1
            self.bulb.set_state(brightness=brightness)
        self.is_brightness_loop_running = False
        print("Stopped running brightness loop")

    async def colors_scene_loop(self):
        print("Starting colors scene loop")
        while self.is_colors_scene_loop_running:
            for color in lamp_colors:
                if not self.is_colors_scene_loop_running:
                    break
                self.bulb.set_state(red=color[0], green=color[1], blue=color[2])
                await asyncio.sleep(2.5)

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
                self.bulb_pwr = self.bulb.get_state()['pwr']
                print("---------------")
                print("Smart bulb detected, model:", self.bulb.type)
                return None
            except Exception:
                max_retries -= 1
                print(f"Attempt number {self.max_bulb_connection_retries - max_retries} - error above ^^")

        self.is_bulb_connected = False
        print("---------------")
        print(f"Could not connect to smart bulb after {self.max_bulb_connection_retries} retries, finishing program...")