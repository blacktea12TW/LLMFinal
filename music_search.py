import time
import requests
import os
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

MUSICBRAINZ_SEARCH_URL = "https://musicbrainz.org/ws/2/artist/"
MUSICBRAINZ_RECORDING_URL = "https://musicbrainz.org/ws/2/recording/"
WIKIPEDIA_ZH_URL = "https://zh.wikipedia.org/w/api.php"
WIKIPEDIA_EN_URL = "https://en.wikipedia.org/w/api.php"

# 提供合理的 User-Agent；MusicBrainz 與 MediaWiki 建議包含聯絡資訊。
DEFAULT_USER_AGENT = "LocalMusicAgent/1.0 (contact: blacktea12ouo@gmail.com)"


def _default_headers():
    return {"User-Agent": os.getenv("USER_AGENT", DEFAULT_USER_AGENT)}


def search_musicbrainz_artist(artist_name: str) -> Optional[Dict]:
    params = {
        "query": f"artist:{artist_name}",
        "fmt": "json",
        "limit": 10,
    }
    try:
        response = requests.get(MUSICBRAINZ_SEARCH_URL, params=params, headers=_default_headers(), timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return None

    data = response.json()
    artists = data.get("artists", [])
    if not artists:
        return None

    for artist in artists:
        if artist_name.lower() in artist.get("name", "").lower():
            return artist
    return artists[0]


def fetch_recordings_for_artist(artist_id: str, max_songs: int = 250) -> List[Dict]:
    songs = []
    seen = set()
    limit = 100
    offset = 0
    # 使用 Session + Retry 以處理暫時性錯誤與速率限制
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retries))

    # 先嘗試直接以 artist=MBID 的方式取得 recordings
    while len(songs) < max_songs:
        params = {
            "artist": artist_id,
            "fmt": "json",
            "limit": limit,
            "offset": offset,
            "inc": "releases+artist-credits",
        }
        try:
            response = session.get(MUSICBRAINZ_RECORDING_URL, params=params, headers=_default_headers(), timeout=15)
            response.raise_for_status()
        except requests.RequestException:
            # 如果第一次方式失敗或沒有回傳資料，嘗試使用回退的搜尋方式 below
            break

        data = response.json()
        recordings = data.get("recordings", [])
        if not recordings:
            break

        for recording in recordings:
            title = recording.get("title", "未知歌曲")
            artist_credit = recording.get("artist-credit", [])
            artist_text = ", ".join([item.get("name", "") for item in artist_credit if item.get("name")])
            release_title = "未知發行"
            release_date = "未知年份"
            release_type = "未知類型"
            releases = recording.get("releases", [])
            if releases:
                first = releases[0]
                release_title = first.get("title", release_title)
                release_date = first.get("date", release_date)
                release_type = first.get("release-group", {}).get("primary-type", release_type)

            key = f"{title}|{release_title}|{release_date}"
            if key in seen:
                continue
            seen.add(key)

            songs.append(
                {
                    "title": title,
                    "artist": artist_text,
                    "release_title": release_title,
                    "release_date": release_date,
                    "release_type": release_type,
                }
            )
            if len(songs) >= max_songs:
                break

        if len(recordings) < limit:
            break
        offset += limit
        time.sleep(1.0)

    # 若使用 artist=MBID 未取得結果，改用 recording search query: arid:ARTIST_ID
    if not songs:
        offset = 0
        while len(songs) < max_songs:
            params = {
                "query": f"arid:{artist_id}",
                "fmt": "json",
                "limit": limit,
                "offset": offset,
            }
            try:
                response = session.get(MUSICBRAINZ_RECORDING_URL, params=params, headers=_default_headers(), timeout=15)
                response.raise_for_status()
            except requests.RequestException:
                break

            data = response.json()
            recordings = data.get("recordings", [])
            if not recordings:
                break

            for recording in recordings:
                title = recording.get("title", "未知歌曲")
                artist_credit = recording.get("artist-credit", [])
                artist_text = ", ".join([item.get("name", "") for item in artist_credit if item.get("name")])
                release_title = "未知發行"
                release_date = "未知年份"
                release_type = "未知類型"
                releases = recording.get("releases", [])
                if releases:
                    first = releases[0]
                    release_title = first.get("title", release_title)
                    release_date = first.get("date", release_date)
                    release_type = first.get("release-group", {}).get("primary-type", release_type)

                key = f"{title}|{release_title}|{release_date}"
                if key in seen:
                    continue
                seen.add(key)

                songs.append(
                    {
                        "title": title,
                        "artist": artist_text,
                        "release_title": release_title,
                        "release_date": release_date,
                        "release_type": release_type,
                    }
                )
                if len(songs) >= max_songs:
                    break

            if len(recordings) < limit:
                break
            offset += limit
            time.sleep(1.0)

    return songs


def search_wikipedia_summary(artist_name: str) -> Optional[str]:
    params = {
        "action": "query",
        "list": "search",
        "srsearch": artist_name,
        "format": "json",
        "utf8": 1,
        "srlimit": 1,
    }

    # 先嘗試中文維基百科
    try:
        response = requests.get(WIKIPEDIA_ZH_URL, params=params, headers=_default_headers(), timeout=15)
        if response.status_code == 403:
            # 403 常因為缺少正確 User-Agent，或是臨時性封鎖；嘗試回退到英文維基百科
            response = requests.get(WIKIPEDIA_EN_URL, params=params, headers=_default_headers(), timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return None

    results = response.json().get("query", {}).get("search", [])
    if not results:
        return None

    page_title = results[0].get("title")
    params = {
        "action": "query",
        "prop": "extracts",
        "titles": page_title,
        "format": "json",
        "explaintext": True,
        "exintro": True,
        "utf8": 1,
    }
    try:
        response = requests.get(response.url.split('?')[0], params=params, headers=_default_headers(), timeout=15)
        response.raise_for_status()
    except requests.RequestException:
        return None

    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        extract = page.get("extract")
        if extract:
            return extract.strip()
    return None


def artist_summary_from_mb(artist: Optional[Dict]) -> Optional[str]:
    """Generate a short artist summary using MusicBrainz metadata (no Wikipedia)."""
    if not artist:
        return None

    parts = []
    name = artist.get("name")
    if name:
        parts.append(f"藝名：{name}")

    disamb = artist.get("disambiguation")
    if disamb:
        parts.append(disamb)

    typestr = artist.get("type")
    if typestr:
        parts.append(f"類型：{typestr}")

    area = None
    if artist.get("area") and isinstance(artist.get("area"), dict):
        area = artist["area"].get("name")
    country = artist.get("country")
    if area or country:
        loc = area or country
        parts.append(f"來源地：{loc}")

    life = artist.get("life-span", {}) or {}
    begin = life.get("begin")
    end = life.get("end")
    if begin or end:
        span = f"出/在世時間：{begin or '?'} - {end or '至今'}"
        parts.append(span)

    if parts:
        return "；".join(parts)
    return None
