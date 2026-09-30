import fs from 'node:fs';
import path from 'node:path';
import process from 'node:process';

const root = path.resolve(import.meta.dirname, '..');
const required = [
  'appinfo.json',
  'index.html',
  'styles.css',
  'app.js',
  'hls.min.js',
  'icon.png',
  'largeIcon.png',
  'splash.png'
];

const failures = [];
for (const file of required) {
  const filePath = path.join(root, file);
  if (!fs.existsSync(filePath) || fs.statSync(filePath).size === 0) {
    failures.push(`Missing or empty required file: ${file}`);
  }
}

const appInfo = JSON.parse(fs.readFileSync(path.join(root, 'appinfo.json'), 'utf8'));
const packageInfo = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const script = fs.readFileSync(path.join(root, 'app.js'), 'utf8');
const styles = fs.readFileSync(path.join(root, 'styles.css'), 'utf8');
const pngSignature = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function readPngDimensions(file) {
  const data = fs.readFileSync(path.join(root, file));
  if (!data.subarray(0, 8).equals(pngSignature)) {
    failures.push(`${file} is not a PNG`);
    return null;
  }
  return { width: data.readUInt32BE(16), height: data.readUInt32BE(20) };
}

if (appInfo.id !== 'app.tvviewer.webos') failures.push('Unexpected webOS application ID');
if (appInfo.type !== 'web' || appInfo.main !== 'index.html') failures.push('Invalid webOS web application entry point');
if (!Array.isArray(appInfo.requiredACG)) failures.push('requiredACG must be declared for LG submission checks');
if (appInfo.version !== packageInfo.version) failures.push('appinfo.json and package.json versions differ');
const icon = readPngDimensions('icon.png');
const largeIcon = readPngDimensions('largeIcon.png');
const splash = readPngDimensions('splash.png');
if (icon && (icon.width !== 80 || icon.height !== 80)) failures.push('icon.png must be 80x80');
if (largeIcon && (largeIcon.width !== 130 || largeIcon.height !== 130)) failures.push('largeIcon.png must be 130x130');
if (splash && (splash.width !== 1920 || splash.height !== 1080)) failures.push('splash.png must be 1920x1080');
if (appInfo.splashBackground !== 'splash.png') failures.push('splashBackground must reference splash.png');
if (!appInfo.iconColor) failures.push('iconColor is required for the launcher tile');
if (!appInfo.appDescription || appInfo.appDescription.length > 60) failures.push('appDescription must be 1-60 characters');
if (!html.includes('hls.min.js') || !html.includes('app.js')) failures.push('HTML does not include packaged scripts');
if (/https:\/\/cdn\.|unpkg\.com/i.test(html)) failures.push('Runtime code must not depend on a CDN');
if (!script.includes('FDROID_BUILD') && script.includes('/api/analytics')) failures.push('Unexpected analytics endpoint in webOS client');
if (!script.includes('handleRemoteKey') || !script.includes('moveFocus')) failures.push('Remote navigation implementation is missing');
if (!script.includes('handleWheel')) failures.push('Magic Remote wheel handling is missing');
if (/firstRunModal\.classList\.contains\('hidden'\)\)\s*return/.test(script)) failures.push('Back must exit from the first-run entry screen');
if (!script.includes('function exitApp()')) failures.push('Entry-screen Back exit handling is missing');
if (!script.includes('localStorage') || !script.includes('favorites')) failures.push('Local favorites support is missing');
if (!script.includes('STORE_CATEGORIES') || !script.includes('EXPLICIT_NAME_PATTERN')) failures.push('LG catalog content guard is missing');
if (script.includes('SUPABASE_KEY')) failures.push('Public Supabase value must not use a credential-like variable name');
if (!script.includes('SUPABASE_PUBLISHABLE_VALUE')) failures.push('Public Supabase value naming/documentation is missing');
if (!/button\s*\{[^}]*min-height:\s*7[5-9]px/s.test(styles)) failures.push('FHD buttons must be at least 75px high');
if (!/input,\s*\nselect\s*\{[^}]*height:\s*7[5-9]px/s.test(styles)) failures.push('FHD inputs must be at least 75px high');
for (const size of styles.matchAll(/font-size:\s*(\d+)px/g)) {
  if (Number(size[1]) < 20) failures.push(`FHD text size is below 20px: ${size[1]}px`);
}

if (failures.length) {
  console.error(failures.map((failure) => `ERROR: ${failure}`).join('\n'));
  process.exit(1);
}

console.log(`Validated ${appInfo.id} ${appInfo.version}`);
