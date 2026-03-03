# Project Arcus - Teach the AI Detector to Talk

Author: mrccie

Date: 6-FEB-2026

Version: 1.0


---

![Project Arcus Logo](assets/logo_color_png.png)

***Project Arcus: Geometry drawn from presence and perception.***

---

## Purpose of this Section

The issue we have out of the box is that the method we use to identify objects cannot, by default, output data about where the objects are within the cameras view in a way that Python can make use of. Thus we will need to create a post-processing stage that will emit that information via UDP to the system's loopback interface, which we can read via Python when controlling pan and tilt.  The mechanism is a bit in the weeds, but if you follow the guide you will get through it.




## Step 1: Adding new required packages

Install the prerequisite packages to the system.
```sh
sudo apt install -y libcamera-dev pkg-config
sudo apt install -y libboost-dev libboost-program-options-dev libboost-filesystem-dev libboost-system-dev libboost-thread-dev
sudo apt install -y libopencv-dev
```


## Step 2: Clone the rpicam-apps Repo

In this step we will download the source code for rpicam-apps.  We will add some source code of our own and re-compile it.  Trust me, this sounds much scarier than it's going to be (you just have to copy/paste instructions).

```sh
cd ~
git clone https://github.com/raspberrypi/rpicam-apps.git
```



## Step 3: Prepare a New Post-Processing Stage

This new stage will:
- Read object-detect.results (if present)
- Filters by label (default "person")
- Choose the largest bbox with the given label (highest confidence % is used as a tiebreaker)
- Produce exactly one JSON message (string) per frame, outlining whether the label is found and, if so, where
- Push that JSON into a bounded in-memory queue with drop-oldest policy (no I/O, no blocking)


### Create and Populate the File

Use the command below to create a new object detection emitter file. Paste in the contents from the file with the same name from this project.

```sh
vim ~/rpicam-apps/post_processing_stages/hailo/object_detect_emit_udp_stage.cpp
```


### Create the Directory we will put a new Build File In

```sh
mkdir ~/rpicam-apps/post_processing_stages/emit
```


### Create the Build File

Create the file and paste in the contents from the meson.build file in this phase. This file will tell the compiler to include the ".cpp" file we made earlier.

The new file this will ultimately produce and install is at:
  /usr/lib/aarch64-linux-gnu/rpicam-apps-postproc/emit-postproc.so

```sh
vim ~/rpicam-apps/post_processing_stages/emit/meson.build
```


### Add '/emit/' to the Build Path for rpicam-apps

This command will tell the main build doc for rpicam-apps to include the new build doc we just made.

```sh
echo "" >> ~/rpicam-apps/post-processing_stages/meson.build
echo "subdir('emit')" >> ~/rpicam-apps/post-processing_stages/meson.build
```


### Create a JSON File that Includes the New Stage

Create the file and paste in the contents from the 'hailo_yolov8_inference_udp.json' file in this phase. This file instructs the classifier which object to emit data about, and on which port.

(NOTE FOR FUTURE REVISION: Validate moving this to "~/rpicam-apps/post-processing_stages/assets/" instead)

```sh
vim /usr/share/rpi-camera-assets/hailo_yolov8_inference_udp.json
```



## Step 4: Build and Install the New Module

### Double Check That Everything is Ready

Validate the following files are in place:

```sh
ls ~/rpicam-apps/post_processing_stages/hailo/object_detect_emit_udp_stage.cpp
ls ~/rpicam-apps/post_processing_stages/emit/meson.build
ls /usr/share/rpi-camera-assets/hailo_yolov8_inference_udp.json
```

Validate that the file "post_processing_stages/meson.build" contains "subdir('emit')"

```sh
grep -q "subdir('emit')" post_processing_stages/meson.build \
  && echo "emit subdir is present" \
  || echo "emit subdir is NOT present"
```


### Build

The build process can take a minute; I recommend running each command separately so you can be sure what succeeded and what did not if there is a problem.

```sh
cd ~/rpicam-apps/post_processing_stages
ninja -C build
sudo ninja -C build install
```


### Confirm the ".so" file landed where expected

We validate that the build executed properly.  You should see a file listed named "emit-postproc.so":

```sh
ls -la /usr/lib/aarch64-linux-gnu/rpicam-apps-postproc/ | grep emit
```



## Step 5: Validate

*You will need TWO open terminals for this*

In this step we validate that the build we executed works as designed.

On terminal 1, execute:
```sh
nc -klu 127.0.0.1 12347
```

While terminal 1 is running, execute the following on terminal 2:
```sh
rpicam-vid -t 5000 --rotation 180 \
  --width 1280 --height 720 \
  --lores-width 640 --lores-height 640 \
  --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference_udp.json
```

Expected Outcomes:
- The Pi camera turns on and the output shows bounding boxes on classified objects
- "nc" (terminal 1) prints one JSON object per frame that includes {..."found":true,...} when a person IS detected
- "nc" (terminal 1) prints one JSON object per frame that includes {..."found":false,...} when a person is NOT detected

*If you made it this far, great!  You've come through the hardest and most techncially demanding parts!*
