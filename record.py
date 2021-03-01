import picamera
import time
from button import Button
from led import Led
import RPi.GPIO as GPIO

class CameraRecorder(object):
    def __init__(self, camera):
        self._camera = camera
        self._is_recording = False

    def toggle_record(self, pin):
        if self._is_recording:
            print("stop recording...")
            self._camera.stop_recording()
            self._is_recording = False
        else:
            print("start recording...")
            recording_file_name = "recording_{}.h264".format(time.strftime("%Y%m%d-%H%M%S"))
            self._camera.start_recording(recording_file_name, quality=10, format='h264')
            self._is_recording = True

    @property
    def is_recording(self):
        return self._is_recording


def main():
    button_pin = 8
    led_pin = 10
    button = Button(button_pin)
    led = Led(led_pin)

    with picamera.PiCamera(resolution='1280x960', framerate=30) as camera:
        recorder = CameraRecorder(camera)
        button.add_pressed_cb(recorder.toggle_record)
        while(True):
            if recorder.is_recording:
                camera.wait_recording(1)
                led.toggle()
            else:
                led.on()
                time.sleep(1)

if __name__ == "__main__":
    main()
