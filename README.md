### Dependencies
pip3 install -r requirements.txt

### Hardwares
- led light on pin 10
- button on pin 8
- exteral usb stick for saving the videos. To mount it at boot refer to [mount external-storage](https://www.raspberrypi.org/documentation/configuration/external-storage.md)

### Execute
python3 record.py

### Start RPI dash-cam on boot
sudo apt-get install supervisor
sudo cp rpicam-record-proccess.conf_ /etc/supervisor/conf.d/
