#!/usr/bin/env python3
import argparse
import json
import math
import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional, Tuple

import pantilthat


@dataclass
class DetectionFrame:
    seq: int
    found: bool
    frame_w: int
    frame_h: int
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0
    confidence: float = 0.0
    dropped: Optional[int] = None


def clamp(v: float, lo: float, hi: float) -> float:
    return lo if v < lo else hi if v > hi else v


def sign(v: float) -> float:
    return -1.0 if v < 0 else 1.0


def parse_frame(payload: bytes) -> Optional[DetectionFrame]:
    try:
        obj = json.loads(payload.decode("utf-8", errors="strict"))
    except Exception:
        return None

    try:
        seq = int(obj.get("seq", 0))
        found = bool(obj.get("found", False))
        frame_w = int(obj.get("frame_w", 0))
        frame_h = int(obj.get("frame_h", 0))
        if frame_w <= 0 or frame_h <= 0:
            return None
    except Exception:
        return None

    if not found:
        return DetectionFrame(seq=seq, found=False, frame_w=frame_w, frame_h=frame_h, dropped=obj.get("dropped"))

    try:
        x = int(obj.get("x", 0))
        y = int(obj.get("y", 0))
        w = int(obj.get("w", 0))
        h = int(obj.get("h", 0))
        conf = float(obj.get("confidence", 0.0))
    except Exception:
        return None

    if w <= 0 or h <= 0:
        return DetectionFrame(seq=seq, found=False, frame_w=frame_w, frame_h=frame_h, dropped=obj.get("dropped"))

    return DetectionFrame(
        seq=seq,
        found=True,
        frame_w=frame_w,
        frame_h=frame_h,
        x=x,
        y=y,
        w=w,
        h=h,
        confidence=conf,
        dropped=obj.get("dropped"),
    )


def bbox_center(f: DetectionFrame) -> Tuple[float, float]:
    return (f.x + f.w / 2.0, f.y + f.h / 2.0)


def touches_both_borders(axis_start: int, axis_len: int, frame_len: int, margin_px: int) -> bool:
    min_touch = axis_start <= margin_px
    max_touch = (axis_start + axis_len) >= (frame_len - margin_px)
    return min_touch and max_touch


def soft_deadzone(e: float, deadband: float, softband: float, soft_gain: float) -> float:
    """
    Apply a soft dead-zone around zero.
    - |e| <= deadband        -> 0
    - deadband < |e| < softband -> smoothly ramps up
    - |e| >= softband        -> e
    """
    ae = abs(e)
    if ae <= deadband:
        return 0.0

    if ae >= softband:
        return e

    # Normalize into [0, 1]
    t = (ae - deadband) / (softband - deadband)

    # Smoothstep (cubic Hermite)
    t = t * t * (3.0 - 2.0 * t)

    scaled = deadband + t * (softband - deadband)

    # Apply gentler gain near center
    return math.copysign(scaled * soft_gain + (ae - scaled), e)


class LatestFrameStore:
    """
    Thread-safe, overwrite-only store for the most recent UDP frame.
    """
    def __init__(self):
        self._lock = threading.Lock()
        self._frame: Optional[DetectionFrame] = None
        self._t: float = 0.0
        self._seq: Optional[int] = None

    def update(self, f: DetectionFrame, t_now: float):
        with self._lock:
            self._frame = f
            self._t = t_now
            self._seq = f.seq

    def snapshot(self) -> Tuple[Optional[DetectionFrame], float, Optional[int]]:
        with self._lock:
            return self._frame, self._t, self._seq


def udp_receiver(sock: socket.socket, store: LatestFrameStore, stop_evt: threading.Event, debug_bad_json: bool = False):
    """
    Dedicated receiver thread: blocks on recvfrom and updates latest-frame store.
    """
    # If Python falls behind, a larger kernel receive buffer helps avoid drops.
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 4 * 1024 * 1024)
    except Exception:
        pass

    while not stop_evt.is_set():
        try:
            data, _addr = sock.recvfrom(65535)
        except socket.timeout:
            continue
        except Exception:
            # Keep thread alive on transient errors.
            continue

        f = parse_frame(data)
        if f is None:
            if debug_bad_json:
                # Avoid printing too much; enable only for troubleshooting.
                print("WARN: failed to parse frame")
            continue

        store.update(f, time.monotonic())


