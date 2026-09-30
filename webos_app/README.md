# TV Viewer for LG webOS TV

Standalone ten-foot TV client for LG webOS 5.0 and newer. It reads the public, RLS-protected
TV Viewer channel catalog directly from Supabase and stores favorites only in
the television's local storage.

## Build

Requirements: Node.js 20 or newer.

```powershell
Set-Location webos_app
npm ci
npm run validate
npm run package
```

Two packages are written for LG's supported graphics resolutions:

- `webos_app\dist\app.tvviewer.webos_2.25.0_1080p_all.ipk`
- `webos_app\dist\app.tvviewer.webos_2.25.0_720p_all.ipk`

Only the eight runtime files are staged into each package; Node dependencies
and development scripts are excluded.

The same packages are published as versioned assets on the TV Viewer GitHub
Release so the LG client can be installed through Developer Mode before Seller
Lounge certification is complete.

## Test on an LG TV

Enable Developer Mode on the television and configure it using the official
webOS CLI:

```powershell
ares-setup-device
ares-install -d <device-name> .\dist\app.tvviewer.webos_2.25.0_1080p_all.ipk
ares-launch -d <device-name> app.tvviewer.webos
ares-inspect -d <device-name> -a app.tvviewer.webos --open
```

Remote navigation supports the directional pad, OK, Back, Play/Pause, Stop,
and Magic Remote pointer clicks.

## Seller Lounge readiness

The repository build produces a technically valid IPK, but LG store
publication still requires:

- An LG Seller Lounge account with app ownership details.
- Physical-device testing across the supported webOS TV range.
- Store icon, screenshots, territories, age rating, privacy URL, support URL,
  and an App Self Checklist.
- Confirmation that listed streams and territories comply with content rights.
- Manual submission and LG certification approval.

The application performs no analytics and does not require an account. It
displays a first-run content and privacy notice before the first network call.
Prepared listing copy and the Seller Lounge checklist are in
`store-listings\lg-webos\README.md`.
