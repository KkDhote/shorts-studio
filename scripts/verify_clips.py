import subprocess
import glob
import json
import os

files = sorted(glob.glob('final_clips/*.mp4'))
print(f"Found {len(files)} clips:")
for f in files:
    cmd = ['bin/ffmpeg.exe', '-v', 'error'] # test ffprobe
    probe_cmd = ['bin/ffprobe.exe', '-v', 'quiet', '-print_format', 'json', '-show_streams', '-show_format', f]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    data = json.loads(res.stdout)
    v_stream = next(s for s in data['streams'] if s['codec_type'] == 'video')
    a_stream = next(s for s in data['streams'] if s['codec_type'] == 'audio')
    fmt = data['format']
    size_mb = float(fmt['size']) / (1024 * 1024)
    fps_val = eval(v_stream['r_frame_rate'])
    dur = float(fmt['duration'])
    v_start = float(v_stream.get('start_time', 0))
    a_start = float(a_stream.get('start_time', 0))
    sync_diff_ms = abs(v_start - a_start) * 1000
    
    print(f"File: {os.path.basename(f)}")
    print(f"  Path: {os.path.abspath(f)}")
    print(f"  Size: {size_mb:.2f} MB")
    print(f"  Resolution: {v_stream['width']}x{v_stream['height']}")
    print(f"  FPS: {fps_val:.2f}")
    print(f"  Duration: {dur:.2f}s")
    print(f"  Video: {v_stream['codec_name']} | Audio: {a_stream['codec_name']}")
    print(f"  A/V Sync Offset: {sync_diff_ms:.1f} ms")
    print("-" * 50)
