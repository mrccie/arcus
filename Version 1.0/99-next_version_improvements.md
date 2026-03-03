# Project Arcus - Next Version Targets

Author: mrccie

Date: 6-FEB-2026

Version: 1.0


---

![Project Arcus Logo](assets/logo_color_png.png)

***Project Arcus: Geometry drawn from presence and perception.***

---


**Current Targets**

All items listed as Current Targets are subject to change based on demand and user input.  All changes listed in this section will ideally be included in Verison 2.0.

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

