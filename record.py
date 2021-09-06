import picamera
import time
from button import Button
from led import Led
import RPi.GPIO as GPIO

import threading
import logging
import io
import os
import queue
import subprocess
from statemachine import StateMachine, State

logging.basicConfig(
    filename="{}/rpi_dashcam.log".format(os.getcwd()), level=logging.DEBUG
)


class Tape(object):
    MAX_QUEUE_SIZE = 50
    MAX_BUFFER_SIZE = (
        1 * 1024 * 1024
    )  # memory buffer size, before put into the queue for disk writing

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
    def __init__(self, camera_recorder):
        self._camera_recorder = camera_recorder

    def execute(self):
        self._camera_recorder.toggle()


class ConvertMP4Event(object):
    def __init__(self, camera_recorder):
        self._camera_recorder = camera_recorder
        # copy once, since it can change in recorder
        self._filename = self._camera_recorder.filename

    def execute(self):
        t = threading.Thread(target=self._convert_to_MP4)
        t.start()

    def _convert_to_MP4(self):
        cmd = "MP4Box -add {filename}:fps={fps} {filename}.mp4".format(
            filename=self._filename, fps=self._camera_recorder.fps
        )
        code = subprocess.call(cmd.split())
        if code == 0:
            self._delete_h264_file()
            logging.info("converted h264 file to {}.mp4".format(self._filename))
        else:
            logging.error("conversion to mp4 failed")

    def _delete_h264_file(self):
        cmd = "rm {filename}".format(filename=self._filename)
        subprocess.call(cmd.split())


def is_rtc_available():
    cmd = "timedatectl | grep 'RTC time' | cut -d ':' -f2|sed 's/^ *//g'"
    ps = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    output = ps.communicate()[0].strip()
    return False if output == "n/a".encode("ASCII") else True


def generate_recording_filename(folder):
    filename = None
    if is_rtc_available():
        filename = "{}/recording_{}.h264".format(folder, time.strftime("%Y%m%d-%H%M%S"))
    else:
        counter_file = "{}/counter.txt".format(folder)
        if os.path.isfile(counter_file):
            with open(counter_file, "r+") as f:
                line = f.readline()
                content = line.strip()
                new_count = int(content) + 1
                f.seek(0)
                f.write(str(new_count))
                f.truncate()
        else:
            with open(counter_file, "w+") as f:
                new_count = 0
                f.seek(0)
                f.write(str(new_count))

        filename = "{}/recording_{}.h264".format(folder, new_count)
    return filename


class CameraRecorder(StateMachine):

    recording = State("Recording")
    idle = State("Idle", initial=True)

    toggle = idle.to(recording) | recording.to(idle)

    def __init__(self, camera, button, led, recording_folder):
        StateMachine.__init__(self)
        self._folder = recording_folder
        self._camera = camera
        self._button = button
        self._led = led
        self._tape = Tape()
        self._events = queue.Queue()
        self._conversion_queue = queue.Queue()
        self._button.add_pressed_cb(self._add_toggle_event)
        self._rtc_available = is_rtc_available()

    @property
    def fps(self):
        return self._camera.framerate

    @property
    def filename(self):
        return self._filename

    # async call from button interrupt
    def _add_toggle_event(self, pin):
        logging.info("button pressed")
        self._events.put(ToggleEvent(self))

    def _add_convert_mp4_event(self):
        self._events.put(ConvertMP4Event(self))

    def _process_event(self):
        if not self._events.empty():
            evt = self._events.get()
            evt.execute()

    def on_enter_recording(self):
        self._filename = generate_recording_filename(self._folder)
        logging.info("start recording, saving to {}".format(self._filename))
        self._tape.open(self._filename)
        self._camera.start_recording(self._tape, format="h264")

    def on_enter_idle(self):
        logging.info("stop recording...")
        self._led.off()
        self._camera.stop_recording()
        self._tape.close()
        self._add_convert_mp4_event()

    def run(self):
        self.toggle()
        while True:
            self._process_event()
            if self.is_recording:
                self._camera.wait_recording(1)
                self._led.toggle()
            else:
                self._led.on()
                time.sleep(1)


def main():
    logging.info("rpi dashcam ready to record!")
    button_pin = 8
    led_pin = 10
    button = Button(button_pin)
    led = Led(led_pin)
    recording_folder = "/home/pi"

    with picamera.PiCamera(resolution="1280x960", framerate=24) as camera:
        recorder = CameraRecorder(camera, button, led, recording_folder)
        recorder.run()


if __name__ == "__main__":
    main()
