# Project Arcus - Hardware Build with Component Setup and Testing

Author: mrccie

Date: 6-FEB-2026

Version: 1.0


---

![Project Arcus Logo](assets/logo_color_png.png)

***Project Arcus: Geometry drawn from presence and perception.***

---

## Step 1: Set up and test the Camera ##

### Shut Down and Disconnect Power from the RPi ###

If the Raspberry Pi is on, issue the command below and disconnect the power once the system has shut down.

```sh
sudo shutdown -h now
```


### Connect the Camera to the RPi ###

Use camera slot 0 or 1; it should auto-detect.

Connect power to the RPi to boot it when complete.


### Ensure the rpicam package is installed ###

This should be installed by default, but let's make sure.

```sh
sudo apt install -y rpicam-apps
```


### Test the Camera ###

Execute the command below. A video screen should open in the GUI displaying what the camera sees, and it will close after 10 seconds.  If the camera, cable, or RPi are not working properly you will get an error stating "no cameras found". In my experience, this is a result of the camera cable not being seated properly 10 times out of 10.  Troubleshoot and repeat until successful.  Remember to always shut down the RPi and remove power before touching the board or components.

```sh
rpicam-hello
```



## Step 2: Connect the AI HAT ##

### Shut Down and Disconnect Power from the RPi ###

Issue the command below and disconnect the power once the system has shut down.

```sh
sudo shutdown -h now
```


### Add On the Extra Tall Header Stack ###

Connect the extra tall 2x20 pin header stack to the pin array on the Raspberry Pi.  Not the one that came with the AI HAT though - use the even taller one suggested in the Hardware section.


### Connect the AI HAT to the Tall Header Stack ###

When connecting the AI HAT, ensure the camera ribbon is run through the purpose-built slot. Use the spacers that came with the product to keep all 4 edges up.  Do NOT screw the bottom of the spacers in yet; screw the 10mm+6mm spacers DOWN from the top of the hat.  The bottom will be "floating" for now; screwing the whole assembly to the Raspberry Pi case is the LAST step.


### (OPTIONAL) Attach the Aluminum Heatsink that came with the RPi Case to the AI CPU ###

Just peel off the non-stick tape and press the heatsink onto the AI HAT CPU.


### Install the Hailo Package ###

Install the package needed for the Hailo unit and reboot.

```sh
sudo apt install -y hailo-all
sudo reboot
```


### Verify that we can see the AI HAT ###

We're going to make sure that the hardware is identified by the Raspberry Pi.  Expect a single device (e.g., 0000:01:00.0) and firmware info from the command below. If nothing appears, it’s almost always the PCIe FFC (ribbon) seating; shut down, re-seat it, and try again.

```sh
hailortcli scan
hailortcli fw-control identify
```


### Test the AI HAT in Conjunection with the Camera ###

This is a bit of a jump from the last test; we're going to demonstrate the AI HAT working by using it in conjunction with the camera.  This worked the first time for me, so I have no suggestions if it does not work.  This will run the rpicam-hello video again, but this time it should show classification bounding boxes on images.  It will run for 10 seconds before stopping.

```sh
rpicam-hello -t 10000 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json --lores-width 640 --lores-height 640
```



## Step 3: Connect the Pan-Tilt Hat ##

### Enable I2C Interface ###

!! This is designed to require a reboot !!

Issue the command below.  This will enable i2c, which should be done prior to powering on the Pan-Tilt HAT.

```sh
sudo sed -i 's/^#\?dtparam=i2c_arm=.*/dtparam=i2c_arm=on/' /boot/firmware/config.txt || echo 'dtparam=i2c_arm=on' | sudo tee -a /boot/config.txt
```


### Shut Down and Disconnect Power from the RPi ###

Issue the command below and disconnect the power once the system has shut down.

```sh
sudo shutdown -h now
```


### Disconnect the Camera Ribbon Cable from the Camera 3 Module ###

The ribbon cable  is connected to both the RPi 5 and the Camera 3 module; disconnect the Camera 3 end.  This is necessary so that you can slot the cable through the Pan-Tilt HAT and more easily mount the camera.


