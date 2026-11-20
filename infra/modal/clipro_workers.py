"""Clipro serverless media workers.

Deploy with the Clipro worker Secret configured. Functions download only
server-approved object keys from the private R2 bucket; they never fetch
platform URLs supplied by users.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import asyncpg
import boto3
import modal
from botocore.config import Config

from services.worker.app.media_probe import (
    create_thumbnail,
    probe_media,
    sha256_file,
)

APP_NAME = "clipro-workers"
SECRET_NAME = "clipro-worker-secrets"
THUMBNAIL_ROOT = "assets"

app = modal.App(APP_NAME)
image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("ffmpeg")
    .pip_install("asyncpg>=0.30,<1", "boto3>=1.35,<2")
    .add_local_python_source("services")
)
analysis_image = image.pip_install(
    "torch>=2.5,<3", "transformers>=4.49,<5", "accelerate>=1.2,<2",
    "qwen-vl-utils>=0.0.10", "Pillow>=10,<12", "faster-whisper>=1.1,<2",
)


def _database_url_and_ssl() -> tuple[str, str | bool]:
    """Accept Supabase's sslmode=require URL but pass TLS via asyncpg's ssl arg."""
    raw_url = os.environ["DATABASE_URL"]
    parts = urlsplit(raw_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    ssl_mode = query.pop("sslmode", "require")
    clean_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
    ssl_value: str | bool = "require" if ssl_mode in {"require", "verify-ca", "verify-full"} else False
    return clean_url, ssl_value


def _r2_client():
    account_id = os.environ["R2_ACCOUNT_ID"]
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        region_name="auto",
        aws_access_key_id=os.environ["R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["R2_SECRET_ACCESS_KEY"],
        config=Config(
            signature_version="s3v4",
            s3={"addressing_style": "path"},
            retries={"max_attempts": 4, "mode": "standard"},
        ),
    )


async def _set_job_failed(connection, job_id: str, asset_id: str, error: str) -> None:
    safe_error = (error or "Media probe failed.")[:500]
    await connection.execute(
        """UPDATE public.processing_jobs
           SET status='failed', progress=100, error_message=$2, completed_at=now(), updated_at=now()
           WHERE job_id=$1""",
        job_id,
        safe_error,
    )
    await connection.execute(
        "UPDATE public.media_assets SET state='failed' WHERE asset_id=$1",
        asset_id,
    )


@app.function(
    image=image,
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    cpu=2,
    memory=4096,
    ephemeral_disk=50 * 1024,
    timeout=1800,
    retries=1,
    max_containers=2,
    scaledown_window=60,
)
def probe_asset(job_id: str, asset_id: str, workspace_id: str) -> dict:
    """Download one authorized R2 source, probe it and create a thumbnail."""
    async def run() -> dict:
        dsn, ssl_value = _database_url_and_ssl()
        connection = await asyncpg.connect(dsn=dsn, ssl=ssl_value)
        try:
            row = await connection.fetchrow(
                """SELECT asset_id, workspace_id, storage_key, original_filename
                   FROM public.media_assets
                   WHERE asset_id=$1 AND workspace_id=$2""",
                asset_id,
                workspace_id,
            )
            if row is None:
                raise RuntimeError("The media asset does not exist in this workspace.")

            await connection.execute(
                """UPDATE public.processing_jobs
                   SET status='running', progress=5, started_at=coalesce(started_at, now()),
                       attempt_count=attempt_count+1, updated_at=now()
                   WHERE job_id=$1 AND asset_id=$2 AND workspace_id=$3""",
                job_id,
                asset_id,
                workspace_id,
            )
            await connection.execute(
                "UPDATE public.media_assets SET state='probing' WHERE asset_id=$1",
                asset_id,
            )

            bucket = os.environ["R2_BUCKET_NAME"]
            storage_key = str(row["storage_key"])
            s3 = _r2_client()

            with tempfile.TemporaryDirectory(prefix="clipro-probe-") as temp_dir:
                local_source = Path(temp_dir) / "source-video"
                local_thumbnail = Path(temp_dir) / "thumbnail.jpg"
                s3.download_file(bucket, storage_key, str(local_source))

                probe = probe_media(local_source)
                checksum = sha256_file(local_source)
                create_thumbnail(
                    local_source,
                    local_thumbnail,
                    duration_ms=probe["duration_ms"],
                )

                thumbnail_key = (
                    f"workspaces/{workspace_id}/{THUMBNAIL_ROOT}/{asset_id}/thumbnail.jpg"
                )
                s3.upload_file(
                    str(local_thumbnail),
                    bucket,
                    thumbnail_key,
                    ExtraArgs={
                        "ContentType": "image/jpeg",
                        "Metadata": {
                            "clipro-asset-id": asset_id,
                            "clipro-workspace-id": workspace_id,
                        },
                    },
                )

            probe["checksum_sha256"] = checksum
            probe["thumbnail_key"] = thumbnail_key
            encoded_probe = json.dumps(probe)

            await connection.execute(
                """UPDATE public.media_assets
                   SET state='ready',
                       duration_ms=$2,
                       width=$3,
                       height=$4,
                       frame_rate_num=$5,
                       frame_rate_den=$6,
                       video_codec=$7,
                       audio_codec=$8,
                       checksum_sha256=$9,
                       probe_metadata=$10::jsonb,
                       thumbnail_key=$11
                   WHERE asset_id=$1 AND workspace_id=$12""",
                asset_id,
                probe["duration_ms"],
                probe["width"],
                probe["height"],
                probe["frame_rate_num"],
                probe["frame_rate_den"],
                probe["video_codec"],
                probe["audio_codec"],
                checksum,
                encoded_probe,
                thumbnail_key,
                workspace_id,
            )
            await connection.execute(
                """UPDATE public.processing_jobs
                   SET status='succeeded', progress=100, result_json=$2::jsonb,
                       error_message=NULL, completed_at=now(), updated_at=now()
                   WHERE job_id=$1""",
                job_id,
                encoded_probe,
            )
            return {
                "job_id": job_id,
                "asset_id": asset_id,
                "status": "ready",
                "probe": probe,
            }
        except Exception as exc:
            try:
                await _set_job_failed(connection, job_id, asset_id, str(exc))
            except Exception:
                pass
            raise
        finally:
            await connection.close()

    return asyncio.run(run())


_MODEL_CACHE = None
_PROCESSOR_CACHE = None
MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"


def _load_vision_model():
    global _MODEL_CACHE, _PROCESSOR_CACHE
    if _MODEL_CACHE is None or _PROCESSOR_CACHE is None:
        import torch
        from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
        _PROCESSOR_CACHE = AutoProcessor.from_pretrained(MODEL_ID)
        _MODEL_CACHE = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            MODEL_ID, torch_dtype=torch.float16, device_map="auto"
        )
        _MODEL_CACHE.eval()
    return _MODEL_CACHE, _PROCESSOR_CACHE


def _extract_transcript(source: Path, workdir: Path) -> list[dict]:
    wav_path = workdir / "audio-16khz.wav"
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", str(wav_path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=900)
    if completed.returncode != 0 or not wav_path.exists() or wav_path.stat().st_size == 0:
        return []
    from faster_whisper import WhisperModel
    whisper = WhisperModel("small", device="cpu", compute_type="int8", cpu_threads=4)
    segments, _ = whisper.transcribe(
        str(wav_path), beam_size=3, vad_filter=True, condition_on_previous_text=False
    )
    transcript = []
    for segment in segments:
        value = segment.text.strip()
        if value:
            transcript.append({
                "start_ms": round(segment.start * 1000),
                "end_ms": round(segment.end * 1000),
                "text": value[:500],
            })
    del whisper
    return transcript


def _extract_frames(source: Path, workdir: Path, duration_ms: int) -> list[tuple[int, Path]]:
    interval = max(3.0, (duration_ms / 1000) / 17.0)
    pattern = workdir / "frame-%03d.jpg"
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-i", str(source), "-vf", f"fps=1/{interval:.3f},scale=640:-1",
        "-frames:v", "18", "-q:v", "4", str(pattern),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=300)
    if completed.returncode != 0:
        raise RuntimeError("FFmpeg could not extract visual samples from this video.")
    frames = sorted(workdir.glob("frame-*.jpg"))
    return [(round(index * interval * 1000), path) for index, path in enumerate(frames)]


def _run_highlight_model(frames: list[tuple[int, Path]], transcript: list[dict], duration_ms: int) -> list[dict]:
    import torch
    from qwen_vl_utils import process_vision_info
    from services.worker.app.highlight_analysis import parse_highlights
    model, processor = _load_vision_model()
    transcript_text = "\n".join(
        f"[{item['start_ms'] / 1000:.1f}s] {item['text']}" for item in transcript
    )
    if len(transcript_text) > 18000:
        transcript_text = transcript_text[:18000] + "\n[transcript truncated]"
    content = []
    for timestamp_ms, frame_path in frames:
        content.append({"type": "text", "text": f"Video frame at {timestamp_ms / 1000:.1f} seconds:"})
        content.append({"type": "image", "image": str(frame_path)})
    prompt = f"""You are Clipro, an expert short-form gaming video editor.
