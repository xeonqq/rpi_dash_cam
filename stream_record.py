import subprocess
import time
from button import Button
import os

process = None

def switch_to_record_mode(channel):
    process.terminate()
    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
    bashCommand = "python3 record.py"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    print(output)
    print(error)

def main():
    button_pin = 8
    button = Button(button_pin)

    bashCommand = "python3 camera_server.py"
    process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    output, error = process.communicate()
    button.add_pressed_cb(switch_to_record_mode)
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