### Connect the Pan-Tilt HAT to the Headers Sticking Out of the AI HAT ###

Wire it up per the device's instructions, then feed the camera ribbon cable through the provided slot and stack it on the AI HAT headers.  Use screws through the top to secure it to the standoffs on top of the AI HAT.


### Connect the Camera to the Ribbon Cable ###

Re-connect the camera to the ribbon cable.  Remember, the side with the pins goes toward the PCB.


### Connect Power to the RPi ###

Start the RPi.


### Test the AI HAT and the Camera -- AGAIN ###

We're going to make sure the AI HAT and Camera are both still working.  It will run for 10 seconds before stopping.

```sh
rpicam-hello -t 10000 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json --lores-width 640 --lores-height 640
```

You may have noticed that the camera is installed upside-down on the Pan-Tilt HAT. That's fine!  Here's how you can validate it working with the correct orientation, if it makes you feel better.

```sh
rpicam-hello -t 10000 --rotation 180 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json --lores-width 640 --lores-height 640
```


### Validate that the Pan-Tilt HAT is Correctly Connected ###

Run the command below.  You should see a field of dashes, with one of them being replaced with "15".  If you do, the HAT has been detected properly.  If you see "40" you have a Waveshare PCA9685 board; that can still work, but it uses a different set of drivers than this project guide will (best of luck to you).

```sh
sudo apt install -y i2c-tools
i2cdetect -y 1  # scanning bus 1
```


### Validate the Pan-Tilt Hat Turns ###

To test the Pan-Tilt HAT we are going to need to use python.  We will create a virtual environment and run a small script, with the goal of seeing smooth motion with no buzz/jitter storms.  Be sure to also watch the screen, to ensure no undervoltage icon appears.

Install a necessary system bit:
```sh
sudo apt install -y python3-smbus
```

Set up the virtual environment. We will stay in this activated environment until we reboot (later).
```sh
python3 -m venv --system-site-packages ~/pantilt-test-venv
source ~/pantilt-test-venv/bin/activate
python3 -m pip install --upgrade pip setuptools wheel
python3 -m pip install pantilthat
```

Create the file 'pantilt-test.py' and populate it with the file of the same name from this step:
```sh
mkdir ~/pantilt-v1/
mkdir ~/pantilt-v1/hardware_tests/
touch ~/pantilt-v1/hardware_tests/pantilt_test.py
```

Run the file.  If all is well your pan-tilt should... pan and tilt.  Your virtual environment will need to be active for this to work (command: source ~/pantilt-test-venv/bin/activate)
```sh
python3 ~/pantilt-v1/hardware_tests/pantilt_test.py
```



## Step 4: Full Equipment Test ##

This is important because it tests that all systems can function simultaneously.

Run the command below and you should have the camera turn on and see object identification boxes, and the pan-tilt should engage as well.  As before, the virtual environment must be present for this to work.

```sh
rpicam-hello -t 5000 --rotation 180 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json --lores-width 640 --lores-height 640 & python3 ~/pantilt-v1/hardware_tests/pantilt_test.py
```


### Validate Power Stability

Read all of the instructions in this section before proceeding so that you can execute quickly.

Just to clear everything out, let's reboot first:
```sh
sudo reboot now
```

After reboot, run the pan-tilt and inference combo for a slightly extended period:
```sh
source ~/pantilt-test-venv/bin/activate

rpicam-hello -t 10000 --rotation 180 --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference.json --lores-width 640 --lores-height 640 & python3 ~/pantilt-v1/hardware_tests/pantilt_test.py
```

Immediately issue this command to check for messages reslating to undervoltage conditions occurring.  If you see any, you will need a better power supply.  The power requirements are only going to go up from here.
```sh
sudo dmesg -T | grep -i undervoltage || echo "No undervoltage seen"
```

Deactive the virtual environment now that you no longer need it.
```sh
deactivate
```


## You Are Now Ready to Set Up Motion Tracking ##

Your hardware is fully tested and ready - you can do this!
