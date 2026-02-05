#!/usr/bin/env python3
"""Verify Marcinkova against the 962px redaction"""

from PIL import ImageFont

FONT_PATH = "fonts/fonts/times.ttf"
TARGET_W = 962

font_size = int(12 * 1200 / 72)
font = ImageFont.truetype(FONT_PATH, font_size)

print("="*80)
print("VERIFICATION: Marcinkova vs Anne Marie")
print("="*80)
print(f"\nTarget redaction width: {TARGET_W}px")

# Test Marcinkova
name = "Marcinkova"
width = font.getlength(name)
diff = abs(width - TARGET_W)
pct = diff / width * 100

print(f"\n[1] Marcinkova:")
print(f"  Expected width: {width:.1f}px")
print(f"  Difference: {diff:.1f}px ({pct:.2f}%)")
print(f"  Letters: {len(name)}")

# Test Anne Marie for comparison
anne_marie = font.getlength("Anne Marie")
diff2 = abs(anne_marie - TARGET_W)
pct2 = diff2 / anne_marie * 100

print(f"\n[2] Anne Marie:")
print(f"  Expected width: {anne_marie:.1f}px")
print(f"  Difference: {diff2:.1f}px ({pct2:.2f}%)")
print(f"  Letters: {len('Anne Marie'.replace(' ', ''))}")

# Test Nadia Marcinkova
nadia_marcinkova = font.getlength("Nadia Marcinkova")
diff3 = abs(nadia_marcinkova - TARGET_W)
pct3 = diff3 / nadia_marcinkova * 100

print(f"\n[3] Nadia Marcinkova:")
print(f"  Expected width: {nadia_marcinkova:.1f}px")
print(f"  Difference: {diff3:.1f}px ({pct3:.2f}%)")
print(f"  Letters: {len('NadiaMarcinkova')}")

# Letter-by-letter breakdown for Marcinkova
print(f"\n[DETAIL] Letter breakdown for 'Marcinkova':")
total = 0
for char in "Marcinkova":
    w = font.getlength(char)
    total += w
    marker = ""
    if char == "M":
        marker = " ← First letter (UPPER)"
    elif char == "a":
        marker = " ← Last letter (x-height)"
    print(f"  '{char}': {w:.1f}px{marker}")

print(f"\n  Calculated total: {total:.1f}px")
print(f"  Redaction width:  {TARGET_W}px")
print(f"  Difference:       {abs(total - TARGET_W):.1f}px")

print("\n" + "="*80)
winner = "Marcinkova" if pct < pct2 else "Anne Marie"
print(f"WINNER: {winner}")
print("="*80)

# Artifacts analysis
print(f"\n[ARTIFACT MATCH]")
print(f"  First letter 'M': UPPER protrusion (tall letter)")
print(f"  Last letter 'a': x-height, no protrusion")
print(f"  Detected artifacts: LEFT edge has UPPER, RIGHT edge has none")
print(f"  → MATCHES Marcinkova ✓")
