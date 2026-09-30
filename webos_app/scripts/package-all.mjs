import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const root = path.resolve(import.meta.dirname, '..');
const dist = path.join(root, 'dist');
const cli = path.join(root, 'node_modules', '@webos-tools', 'cli', 'bin', 'ares-package.js');
const runtimeFiles = [
  'index.html',
  'styles.css',
  'app.js',
  'hls.min.js',
  'icon.png',
  'largeIcon.png',
  'splash.png'
];
const variants = [
  { label: '1080p', resolution: '1920x1080' },
  { label: '720p', resolution: '1280x720' }
];

fs.rmSync(dist, { recursive: true, force: true });
fs.mkdirSync(dist, { recursive: true });

const baseAppInfo = JSON.parse(fs.readFileSync(path.join(root, 'appinfo.json'), 'utf8'));

for (const variant of variants) {
  const stage = path.join(dist, `stage-${variant.label}`);
  const output = path.join(dist, `package-${variant.label}`);
  fs.mkdirSync(stage, { recursive: true });
  fs.mkdirSync(output, { recursive: true });

  for (const file of runtimeFiles) {
    fs.copyFileSync(path.join(root, file), path.join(stage, file));
  }

  fs.writeFileSync(
    path.join(stage, 'appinfo.json'),
    `${JSON.stringify({ ...baseAppInfo, resolution: variant.resolution }, null, 2)}\n`
  );

  execFileSync(process.execPath, [cli, stage, '--outdir', output], {
    cwd: root,
    stdio: 'inherit'
  });
  const generated = fs.readdirSync(output).find((file) => file.endsWith('.ipk'));
  if (!generated) throw new Error(`webOS CLI did not create the ${variant.label} IPK`);

  const target = path.join(
    dist,
    `app.tvviewer.webos_${baseAppInfo.version}_${variant.label}_all.ipk`
  );
  fs.renameSync(path.join(output, generated), target);
  console.log(`Created ${path.basename(target)}`);
}