def main():
    ap = argparse.ArgumentParser(description="UDP consumer for object_detect_emit_udp -> pan/tilt tracking.")
    ap.add_argument("--bind-ip", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=12347)

    # These two boxes are what define how quickly the pan-tilt moves with you
    # Note that the tick-hz rate is already pretty high... 20 seems to catch on occasion
    ap.add_argument("--tick-hz", type=float, default=15.0, help="Servo update rate (Hz).")
    ap.add_argument("--aggression", choices=["smooth", "normal", "aggressive"], default="smooth")

    # Pan default appropriate for a Pan-Tilt Pimoroni hat
    ap.add_argument("--invert-pan", dest="invert_pan", action="store_true", help="Invert pan direction")
    ap.add_argument("--no-invert-pan", dest="invert_pan", action="store_false", help="Do not invert pan direction")
    ap.set_defaults(invert_pan=False)

    # Tilt default appropriate for a Pan-Tilt Pimoroni hat
    ap.add_argument("--invert-tilt", dest="invert_tilt", action="store_true", help="Invert tilt direction")
    ap.add_argument("--no-invert-tilt", dest="invert_tilt", action="store_false", help="Do not invert tilt direction")
    ap.set_defaults(invert_tilt=True)

    # This is what ensures your head is in the frame and not glued to the top
    ap.add_argument("--top-target", type=float, default=0.15, help="Target vertical position for TOP of bbox, as fraction from top of frame (default:0.2)")

    # Motion smoothing -- reduce micro-jitter if you slightly straighten/slouch (as humans do)
    # Defaults:
    # : +/- 3% of frame change -> no movement
    # : 3 -12% -> gentle correction
    # :   >12% -> full correction
    ap.add_argument("--pan-deadband", type=float, default=0.03, help="Normalized dead-zone around vertical target (no tilt movement) (default:0.03).")
    ap.add_argument("--pan-softband", type=float, default=0.12, help="Normalized range over which tilt ramps from dead-zone to full response (default:0.12).")
    ap.add_argument("--pan-soft-gain", type=float, default=0.35, help="Gain applied just outside the dead-zone (0..1) (default:0.35).")
    ap.add_argument("--tilt-deadband", type=float, default=0.03, help="Normalized dead-zone around vertical target (no tilt movement) (default:0.03).")
    ap.add_argument("--tilt-softband", type=float, default=0.12, help="Normalized range over which tilt ramps from dead-zone to full response (default:0.12).")
    ap.add_argument("--tilt-soft-gain", type=float, default=0.35, help="Gain applied just outside the dead-zone (0..1) (default:0.35).")

    # Center the camera when script finishes
    ap.add_argument("--center-when-done", type=bool, default=True, help="Return servos to start position when script ends.")

    ap.add_argument("--border-margin", type=int, default=3, help="Pixels from edge considered 'touching border'.")
    ap.add_argument("--deadband", type=float, default=0.05, help="Normalized deadband around center (0..1).")
    ap.add_argument("--lost-seconds", type=float, default=0.6, help="How long target must be missing before recenter starts.")
    ap.add_argument("--idle-seconds", type=float, default=1.2, help="If no *fresh* frames, treat as idle after this.")
    ap.add_argument("--max-frame-age-ms", type=int, default=250,
                    help="Frames older than this are treated as stale/unusable (prevents backlog behavior).")
    ap.add_argument("--recenter-rate-deg-per-sec", type=float, default=12.0)
    ap.add_argument("--max-step-deg", type=float, default=2.5, help="Max servo movement per tick (degrees).")
    ap.add_argument("--lock-jump-threshold", type=float, default=0.22,
                    help="If new target jumps farther than this (normalized), require stability before accepting.")
    ap.add_argument("--lock-stable-frames", type=int, default=3)
    ap.add_argument("--pan-min", type=float, default=-70.0)
    ap.add_argument("--pan-max", type=float, default=70.0)
    ap.add_argument("--tilt-min", type=float, default=-80.0)
    ap.add_argument("--tilt-max", type=float, default=30.0)
    ap.add_argument("--center-pan", type=float, default=0.0)
    ap.add_argument("--center-tilt", type=float, default=0.0)
    ap.add_argument("--status-every", type=int, default=50, help="Print a status line every N ticks (0 disables).")
    ap.add_argument("--debug-bad-json", action="store_true")

    args = ap.parse_args()

    # Aggression presets
    if args.aggression == "smooth":
        kp = 18.0
        alpha = 0.18
        max_step = args.max_step_deg
    elif args.aggression == "normal":
        kp = 26.0
        alpha = 0.28
        max_step = max(args.max_step_deg, 3.5)
    else:
        kp = 34.0
        alpha = 0.40
        max_step = max(args.max_step_deg, 5.0)

    # Ensure the user doesn't provide an input that is out of range
    args.top_target = clamp(args.top_target, 0.0, 1.0)

    tick_dt = 1.0 / max(args.tick_hz, 1.0)
    max_age_s = max(0.001, args.max_frame_age_ms / 1000.0)

    # UDP socket (receiver thread will block on this).
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.bind_ip, args.port))
    sock.settimeout(0.2)

    # Start receiver thread
    store = LatestFrameStore()
    stop_evt = threading.Event()
    rx = threading.Thread(target=udp_receiver, args=(sock, store, stop_evt, args.debug_bad_json), daemon=True)
    rx.start()

    # Servo init
    # If your pantilthat version supports these, they help avoid silent disable/idle issues
    # "servo_enable" is not functional in my library, but here in case they bring it back
    if hasattr(pantilthat, "servo_enable"):
        try:
            pantilthat.servo_enable(1)
        except Exception:
            pass
    # This one is functional
    if hasattr(pantilthat, "idle_timeout"):
        try:
            pantilthat.idle_timeout(0)
        except Exception:
            pass

    pantilthat.pan(args.center_pan)
    pantilthat.tilt(args.center_tilt)

    pan = args.center_pan
    tilt = args.center_tilt
    pan_target = pan
    tilt_target = tilt

    # Target lock / hysteresis
    last_target_norm: Optional[Tuple[float, float]] = None
    pending_target_norm: Optional[Tuple[float, float]] = None
    pending_count = 0

    # Timing for lost handling
    last_found_time = 0.0

    tick = 0
    try:
        while True:
            now = time.monotonic()

            latest, latest_t, latest_seq = store.snapshot()
            age = (now - latest_t) if latest is not None else 1e9
            stale = age > max_age_s

            # Consider "idle" if no fresh frames recently.
            idle = age > args.idle_seconds

            # Determine whether we have a usable target this tick.
            use_target = False
            move_freeze_x = False
            move_freeze_y = False
            err_x = 0.0
            err_y = 0.0
            dropped = None
            seq = None
            found_raw = False

            if latest is not None:
                dropped = latest.dropped
                seq = latest.seq
                found_raw = latest.found

            # Only use the frame if it is fresh; otherwise treat as no target.
            if latest is not None and (not stale) and latest.found:

                # Border freeze
                move_freeze_x = touches_both_borders(latest.x, latest.w, latest.frame_w, args.border_margin)
                move_freeze_y = touches_both_borders(latest.y, latest.h, latest.frame_h, args.border_margin)

                cx, cy = bbox_center(latest)

                ## Pan: Center the box.

                #    Normalize Pan error to [-1, +1]
                err_x = ((latest.frame_w / 2.0) - cx) / (latest.frame_w / 2.0)

                #    Apply inversion if necessary
                if args.invert_pan:
                    err_x = -err_x

                #     Apply soft dead-zone to prevent horizontal micro-twitches
                err_x = soft_deadzone(
                    err_x,
                    deadband=args.pan_deadband,
                    softband=args.pan_softband,
                    soft_gain=args.pan_soft_gain,
                )

                ## Tilt: drive TOP of bbox toward a target line (default 15% down from top)
                y_top = float(latest.y)
                y_target = float(latest.frame_h) * float(args.top_target)

                #     Normalize Pan error to [-1, +1]
                err_y = (y_top - y_target) / (latest.frame_h / 2.0)

                #     Apply inversion if necessary
                if args.invert_tilt:
                    err_y = -err_y

                #     Apply soft dead-zone to prevent vertical micro-twitches
                err_y = soft_deadzone(
                    err_y,
                    deadband=args.tilt_deadband,
                    softband=args.tilt_softband,
                    soft_gain=args.tilt_soft_gain,
                )


                # Deadband
                if abs(err_x) < args.deadband:
                    err_x = 0.0
                if abs(err_y) < args.deadband:
                    err_y = 0.0

                # Inversion flags
                if args.invert_pan:
                    err_x = -err_x
                if args.invert_tilt:
                    err_y = -err_y

                # Anti-snap lock
                cur_norm = (err_x, err_y)
                if last_target_norm is None:
                    last_target_norm = cur_norm
                    use_target = True
                else:
                    dx = cur_norm[0] - last_target_norm[0]
                    dy = cur_norm[1] - last_target_norm[1]
                    dist = math.hypot(dx, dy)

                    if dist <= args.lock_jump_threshold:
                        pending_target_norm = None
                        pending_count = 0
                        last_target_norm = cur_norm
                        use_target = True
                    else:
                        if pending_target_norm is None:
                            pending_target_norm = cur_norm
                            pending_count = 1
                        else:
                            pdx = cur_norm[0] - pending_target_norm[0]
                            pdy = cur_norm[1] - pending_target_norm[1]
                            if math.hypot(pdx, pdy) <= (args.lock_jump_threshold * 0.35):
                                pending_count += 1
                            else:
                                pending_target_norm = cur_norm
                                pending_count = 1

                        if pending_count >= max(1, args.lock_stable_frames):
                            last_target_norm = pending_target_norm
                            pending_target_norm = None
                            pending_count = 0
                            use_target = True

                if use_target:
                    last_found_time = now

            # Compute targets
            if use_target:
                if not move_freeze_x:
                    pan_target = pan + (kp * err_x)
                else:
                    pan_target = pan

                if not move_freeze_y:
                    tilt_target = tilt + (kp * err_y)
                else:
                    tilt_target = tilt

                pan_target = clamp(pan_target, args.pan_min, args.pan_max)
                tilt_target = clamp(tilt_target, args.tilt_min, args.tilt_max)

            else:
                # No usable target; after lost-seconds OR idle, begin recenter
                target_age = (now - last_found_time) if last_found_time > 0 else 1e9
                if target_age >= args.lost_seconds or idle:
                    step = args.recenter_rate_deg_per_sec * tick_dt

                    if abs(pan - args.center_pan) <= step:
                        pan_target = args.center_pan
                    else:
                        pan_target = pan + step * sign(args.center_pan - pan)

                    if abs(tilt - args.center_tilt) <= step:
                        tilt_target = args.center_tilt
                    else:
                        tilt_target = tilt + step * sign(args.center_tilt - tilt)

            # Smooth + rate limit
            pan_target = pan * (1.0 - alpha) + pan_target * alpha
            tilt_target = tilt * (1.0 - alpha) + tilt_target * alpha

            pan_delta = clamp(pan_target - pan, -max_step, max_step)
            tilt_delta = clamp(tilt_target - tilt, -max_step, max_step)

            pan = clamp(pan + pan_delta, args.pan_min, args.pan_max)
            tilt = clamp(tilt + tilt_delta, args.tilt_min, args.tilt_max)

            # Drive hardware
            pantilthat.pan(pan)
            pantilthat.tilt(tilt)

            tick += 1
            if args.status_every and (tick % args.status_every == 0):
                usable = (latest is not None) and (not stale)
                age_ms = age * 1000.0
                print(
                    f"tick={tick} seq={seq} usable={int(usable)} age_ms={age_ms:.0f} "
                    f"found_raw={int(found_raw)} use_target={int(use_target)} "
                    f"pan={pan:.1f} tilt={tilt:.1f} err=({err_x:+.2f},{err_y:+.2f}) "
                    f"freeze=({int(move_freeze_x)},{int(move_freeze_y)}) dropped={dropped}"
                )

            time.sleep(tick_dt)

    finally:

        # Stop the tracking loop
        stop_evt.set()
        try:
            sock.close()
        except Exception:
            pass

        # Center the Camera
        if(args.center_when_done):
            pantilthat.pan(args.center_pan)
            pantilthat.tilt(args.center_tilt)
            time.sleep(1.0)

        # Disable the Servos
        # If your pantilthat version supports these, they will disable the servos
        # so you don't hear ticking and power the servos when not in use
        if hasattr(pantilthat, "idle_timeout"):
            try:
                pantilthat.idle_timeout(1)
            except Exception:
                pass
        # Not functional in my library, but here in case they bring it back
        if hasattr(pantilthat, "servo_enable"):
            try:
                pantilthat.servo_enable(0)
            except Exception:
                pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass

