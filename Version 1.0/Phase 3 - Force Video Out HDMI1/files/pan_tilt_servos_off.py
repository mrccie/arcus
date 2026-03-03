#!/usr/bin/env python3
import time

try:
    import pantilthat
except Exception as e:
    raise SystemExit(f"Failed to import pantilthat: {e}")


def main():
    # Command center
    pantilthat.pan(0)
    pantilthat.tilt(0)

    # Give the servos time to physically move (adjust if needed)
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
    main()

