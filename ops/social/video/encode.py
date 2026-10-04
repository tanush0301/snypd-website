"""python ops/social/video/encode.py OUT_DIR -- OUT_DIR/frames/*.jpg -> OUT_DIR/snypd-demo-9x16.mp4
(H.264 via OpenCV's bundled FFmpeg, FPS env var, default 30, no audio) and reads the file back to prove it decodes."""
import glob
import os
import sys

import cv2

out = sys.argv[1]
frames = sorted(glob.glob(os.path.join(out, 'frames', '*.jpg')))
if not frames:
    sys.exit('no frames')
h, w = cv2.imread(frames[0]).shape[:2]
dst = os.path.join(out, 'snypd-demo-9x16.mp4')
vw = cv2.VideoWriter(dst, cv2.VideoWriter_fourcc(*'avc1'), int(os.environ.get('FPS', 30)), (w, h))
if not vw.isOpened():
    sys.exit('H.264 writer did not open')
for f in frames:
    vw.write(cv2.imread(f))
vw.release()

cap = cv2.VideoCapture(dst)
codec = int(cap.get(cv2.CAP_PROP_FOURCC)).to_bytes(4, 'little').decode(errors='replace')
n, fps = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)), cap.get(cv2.CAP_PROP_FPS)
print(f'{dst}: {w}x{h} {codec} {n} frames {fps:.0f} fps = {n / fps:.2f} s, {os.path.getsize(dst) / 1e6:.2f} MB')
