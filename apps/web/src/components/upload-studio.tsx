"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Uppy from "@uppy/core";
import AwsS3, { type AwsBody } from "@uppy/aws-s3";
import { createClient as createSupabaseClient } from "@/lib/supabase/client";
import "@uppy/core/css/style.min.css";

type Platform = "twitch" | "kick" | "youtube" | "upload";
type SourceKind = "live_stream" | "past_broadcast" | "uploaded_video";
type RightsStatus = "creator_authorized" | "user_owned" | "licensed" | "public_domain" | "pending_review";
type FileMeta = Record<string, unknown>;
type SourceMetadata = {
  platform: Platform;
  source_kind: SourceKind;
  streamer_id: string;
  campaign_id: string;
  source_url: string;
  rights_status: RightsStatus;
  permission_confirmed: boolean;
};

const MAX_FILE_SIZE = 20 * 1024 * 1024 * 1024;
const API_BASE = (process.env.NEXT_PUBLIC_CLIPRO_API_URL ?? "").replace(/\/$/, "");

async function apiRequest<T>(path: string, token: string, body?: unknown): Promise<T> {
  if (!API_BASE) throw new Error("NEXT_PUBLIC_CLIPRO_API_URL is not configured.");
  const response = await fetch(API_BASE + path, {
    method: body === undefined ? "GET" : "POST",
    headers: { Authorization: "Bearer " + token, ...(body === undefined ? {} : { "Content-Type": "application/json" }) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    let detail = "The Clipro API request failed.";
    try {
      const data = await response.json();
      detail = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail ?? data);
    } catch { /* keep generic error */ }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

async function getAccessToken() {
  const result = await createSupabaseClient().auth.getSession();
  const token = result.data.session?.access_token;
  if (result.error || !token) throw new Error("Your sign-in session expired. Sign in again and retry.");
  return token;
}

function acquisitionMode(meta: SourceMetadata) {
  if ((meta.platform === "twitch" || meta.platform === "kick") && meta.source_kind !== "uploaded_video") {
    return "viewer_native_clip_manual_download";
  }
  return "authorized_source_file";
}

function formatBytes(bytes: number) {
  if (bytes >= 1024 ** 3) return (bytes / 1024 ** 3).toFixed(2) + " GB";
  if (bytes >= 1024 ** 2) return (bytes / 1024 ** 2).toFixed(1) + " MB";
  return Math.max(1, Math.round(bytes / 1024)) + " KB";
}

export default function UploadStudio({ workspaceId }: { workspaceId: string }) {
  const [platform, setPlatform] = useState<Platform>("twitch");
  const [sourceKind, setSourceKind] = useState<SourceKind>("live_stream");
  const [streamerId, setStreamerId] = useState("diegoloveless");
  const [campaignId, setCampaignId] = useState("diego-gta");
  const [sourceUrl, setSourceUrl] = useState("https://www.twitch.tv/diegoloveless");
  const [rightsStatus, setRightsStatus] = useState<RightsStatus>("pending_review");
  const [permissionConfirmed, setPermissionConfirmed] = useState(false);
  const [metadataReady, setMetadataReady] = useState(false);
  const [selectedName, setSelectedName] = useState("");
  const [selectedSize, setSelectedSize] = useState(0);
  const [progress, setProgress] = useState(0);
  const [statusMessage, setStatusMessage] = useState("");
  const [assetId, setAssetId] = useState("");
  const [uploading, setUploading] = useState(false);
  const metadataRef = useRef<SourceMetadata>({
    platform: "twitch", source_kind: "live_stream", streamer_id: "diegoloveless",
    campaign_id: "diego-gta", source_url: "https://www.twitch.tv/diegoloveless",
    rights_status: "pending_review", permission_confirmed: false,
  });
  const assetIdRef = useRef("");

  const uppy = useMemo(() => {
    const instance = new Uppy<FileMeta, AwsBody>({
      id: "clipro-source-upload",
      autoProceed: false,
      restrictions: { maxNumberOfFiles: 1, maxFileSize: MAX_FILE_SIZE, allowedFileTypes: ["video/*", ".mkv"] },
    });

    instance.use(AwsS3, {
      shouldUseMultipart: () => true,
      getChunkSize: () => 32 * 1024 * 1024,
      limit: 1,
      createMultipartUpload: async file => {
        const token = await getAccessToken();
        const meta = metadataRef.current;
        const result = await apiRequest<{ upload_id: string; key: string; asset_id: string }>("/api/v1/uploads", token, {
          workspace_id: workspaceId,
          original_filename: file.name,
          content_type: file.type || "application/octet-stream",
          file_size_bytes: file.size ?? 0,
          platform: meta.platform,
          source_kind: meta.source_kind,
          acquisition_mode: acquisitionMode(meta),
          streamer_id: meta.streamer_id.trim() || null,
          campaign_id: meta.campaign_id.trim() || null,
          source_url: meta.source_url.trim() || null,
          permission_confirmed: meta.permission_confirmed,
          rights_status: meta.rights_status,
        });
        assetIdRef.current = result.asset_id;
        return { uploadId: result.upload_id, key: result.key };
      },
      signPart: async (_file, part) => {
        const token = await getAccessToken();
        return apiRequest<{ url: string }>("/api/v1/uploads/sign-part", token, {
          uploadId: part.uploadId, key: part.key, partNumber: part.partNumber,
        });
      },
      listParts: async (_file, part) => {
        const token = await getAccessToken();
        const result = await apiRequest<{ parts: Array<{ PartNumber: number; Size: number; ETag: string }> }>(
          "/api/v1/uploads/list-parts", token, { uploadId: part.uploadId, key: part.key },
        );
        return result.parts;
      },
      completeMultipartUpload: async (_file, data) => {
        const token = await getAccessToken();
        const result = await apiRequest<{ asset_id: string }>("/api/v1/uploads/complete", token, {
          uploadId: data.uploadId, key: data.key, parts: data.parts,
        });
        assetIdRef.current = result.asset_id;
        return { location: "clipro://asset/" + result.asset_id };
      },
      abortMultipartUpload: async (_file, data) => {
        const token = await getAccessToken();
        await apiRequest("/api/v1/uploads/abort", token, { uploadId: data.uploadId, key: data.key });
      },
    });
    return instance;
  }, [workspaceId]);

  useEffect(() => {
    const progressHandler = (_file: unknown, value: { bytesUploaded: number; bytesTotal: number }) => {
      if (value.bytesTotal > 0) setProgress(Math.round(value.bytesUploaded / value.bytesTotal * 100));
    };
    const uploadHandler = () => { setUploading(true); setStatusMessage("Uploading video parts directly to private storage…"); };
    const completeHandler = (result: { successful: unknown[]; failed: unknown[] }) => {
      setUploading(false);
      if (result.failed.length) setStatusMessage("Upload incomplete. Review the error and retry.");
      else if (result.successful.length) {
        setAssetId(assetIdRef.current);
        setProgress(100);
        setStatusMessage("Source uploaded successfully. Media probing is the next step.");
      }
    };
    const errorHandler = (error: Error) => { setUploading(false); setStatusMessage(error.message || "Upload failed."); };

    uppy.on("upload", uploadHandler);
    uppy.on("upload-progress", progressHandler);
    uppy.on("complete", completeHandler);
    uppy.on("error", errorHandler);

    return () => {
      uppy.off("upload", uploadHandler);
      uppy.off("upload-progress", progressHandler);
      uppy.off("complete", completeHandler);
      uppy.off("error", errorHandler);
      uppy.destroy();
    };
  }, [uppy]);

  function saveMetadata(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    metadataRef.current = { platform, source_kind: sourceKind, streamer_id: streamerId, campaign_id: campaignId, source_url: sourceUrl, rights_status: rightsStatus, permission_confirmed: permissionConfirmed };
    setMetadataReady(true);
    setStatusMessage("Source details saved. Choose your video below.");
  }

  function chooseFile(file?: File) {
    if (!file) return;
    if (file.size > MAX_FILE_SIZE) { setStatusMessage("This file exceeds Clipro's 20 GB source limit."); return; }
    uppy.getFiles().forEach(existing => uppy.removeFile(existing.id));
    try {
      uppy.addFile({ name: file.name, type: file.type || "application/octet-stream", data: file, source: "Local" });
      setSelectedName(file.name);
      setSelectedSize(file.size);
      setAssetId("");
      setProgress(0);
      setStatusMessage("Video selected. Start upload when you're ready.");
    } catch (error) {
      setStatusMessage(error instanceof Error ? error.message : "Could not add this file.");
    }
  }

  async function startUpload() {
    if (!metadataReady) return setStatusMessage("Save the source details first.");
    if (!permissionConfirmed || rightsStatus === "pending_review") return setStatusMessage("Confirm source permission and rights basis first.");
    if (!uppy.getFiles().length) return setStatusMessage("Choose a video file first.");
    setUploading(true);
    setStatusMessage("Preparing secure multipart upload…");
    try {
      const result = await uppy.upload();
      if (result.failed.length) { setUploading(false); setStatusMessage("Some upload steps failed. You can retry."); }
    } catch (error) {
      setUploading(false);
      setStatusMessage(error instanceof Error ? error.message : "Upload failed.");
    }
  }

  const youtube = platform === "youtube";
  return (
    <div className="studio-grid" id="new-upload">
      <div className="form-column">
        <section className="surface-card">
          <div className="card-header"><div className="card-step">1</div><div><h2>Source details</h2><p>Tell Clipro where the footage came from.</p></div><span className="card-status">REQUIRED</span></div>
          <form className="source-form" onSubmit={saveMetadata}>
            <div className="field-grid">
              <div className="field"><label htmlFor="platform">Source platform</label>
                <select id="platform" value={platform} onChange={event => {
                  const next = event.target.value as Platform;
                  setPlatform(next);
                  if (next === "upload") setSourceKind("uploaded_video");
                  setMetadataReady(false);
                }}>
                  <option value="twitch">Twitch</option><option value="kick">Kick</option><option value="youtube">YouTube</option><option value="upload">Direct video upload</option>
                </select>
                <small>{youtube ? "Upload an authorized source file; a YouTube Clip URL alone cannot be edited." : "Choose where the original footage was captured."}</small>
              </div>
              <div className="field"><label htmlFor="source-kind">Source type</label>
                <select id="source-kind" value={sourceKind} onChange={event => { setSourceKind(event.target.value as SourceKind); setMetadataReady(false); }}>
                  <option value="live_stream">Clip from a live stream</option><option value="past_broadcast">Clip from a past broadcast</option><option value="uploaded_video">Full / already uploaded video</option>
                </select><small>All source types use the same editing engine.</small>
              </div>
              <div className="field"><label htmlFor="streamer-id">Streamer profile ID <span className="optional">OPTIONAL</span></label><input id="streamer-id" value={streamerId} onChange={event => { setStreamerId(event.target.value); setMetadataReady(false); }} placeholder="e.g. diegoloveless" /></div>
              <div className="field"><label htmlFor="campaign-id">Campaign ID <span className="optional">OPTIONAL</span></label><input id="campaign-id" value={campaignId} onChange={event => { setCampaignId(event.target.value); setMetadataReady(false); }} placeholder="e.g. diego-gta" /></div>
              <div className="field field-full"><label htmlFor="source-url">Original stream / clip URL <span className="optional">REFERENCE ONLY</span></label><input id="source-url" type="url" value={sourceUrl} onChange={event => { setSourceUrl(event.target.value); setMetadataReady(false); }} placeholder="https://…" /><small>Stored as metadata only. Clipro never downloads video from this URL.</small></div>
            </div>
            <div className="rights-panel">
              <div className="rights-heading"><span className="shield">✓</span><div><strong>Source rights and permission</strong><p>Confirm you are allowed to edit and publish this footage.</p></div></div>
              <div className="field rights-select"><label htmlFor="rights-status">Rights basis</label><select id="rights-status" value={rightsStatus} onChange={event => { setRightsStatus(event.target.value as RightsStatus); setMetadataReady(false); }}><option value="pending_review">Select rights basis</option><option value="creator_authorized">Creator / campaign authorized</option><option value="user_owned">I own this video</option><option value="licensed">Licensed for this use</option><option value="public_domain">Public domain</option></select></div>
              <label className="checkbox-row"><input type="checkbox" checked={permissionConfirmed} onChange={event => { setPermissionConfirmed(event.target.checked); setMetadataReady(false); }} /><span>I have permission to edit and publish this source under the applicable platform and campaign rules.</span></label>
            </div>
            <div className="form-actions"><button className="primary-button" type="submit">Save source details <span>→</span></button>{metadataReady && <span className="saved-label">✓ Details saved</span>}</div>
          </form>
        </section>

        <section className={"surface-card upload-card " + (!metadataReady ? "locked" : "")}>
          <div className="card-header"><div className="card-step">2</div><div><h2>Upload your video</h2><p>MP4, MOV, M4V, WebM or MKV · up to 20 GB</p></div><span className={"card-status " + (metadataReady ? "ready" : "")}>{metadataReady ? "READY" : "LOCKED"}</span></div>
          {!metadataReady ? <div className="locked-hint">Save the source details above to unlock upload.</div> : (
            <div className="upload-drop-area">
              <div className="upload-symbol">↑</div>
              <strong>{selectedName || "Drop a video here, or browse files"}</strong>
              <p>{selectedName ? formatBytes(selectedSize) + " · Ready to upload" : "Choose a clip or authorized source video from your device."}</p>
              <label className="file-picker-button">Browse video<input type="file" accept="video/*,.mkv" onChange={event => chooseFile(event.currentTarget.files?.[0])} disabled={uploading} /></label>
              {selectedName && !assetId && <button className="primary-button upload-start-button" type="button" onClick={startUpload} disabled={uploading}>{uploading ? "Uploading…" : "Start secure upload"} <span>→</span></button>}
              {uploading && <div className="progress-wrap"><div className="progress-label"><span>Uploading parts</span><strong>{progress}%</strong></div><div className="progress-track"><div className="progress-fill" style={{ width: progress + "%" }} /></div></div>}
            </div>
          )}
          {statusMessage && <div className="upload-status">{statusMessage}</div>}
          {assetId && <div className="asset-result"><span className="asset-check">✓</span><div><strong>Source stored successfully</strong><small>Asset ID: {assetId}</small></div></div>}
        </section>
      </div>
      <aside className="guide-column">
        <section className="guide-card"><div className="guide-label">SOURCE GUIDE</div><h3>How to get your clip</h3>
          <div className="guide-step"><span>01</span><div><strong>Create or select the source</strong><p>{platform === "kick" ? "Use Kick's native clip tool on a live stream or past broadcast." : youtube ? "Use a source file supplied by the creator or campaign." : platform === "upload" ? "Choose a video you own or are authorized to edit." : "Create a Twitch clip while live or from a VOD, when clipping is enabled."}</p></div></div>
          <div className="guide-step"><span>02</span><div><strong>Get the video file</strong><p>{platform === "twitch" ? "Download a clip you created from Twitch Clips Manager." : platform === "kick" ? "Download a clip you created from its Kick clip page." : "Select the authorized source file."}</p></div></div>
          <div className="guide-step"><span>03</span><div><strong>Upload it here</strong><p>Clipro stores your file privately and validates the actual media before AI analysis starts.</p></div></div>
          <a className="guide-link" href={platform === "kick" ? "https://kick.com" : youtube ? "https://www.youtube.com" : "https://www.twitch.tv/diegoloveless/videos"} target="_blank" rel="noreferrer">Open {platform === "kick" ? "Kick" : youtube ? "YouTube" : "Twitch"} <span>↗</span></a>
        </section>
        <section className="pipeline-card"><div className="guide-label">WHAT HAPPENS NEXT</div><h3>From footage to finished edit</h3>
          <div className="pipeline-item active"><span className="pipeline-dot" /><div><strong>Source intake</strong><small>Metadata and original video</small></div><em>NOW</em></div>
          <div className="pipeline-item"><span className="pipeline-dot" /><div><strong>Media validation</strong><small>Codec, duration, audio and proxy</small></div></div>
          <div className="pipeline-item"><span className="pipeline-dot" /><div><strong>AI moment analysis</strong><small>Transcription, context and highlights</small></div></div>
          <div className="pipeline-item"><span className="pipeline-dot" /><div><strong>Professional editing</strong><small>Captions, motion, sound and reframing</small></div></div>
          <div className="pipeline-item"><span className="pipeline-dot" /><div><strong>Your review</strong><small>Approve or request another version</small></div></div>
        </section>
        <div className="privacy-card"><span>◈</span><div><strong>Private by default</strong><p>Uploads are private. Clipro will not publish or share anything on your behalf.</p></div></div>
      </aside>
    </div>
  );
}
