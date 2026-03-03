# Project Arcus -- NOT READY FOR USE YET

Author: mrccie

Copyright: 2026, mrccie

Date: 6-FEB-2026

Latest Working Version: 1.0


---

![Project Arcus Logo](assets/logo_color_png.png)

***Project Arcus: Geometry drawn from presence and perception.***

---


## Purpose
Project Arcus is a pan-tilt webcam system designed to recognize and follow a user’s face or body, creating an intelligent, dynamic camera presence.


### Primary Objectives

This project has three primary objectives:
- Build a webcam that tracks a human.
- Keep hardware simple, functional, and quiet.
- Provide a complete, reproducible setup process.


### Secondary Objectives

Secondary objectives for this project include:
- Practice applied Machine Learning
- Enjoy the process of building a physical/electrical system

---

Hardware Requirements

- 1 × Raspberry Pi 5 (8GB) — [$80]  
- 1 × Raspberry Pi Camera Module 3 — [$28]  
- 1 × Raspberry Pi 27W USB‑C Power Supply — [$13]  
- 1 × Raspberry Pi Case for Pi 5 (Red/White) — [$11]  
- 1 × Raspberry Pi AI HAT+ 26 TOPS — [$120]  
- 1 × Camera Cable for Raspberry Pi 5 (300 mm) — [$3]  
- 1 × Pimoroni Pan‑Tilt HAT — [$42]  
- 1 × Set of Heatsinks for Raspberry Pi 5, 4‑pack, Copper — [$5] *(optional; no fan = no fan noise)*  
- 1 × 64 GB Micro‑SD card (A2 recommended; 32 GB minimum) — [$13]  

