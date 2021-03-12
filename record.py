import picamera
import time
from button import Button
from led import Led
import RPi.GPIO as GPIO

import threading
import logging
import io
import queue
from statemachine import StateMachine, State
logging.basicConfig(level=logging.DEBUG)


class Tape(object):
    MAX_QUEUE_SIZE = 50 
    MAX_BUFFER_SIZE = 1 * 1024 * 1024 # memory buffer size, before put into the queue for disk writing

    def __init__(self):
        self._tape_queue = queue.Queue(Tape.MAX_QUEUE_SIZE)
        self._buffer_size = 0
        self._buffer = io.BytesIO()

    def _record(self):
        with open(self._filename, "wb") as f:
            for data in iter(self._tape_queue.get, None):
                f.write(data)

    def open(self, filename):
        self._filename = filename
        self._thread = threading.Thread(target=self._record)
        self._thread.start()

    def _write_buffer_to_queue(self):
        self._buffer.truncate()
        self._tape_queue.put(self._buffer.getvalue())
        self._buffer.seek(0)
        self._buffer_size = 0

    def write(self, frame):
        self._buffer.write(frame)
        self._buffer_size += len(frame)

        if self._buffer_size > Tape.MAX_BUFFER_SIZE:
            self._write_buffer_to_queue()

    def flush(self):
        if self._buffer_size > 0:
            self._write_buffer_to_queue()

    def close(self):
        self.flush()
        self._tape_queue.put(None)
        self._thread.join()


class ToggleEvent(object):
    pass


class CameraRecorder(StateMachine):

    idle = State("Idle", initial=True)
    recording = State("Recording")

    toggle = idle.to(recording) | recording.to(idle)

    def __init__(self, camera, button, led, recording_folder):
        StateMachine.__init__(self)
        self._folder = recording_folder
        self._camera = camera
        self._button = button
        self._led = led
        self._tape = Tape()
        self._events = queue.Queue()
        self._button.add_pressed_cb(self._add_toggle_event)

    # async call from button interrupt
    def _add_toggle_event(self, pin):
        self._events.put(ToggleEvent())

    def _process_event(self):
        if not self._events.empty():
            if self._events.qsize() % 2 == 1:
                with self._events.mutex:
                    self._events.queue.clear()
                self.toggle()

    def on_enter_recording(self):
        filename = "{}/recording_{}.h264".format(self._folder, time.strftime("%Y%m%d-%H%M%S"))
        logging.info("start recording, saving to {}".format(filename))
        self._tape.open(filename)
        self._camera.start_recording(self._tape, format="h264")

    def on_enter_idle(self):
        logging.info("stop recording...")
        self._camera.stop_recording()
        self._tape.close()

    def run(self):
        while True:
            self._process_event()
            if self.is_recording:
                self._camera.wait_recording(1)
                self._led.toggle()
            else:
                self._led.on()
                time.sleep(1)


def main():
    button_pin = 8
    led_pin = 10
    button = Button(button_pin)
    led = Led(led_pin)
    recording_folder = "/mnt/hdd"

    with picamera.PiCamera(resolution="1280x960", framerate=24) as camera:
        recorder = CameraRecorder(camera, button, led, recording_folder)
        recorder.run()


if __name__ == "__main__":
    main()
