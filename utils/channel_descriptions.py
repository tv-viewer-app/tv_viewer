"""Channel description lookup for the Info feature.

Maps channel name patterns (lowercase) to 1-sentence descriptions.
To add a new description, add an entry to the ``CHANNEL_DESCRIPTIONS`` dict.
Keys should be lowercase and match the most recognizable part of the channel name.
"""

from typing import Optional

# ─── Channel Descriptions ────────────────────────────────────────────────────
# Keys are lowercase patterns. Values are single-sentence factual descriptions.
CHANNEL_DESCRIPTIONS: dict[str, str] = {
    # ── Israeli TV Channels ──────────────────────────────────────────
    "kan 11": "Israeli public broadcasting main channel with news, drama, and entertainment.",
    "kan 23": "Kan educational and children programming channel.",
    "kan 88": "Kan 88 music radio — Israeli public radio station playing diverse music.",
    "kan bet": "Reshet Bet news and talk radio — Israel's main news radio station.",
    "kan gimel": "Kan Gimel — Israeli public radio station for music and culture.",
    "makan 33": "Makan — Israeli Arabic-language public TV channel.",
    "reshet 13": "Reshet 13 — Israeli commercial TV channel with news, sports, and entertainment.",
    "channel 14": "Channel 14 Now — Israeli news and opinion TV channel.",
    "now 14": "Channel 14 Now — Israeli news and opinion TV channel.",
    "keshet 12": "Keshet 12 — Israel's leading commercial TV channel with drama and entertainment.",
    "channel 12": "Keshet 12 — Israel's leading commercial TV channel with drama and entertainment.",
    "knesset": "Live broadcast from the Israeli Knesset (parliament).",
    "ynet": "Ynet Live — Israeli news streaming from Ynet/Yedioth Ahronoth.",
    "n12": "N12 — Mako/Channel 12 digital news platform.",
    "hala tv": "Hala TV — Arabic entertainment and cultural programming from Israel.",
    "kabbalah": "Kabbalah TV — Educational channel about Kabbalah and spirituality.",
    "i24": "i24NEWS — Israeli international 24-hour news channel in English, French, and Arabic.",
    "i24news": "i24NEWS — Israeli international 24-hour news channel.",
    "hot cinema": "HOT Cinema — Israeli premium movie channel.",
    "hot 3": "HOT 3 — Israeli cable TV entertainment channel.",
    "yes drama": "Yes Drama — Israeli satellite TV drama channel.",
    "yes action": "Yes Action — Israeli satellite TV action and thriller movies.",
    "sport 5": "Sport 5 — Israel's main sports television channel.",
    "sport5": "Sport 5 — Israel's main sports television channel.",
    "one israel": "One — Israeli lifestyle and entertainment channel.",
    "walla": "Walla! News — Israeli news and content portal live stream.",
    "zoom channel": "Zoom — Israeli music and entertainment TV channel.",
    "music 24": "Music 24 — Israeli 24-hour music video channel.",
    "logi": "Logi — Israeli educational and cultural channel.",
    "hop!": "HOP! — Israeli children's TV channel for preschoolers.",
    "hop channel": "HOP! — Israeli children's TV channel for preschoolers.",
    "luli": "Luli — Israeli baby and toddler channel.",
    "junior channel": "Junior — Israeli children's entertainment channel.",
    "channel 20": "Channel 20 — Israeli TV channel focused on heritage and culture.",
    "channel 9": "Channel 9 — Israeli Russian-language TV channel.",

    # ── Israeli Radio Stations ───────────────────────────────────────
    "100fm": "100FM Radio — Israeli commercial music and entertainment radio.",
    "radius 100fm": "Radius 100FM — Tel Aviv-based music and entertainment radio.",
    "88fm": "88FM — Israeli radio station with indie and alternative music.",
    "103fm": "103FM — Israeli talk radio and music station.",
    "eco99": "Eco 99FM — Israeli radio station playing international and local hits.",
    "eco99fm": "Eco 99FM — Israeli radio station playing international and local hits.",
    "galgalatz": "Galgalatz — IDF radio station playing Israeli and international pop music.",
    "galatz": "Galatz — IDF's main radio station with news and current affairs.",
    "reshet bet": "Reshet Bet — Israel's main news and talk radio station.",
    "kol israel": "Kol Israel — Voice of Israel public radio network.",
    "gali israel": "Galei Zahal — Israeli military radio station.",
    "kan reshet moreshet": "Kan Moreshet — Israeli public radio station for Jewish heritage and culture.",

    # ── International News ───────────────────────────────────────────
    "bbc": "BBC — British Broadcasting Corporation, world-class news and programming.",
    "bbc one": "BBC One — BBC's flagship television channel with a mix of news and entertainment.",
    "bbc two": "BBC Two — BBC channel known for documentaries, arts, and cultural programming.",
    "bbc news": "BBC News — 24-hour rolling news channel from the BBC.",
    "bbc world": "BBC World News — International news channel broadcasting worldwide.",
    "cnn": "CNN — Cable News Network, 24-hour American news channel.",
    "cnn international": "CNN International — Global edition of CNN broadcasting to 200+ countries.",
    "al jazeera": "Al Jazeera — Qatar-based international news network.",
    "al arabiya": "Al Arabiya — Saudi-owned pan-Arab news channel based in Dubai.",
    "france 24": "France 24 — French international 24-hour news channel.",
    "dw": "Deutsche Welle — Germany's international broadcaster with global news.",
    "dw news": "DW News — English-language news service from Deutsche Welle.",
    "deutsche welle": "Deutsche Welle — Germany's international broadcaster with global news.",
    "rt": "RT — Russian international television network.",
    "russia today": "RT (Russia Today) — Russian state-funded international TV network.",
    "nhk": "NHK World — Japan's international broadcasting service.",
    "nhk world": "NHK World-Japan — English-language international service of NHK.",
    "euronews": "Euronews — European multilingual news channel covering world events.",
    "sky news": "Sky News — British 24-hour rolling news channel.",
    "fox news": "Fox News — American cable news channel.",
    "msnbc": "MSNBC — American cable news channel with progressive commentary.",
    "abc news": "ABC News — American Broadcasting Company news division.",
    "cbs news": "CBS News — American news division of CBS.",
    "nbc news": "NBC News — News division of the NBC television network.",
    "bloomberg": "Bloomberg TV — Global business and financial news network.",
    "cnbc": "CNBC — American business news and financial market channel.",
    "c-span": "C-SPAN — American cable network covering federal government proceedings.",
    "pbs": "PBS — American public broadcasting service with educational programming.",
    "bfm tv": "BFM TV — French 24-hour rolling news and weather channel.",
    "cnews": "CNews — French news channel with debate and opinion programming.",
    "lci": "LCI — La Chaîne Info, French 24-hour news channel.",
    "cgtn": "CGTN — China Global Television Network, China's English-language news channel.",
    "cna": "CNA — Channel NewsAsia, Singaporean English-language news channel.",
    "wion": "WION — World Is One News, Indian English-language international news channel.",
    "arirang": "Arirang TV — South Korean English-language international broadcaster.",
    "ndtv": "NDTV — New Delhi Television, leading Indian English-language news network.",
    "times now": "Times Now — Indian English-language news channel from the Times Group.",
    "aaj tak": "Aaj Tak — India's leading Hindi-language news channel.",
    "republic": "Republic TV — Indian English-language news channel.",
    "trt world": "TRT World — Turkey's English-language international news channel.",
    "press tv": "Press TV — Iranian English-language news and documentary network.",
    "telesur": "teleSUR — Latin American multi-state news network based in Venezuela.",

    # ── US Broadcast & Cable ─────────────────────────────────────────
    "abc": "ABC — American Broadcasting Company, major US television network.",
    "nbc": "NBC — National Broadcasting Company, major US television network.",
    "cbs": "CBS — Major American commercial broadcast television network.",
    "fox": "Fox — American commercial broadcast TV network.",
    "hbo": "HBO — Premium American entertainment network with original series and films.",
    "showtime": "Showtime — American premium cable and streaming TV network.",
    "starz": "Starz — American premium cable and streaming channel with movies and series.",
    "cinemax": "Cinemax — American premium cable channel focused on movies.",
    "amc": "AMC — American cable channel known for original drama series.",
    "fx": "FX — American cable channel known for original drama and comedy series.",
    "tnt": "TNT — Turner Network Television, American cable channel with drama and movies.",
    "tbs": "TBS — American cable channel with comedy and entertainment programming.",
    "usa network": "USA Network — American cable channel with original series and movies.",
    "bravo": "Bravo — American cable channel focused on entertainment and reality TV.",
    "syfy": "Syfy — American cable channel for science fiction and fantasy programming.",
    "lifetime": "Lifetime — American cable channel with movies and series targeting women.",
    "hallmark": "Hallmark Channel — American cable channel known for family-friendly movies.",
    "paramount": "Paramount Network — American cable channel with original series and movies.",
    "bet": "BET — Black Entertainment Television, American cable network.",
    "comedy central": "Comedy Central — American cable channel dedicated to comedy programming.",
    "e!": "E! — American cable channel focused on entertainment and pop culture news.",

    # ── UK Channels ──────────────────────────────────────────────────
    "itv": "ITV — Britain's largest commercial terrestrial TV network.",
    "channel 4": "Channel 4 — British free-to-air public broadcast TV channel.",
    "channel 5": "Channel 5 — British free-to-air commercial TV channel.",
    "sky sports": "Sky Sports — British pay-TV sports network with Premier League coverage.",
    "sky cinema": "Sky Cinema — British premium movie channel from Sky.",
    "sky atlantic": "Sky Atlantic — British pay-TV channel featuring HBO and original content.",
    "dave": "Dave — British free-to-air comedy and entertainment channel.",
    "film4": "Film4 — British free-to-air channel dedicated to films.",
    "cbbc": "CBBC — BBC's channel for children aged 6-12.",
    "cbeebies": "CBeebies — BBC's channel for preschool children.",

    # ── European Channels ────────────────────────────────────────────
    "ard": "ARD — Germany's consortium of public broadcasters (Das Erste).",
    "zdf": "ZDF — Germany's national public TV broadcaster.",
    "rtl": "RTL — Germany's largest private TV channel.",
    "pro7": "ProSieben — German commercial TV channel with entertainment and movies.",
    "prosieben": "ProSieben — German commercial TV channel with entertainment and movies.",
    "sat.1": "Sat.1 — German commercial TV channel.",
    "sat1": "Sat.1 — German commercial TV channel.",
    "arte": "ARTE — Franco-German public TV channel for culture and arts.",
    "kika": "KiKA — German public children's channel by ARD and ZDF.",
    "tf1": "TF1 — France's most-watched commercial TV channel.",
    "france 2": "France 2 — French public national TV channel.",
    "france 3": "France 3 — French public TV channel with regional programming.",
    "canal+": "Canal+ — French premium pay-TV channel.",
    "canal plus": "Canal+ — French premium pay-TV channel.",
    "m6": "M6 — French commercial TV channel with entertainment programming.",
    "rai": "RAI — Italy's national public broadcasting company.",
    "rai 1": "Rai 1 — RAI's flagship Italian public TV channel.",
    "mediaset": "Mediaset — Major Italian commercial broadcasting company.",
    "canale 5": "Canale 5 — Italy's most-watched Mediaset commercial channel.",
    "tve": "TVE — Televisión Española, Spain's public broadcaster.",
    "antena 3": "Antena 3 — Major Spanish commercial TV channel.",
    "telecinco": "Telecinco — Spanish commercial TV channel by Mediaset España.",
    "la sexta": "La Sexta — Spanish free-to-air commercial TV channel.",

    # ── Sports ───────────────────────────────────────────────────────
    "espn": "ESPN — Leading American sports network covering major leagues worldwide.",
    "bein sports": "beIN Sports — International sports broadcasting network.",
    "fox sports": "Fox Sports — American sports broadcasting network.",
    "nfl network": "NFL Network — American channel dedicated to National Football League.",
    "mlb network": "MLB Network — American channel dedicated to Major League Baseball.",
    "nba tv": "NBA TV — American channel dedicated to the National Basketball Association.",
    "star sports": "Star Sports — Indian sports TV network with cricket and football.",
    "dazn": "DAZN — Global sports streaming service for boxing, soccer, and more.",

    # ── Kids & Family ────────────────────────────────────────────────
    "nickelodeon": "Nickelodeon — Children's entertainment channel with cartoons and live-action shows.",
    "nick jr": "Nick Jr. — Preschool programming channel from Nickelodeon.",
    "cartoon network": "Cartoon Network — Animated entertainment channel for children and teens.",
    "disney channel": "Disney Channel — Family entertainment channel with original movies and series.",
    "disney junior": "Disney Junior — Disney's channel for preschool-aged children.",
    "disney xd": "Disney XD — Disney's channel for action-adventure and comedy animation.",
    "baby tv": "BabyTV — Channel for babies and toddlers with educational content.",
    "pbs kids": "PBS Kids — American public broadcasting channel for children.",
    "boomerang": "Boomerang — Channel featuring classic and modern animated cartoons.",
    "gulli": "Gulli — French free-to-air children's TV channel.",

    # ── Entertainment & Lifestyle ────────────────────────────────────
    "mtv": "MTV — Music Television, pop culture and entertainment channel.",
    "mtv music": "MTV Music — Dedicated music video and entertainment channel.",
    "vh1": "VH1 — Music-based cable channel with pop culture programming.",
    "discovery": "Discovery Channel — Factual entertainment with science, nature, and exploration.",
    "nat geo": "National Geographic — Nature, science, culture, and exploration channel.",
    "national geographic": "National Geographic — Nature, science, culture, and exploration channel.",
    "history": "History Channel — Documentary programming about history and civilization.",
    "history channel": "History Channel — Documentary programming about history and civilization.",
    "animal planet": "Animal Planet — Channel dedicated to wildlife and nature programming.",
    "tlc": "TLC — The Learning Channel, reality and lifestyle programming.",
    "food network": "Food Network — American cable channel about food and cooking.",
    "hgtv": "HGTV — Home & Garden Television with home improvement programming.",
    "travel channel": "Travel Channel — Programming about travel, adventure, and world cultures.",
    "weather channel": "The Weather Channel — 24-hour American weather forecast and news.",

    # ── Arabic / Middle East ─────────────────────────────────────────
    "mbc": "MBC — Middle East Broadcasting Center, leading Arab entertainment network.",
    "mbc 1": "MBC 1 — MBC's flagship Arabic-language general entertainment channel.",
    "rotana": "Rotana — Saudi-owned Arabic music and entertainment channel.",
    "lbc": "LBC — Lebanese Broadcasting Corporation, major Lebanese TV network.",
    "dubai tv": "Dubai TV — Official TV channel of the Emirate of Dubai.",
    "abu dhabi tv": "Abu Dhabi TV — Official TV channel of the Emirate of Abu Dhabi.",
    "al mayadeen": "Al Mayadeen — Pan-Arab news channel based in Beirut.",

    # ── Asian Channels ───────────────────────────────────────────────
    "zee tv": "Zee TV — Leading Hindi-language entertainment channel from India.",
    "star plus": "Star Plus — Popular Indian Hindi entertainment TV channel.",
    "colors": "Colors TV — Hindi-language Indian entertainment channel.",
    "sony tv": "Sony TV — Indian Hindi entertainment channel by Sony Pictures Networks.",
    "kbs": "KBS — Korean Broadcasting System, South Korea's public broadcaster.",
    "tvb": "TVB — Television Broadcasts Limited, Hong Kong's leading TV station.",
    "cctv": "CCTV — China Central Television, China's state broadcaster.",
    "abs-cbn": "ABS-CBN — Major Philippine commercial broadcasting network.",
    "gma": "GMA — GMA Network, leading Philippine commercial TV and radio network.",
    "astro": "Astro — Malaysian satellite TV and IPTV provider.",

    # ── Russian Channels ─────────────────────────────────────────────
    "russia 1": "Russia-1 — Major Russian federal TV channel.",
    "russia 24": "Russia-24 — Russian 24-hour news channel.",
    "channel one russia": "Channel One Russia — Russia's most-watched state TV channel.",
    "perviy kanal": "Perviy Kanal (Channel One) — Russia's flagship state TV channel.",
    "ntv": "NTV — Major Russian commercial TV channel.",

    # ── Latin American Channels ──────────────────────────────────────
    "globo": "TV Globo — Brazil's largest commercial TV network.",
    "televisa": "Televisa — Mexico's largest mass-media company.",
    "tv azteca": "TV Azteca — Major Mexican commercial broadcast TV network.",
    "caracol": "Caracol TV — Leading Colombian commercial TV network.",

    # ── Free Streaming / FAST Channels ───────────────────────────────
    "pluto tv": "Pluto TV — Free ad-supported streaming service with 250+ live channels.",
    "pluto": "Pluto TV — Free ad-supported streaming service with 250+ live channels.",
    "samsung tv plus": "Samsung TV Plus — Free ad-supported streaming service on Samsung devices.",
    "plex": "Plex — Media server and free ad-supported streaming service.",
    "tubi": "Tubi — Free ad-supported streaming service with movies and TV shows.",
    "roku": "The Roku Channel — Free ad-supported streaming channel on Roku devices.",
    "xumo": "Xumo — Free ad-supported streaming service with news and entertainment.",
    "peacock": "Peacock — NBCUniversal's streaming service with free and premium tiers.",
    "freevee": "Freevee — Amazon's free ad-supported streaming service.",

    # ── Music / Radio ────────────────────────────────────────────────
    "classic fm": "Classic FM — Britain's most popular classical music radio station.",
    "bbc radio": "BBC Radio — British Broadcasting Corporation's radio network.",
    "npr": "NPR — National Public Radio, American non-profit news and culture network.",
    "radio paradise": "Radio Paradise — Eclectic listener-supported online radio station.",
    "soma fm": "SomaFM — Listener-supported commercial-free internet radio.",
    "heart": "Heart — UK commercial radio network playing pop and adult contemporary.",
    "capital": "Capital FM — UK commercial radio station playing pop hits.",
    "kiis fm": "KIIS FM — American Top 40 radio station based in Los Angeles.",
}


def get_description(channel_name: str) -> Optional[str]:
    """Get a 1-sentence description for a channel by name (fuzzy match).

    Tries exact match first, then partial/contains match.
    Short patterns (< 4 chars) require a word-boundary match to avoid
    false positives (e.g. "rt" matching "Sport").

    Args:
        channel_name: The channel name to look up.

    Returns:
        A description string, or ``None`` if no match is found.
    """
    if not channel_name:
        return None

    lower = channel_name.lower().strip()

    # 1. Exact match (O(1) dict lookup)
    if lower in CHANNEL_DESCRIPTIONS:
        return CHANNEL_DESCRIPTIONS[lower]

    # 2. Partial / contains match with word-boundary safety
    import re
    words = set(re.split(r'[\s\-_/|,]+', lower))

    for pattern, desc in CHANNEL_DESCRIPTIONS.items():
        if len(pattern) < 4:
            # Short patterns must appear as a whole word to avoid false positives
            if pattern in words:
                return desc
        else:
            if pattern in lower or lower in pattern:
                return desc

    return None
