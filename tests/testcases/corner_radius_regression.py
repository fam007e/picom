#!/usr/bin/env python3
import xcffib.xproto as xproto
import xcffib
import time
import sys
import struct

# Robust Magenta check: R=FF, G=00, B=FF.
# We'll check the middle 10x10 area of the window.
def create_window(conn, size, x, y, color):
    setup = conn.get_setup()
    root = setup.roots[0].root
    visual = setup.roots[0].root_visual
    depth = setup.roots[0].root_depth
    
    wid = conn.generate_id()
    conn.core.CreateWindowChecked(
        depth, wid, root, x, y, size, size, 0,
        xproto.WindowClass.InputOutput, visual,
        xproto.CW.BackPixel, [color]
    ).check()
    conn.core.MapWindowChecked(wid).check()
    return wid

def get_pixel(conn, x, y):
    setup = conn.get_setup()
    root = setup.roots[0].root
    reply = conn.core.GetImage(xproto.ImageFormat.ZPixmap, root, x, y, 1, 1, 0xFFFFFFFF).reply()
    return reply.data.buf()

conn = xcffib.connect()

# Create a 10x10 window. With corner-radius 15, it should be capped to 5.
# If not capped, it would be clipped to 0x0 and invisible.
# Color: Magenta (0xFFFF00FF)
# Note: X11 back-pixel usually takes a long, but GetImage returns bytes.
wid = create_window(conn, 10, 50, 50, 0xFF00FF)
conn.flush()

success = False
for i in range(20): # 10 seconds total max
    time.sleep(0.5)
    pixel = get_pixel(conn, 55, 55)
    
    # GetImage in 24/32-bit depth usually returns 4 bytes per pixel.
    # We match Magenta (R=FF, B=FF, G=00).
    # Both BGRA and RGBA formats put G at index 1, R and B at 0 and 2.
    if len(pixel) >= 3:
        if pixel[1] == 0x00 and pixel[0] == 0xff and pixel[2] == 0xff:
            success = True

    if success:
        print(f"Regression Test Match: {pixel.hex()}")
        break

# Clean up
conn.core.UnmapWindowChecked(wid).check()
conn.core.DestroyWindowChecked(wid).check()
conn.disconnect()

if success:
    print("CORNER-RADIUS REGRESSION TEST PASSED")
    sys.exit(0)
else:
    print("CORNER-RADIUS REGRESSION TEST FAILED: Window not visible or incorrect color")
    sys.exit(1)
