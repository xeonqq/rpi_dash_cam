### Dependencies
```bash
pip3 install -r requirements.txt
sudo apt-get install gpac # for MP4Box, or build standalone binary from [source](https://github.com/gpac/gpac/wiki/GPAC-Build-Guide-for-Linux#mp4box-only) to save disk space
```
### Hardwares
- led light on pin 10
- button on pin 8
- exteral usb stick for saving the videos. To mount it at boot refer to [mount external-storage](https://www.raspberrypi.org/documentation/configuration/external-storage.md)

### Execute
```bash
python3 record.py
```

### Start RPI dash-cam on boot
```bash
sudo apt-get install supervisor
sudo cp rpicam-record-proccess.conf_ /etc/supervisor/conf.d/
```
