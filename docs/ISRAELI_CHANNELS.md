# Israeli Channels Audit

Audit date: 2026-07-05


## Summary

- Israeli rows in Supabase: **119**
- Validated as working from this environment: **73**
- Broken/unreachable from this environment: **46**
- Explicit geo-block/forbidden responses: **2**
- New channels added: **0** (no stable new public streams were validated, and anonymous writes to `channels` are currently blocked by Supabase RLS).
- Persistent DB fixes applied: **0**. I identified multiple repair candidates, but the provided publishable key cannot modify the `channels` table in its current policy state.

## Update attempt result

- `PATCH /rest/v1/channels?...` returned `204`, but follow-up `GET` requests showed the rows unchanged.
- `POST /rest/v1/channels` with `Prefer: resolution=merge-duplicates` returned `401` / `42501` (`new row violates row-level security policy`).
- `rpc/promote_channel_source` is also unusable against the current schema: it failed with `400` because the function still tries to update a removed `channels.url` column while the table now stores `urls`.
- Result: audit findings below are accurate, but DB corrections need either a service-role key or a fixed maintenance RPC.

## Key channel findings

- **Kan 11:** Working variants exist in DB (`Kan 11 News`, `Kan 11 Subtitled`, `Kan 11 4K`). Broken legacy entries still point at deprecated Kan hosts.
- **Kan Kids / Educational:** Working via MedOne CDN and legacy `kan23.media.kan.org.il` URL.
- **Kan Bet:** Canonical working row is `Kan Bet / Reshet Bet` on MedOne CDN; legacy `Kan Bet` row still points at a dead host.
- **Kan Moreshet:** Working canonical row exists; two legacy Hebrew-name rows still point at dead icy endpoints.
- **Reshet 13:** Working on both `reshet.g-mana.live` and CloudFront variants. Legacy `IL: Reshet 13` skylogic entry is dead.
- **Keshet 12 / N12:** No stable public static URL in DB. Official live page is `https://www.n12.co.il/live/`, but stream URLs are tokenized Akamai manifests and the unsigned paths return 403 from this environment.
- **Channel 14 / Now 14:** Working rows exist (`Channel 14`, `Channel 14 Alt`). Public `now14.g-mana.live` URL returned 503/404 during validation.
- **Knesset Channel:** Working canonical row exists on `kneset.gostreaming.tv`; old contact.gostreaming and skylogic rows are dead.
- **i24NEWS:** Hebrew has a working public stream candidate (`https://i24newshebrew-cdn.encoders.immergo.tv/master.m3u8`), but existing DB rows still point at dead/geo-blocked URLs. English/Arabic/French public DB URLs are dead; no stable replacement was validated.
- **Channel 10 Business:** Working.
- **Sport 5:** Only `Sport 5 Studio` validated. Main `YES SPORT 5` / `YES SPORT 5 PLUS HD` rows are dead, and no stable public replacement was confirmed.
- **Makan 33:** Working canonical MedOne CDN row exists; one flutter-m3u legacy row points at a dead `makan.media.kan.org.il` host.

## Proposed replacements (not persisted)

- **Israel: Kan 11** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11/live.livx/playlist.m3u8`
- **KAN 11 Israel (1080p)** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11/live.livx/playlist.m3u8`
- **Kan Bet** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_reshet_bet/live.livx/playlist.m3u8`
- **Hala TV** → `https://stream.panet.com/edge/halaTV/playlist.m3u8`
- **IL: Knesset Channel** → `https://kneset.gostreaming.tv/p2-kneset/_definst_/myStream/index.m3u8`
- **IL: Reshet 13** → `https://reshet.g-mana.live/media/87f59c77-03f6-4bad-a648-897e095e7360/mainManifest.m3u8`
- **i24NEWS Hebrew** → `https://i24newshebrew-cdn.encoders.immergo.tv/master.m3u8`
- **88FM / Kan 88** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_88/live.livx/playlist.m3u8`
- **Kan Gimel** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_gimel/live.livx/playlist.m3u8`
- **Kan Moreshet** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_moreshet/live.livx/playlist.m3u8`
- **Kan Tarbut** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_tarbut/live.livx/playlist.m3u8`
- **Kan Kol Hamuzika** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_kol_hamuzika/live.livx/playlist.m3u8`
- **Kan Reka** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_reka/live.livx/playlist.m3u8`
- **Radio Makan** → `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/radio_makan/live.livx/playlist.m3u8`
- **100FM DJ Set / Hip Hop / K-Pop / TikTok (flutter-m3u duplicates)** → `Use the case-correct StreamGates URLs already present in the matching iptv-org rows.`
- **Keshet 12 / N12** → `Official Akamai patterns discovered, but all stable unsigned URLs returned 403 and tokenized URLs expire quickly; manual/session-based extraction from `https://www.n12.co.il/live/` is still required.`

