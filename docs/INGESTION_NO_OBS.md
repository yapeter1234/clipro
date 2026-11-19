# Source acquisition: live streams, past broadcasts and uploaded videos

Clipro is a general-purpose clipping and editing studio. It supports source jobs from Twitch, Kick and YouTube, with separate acquisition rules for live streams and past broadcasts.

**The media workflow is deliberately browser-based:** capture a native clip or select an authorized source file on the platform, download/upload the file where supported, and submit it to Clipro. Clipro never assumes that a public player URL is a downloadable MP4.

## Source types

Every media job must declare exactly one source type:

1. `live_stream`: a moment captured while the creator is currently broadcasting.
2. `past_broadcast`: a moment captured from an archived livestream/VOD.
3. `uploaded_video`: a creator- or campaign-authorized video file supplied for automatic highlight discovery or manual editing.

The source type is separate from acquisition method. For example, a Twitch viewer-created clip from a VOD is `past_broadcast + viewer_native_clip_manual_download`.

## Platform capability matrix (viewer workflow)

| Platform | Live stream clip | Past broadcast/VOD clip | Viewer can download created clip | Full VOD download from another creator |
|---|---|---|---|---|
| Twitch | Yes, up to 60 sec | Yes, up to 60 sec | Yes, from Clips Manager | No viewer-wide full-VOD download |
| Kick | Yes, 10–180 sec | Yes, 10–180 sec | Yes, from clip page | No; Kick says only channel owners can download their own VOD |
| YouTube | Yes, if DVR/eligibility limits permit; clip may only be available after archive processing | Yes, 5–60 sec | A Clip is a shareable link/loop, not a normal MP4 export flow | Creator must supply an authorized source file for custom Clipro editing |

These are platform UI capabilities, not Clipro download APIs. They may be restricted by the creator's settings, regional/platform changes, stream/VOD status, follower/subscriber requirements, account restrictions or the original video's availability.

## Twitch — recommended for Diego's first campaign

Official help: https://help.twitch.tv/s/article/how-to-use-clips

Twitch says logged-in viewers may create clips of a channel's live streams and VODs when the streamer has enabled clipping and has not restricted it to followers/subscribers or blocked the viewer. Clips can be up to 60 seconds. A viewer can download clips they created through the Clips Manager.

### Live stream
1. Open the creator's live channel while signed in.
2. Use Twitch's Clip button/Clip Creator around the moment.
3. Trim to include the setup and payoff; keep within Twitch's 60-second clip limit.
4. Publish/create the native Twitch clip. This creates a Twitch clip asset; it is distinct from publishing a Short/Reel.
5. Find the clip under your Clips Manager, download the landscape or portrait file you created.
6. Upload that MP4 to Clipro and choose `Live stream` as the source type.

### Past broadcast
1. Open the creator's past broadcast/VOD.
2. Use the Clip button/Clip Creator on the VOD if the channel settings allow it.
3. Select the relevant moment and create the native clip.
4. Download the clip you created from Clips Manager.
5. Upload the MP4 to Clipro and choose `Past broadcast`.

### Important limits
- The user cannot use Twitch's editor-only Get Clips Download API from an ordinary viewer account.
- Do not use the Editor-only Create Clip From VOD API in the Diego pilot.
- Do not download arbitrary full VODs through undocumented player/HLS/GraphQL methods.
- Twitch native clip creation publishes a clip asset on Twitch. The user chooses when to create it; Clipro never creates it automatically.
- Twitch's portrait crop/layout may be adjusted in its Clip Manager; Clipro can also reframe the downloaded file after upload.

## Kick

Official help: https://help.kick.com/en/articles/7120566-how-to-create-clips-on-kick

Kick's official help says a logged-in viewer can create clips from live streams and VODs. Clips are 10–180 seconds. The viewer can download a clip they created from the clip page as an MP4.

