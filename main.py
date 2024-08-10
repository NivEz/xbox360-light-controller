import os
from dotenv import load_dotenv
from LightController import LightController


def main():
    load_dotenv()
    bulb_ip = os.getenv("BULB_IP")
    ssid = os.getenv("SSID")
    wifi_pass = os.getenv("WIFI_PASS")

    light_controller = LightController(bulb_ip, ssid, wifi_pass)
    light_controller.start()


if __name__ == '__main__':
    main()
