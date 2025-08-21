# Project Arcus -- NOT READY FOR USE YET

Author: mrccie

Copyright: 2025, mrccie

Date: 21-AUG-2025

Version: 0.1


---

![Project Arcus Logo](assets/project_arcus_web.png)

**Project Arcus: Geometry drawn from presence and perception.**

---


## Purpose
Project Arcus is a pan-tilt webcam system designed to recognize and follow a user’s face or body, creating an intelligent, dynamic camera presence.


### Primary Objectives

This project has three primary objectives:
- Build a webcam that tracks presence.
- Keep hardware simple, functional, and quiet.
- Provide a complete, reproducible setup process.


### Secondary Objectives

Secondary objectives for this project include:
- Practice applied Machine Learning
- Enjoy the process of building a physical/electrical system


### Notable Refinements

**USB Detection Evasion**

Some companies are flagging USB devices which identify as Raspberry Pi as security issues, as they can be used to create mouse jigglers or enable remote worker scams (seach North Korean Work Scams).  Fuck that noise.  We're going to update the USB identity to enable awesome web interactions without Big Brother declaring us adversaries of the state.  Hack the Planet, and all that.

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

## Step 1: Hardware Setup
*To be added: wiring, assembly, and mounting instructions for Pi 5, Camera Module 3, AI HAT+, and Pan‑Tilt HAT.*

---

## Step 2: Raspberry Pi Initialization

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

Restar the system:
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

## Step 3: Hardware Testing (OPTIONAL, but RECOMMENDED)


---

## Step 4: Software Installation
Prerequisites: Hardware assembled; Raspberry Pi OS installed and networked.

1. Clone the repository:
   ```bash
   cd ~
   git clone https://github.com/mrccie/arcus.git
   ```

2. Run the installer:
   ```bash
   cd ~/arcus
   sudo ./install.sh
   ```

3. Follow the interactive prompts.

4. Test the system.

5. Celebrate. You are done!

---

Thoughts for Next Iteration
In (constantly evolving) prioritized order, the next additions for this project include:
- Add buttons for device shutdown and restart
- Add a button that controls whether the camera is on (ideally with a light to indicate when it is on)
- Add a light that indicates when the system is fully booted up
- Add an LED light strip for better images
- Add a microphone array
- Designing an enclosure specifically for this webcam
