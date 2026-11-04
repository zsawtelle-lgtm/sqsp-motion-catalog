"""Timing for the mask/clip wipe, shared by scene.py and checks.py.
The snippet's CSS/JS uses these exact numbers (checks.py verifies the copy).

Per block, from its start time (s):
    0.00 -> 0.55   curtain grows across the block       (ease .65,0,.35,1)
    0.55 -> 0.62   curtain holds, block fully covered
    0.62 -> 1.30   curtain exits, image uncovered behind it (same edge, same ease)
    0.62 -> 1.82   image settles scale 1.08 -> 1           (ease .33,1,.68,1)
Text blocks (opt-in): plain clip wipe 0.00 -> 0.80, no curtain.
Blocks that trigger together start STAGGER apart (DOM / top-left order).
"""
CURTAIN_IN = 0.55
HOLD = 0.07
UNCOVER = 0.68
SCALE_FROM = 1.08
SCALE_DUR = 1.20
TEXT_DUR = 0.80
STAGGER = 0.28
THRESHOLD = 0.20       # share of the block inside the (shrunk) viewport
BOTTOM_MARGIN = 0.10   # rootMargin 0 0 -10% 0

UNCOVER_AT = CURTAIN_IN + HOLD               # 0.62
CURTAIN_TOTAL = UNCOVER_AT + UNCOVER          # 1.30
BLOCK_TOTAL = UNCOVER_AT + SCALE_DUR          # 1.82
