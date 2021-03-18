<p align="center">
  <img src="pics/rpi_dashcam.jpg?sanitize=true" width="200px" height="200px">
  </p>
  <h2 align="center">Raspberry pi Dashcam</h2>


  `rpi dash cam` uses raspberrypi + rpi camera to create your own dashcam. It supports button control and LED indication. Very simple and minmal code. Most importantly, **it has no frame drop**!

  During recording `rpi dash cam` requires very little CPU and memory source, it uses techniques like *Theading* and *Event Queue* to handle the workload between capturing and buffer saving. Thus solves the frame dropping problem many people are facing when recording long-duration video.
  
  *Tested on RPI3 model B with rpi camera V2*. [Demo video](https://youtu.be/LCdgOeGI45s).

  <a class="bmc-button" target="_blank" href="https://www.buymeacoffee.com/xeonqq"><img src="https://cdn.buymeacoffee.com/buttons/bmc-new-btn-logo.svg" alt="Buy me a coffee 😇"><span style="margin-left:5px;font-size:19px !important;">Buy me a coffee 😇</span></a>


### Installation
```bash
ssh pi@raspberrypi.local
cd ~
git clone https://github.com/xeonqq/rpi_dash_cam.git camera_record
cd camera_record
pip3 install -r requirements.txt
sudo apt-get install gpac # for MP4Box, or build standalone binary from [source](https://github.com/gpac/gpac/wiki/GPAC-Build-Guide-for-Linux#mp4box-only) to save disk space
```

### Hardwares
- LED light on pin 10
- button on pin 8
- exteral usb stick for saving the videos. To mount it at boot refer to [mount external-storage](https://www.raspberrypi.org/documentation/configuration/external-storage.md)

### Execute
```bash
python3 record.py
```
Usage:
- LED constant on indicating ready to record
- Press button once to start recording, LED start blinking in 1 sec interval
- Press button again to stop recording

### Start RPI dash-cam on boot
```bash
sudo apt-get install supervisor
sudo cp rpicam-record-proccess.conf /etc/supervisor/conf.d/
```

