#!/usr/bin/env bash
set -euo pipefail

### -----------------------------
### User-tunable settings
### -----------------------------
RECENTER_WHEN_DONE=1      # 1 = center to (0,0) then release; 0 = just release
CENTER_PAN=0
CENTER_TILT=0
SERVO_DWELL_SEC=1.0       # time to allow the servos to move before releasing

SERVO_OFF_SCRIPT="$HOME/pantilt-v1/pan_tilt_servos_off.py"

### -----------------------------
### Internal
### -----------------------------
CLEANED_UP=0

cleanup() {
  # idempotent (INT + EXIT can both fire)
  if [[ "$CLEANED_UP" -eq 1 ]]; then
    return
  fi
  CLEANED_UP=1

  echo
  echo "Stopping..."

  # 1) Stop everything in our process group (your original behavior)
  kill -- -$$ 2>/dev/null || true

  # 2) After termination, do a best-effort servo center+release
  #    We run it in a subshell with "|| true" so cleanup never fails.
  if [[ -f "$SERVO_OFF_SCRIPT" ]]; then
    echo "Running servo shutdown helper..."
    if [[ "$RECENTER_WHEN_DONE" -eq 1 ]]; then
      # The python helper centers to 0,0 by design. If you later extend it to take args,
      # wire CENTER_PAN/CENTER_TILT/SERVO_DWELL_SEC into that here.
      python3 "$SERVO_OFF_SCRIPT" >/dev/null 2>&1 || true
    else
      # If you want a "release only" script later, call it here.
      python3 "$SERVO_OFF_SCRIPT" >/dev/null 2>&1 || true
    fi
  else
    echo "Servo shutdown helper not found at: $SERVO_OFF_SCRIPT"
  fi

  # Stop the Python Environment
  deactivate

}

trap cleanup INT TERM EXIT

# Start the Python Environment
source ~/pantilt-test-venv/bin/activate

# Start camera + UDP emitter
rpicam-vid \
  --timeout 0 \
  --rotation 180 \
  --width 1920 \
  --height 1080 \
  --post-process-file /usr/share/rpi-camera-assets/hailo_yolov8_inference_udp.json \
  --lores-width 640 \
  --lores-height 640 \
  >/dev/null 2>&1 &

# Start pan/tilt tracker
python3 ~/pantilt-v1/pan_tilt_track_udp.py \
  --bind-ip 127.0.0.1 \
  --port 12347 \
  --aggression smooth \
  --tick-hz 18 \
  --top-target 0.20 \
  --tilt-deadband 0.03 --tilt-softband 0.12 --tilt-soft-gain 0.35 \
  --pan-deadband 0.04  --pan-softband 0.14  --pan-soft-gain 0.40 \
  --status-every 50 \
  &

# Wait for either to exit (Ctrl-C triggers trap)
wait -n