Analyze this authorized gameplay video using timestamped visual samples and transcript.
Find up to 8 genuinely compelling moments suitable for short-form clips. Prioritize clear action,
unexpected events, wins/fails, funny situations, suspense, strong reactions, and clear payoffs.
Do not invent events or infer details that are not visible or spoken. Estimate accurate source
boundaries from the frame and transcript timestamps. Each clip should normally be 12-45 seconds
and stay inside the source duration ({duration_ms / 1000:.1f}s). Avoid overlapping clips.
If there are no compelling moments, return an empty highlights array. Return ONLY JSON:
{{"highlights":[{{"start_seconds":12.0,"end_seconds":34.0,"title":"Short title","hook":"Opening hook","rationale":"Why it works","score":8.7}}]}}
Scores are 0-10. Include a few seconds before the payoff for context.
TRANSCRIPT:
{transcript_text or "[No speech transcript available]"}"""
    content.append({"type": "text", "text": prompt})
    messages = [{"role": "user", "content": content}]
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)],
        images=image_inputs, videos=video_inputs, padding=True, return_tensors="pt",
    ).to(model.device)
    with torch.inference_mode():
        generated = model.generate(**inputs, max_new_tokens=1200, do_sample=False)
    trimmed = [out[len(ids):] for ids, out in zip(inputs.input_ids, generated)]
    response = processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]
    return parse_highlights(response, duration_ms=duration_ms)


@app.function(
    image=analysis_image,
    gpu="T4",
    secrets=[modal.Secret.from_name(SECRET_NAME)],
    cpu=4,
    memory=16384,
    ephemeral_disk=50 * 1024,
    timeout=3600,
    retries=0,
    max_containers=1,
    scaledown_window=60,
)
def analyze_asset(job_id: str, asset_id: str, workspace_id: str) -> dict:
    async def run() -> dict:
        dsn, ssl_value = _database_url_and_ssl()
        connection = await asyncpg.connect(dsn=dsn, ssl=ssl_value)
        try:
            row = await connection.fetchrow(
                """SELECT asset_id, workspace_id, storage_key, duration_ms, state
                   FROM public.media_assets WHERE asset_id=$1 AND workspace_id=$2""",
                asset_id, workspace_id,
            )
            if row is None:
                raise RuntimeError("The media asset does not exist in this workspace.")
            if row["state"] != "ready" or not row["duration_ms"]:
                raise RuntimeError("The source must pass media validation before analysis.")
            await connection.execute(
                """UPDATE public.processing_jobs SET status='running', progress=5,
                   started_at=coalesce(started_at, now()), attempt_count=attempt_count+1,
                   updated_at=now() WHERE job_id=$1 AND asset_id=$2 AND workspace_id=$3""",
                job_id, asset_id, workspace_id,
            )
            with tempfile.TemporaryDirectory(prefix="clipro-analysis-") as temp_dir:
                workdir = Path(temp_dir)
                source = workdir / "source-video"
                _r2_client().download_file(os.environ["R2_BUCKET_NAME"], str(row["storage_key"]), str(source))
                await connection.execute("UPDATE public.processing_jobs SET progress=15, updated_at=now() WHERE job_id=$1", job_id)
                transcript = await asyncio.to_thread(_extract_transcript, source, workdir)
                await connection.execute("UPDATE public.processing_jobs SET progress=45, updated_at=now() WHERE job_id=$1", job_id)
                frames = await asyncio.to_thread(_extract_frames, source, workdir, int(row["duration_ms"]))
                if not frames:
                    raise RuntimeError("No visual samples could be extracted from this video.")
                await connection.execute("UPDATE public.processing_jobs SET progress=60, updated_at=now() WHERE job_id=$1", job_id)
                highlights = await asyncio.to_thread(_run_highlight_model, frames, transcript, int(row["duration_ms"]))
            result = {
                "analysis_version": "1.0", "model": MODEL_ID,
                "transcription_model": "Systran/faster-whisper-small",
                "duration_ms": int(row["duration_ms"]), "transcript": transcript[:500],
                "highlights": highlights, "sampled_frames": len(frames),
            }
            await connection.execute(
                """UPDATE public.processing_jobs SET status='succeeded', progress=100,
                   result_json=$2::jsonb, error_message=NULL, completed_at=now(), updated_at=now()
                   WHERE job_id=$1 AND asset_id=$3""",
                job_id, json.dumps(result), asset_id,
            )
            return {"job_id": job_id, "asset_id": asset_id, "status": "succeeded", **result}
        except Exception as exc:
            await connection.execute(
                """UPDATE public.processing_jobs SET status='failed', progress=100,
                   error_message=$2, completed_at=now(), updated_at=now() WHERE job_id=$1""",
                job_id, (str(exc) or "Highlight analysis failed.")[:500],
            )
            raise
        finally:
            await connection.close()
    return asyncio.run(run())
