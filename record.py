import picamera
import time
from button import Button
from led import Led
import RPi.GPIO as GPIO

import threading
import io
import queue
from statemachine import StateMachine, State


class Tape(object):
    MAX_QUEUE_SIZE = 50
    MAX_BUFFER_SIZE = 1 * 1024 * 1024

    def __init__(self):
        self._tape_queue = queue.Queue(Tape.MAX_QUEUE_SIZE)
        self._buffer_size = 0
        self._buffer = io.BytesIO()
        self._thread = None

    def open(self, filename):
        self._filename = filename
        self._thread = threading.Thread(target=self.record)
        self._thread.start()

    def _write_buffer_to_queue(self):
        self._buffer.truncate()
        self._tape_queue.put(self._buffer.getvalue())
        self._buffer.seek(0)
        self._buffer_size = 0

    def write(self, frame):
        #        if not self._thread :
        #           raise IOError("Tape is not open, call open()")
        self._buffer.write(frame)
        self._buffer_size += len(frame)

        if self._buffer_size > Tape.MAX_BUFFER_SIZE:
            self._write_buffer_to_queue()

    def record(self):
        with open(self._filename, "wb") as f:
            for data in iter(self._tape_queue.get, None):
                f.write(data)

    def flush(self):
        if self._buffer_size > 0:
            self._write_buffer_to_queue()

    def close(self):
        self.flush()
        self._tape_queue.put(None)
        self._thread.join()
        self._thread = None


class ToggleEvent(object):
    pass


class CameraRecorder(StateMachine):

    idle = State("Idle", initial=True)
    recording = State("Recording")

    toggle = idle.to(recording) | recording.to(idle)

    def __init__(self, camera):
        StateMachine.__init__(self)
        self._camera = camera
        self._tape = Tape()
        self._events = queue.Queue()

    def add_toggle_event(self, pin):
        self._events.put(ToggleEvent())

    def on_enter_recording(self):
        print("start recording...")
        filename = "/mnt/hdd/recording_{}.h264".format(time.strftime("%Y%m%d-%H%M%S"))
        self._tape.open(filename)
        self._camera.start_recording(self._tape, format="h264")

    def on_enter_idle(self):
        print("stop recording...")
        self._camera.stop_recording()
        self._tape.close()

    def process_event(self):
        if not self._events.empty():
            if self._events.qsize() % 2 == 1:
                self._events.queue.clear()
                self.toggle()


def main():
    button_pin = 8
    led_pin = 10
    button = Button(button_pin)
    led = Led(led_pin)

    with picamera.PiCamera(resolution="1280x960", framerate=24) as camera:
        recorder = CameraRecorder(camera)
        button.add_pressed_cb(recorder.add_toggle_event)
        while True:
            recorder.process_event()
            if recorder.is_recording:
                camera.wait_recording(1)
                led.toggle()
            else:
                led.on()
                time.sleep(1)


if __name__ == "__main__":
    main()
