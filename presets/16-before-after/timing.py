"""Timing for the before / after slider, shared by scene.py and checks.py.
The snippet's JS uses these exact numbers (checks.py verifies the copy).

Divider position is a percent of the block width (0 = all after,
100 = all before; before shows left of the divider, after right of it).

Intro hint, once, when the block is THRESHOLD on screen (ms in the JS):
    0.00 -> 0.55   START -> START + HINT_DX      (ease .65,0,.35,1 ~ cosine)
    0.55 -> 0.70   hold
    0.70 -> 1.40   back to START                 (same ease)
Keyboard: arrows move STEP, Home = 0, End = 100.
"""
START = 50
HINT_DX = -15          # 50 -> 35 -> 50
HINT_OUT = 0.55
HINT_HOLD = 0.15
HINT_BACK = 0.70
STEP = 5
THRESHOLD = 0.5

HINT_TOTAL = HINT_OUT + HINT_HOLD + HINT_BACK   # 1.40