## Remaining broken / blocked rows

| Channel | Source | Failure | Primary URL |
|---|---|---|---|
| 100FM DJ Set | flutter-m3u | http_error | `https://gb25.streamgates.net/radios-audio/100DJSet/playlist.m3u8` |
| 100FM Hip Hop | flutter-m3u | http_error | `https://gb25.streamgates.net/radios-audio/100HipHop/playlist.m3u8` |
| 100FM K-Pop | flutter-m3u | http_error | `https://gb25.streamgates.net/radios-audio/100KPop/playlist.m3u8` |
| 100FM TikTok | flutter-m3u | http_error | `https://gb25.streamgates.net/radios-audio/100TikTok/playlist.m3u8` |
| 88FM | flutter-m3u | connection_error | `https://kan88.media.kan.org.il/hls/live/2024812/2024812/kan88_mp3/chunklist.m3u8` |
| Big Brother Israel | flutter-m3u | connection_error | `https://d2lckchr9cxrss.cloudfront.net/out/v1/c73af7694cce4767888c08a7534b503c/index.m3u8` |
| Channel 13 (720p) [Not 24/7] | flutter-m3u | connection_error | `https://stream.theyraonline.com/live/channel13@live/index.m3u8` |
| Diki Radio | iptv-org | connection_error | `https://diki.mediacast.co.il/diki` |
| Hala TV | flutter-m3u | timeout | `https://gstream4.panet.co.il/edge/halaTV/chunks.m3u8` |
| i24NEWS Arabic | iptv-org | http_error | `https://video.i24news.tv/live/i24news-ar/index.m3u8` |
| i24NEWS English | iptv-org | http_error | `https://video.i24news.tv/live/i24news-en/index.m3u8` |
| i24NEWS French | iptv-org | http_error | `https://video.i24news.tv/live/i24news-fr/index.m3u8` |
| i24NEWS Hebrew | iptv-org | http_error | `https://video.i24news.tv/live/i24news-he/index.m3u8` |
| i24NEWS Hebrew | flutter-m3u | geo_or_forbidden | `https://bcovlive-a.akamaihd.net/d89ede8094c741b7924120b27764153c/eu-central-1/5377161796001/profile_0/chunklist.m3u8` |
| IL: Keshet 12 HD | flutter-m3u | timeout | `http://skylogic.site:8080/esterichannel50con/36cb6c13/23363` |
| IL: Knesset Channel | flutter-m3u | timeout | `http://skylogic.site:8080/esterichannel50con/36cb6c13/24105` |
| IL: Reshet 13 | flutter-m3u | timeout | `http://skylogic.site:8080/esterichannel50con/36cb6c13/14772` |
| IL: YES SPORT 5 | flutter-m3u | timeout | `http://skylogic.site:8080/esterichannel50con/36cb6c13/172323` |
| IL: YES SPORT 5 PLUS HD | flutter-m3u | timeout | `http://skylogic.site:8080/esterichannel50con/36cb6c13/14789` |
| Israel: Kan 11 | flutter-m3u | http_error | `https://kanlivep2event-i.akamaihd.net/hls/live/747610/747610/source1_2.5k/chunklist.m3u8` |
| KAN 11 Israel (1080p) | flutter-m3u | connection_error | `https://kan11w.media.kan.org.il/hls/live/2105694/2105694/master.m3u8` |
| Kan 88 | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/kan88_mp3` |
| KAN 88 | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/749623_mp3?providername=tunein` |
| Kan Bet | flutter-m3u | connection_error | `https://kanbet.media.kan.org.il/hls/live/2024811/2024811/playlist.m3u8` |
| KAN gimel (real) | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/749625_mp3` |
| Kan Israel Reshet Moreshet 92.5 FM | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/kanmoreshet_mp3` |
| Kan Israel Tarbut | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/kantarbut_mp3` |
| Kan Kol HaMusica | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/kankolhamusica_mp3` |
| Kan Reshet Bet | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/kanbet_mp3` |
| Knesset Channel (480p) [Not 24/7] | flutter-m3u | http_error | `https://contact.gostreaming.tv/Knesset/myStream/playlist.m3u8` |
| Musayof (Israel) (240p) [Not 24/7] | flutter-m3u | http_error | `http://wowza.media-line.co.il/Musayof-Live/livestream.sdp/playlist.m3u8` |
| Music-ToraVeZimra | flutter-m3u | timeout | `https://cast.breslevforyou.co.il/listen/music-toravezimra/radio.mp3` |
| Nachman | flutter-m3u | timeout | `https://cast.breslevforyou.co.il/listen/radiobreslev/radio.mp3` |
| reka | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/kanreka_mp3` |
| The Shopping Channel | flutter-m3u | connection_error | `https://shoppingil-rewriter.vidnt.com/index.m3u8` |
| Ynet Live | flutter-m3u | geo_or_forbidden | `https://hls-video-ynet.ynethd.com/ynet/live.m3u8` |
| ברסלב פוריו: הלכות ודף יומי | flutter-m3u | timeout | `https://cast.breslevforyou.co.il/listen/halachot/radio.mp3` |
| ברסלב פוריו: ספרי ברסלב | flutter-m3u | timeout | `https://cast.breslevforyou.co.il/listen/books/radio.mp3` |
| ברסלב פוריו: קצר וקולע | flutter-m3u | timeout | `https://cast.breslevforyou.co.il/listen/shorts/radio.mp3` |
| כאן 11 | flutter-m3u | connection_error | `https://kan11.media.kan.org.il/hls/live/2024514/2024514/master.m3u8` |
| כאן מורשת - Kan Moreshet | flutter-m3u | connection_error | `https://kanliveicy.media.kan.org.il/icy/kanmoreshet_mp3` |
| כאן מורשת - Kan Moreshet | flutter-m3u | connection_error | `https://kanliveicy.media.kan.org.il/icy/749629_mp3` |
| ערוץ 14 | flutter-m3u | http_error | `https://now14.g-mana.live/media/91517161-44ab-4e46-af70-e9fe26117d2e/mainManifest.m3u8` |
| רשת ג בדיקה | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/kangimmel_mp3` |
| راديو مكان  - Kan Israel Makan | flutter-m3u | connection_error | `http://kanliveicy.media.kan.org.il/icy/makan_mp3` |
| مكان 33 | flutter-m3u | connection_error | `https://makan.media.kan.org.il/hls/live/2024680/2024680/master.m3u8` |