Preferred vendors: [Adafruit](https://www.adafruit.com/) and [PiShop](https://www.pishop.us/). Support them, not Amazon.

*Once configured this system will run headless, but initial hardware testing steps may assume the use of a GUI and monitor.*



---

## Step 1: Raspberry Pi Initialization

If you're installing on a Pi from scratch, you'll need to do a few things first.

[Steps to set up a headless RPi](https://www.tomshardware.com/reviews/raspberry-pi-headless-setup-how-to,6028.html)

### (OPTIONAL) Set a Static IP - HEADLESS SETUP (if a GUI is in use, set it in Network Manager)

Run the following command to list the available network interfaces:
```sh
ip address
```

You'll see output like the below. In this example, eth0 is the interface name (yours may be different).
```sh
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether d8:3a:dd:89:ee:4c brd ff:ff:ff:ff:ff:ff
    inet 192.168.2.118/24 brd 192.168.2.255 scope global dynamic noprefixroute eth0
       valid_lft 50497sec preferred_lft 50497sec
    inet6 fe80::e5ed:478a:a19e:548/64 scope link noprefixroute
       valid_lft forever preferred_lft forever
```

Edit or create a new file in /etc/systemd/network/ for the interface:
```sh
sudo vim /etc/systemd/network/10-static.network
```

Add the following configuration (update IP's for your network):
```sh
[Match]
Name=eth0

[Network]
Address=192.168.2.7/24
Gateway=192.168.2.1
DNS=4.2.2.4 8.8.8.8
```

Run the following commands to enabe systemd-networkd and apply the changes:
```sh
sudo systemctl restart systemd-networkd
sudo systemctl enable systemd-networkd
```

Verify the new IP configuration with:
```sh
ip address
```

(If You're Running a GUI-based distro as Headless...) Disable NetwokManager or it will interfere with DNS
```sh
sudo systemctl stop NetworkManager
sudo systemctl disable NetworkManager

sudo rm /etc/resolv.conf
```

Set up DNS manually:
```sh
echo "nameserver 4.2.2.4" | sudo tee /etc/resolv.conf
echo "nameserver 8.8.8.8" | sudo tee -a /etc/resolv.conf
```

Make sure the file can't be overwritten by marking it immutable:
```sh
sudo chattr +i /etc/resolv.conf
```

Restart Networking
```sh
sudo systemctl restart systemd-networkd
```

Validate DNS is operational:
```sh
ping -c 3 google.com
```


### (OPTIONAL) Disable WiFi (assuming a Raspberry Pi with an ethernet connection)

Edit the following file:
```sh
sudo vim /boot/firmware/config.txt
```

Add to it:
```sh
dtoverlay=disable-wifi
```

Restart the system:
```sh
sudo shutdown -r now
```


### (OPTIONAL) Change the password of the user 'pi' if you haven't done so already:
```sh
passwd
```

### Update the operating system:
```sh
sudo apt-get update
sudo apt-get upgrade
```

### Set your local timezone:
```sh
sudo raspi-config
> 5 - Localization Options
>> L2 - Change Time Zone
>>> Pick accordingly
>>>> Finish
```

---

## Step 2: HAT Setup and Testing

Version 1.0: Skip to the 'Version 1.0' folder and fully read Phase 0 (Hardware Requirements), then construct per Phase 1 (Build and Test Hardware).


---

## Step 4: Software Installation

Version 1.0: Skip to the 'Version 1.0' folder and execute (in sequence) Phase 2 then Phase 3.


---

Thoughts for Future Iterations

**V2 Targets**

All items listed as V2 Targets are subject to change based on demand and user input.  All changes listed in this section will ideally be included in Verison 2.0.

***Giving Back && Process Improvement: Ease of Configuration Improvement***
I will be submitting an improvement propsal to the open source rpicam-apps project to include UDP emission in the default package. If this improvement is accepted this project will no longer need to pull and rebuild the package - substantially streamlining the process.

***New Feature: Light Bar***
The Pimoroni Pan-Tilt hat is sold by Adafruit as a kit with an LED bar. I would like to install and enable that bar, and perhaps use it to indicate things about the camera.  For example, we could turn the light bar on when the camera process is running - or even have just one addressable light turn green when the camera is running, even if the light bar is set to "off".

***New Feature: Controller Keypad***
The goal is to purchase some type of controller device for the Raspberry Pi. Something like the number pad on a computer that connects via USB, with dedicated buttons:
- Enable/disable the camera
- Enable/disable bounding boxes for the video output
- Enable/disable/recolor a camera-mounted bar light
- Enable/disable pan-tilt
- Recenter the camera after video-off (for us pedants)
- Shutdown the Pi

***Quality of Life: Cable Improvements***
The camera ribbon and the pan/tilt power cables are a bit longer than necessary. Shorter ribbon/cable lengths will improve aesthetics.

***Quality of Life: HDMI Cable***
The current cable I use is a bit thick and stiff.  Since this only carries 1080p30, we should be able to find a thinner + more flexible HDMI cable.

***Quality of Life: Tune Pan-Tilt Steps***
It seems like every so often a servo moves and whines; presumably, there is a step being requested that is too small.  This goes away with a tiny human movement (or a bit of time) so it's not a problem but is a quality of life item to address.

***Reliability: Do a Sweep for Extraneous Processes***
We are using a default OS for this application, which may run processes we do not need to. If existant, those may introduce unnecessary latency for video frames. So we should do a quick sweep and cleanup.

***Reliability: Do a Sweep for Extraneous File Write Activities***
We are using a default OS for this application, which may have processes which save to disk more often than necessary.  Those writes will reduce the lifetime of the microSD card, so we should try to minimize them.


**Future Targets**

Items listed as Future Targets are not prioritized yet and will be added to the Current Targets list for the next iteration by community demand.

***Quality of Life: Enclosure***
The current camera sits on top of a standard RPi case bottom, leaving a lot to be dessired. Need a base that is tall or that snaps on to a taller base (or stackable rings).  The base also needs to be weighted to resist cord tugging. Being able to
plug in at the bottom of the base rather than at the Pi itself would also be beneficial.

***New Feature: Sentry Mode***
I would like to be able to leave the RPi running while I am away and have it create alerts when a 'person' is detected by the camera (for at least 1 full second). A "pan and scan" option would also be appreciated, which rotates the camera until a person is identified.
  See also: New Feature: Streaming Webcam
  See also: New Feature: Remote Stream Recording
  See also: New Feature: Hubitat Triggering

***New Feature: Streaming Webcam***
I would like to be able to connect to the camera via a web browser (or similar) and view a live feed from the camera.

***New Feature: Remote Stream Recording***
I would like to be able to stream video to an external location, such as a NAS or existing security camera DVR.

***New Feature: Hubitat Triggering***
I would like to be able to trigger events within Hubitat from the Raspberry Pi, likely by togging a virtual switch On or Off. Use-cases could include turning on a virtual light configuration switch when the camera turns on, or triggering alerts when Sentry Mode detects a person.

