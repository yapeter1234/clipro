# Clipro editing style guide

This document defines the default editorial behavior. A campaign or user-selected template may override a default, but rights, accuracy, caption safety and approval rules cannot be overridden.

## Editorial objective

Make the source moment understandable to a viewer who did not watch the stream, retain the creator's meaning, and build toward a satisfying payoff. Optimize for retention without misleading edits or gratuitous effects.

## Narrative structure

A short may use the following structure when the source supports it:

1. **Hook (0–2 seconds):** intriguing original narration, a short truthful text hook, or a very short preview of the moment.
2. **Context (2–5 seconds):** enough information to understand what is happening; avoid a long explanatory intro.
3. **Build (middle):** preserve the important sequence; remove dead air and repetition; use purposeful reframing/punch-ins.
4. **Payoff:** show the complete reaction, result or statement.
5. **Optional ending:** a brief campaign CTA only if the campaign requires or permits it and it does not interrupt the payoff.

Do not force this structure when it would distort chronology or omit necessary context. Do not fabricate suspense, quotes, reactions or outcomes.

## Motion and transitions

- Prefer clean cuts for dialogue and quick reaction timing.
- Use crossfades for genuine scene/time changes, not between every sentence.
- Use zoom/punch-in to emphasize an actual reaction, reveal or important phrase.
- Use whip-pan, wipe, glitch and speed ramp sparingly and only where motion/context supports them.
- Use animated overlays and title cards to communicate context, not obscure the subject.
- Never cover faces, important UI/gameplay, or platform safe zones.
- Avoid over-sharpening, excessive shake, illegible glow, and strobing effects.

## Captions

- Generate word/phrase timestamps from ASR, then align to the final edit.
- Correct names, game terms and campaign-specific vocabulary using source context.
- Use one or two lines at a time, strong contrast, readable stroke/shadow and consistent placement.
- Emphasize only key words; do not animate every word with distracting motion.
- Avoid UI safe zones and keep captions away from faces and critical gameplay.
- Keep original-language captions by default. Translation is a separate track and must preserve meaning.
- When ASR confidence is low, mark the cue for review rather than silently guessing.

## Voiceover

- Narration is optional and should add context, not repeat every line the streamer says.
- Use an original narrator identity; do not imitate or clone the creator without documented consent.
- Keep narration on a separate audio track and identify it as narration in the edit plan.
- Use a short hook or context bridge; do not talk over the main reaction or important dialogue.
- Match voice tone to content, not to a real-person impersonation.
- Generate a transcript and align narration captions where requested.

## Music and sound effects

- Every music and SFX asset must include source/license/attribution metadata.
- Use music only where the campaign and platform license permit.
- Duck music under dialogue and narration; automatically reduce or remove it where speech is important.
- SFX should support an actual beat (impact, transition, reveal), not mask source audio.
- Keep streamer speech intelligible; normalize the final mix and check true peak.
- Never assume music heard in the livestream is licensed for a separate repost.

## Video composition

- Primary profile: 9:16, 1080x1920.
- Preserve source aspect ratio; use blurred background/contain/crop intelligently.
- Prefer facecam/gameplay split layouts when both are important.
- Reframe only when the subject can be tracked reliably; otherwise choose a stable crop.
- Preserve text and game HUD when they are relevant to the moment.
- Create horizontal and square output profiles from the same timeline schema later.

## Quality assurance

Every render must be checked for:
- output resolution, frame rate, container, codec and duration;
- black frames, freeze frames and unintended gaps;
- audio/video synchronization;
- caption timing, safe areas and spelling confidence;
- narration intelligibility and music ducking;
- clipping/true peak/loudness;
- missing assets, license metadata and attribution;
- no unauthorized voice imitation;
- no misleading chronology or fabricated narration;
- campaign-specific constraints.

A failed QA check should prevent the candidate entering the approval queue until corrected or explicitly marked as requiring user review.
