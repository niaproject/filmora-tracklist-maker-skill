#!/usr/bin/env node
/**
 * Filmora .wfp project file parser
 * Usage: node parse.js <path-to-file.wfp> [options]
 *   --ext=<ext>          Output file extension (default: txt)
 *   --no-seq             Hide sequential numbers
 *   --min-duration=<sec> Exclude clips shorter than this (default: 10)
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const wfp = process.argv[2];
if (!wfp) {
  console.error('Usage: node parse.js <path-to-file.wfp> [--ext=txt] [--no-seq] [--min-duration=10]');
  process.exit(1);
}

// --- Parse options ---
const args = process.argv.slice(3);
const ext = (args.find(a => a.startsWith('--ext=')) || '--ext=txt').split('=')[1];
const showSeq = !args.includes('--no-seq');
const minDuration = parseFloat((args.find(a => a.startsWith('--min-duration=')) || '--min-duration=10').split('=')[1]);
const repeatBelow = parseInt((args.find(a => a.startsWith('--repeat-below=')) || '--repeat-below=0').split('=')[1]);

function unzipFile(zipPath, innerPath) {
  return execSync(`unzip -p "${zipPath}" "${innerPath}"`, { encoding: 'utf8' });
}

function formatTime(units) {
  // units are in 100-nanosecond intervals
  const totalSec = Math.floor(units / 10_000_000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  return `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`;
}

function clipDurationSec(clip) {
  if (clip.tlEnd !== undefined && clip.tlBegin !== undefined) {
    return (clip.tlEnd - clip.tlBegin) / 10_000_000;
  }
  if (clip.duration !== undefined) {
    return clip.duration / 10_000_000;
  }
  return Infinity; // unknown duration — include by default
}

// Track type constants
const TRACK_TYPE = { 1: 'video', 2: 'audio' };

// --- Load project_info.json ---
const info = JSON.parse(unzipFile(wfp, 'ProjectFolder/project_info.json'));

// --- Load medias_info.json ---
const mediasInfo = JSON.parse(unzipFile(wfp, 'ProjectFolder/Medias/medias_info.json'));

// --- Find timeline.wesproj ---
const listing = execSync(`unzip -l "${wfp}"`, { encoding: 'utf8' });
const tlMatch = listing.match(/ProjectFolder\/Medias\/[^\/]+\/timeline\.wesproj/);
if (!tlMatch) {
  console.error('Error: timeline.wesproj not found in the .wfp file.');
  process.exit(1);
}
const timeline = JSON.parse(unzipFile(wfp, tlMatch[0]));

// --- Build resource map: sourceUuid -> resource info ---
const resourceMap = {};
(timeline.resources || []).forEach(r => {
  resourceMap[r.sourceUuid] = r;
});

// --- Build media name map from medias_info ---
const mediaNames = {};
Object.values(mediasInfo.media_items || {}).forEach(m => {
  mediaNames[m.id] = m.name;
});

// --- Find main timeline ---
const mainTl = timeline.timelineInfos.find(t => t.timelineId === timeline.currentTimelineId);
if (!mainTl) {
  console.error('Error: Main timeline not found.');
  process.exit(1);
}

// --- Output ---
const projectName = info.project_file_name || path.basename(wfp, '.wfp');
const [fpsNum, fpsDen] = info.project_timeline_framerate || [30, 1];
const fps = fpsNum / fpsDen;
const [w, h] = info.project_timeline_resolution || [0, 0];
const totalDuration = formatTime(info.project_timeline_duration || 0);

const lines = [];
const out = (s = '') => lines.push(s);

out('='.repeat(60));
out(`Project : ${projectName}`);
out(`Duration: ${totalDuration}`);
out(`FPS     : ${fps}`);
out(`Res     : ${w}x${h}`);
out('='.repeat(60));

let audioTrackNum = 0;

mainTl.trackInfos.forEach((track) => {
  const type = TRACK_TYPE[track.trackType] || 'other';
  if (type !== 'audio') return;

  const allClips = (track.clipList || []).filter(c => c.tlBegin !== undefined);
  audioTrackNum++;

  if (audioTrackNum > 1) return; // only output the first audio track

  const clips = allClips.filter(c => clipDurationSec(c) >= minDuration);
  if (clips.length === 0) return; // skip if no clips pass the filter

  out('');
  out(`[AUDIO Track ${audioTrackNum}]`);
  let repeatAppended = false;
  clips.forEach((clip, ci) => {
    const num = ci + 1;
    if (repeatBelow > 0 && num >= repeatBelow) {
      if (!repeatAppended) {
        const seq = showSeq ? `${String(num).padStart(2)}. ` : '';
        out(`  ${seq}Repeat`);
        repeatAppended = true;
      }
      return;
    }
    const res = resourceMap[clip.sourceUuid];
    const rawName = res?.filename || clip.filename || '';
    const name = rawName ? path.basename(rawName, path.extname(rawName)) : '(unknown)';
    const start = formatTime(clip.tlBegin);
    const seq = showSeq ? `${String(num).padStart(2)}. ` : '';
    out(`  ${seq}${start}  ${name}`);
  });
});

out('');
out('='.repeat(60));

const output = lines.join('\n');
console.log(output);

const outPath = path.join(path.dirname(path.resolve(wfp)), path.basename(wfp, '.wfp') + '.' + ext);
fs.writeFileSync(outPath, output, 'utf8');
console.error(`\nSaved: ${outPath}`);
