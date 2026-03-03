# Project Arcus - Run the Webcam Without a Monitor

Author: mrccie

Date: 6-FEB-2026

Version: 1.0


---

![Project Arcus Logo](assets/logo_color_png.png)

***Project Arcus: Geometry drawn from presence and perception.***

---

## Purpose of this Section

Having a separate keyboard, mouse, and monitor for the webcam seems a bit self-defeating (and adds processing/latency overhead).  In this section we will set up the Arcus Webcam to run headless, triggering it with a single command via an SSH connection.




## Step 0: Pre-Requisites

The following pieces are assumed and required before proceeding any further:
- WiFi is enabled and connected
- You can access the Raspberry Pi via SSH

*These are required because we will be removing ethernet and HDMI cables*



## Step 1: Disable the Desktop

Disabling the desktop reduces compute requirements and latency that could be introduced by X/Wayland (the GUI).

```sh
sudo systemctl set-default multi-user.target
sudo reboot
```



## Step 2: Connect HDMI-1 to your HDMI->USB-C adapter

Use a microHDMI-to-HDMI cable, and plug that into your HDMI->USB-C box. Then plug that into your laptop/desktop.

The HDMI->USB-C device should be detected as a webcam by your system, though at this point it may not be outputting any video (or it might show some command-line terminal text).



## Step 3: Force HDMI-1 to be Active, Even While Headless

### Validate that HDMI 1 is Where we Expect it to be

In this step we will make sure that HDMI-1 is outputting direct camera feed.  We can also test latency between capture and display.

First, confirm HDMI-1 is /dev/dri/card1:
```sh
ls -l /dev/dri/
```

Expected output would include:
```sh
crw-rw----+ 1 root video  226,   0 Feb  5 13:38 card0
crw-rw----+ 1 root video  226,   1 Feb  5 13:38 card1
```


### Force HDMI-1 to be Active

Edit the firmware file and *add* the content from the *ini* snippit:
```sh
sudo vim /boot/firmware/config.txt
```

Lines to add to the file (anywhere):
```ini
# Parameters force HDMI 1 to be active, even when X is not active
hdmi_force_hotplug=1
hdmi_force_hotplug:1=1

hdmi_group:1=1
hdmi_mode:1=16   # 1080p60; capture dongle will down-negotiate if needed
```


### Reboot

Reboot.
```sh
sudo shutdown -r now
```


### Validate the Camera Displays out HDMI-1

Run a 20-second video test. The output should go to HDMI-1, showing up as webcam video on your connected device.

```sh
rpicam-hello \
  -t 20000 \
  --rotation 180 \
  --fullscreen \
  --width 1920 \
  --height 1080 \
  --framerate 30 
  ```



## Step 4: Test Camera With the Pan-Tilt Script and Motion

### Create the Script that will Track the "person" Object:

Create this file and paste in the contents from the similarly-named file provided. You will not need to interact with this file, it will be called from the shell script you just created.

```sh
vim ~/pantilt-v1/pan_tilt_track_udp.py
```


### Create the Script that will Turn Off the Servos when you Stop the Camera:

Create this file and paste in the contents from the similarly-named file provided. You will not need to interact with this file, it will be called from the shell script you just created.

```sh
vim ~/pantilt-v1/pan_tilt_servos_off.py
```


### Create the Script that Combines Video, Detection, and Pan-Tilt

Create a script that combines the Video Camera and Pan-Tilt Script. Paste in the contents from the similarly-named file.
```sh
vim ~/pantilt-v1/hdmi-pantilt.sh
```

Make it executable:
```sh
chmod +x ~/pantilt-v1/hdmi-pantilt.sh
```


### Run the Script

This should be the end product: a running, person-tracking camera that outputs video as webcam footage to your desktop/laptop!

Run it with this command:
```sh
~/pantilt-v1/hdmi-pantilt.sh
```

Stop it anytime by hitting "CTRL-C" (hold down "ctrl" while pressing the "c" key once).



## Step 5: One Last Check

Here we will run the camera with pan-tilt motion trackign and confirm there are still no undervoltage events, which could affect the stability and life of your Arcus Webcam.

Run the camera for for ~10-20 seconds, making sure it does some pan/tilt, then stop with "ctrl-c".
```sh
~/pantilt-v1/hdmi-pantilt.sh
```

Next, immediately check logs.  You want the output to read "No undervoltage seen".  If you do see undervoltage events, you need a bigger/better power supply.
```sh
sudo dmesg -T | grep -i undervoltage || echo "No undervoltage seen"
```



## Step 6: Celebrate

You're done!  Call up someone via Teams/Webex/Zoom (etc) and show off your nifty new webcam!

You can run it at any time via:
```sh
./pantilt-v1/hdmi-pantilt.sh
```


## Step 7: Go Deeper

The Arcus webcam has a lot of options - for example, you can change the tracking to be more aggressive or adjust how far the camera can pan/tilt.

Use this command to look at all the options you can set:
```sh
python3 ~/pantilt-v1/pan_tilt_track_udp.py --help
```

If you want to adjust (or add) any of those flags, do it in the script that calls the camera.  I suggest making a backup of the known-good version first:
```sh
cp ~/pantilt-v1/hdmi-pantilt.sh ~/pantilt-v1/hdmi-pantilt.sh.bak
```

Then edit it any way you want:
```sh
vim ~/pantilt-v1/hdmi-pantilt.sh
```
