# pantilt_test.py
#   Tests moving the servos
import time, sys
try:
    import pantilthat as pth
except Exception as e:
    sys.exit(f"Import failed: {e}\nHint: sudo apt install -y python3-smbus ; pip install pantilthat")

try:
    pth.pan(0); pth.tilt(0); time.sleep(0.6)
    for a in (-50, 0, 50, 0):
        pth.pan(a); time.sleep(0.6)
    for a in (-30, 0, 30, 0):
        pth.tilt(a); time.sleep(0.6)
    print("Pan-Tilt smoke test: OK")

    # Disable the Servos
    # If your pantilthat version supports these, they will disable the servos
    # so you don't hear ticking and power the servos when not in use
    if hasattr(pth, "idle_timeout"):
        try:
            pth.idle_timeout(1)
        except Exception:
            pass
    # Not functional in my library, but here in case they bring it back
    if hasattr(pth, "servo_enable"):
        try:
            pth.servo_enable(0)
        except Exception:
            pass

finally:
    # best-effort recenter
    try: pth.pan(0); pth.tilt(0)
    except: pass
