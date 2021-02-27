import picamera
import time
import RPi.GPIO as GPIO

# will use pin 8
class Button(object):
    def __init__(self, pin):
        self._pin = pin
        GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
        GPIO.setup(self._pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    def is_pressed(self):
        return GPIO.input(self._pin) == GPIO.LOW

    def add_pressed_cb(self, callback):
        GPIO.add_event_detect(self._pin, GPIO.FALLING, callback=callback, bouncetime=300)

# will use pin 10
class Led(object):
    def __init__(self, pin):
        self._pin = pin
        GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
        GPIO.setup(self._pin, GPIO.OUT, initial=GPIO.LOW)
        self._state = GPIO.LOW

    def toggle(self):
        self._state = GPIO.LOW if self._state == GPIO.HIGH else GPIO.HIGH
        GPIO.output(self._pin, self._state)

    def on(self):
        GPIO.output(self._pin, GPIO.HIGH)
        self._state = GPIO.HIGH

    def off(self):
        GPIO.output(self._pin, GPIO.LOW)
        self._state = GPIO.LOW


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
            self._camera.start_recording(recording_file_name)
            self._is_recording = True

    @property
    def is_recording(self):
        return self._is_recording

def main():
    button_pin = 8
    led_pin = 10
    button = Button(button_pin)
    led = Led(led_pin)

    with picamera.PiCamera(resolution='1280x720', framerate=30) as camera:
        camera.rotation = 180
        recorder = CameraRecorder(camera)
        button.add_pressed_cb(recorder.toggle_record)
        while(True):
            time.sleep(1)
            if recorder.is_recording:
                led.toggle()
            else:
                led.off()

if __name__ == "__main__":
    main()
