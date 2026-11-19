"""
Transcribe module for Universal Video Clipper.
Utilizes faster-whisper with word-level timestamps.
Supports English, Hindi, and Hinglish code-switching with auto GPU/CPU fallback.
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

# Ensure Matplotlib cache warning doesn't trigger
os.environ["MPLCONFIGDIR"] = tempfile.gettempdir()


def detect_optimal_device_and_compute(requested_device: str = "auto", requested_compute: str = "auto") -> tuple[str, str]:
    """
    Detect whether CUDA is genuinely available and operational for ctranslate2.
    Fall back seamlessly to CPU with int8 quantization if CUDA libraries are missing.
    """
    if requested_device != "auto":
        device = requested_device
    else:
        try:
            import ctranslate2
            if ctranslate2.get_cuda_device_count() > 0:
                # Check if cuBLAS / CUDA DLLs are loadable
                import ctypes
                try:
                    ctypes.cdll.LoadLibrary("cublas64_12.dll")
                    device = "cuda"
                except Exception:
                    device = "cpu"
            else:
                device = "cpu"
        except Exception:
            device = "cpu"

    if requested_compute != "auto":
        compute_type = requested_compute
    else:
        if device == "cuda":
            compute_type = "float16"
        else:
            compute_type = "int8"

    return device, compute_type


def transcribe_video(
    input_path: str,
    output_path: str = None,
    model_size: str = "small",
    device: str = "auto",
    compute_type: str = "auto",
    language: str = None,
    initial_prompt: str = None
) -> dict:
    from faster_whisper import WhisperModel

    dev, comp = detect_optimal_device_and_compute(device, compute_type)
    
    # Check if local model directory exists
    workspace_dir = Path(__file__).resolve().parent.parent
    local_model_dir = workspace_dir / "models" / f"faster-whisper-{model_size}"
    if local_model_dir.exists() and (local_model_dir / "model.bin").exists():
        model_target = str(local_model_dir.resolve())
        print(f"[transcribe] Using locally cached model at {model_target}", file=sys.stderr)
    elif Path(model_size).exists():
        model_target = model_size
    else:
        model_target = model_size

    print(f"[transcribe] Initializing faster-whisper model='{model_target}' on device='{dev}' with compute_type='{comp}'...", file=sys.stderr)

    try:
        model = WhisperModel(model_target, device=dev, compute_type=comp)
    except Exception as e:
        print(f"[transcribe] Warning: Failed to load on {dev} ({e}). Falling back to CPU int8...", file=sys.stderr)
        dev, comp = "cpu", "int8"
        model = WhisperModel(model_target, device=dev, compute_type=comp)

    # Hinglish and conversational prompt default
    default_prompt = (
        "Conversational speech with natural code-switching between English, Hindi, and Hinglish. "
        "Transcribe faithfully with correct capitalization and punctuation."
    )
    prompt = initial_prompt if initial_prompt else default_prompt

    whisper_lang = None if (language in [None, "auto", ""]) else language

    print(f"[transcribe] Transcribing {input_path} (word_timestamps=True, language={whisper_lang or 'auto'})...", file=sys.stderr)
    segments_gen, info = model.transcribe(
        input_path,
        beam_size=5,
        word_timestamps=True,
        language=whisper_lang,
        initial_prompt=prompt,
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500)
    )

    detected_language = info.language
    language_prob = round(info.language_probability, 4)
    duration = round(info.duration, 2)

    print(f"[transcribe] Detected language='{detected_language}' (p={language_prob}), duration={duration}s", file=sys.stderr)

    segments_list = []
    all_words = []

    for seg_idx, segment in enumerate(segments_gen):
        seg_words = []
        if segment.words:
            for w in segment.words:
                word_entry = {
                    "word": w.word.strip(),
                    "start": round(w.start, 3),
                    "end": round(w.end, 3),
                    "probability": round(w.probability, 3)
                }
                seg_words.append(word_entry)
                all_words.append(word_entry)

        seg_entry = {
            "id": seg_idx,
            "start": round(segment.start, 3),
            "end": round(segment.end, 3),
            "text": segment.text.strip(),
            "words": seg_words
        }
        segments_list.append(seg_entry)

    result = {
        "source_file": str(Path(input_path).resolve()),
        "language": detected_language,
        "language_probability": language_prob,
        "duration": duration,
        "device_used": dev,
        "compute_type": comp,
        "model": model_size,
        "total_segments": len(segments_list),
        "total_words": len(all_words),
        "segments": segments_list
    }

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"[transcribe] Transcript saved to {out_p}", file=sys.stderr)

    return result


def main():
    parser = argparse.ArgumentParser(description="Transcribe video/audio using faster-whisper with word timestamps.")
    parser.add_argument("--input", "-i", required=True, help="Input video or audio file path")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path (optional, prints to stdout if omitted)")
    parser.add_argument("--model", "-m", default="small", choices=["tiny", "base", "small", "medium", "large-v3"], help="Whisper model size")
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto", help="Compute device")
    parser.add_argument("--compute-type", choices=["auto", "float16", "int8", "int8_float16"], default="auto", help="Quantization type")
    parser.add_argument("--language", "-l", default="auto", help="Language code (e.g. en, hi, or auto)")
    parser.add_argument("--prompt", "-p", default=None, help="Initial prompt for Whisper")
    args = parser.parse_args()

    try:
        data = transcribe_video(
            input_path=args.input,
            output_path=args.output,
            model_size=args.model,
            device=args.device,
            compute_type=args.compute_type,
            language=args.language,
            initial_prompt=args.prompt
        )

        if not args.output:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        err = {"status": "error", "message": str(e)}
        print(json.dumps(err, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
