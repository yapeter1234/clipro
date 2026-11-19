# Timeline project

This package owns the source-agnostic editing contract shared by:
- the live-stream clipping pipeline;
- the future manual/non-live video editor;
- the Remotion composition renderer;
- the FFmpeg finalization pipeline.

The JSON Schema lives in `schema.json`. Use integer milliseconds for all time values in v1 to avoid float drift. Source segments use source in/out times; timeline clips use timeline start plus source trim and playback rate.

## Core concepts

- **Project:** one editable composition and export profile.
- **Asset:** a video, audio, image, font or graphic, referenced by stable ID.
- **Track:** ordered video, audio, caption or overlay lane.
- **Clip:** a use of an asset at a timeline position with source trims, speed, transform and effects.
- **Transition:** an explicit effect between two adjacent clips.
- **Caption cue:** timed text with optional word emphasis.
- **Narration:** a separate generated audio asset/track and script metadata.
- **Mix:** per-track gain, fades, ducking and mastering target.
- **Export:** dimensions, fps, codec and audio settings.

No binary data or permanent public URLs belong in the project file. The renderer resolves asset IDs through an authorized asset service.

## Compatibility rules

- Every project has a `schema_version`.
- Breaking changes require a new major schema version and migration.
- Unknown effect types are rejected by the renderer; do not silently execute arbitrary code.
- Model output is untrusted. Validate it before saving or rendering.
- A render references the exact project revision and asset checksums used.
- Approval applies only to that exact render; changing the timeline invalidates approval.

## Example

See `examples/streamer_reaction.json` for an illustrative project with a hook, source clip, captions, voiceover, music ducking and transitions. It contains references, not media files.
