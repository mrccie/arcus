# Project Arcus - Hardware Components Elaborated

Author: mrccie

Date: 6-FEB-2026

Version: 1.0


---

![Project Arcus Logo](assets/logo_color_png.png)

***Project Arcus: Geometry drawn from presence and perception.***

---


## Hardware Used

### Core Hardware

C.1. [Raspberry Pi 5 (8GB model)](https://www.raspberrypi.com/products/raspberry-pi-5/?variant=raspberry-pi-5-8gb)
The 4GB model is probably usable, but I wanted 8 in case I got fancy.  The 16GB model offers no benefits for this application.

C.2. [MicroSD Card (32GB)](https://www.raspberrypi.com/products/sd-cards/)
A 32GB card was more than sufficient for thir project, and any size larger would be fine as well. A 16GB card would likely work but has not been tested. I suggest getting something that is very reliable as the system will be running for many hours a day.

C.3. [Raspberry Pi AI HAT+ (26TOPS Model)](https://www.raspberrypi.com/products/ai-hat/?variant=ai-hat-plus-26)
The 13TOPS model is probably sufficient; I ran this on a 2TOPS Coral NPU with a Raspberry Pi 4 (4GB) previously. However, I wanted the headroom in case I created more complex models for it to track.

C.4. [Pimoroni Pan-Tilt Hat Kit (fully assembled)](https://shop.pimoroni.com/products/pan-tilt-hat?variant=22408353287)
-or-
C.4.1. [Pimoroni Pan-Tilt HAT without Pan-Tilt Module](https://www.adafruit.com/product/3353)
C.4.2. [Mini Pan-Tilt Kit Assembled with Micro Servos](https://www.adafruit.com/product/1967)
Many places will sell (C.4.1.) and (C.4.2.) bundled together (C.4.), but you may save a few bucks if you purchase them seperately.
NOTE: The cut-out for the camera is slightly too small for a Camera Module 3; I used a dremel to enlarge it.

C.5. [Raspberry Pi Camera Module 3](https://www.raspberrypi.com/products/camera-module-3/)
Latest and greatest model available at the time of this project.

C.6. [Raspberry Pi 27W USB-C Power Supply](https://www.raspberrypi.com/products/27w-power-supply/?variant=27w-power-supply-us-white)
You can use a different power supply, but this is the one I used.  If you choose to use another, be aware that you do need a strong power supply or you will encounter the Pi shutting off during some operations.

C.7. [HDMI to USB-C Capture Card](https://www.amazon.com/dp/B08Z3XDYQ7?th=1)
You can use a different one, but this is the one I used.


### Necessary Accessories

A.1. [2x20 Extra-Tall Stacking Header (23mm needed)](https://www.amazon.com/dp/B0827THC7R?ref=ppx_yo2ov_dt_b_fed_asin_title)
The AI HAT does come with a stacking header, but it is not tall enough to accomodate another hat sitting on top of it.

A.2. [200mm long Raspberry Pi Camera Cable](https://www.raspberrypi.com/products/camera-cable/?variant=camera-cable-std-mini-200)
The standard cable that comes with the camera is not long enough for this application.  Be sure to get a "standard-to-mini" cable if you are using an RPi5.

A.3. [M2.5 10mm+6mm Spacers](https://www.amazon.com/dp/B07JYSFMRY?ref=ppx_yo2ov_dt_b_fed_asin_title&th=1) (found in this kit)
These standoffs allow the Pan-Tilt hat to sit on top of the AI hat comfortably, while screwing into the standoffs provided by the AI Hat.  They offer 10mm of standoff, plus 6mm of male screw.  If you buy the linked kit you will get some M2.5 screws included for the top as well.


### Optional Accessories

B.1. [Raspberry Pi 5 Case](https://www.raspberrypi.com/products/raspberry-pi-5-case/)
I purchased this just to use the bottom sled.  It includes anti-slip feet and a functional power button.  Be aware that the total construction of the hats is taller than the sled, however. As a bonus, the case comes with a tiny aluminum heatsink for the raspberry pi CPU, which I repurposed for the AI HAT processor

B.2. [Set of Heatsinks for Raspberry Pi 5, 4-pack, copper](https://www.pishop.us/product/set-of-heatsinks-for-raspberry-pi-5-4-pack-copper/)
There is no room for an active cooler in this configuration; a larger case with a side-mounted fan would be required.  These copper heatsinks make up a lot of the difference.