## Full Israeli channel inventory

| Channel | Source | Status | Primary URL |
|---|---|---|---|
| 100FM 80s | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/10080s/playlist.m3u8` |
| 100FM 90s | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/10090s/playlist.m3u8` |
| 100FM Chillout | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Chillout/playlist.m3u8` |
| 100FM Classic Rock | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100ClassicRock/playlist.m3u8` |
| 100FM Club | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Club/playlist.m3u8` |
| 100FM Dance | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Dance/playlist.m3u8` |
| 100FM Deep | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Deep/playlist.m3u8` |
| 100FM DJ Set | iptv-org | WORKING | `https://gb25.streamgates.net/radios-audio/100Djset/playlist.m3u8` |
| 100FM DJ Set | flutter-m3u | BROKEN | `https://gb25.streamgates.net/radios-audio/100DJSet/playlist.m3u8` |
| 100FM Hip Hop | iptv-org | WORKING | `https://gb25.streamgates.net/radios-audio/100Hiphop/playlist.m3u8` |
| 100FM Hip Hop | flutter-m3u | BROKEN | `https://gb25.streamgates.net/radios-audio/100HipHop/playlist.m3u8` |
| 100FM Hits | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Hits/playlist.m3u8` |
| 100FM Jazz | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Jazz/playlist.m3u8` |
| 100FM K-Pop | iptv-org | WORKING | `https://gb25.streamgates.net/radios-audio/100kpop/playlist.m3u8` |
| 100FM K-Pop | flutter-m3u | BROKEN | `https://gb25.streamgates.net/radios-audio/100KPop/playlist.m3u8` |
| 100FM Latin | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Latin/playlist.m3u8` |
| 100FM Mizrachit | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Mizrachit/playlist.m3u8` |
| 100FM Radio | flutter-m3u | WORKING | `https://cdn.cybercdn.live/Radios_100FM/Audio/icecast.audio` |
| 100FM Radio HLS | flutter-m3u | WORKING | `https://cdn.cybercdn.live/Radios_100FM/Audio/playlist.m3u8` |
| 100FM Retro | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Retro/playlist.m3u8` |
| 100FM TikTok | iptv-org | WORKING | `https://gb25.streamgates.net/radios-audio/100Tiktok/playlist.m3u8` |
| 100FM TikTok | flutter-m3u | BROKEN | `https://gb25.streamgates.net/radios-audio/100TikTok/playlist.m3u8` |
| 100FM Top 40 | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Top40/playlist.m3u8` |
| 100FM Trance | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Trance/playlist.m3u8` |
| 100FM TV | flutter-m3u | WORKING | `https://cdn.cybercdn.live/Radios_100FM/Video/playlist.m3u8` |
| 100FM Workout | flutter-m3u | WORKING | `https://gb25.streamgates.net/radios-audio/100Workout/playlist.m3u8` |
| 102FM Eilat | iptv-org | WORKING | `https://cdn.cybercdn.live/Eilat_Radio/Live/icecast.audio` |
| 103FM Radio | flutter-m3u | WORKING | `https://cdn.cybercdn.live/103FM/Live/icecast.audio` |
| 103FM Radio HLS | flutter-m3u | WORKING | `https://cdn.cybercdn.live/103FM/Live/playlist.m3u8` |
| 106.4FM | iptv-org | WORKING | `https://cdna.streamgates.net/TheBest/live/playlist.m3u8` |
| 88FM | flutter-m3u | BROKEN | `https://kan88.media.kan.org.il/hls/live/2024812/2024812/kan88_mp3/chunklist.m3u8` |
| 9 канал Ⓨ | flutter-m3u | WORKING | `https://www.youtube.com/@israel9tv/live` |
| 99.5FM | iptv-org | WORKING | `https://995.livecdn.biz/995fm` |
| 99FM Eco | iptv-org | WORKING | `http://eco-live.mediacast.co.il/99fm_aac` |
| AudioVersity | flutter-m3u | WORKING | `https://1062onair.runi.ac.il/idc123.mp3` |
| Big Brother Israel | flutter-m3u | BROKEN | `https://d2lckchr9cxrss.cloudfront.net/out/v1/c73af7694cce4767888c08a7534b503c/index.m3u8` |
| Channel 10 Business | flutter-m3u | WORKING | `https://r.il.cdn-redge.media/livehls/oil/calcala-live/live/channel10/live.livx/playlist.m3u8` |
| Channel 13 (720p) [Not 24/7] | flutter-m3u | BROKEN | `https://stream.theyraonline.com/live/channel13@live/index.m3u8` |
| Channel 14 | flutter-m3u | WORKING | `https://ch14channel14.encoders.immergo.tv/app/2/streamPlaylist.m3u8` |
| Channel 14 Alt | flutter-m3u | WORKING | `https://r.il.cdn-redge.media/livehls/oil/ch14/live/ch14/live.livx/playlist.m3u8` |
| Diki Radio | iptv-org | BROKEN | `https://diki.mediacast.co.il/diki` |
| ECO99FM | flutter-m3u | WORKING | `https://eco-live.mediacast.co.il/99fm_aac` |
| Galei Zahal | flutter-m3u | WORKING | `https://glzwizzlv.bynetcdn.com/glz_mp3` |
| Galgalatz | flutter-m3u | WORKING | `https://glzwizzlv.bynetcdn.com/glglz_mp3` |
| Hala TV | flutter-m3u | BROKEN | `https://gstream4.panet.co.il/edge/halaTV/chunks.m3u8` |
| i24NEWS Arabic | iptv-org | BROKEN | `https://video.i24news.tv/live/i24news-ar/index.m3u8` |
| i24NEWS English | iptv-org | BROKEN | `https://video.i24news.tv/live/i24news-en/index.m3u8` |
| i24NEWS French | iptv-org | BROKEN | `https://video.i24news.tv/live/i24news-fr/index.m3u8` |
| i24NEWS Hebrew | iptv-org | BROKEN | `https://video.i24news.tv/live/i24news-he/index.m3u8` |
| i24NEWS Hebrew | flutter-m3u | GEO-BLOCKED | `https://bcovlive-a.akamaihd.net/d89ede8094c741b7924120b27764153c/eu-central-1/5377161796001/profile_0/chunklist.m3u8` |
| IL: Keshet 12 HD | flutter-m3u | BROKEN | `http://skylogic.site:8080/esterichannel50con/36cb6c13/23363` |
| IL: Knesset Channel | flutter-m3u | BROKEN | `http://skylogic.site:8080/esterichannel50con/36cb6c13/24105` |
| IL: Reshet 13 | flutter-m3u | BROKEN | `http://skylogic.site:8080/esterichannel50con/36cb6c13/14772` |
| IL: YES SPORT 5 | flutter-m3u | BROKEN | `http://skylogic.site:8080/esterichannel50con/36cb6c13/172323` |
| IL: YES SPORT 5 PLUS HD | flutter-m3u | BROKEN | `http://skylogic.site:8080/esterichannel50con/36cb6c13/14789` |
| Israel: Kan 11 | flutter-m3u | BROKEN | `https://kanlivep2event-i.akamaihd.net/hls/live/747610/747610/source1_2.5k/chunklist.m3u8` |
| Kabbalah TV Hebrew | flutter-m3u | WORKING | `https://edge3.uk.kab.tv/live/tv66-heb-high/playlist.m3u8` |
| Kabbalah TV Russian | iptv-org | WORKING | `https://edge3.uk.kab.tv/live/tv66-rus-high/playlist.m3u8` |
| Kan 11 4K | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11_4k/live.livx/playlist.m3u8` |
| KAN 11 Israel (1080p) | flutter-m3u | BROKEN | `https://kan11w.media.kan.org.il/hls/live/2105694/2105694/master.m3u8` |
| KAN 11 Israel (360p) [Geo-blocked] | flutter-m3u | WORKING | `https://kanlivep2event-i.akamaihd.net/hls/live/747610/747610/master.m3u8` |
| Kan 11 News | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11/live.livx/playlist.m3u8` |
| Kan 11 Subtitled | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan11_subs/live.livx/playlist.m3u8` |
| Kan 88 | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_88/live.livx/playlist.m3u8` |
| Kan 88 | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/kan88_mp3` |
| KAN 88 | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/749623_mp3?providername=tunein` |
| Kan Bet | flutter-m3u | BROKEN | `https://kanbet.media.kan.org.il/hls/live/2024811/2024811/playlist.m3u8` |
| Kan Bet / Reshet Bet | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_reshet_bet/live.livx/playlist.m3u8` |
| Kan Gimel | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_gimel/live.livx/playlist.m3u8` |
| KAN gimel (real) | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/749625_mp3` |
| Kan Israel Reshet Moreshet 92.5 FM | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/kanmoreshet_mp3` |
| Kan Israel Tarbut | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/kantarbut_mp3` |
| kan kids | iptv-org | WORKING | `https://kan23.media.kan.org.il/hls/live/2024691/2024691/master.m3u8` |
| Kan Kids / Educational | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/kan_edu/live.livx/playlist.m3u8` |
| Kan Kol HaMusica | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/kankolhamusica_mp3` |
| Kan Kol Hamuzika | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_kol_hamuzika/live.livx/playlist.m3u8` |
| Kan Moreshet | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_moreshet/live.livx/playlist.m3u8` |
| Kan Reka | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_reka/live.livx/playlist.m3u8` |
| Kan Reshet Bet | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/kanbet_mp3` |
| Kan Tarbut | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/kan_tarbut/live.livx/playlist.m3u8` |
| Kcm FM Channel 01 Live | flutter-m3u | WORKING | `https://media2.93fm.co.il/livemusic` |
| Knesset Channel | flutter-m3u | WORKING | `https://kneset.gostreaming.tv/p2-kneset/_definst_/myStream/index.m3u8` |
| Knesset Channel (480p) [Not 24/7] | flutter-m3u | BROKEN | `https://contact.gostreaming.tv/Knesset/myStream/playlist.m3u8` |
| Knesset Channel Accessible | iptv-org | WORKING | `https://kneset.gostreaming.tv/p2-Accessibility/_definst_/myStream/index.m3u8` |
| Kol Barama | iptv-org | WORKING | `https://cdn.cybercdn.live/Kol_Barama/Live_Audio/icecast.audio` |
| kzradio | flutter-m3u | WORKING | `https://kzradio.mediacast.co.il/kzradio_live/kzradio/icecast.audio` |
| Makan 33 | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/makan/live.livx/playlist.m3u8` |
| Musayof (Israel) (240p) [Not 24/7] | flutter-m3u | BROKEN | `http://wowza.media-line.co.il/Musayof-Live/livestream.sdp/playlist.m3u8` |
| Music-ToraVeZimra | flutter-m3u | BROKEN | `https://cast.breslevforyou.co.il/listen/music-toravezimra/radio.mp3` |
| Nachman | flutter-m3u | BROKEN | `https://cast.breslevforyou.co.il/listen/radiobreslev/radio.mp3` |
| Radio 5 Live | iptv-org | WORKING | `https://rgelive.akamaized.net/hls/live/2043150/radio5/playlist.m3u8` |
| Radio Makan | flutter-m3u | WORKING | `https://kancdn.medonecdn.net/livehls/oil/kancdn-live/live/radio/radio_makan/live.livx/playlist.m3u8` |
| Radio Sahar | flutter-m3u | WORKING | `https://live.ecast.co.il/stream/sahar/stream` |
| reka | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/kanreka_mp3` |
| Reshet 13 | flutter-m3u | WORKING | `https://reshet.g-mana.live/media/87f59c77-03f6-4bad-a648-897e095e7360/mainManifest.m3u8` |
| Reshet 13 (720p) | flutter-m3u | WORKING | `https://d2xg1g9o5vns8m.cloudfront.net/out/v1/0855d703f7d5436fae6a9c7ce8ca5075/index.m3u8` |
| Reshet 13 Alt | flutter-m3u | WORKING | `https://d18b0e6mopany4.cloudfront.net/out/v1/2f2bc414a3db4698a8e94b89eaf2da2a/index.m3u8` |
| Reshet 13 Comedy | flutter-m3u | WORKING | `https://d15ds134q59udk.cloudfront.net/out/v1/fbba879221d045598540ee783b140fe2/index.m3u8` |
| Reshet 13 Nofesh | flutter-m3u | WORKING | `https://d1yd8hohnldm33.cloudfront.net/out/v1/19dee23c2cc24f689bd4e1288661ee0c/index.m3u8` |
| Reshet 13 Reality | flutter-m3u | WORKING | `https://d2dffl3588mvfk.cloudfront.net/out/v1/d8e15050ca4148aab0ee387a5e2eb46b/index.m3u8` |
| Reshet 13 Subtitled | flutter-m3u | WORKING | `https://reshet.g-mana.live/media/4607e158-e4d4-4e18-9160-3dc3ea9bc677/mainManifest.m3u8` |
| Sport 5 Studio | iptv-org | WORKING | `https://rgelive.akamaized.net/hls/live/2043095/live3/playlist.m3u8` |
| Super Channel 12 (1080p) | flutter-m3u | WORKING | `https://servilive.com:3263/live/channel12live.m3u8` |
| The Shopping Channel | flutter-m3u | BROKEN | `https://shoppingil-rewriter.vidnt.com/index.m3u8` |
| ynet | iptv-org | WORKING | `https://hls-video-ynet.ynethd.com/0323/7a92522310b049209122e2ffbd920508/master.m3u8` |
| Ynet Live | flutter-m3u | GEO-BLOCKED | `https://hls-video-ynet.ynethd.com/ynet/live.m3u8` |
| אקו eco 99fm | flutter-m3u | WORKING | `http://99.mediacast.co.il/99fm_aac?hash=1559501510715.m4a` |
| ברסלב פוריו: הלכות ודף יומי | flutter-m3u | BROKEN | `https://cast.breslevforyou.co.il/listen/halachot/radio.mp3` |
| ברסלב פוריו: ספרי ברסלב | flutter-m3u | BROKEN | `https://cast.breslevforyou.co.il/listen/books/radio.mp3` |
| ברסלב פוריו: קצר וקולע | flutter-m3u | BROKEN | `https://cast.breslevforyou.co.il/listen/shorts/radio.mp3` |
| הקצה - Hakatze | flutter-m3u | WORKING | `http://kzradio.mediacast.co.il/kzradio_live/kzradio/icecast.audio` |
| כאן 11 | flutter-m3u | BROKEN | `https://kan11.media.kan.org.il/hls/live/2024514/2024514/master.m3u8` |
| כאן מורשת - Kan Moreshet | flutter-m3u | BROKEN | `https://kanliveicy.media.kan.org.il/icy/kanmoreshet_mp3` |
| כאן מורשת - Kan Moreshet | flutter-m3u | BROKEN | `https://kanliveicy.media.kan.org.il/icy/749629_mp3` |
| ערוץ 14 | flutter-m3u | BROKEN | `https://now14.g-mana.live/media/91517161-44ab-4e46-af70-e9fe26117d2e/mainManifest.m3u8` |
| קול חי - Kol Chai | flutter-m3u | WORKING | `https://media2.93fm.co.il/live-new` |
| רשת ג בדיקה | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/kangimmel_mp3` |
| راديو مكان  - Kan Israel Makan | flutter-m3u | BROKEN | `http://kanliveicy.media.kan.org.il/icy/makan_mp3` |
| مكان 33 | flutter-m3u | BROKEN | `https://makan.media.kan.org.il/hls/live/2024680/2024680/master.m3u8` |

## N12 / Keshet 12 research note

- Official live entry point: `https://www.n12.co.il/live/` (redirects to Mako live infrastructure).
- Observed/public patterns use `mako-streaming.akamaized.net`, for example `https://mako-streaming.akamaized.net/stream/hls/live/2033791/k12n12wad/profile/1/profileManifest.m3u8`.
- In this environment, all stable unsigned Keshet 12/N12 manifest paths returned `403 Access Denied`, which strongly suggests signed or session-bound tickets are required. Because those tokens expire, I did **not** add a transient N12 URL to the database.

## Recommended next step

Run the same repair set with a Supabase service-role key, or replace `promote_channel_source` with a schema-correct RPC that updates `channels.urls` instead of the removed `channels.url` column.