### Live stream or VOD
1. Open the creator's live stream or VOD while signed in.
2. Click the Clip icon or use the documented keyboard shortcut.
3. Choose a moment between 10 and 180 seconds and create the clip.
4. Open the clip and download the MP4.
5. Upload it to Clipro with the correct source type.

Kick says viewers cannot download another channel's full VOD; use the native clip workflow or obtain a creator/campaign-supplied source file.

## YouTube

Official help: https://support.google.com/youtube/answer/10332730

YouTube Clips are public shareable excerpts from an eligible video/live stream. They are 5–60 seconds and play from the original watch page. They are not a general MP4 download mechanism for a third-party video.

For live streams:
- DVR must be enabled and the stream must satisfy YouTube's eligibility limits.
- Some clips are not playable until the live stream ends and the archive has uploaded.
- Live streams over the DVR window and certain long streams may be ineligible.

For Clipro's custom editing workflow, the user must upload an authorized source video file/excerpt supplied by the creator/campaign or otherwise lawfully available to them. A YouTube Clip URL alone is stored as a reference, not ingested as raw media.

## Browser upload to Clipro

The future browser dashboard must provide:
- Drag/drop MP4/MOV/WebM upload.
- Platform, channel URL, source type (live/past/uploaded) and source link fields.
- A checkbox/record for campaign or creator authorization and the allowed purpose.
- A clear status if only a platform Clip URL was supplied but no media file.
- File duration, resolution, frame rate, codec, audio stream and size inspection.
- User selection of a source range for long uploaded videos.
- Progress, retry and resumable upload for large files.
- Checksum, temporary storage key and retention/expiry.
- No arbitrary URL-to-video download button.

A public URL alone is never treated as a media file. Arbitrary server-side URL fetching is disabled to avoid SSRF, platform access bypass, and rights confusion.

## Multi-streamer and multi-campaign support

Clipro is not hard-coded to Diego. Each job selects a streamer/source profile and optionally a campaign profile.

- A streamer profile stores platform, channel identity, display name and optional creator-specific layout preferences.
- A campaign profile stores source restrictions, allowed game/topic, required CTA, captions/hashtags, disclosure, content restrictions, duration targets and post-publish analytics requirements.
- A style profile stores editing treatment (streamer/brainrot, documentary, clean captions, etc.).
- The rendering engine consumes the same normalized project schema regardless of platform or source type.

One creator's restrictions must not leak into another creator's job. For example, Diego's Twitch-only GTA rule must not restrict a Kick or YouTube campaign for another streamer.

## DiegoLoveless campaign mapping

- Platform: Twitch only.
- Channel: https://twitch.tv/diegoloveless
- Source types: live streams and past broadcasts.
- Acquisition: viewer-created Twitch native clip, manual download, then Clipro upload.
- No OBS relay.
- No Twitch Editor role or Editor-only API.
- English only.
- Must show Diego playing Grand Theft Auto content and preserve the actual GTA title shown.
- Required CTA: https://twitch.tv/diegoloveless, on-screen or in caption.
- Required hashtags: #GTA and #DiegoLoveless. Optional: #GrandTheftAuto and #Speedrun where relevant. Any game-specific hashtag must match the exact game title in the clip.
- Full rules are recorded in `docs/campaigns/diego-loveless-gta6.md` and `config/campaigns/diego-loveless-gta6.json`.

## What the pipeline can and cannot automate

After a file is uploaded, Clipro can automatically:
- inspect and transcribe it;
- find highlights in longer authorized source files;
- create the edit plan;
- generate captions, hook graphics, original narration, licensed music/SFX, transitions and motion;
- render, validate and return the MP4 for approval.

With manual viewer capture, Clipro cannot independently watch all raw frames of a third-party stream or automatically retrieve the original full VOD. The user must create/download a permitted native clip or provide an authorized source file first.

For future creators who grant broader API permissions or provide a media relay, additional acquisition modes can be enabled as explicit, separate integrations.
