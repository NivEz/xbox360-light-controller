# Xbox 360 Light Controller

This project is a Python-based application designed to control a smart bulb using an Xbox 360 controller. The application allows users to adjust the bulb's color and brightness through joystick movements and button presses.

## Features

- **Color Control**: Adjust the red, green, and blue components of the bulb's color using the Xbox 360 controller buttons, pad and left joystick.
- **Brightness Control**: Modify the brightness of the bulb using the right joystick.
- **Automatic Reconnection**: Attempts to reconnect to the smart bulb if the connection is lost.
- **Color Scene Loop**: Cycles through predefined colors in a loop.

## Buttons Mapping
- **start**: Turn the bulb on/off.
- **back**: Turn the color mode on/off.
- **X**: Blue.
- **A**: Green.
- **B**: Red.
- **Y**: Gold.
- **Left Joystick**: Adjust the red/green/blue colors by long-pressing (holding) X/A/B.
- **Right Joystick**: Adjust the brightness of the bulb.
- **UP PAD**: Magenta.
- **RIGHT PAD**: Indigo / purple.
- **DOWN PAD**: Chocolate / light pink.
- **LEFT PAD**: Cyan / Aqua.
- **LB**: Prints the state of the bulb.
- **RB**: Turning on/off the scene mode which cycles through predefined colors.

## Requirements

- Python 3.10+
- `pip` for package management
- `dotenv` for environment variable management

## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Create a virtual environment:
    ```sh
    python -m venv venv
    source venv/bin/activate
    ```
   
3. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```

4. Create a `.env` file with the following variables:
    ```env
    BULB_IP=<your-bulb-ip>
    SSID=<your-wifi-ssid>
    WIFI_PASS=<your-wifi-password>
    ```

## Usage

Run the application using:
```sh
python main.py