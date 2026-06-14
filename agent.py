import os
import shutil
import subprocess
from typing import List
from music_search import fetch_recordings_for_artist, search_musicbrainz_artist, artist_summary_from_mb

MODEL_ENV = "OLLAMA_MODEL"
DEFAULT_MODEL = "gemma:2b"
OLLAMA_BINARY_ENV = "OLLAMA_BINARY"
DEFAULT_OLLAMA_BINARY = "ollama"


class LocalAIAgent:
    def __init__(self):
        self.model_name = os.getenv(MODEL_ENV, DEFAULT_MODEL)
        self.ollama_bin = os.getenv(OLLAMA_BINARY_ENV, DEFAULT_OLLAMA_BINARY)

        if not shutil.which(self.ollama_bin):
            raise FileNotFoundError(
                f"未找到 Ollama CLI：{self.ollama_bin}\n請安裝 Ollama 並確認命令可執行。"
            )

    def _generate_text(self, prompt: str) -> str:
        # Ollama CLI expects the prompt as a positional argument (no --prompt flag)
        cmd = [self.ollama_bin, "run", self.model_name, prompt]
        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True,
                timeout=300,
            )
            output = (process.stdout or "").strip()
            if not output:
                stderr = (process.stderr or "").strip()
                if stderr:
                    raise RuntimeError(f"Ollama 無輸出，stderr: {stderr}")
            return output
        except subprocess.CalledProcessError as exc:
            stderr = exc.stderr.strip() if exc.stderr else ""
            stdout = exc.stdout.strip() if exc.stdout else ""
            raise RuntimeError(
                f"Ollama 執行失敗 (code {exc.returncode})，stderr: {stderr or '無'}，stdout: {stdout or '無'}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("Ollama 執行逾時") from exc
        except Exception as exc:
            raise RuntimeError(f"Ollama 執行失敗：{exc}") from exc

    def format_song_list(self, songs: List[dict]) -> str:
        lines = []
        total = len(songs)
        for idx, song in enumerate(songs[:50], start=1):
            release_date = song.get("release_date", "未知")
            release_title = song.get("release_title", "未知發行")
            release_type = song.get("release_type", "未知類型")
            lines.append(
                f"{idx}. 《{song['title']}》 - 發行：{release_date}；專輯/單曲：{release_title}；類型：{release_type}"
            )
        if total > 50:
            lines.append(f"... 此處顯示前 50 首歌曲，系統共搜尋到 {total} 筆項目。")
        return "\n".join(lines)

    def build_prompt(self, artist_name: str, biography: str, songs: List[dict]) -> str:
        song_text = self.format_song_list(songs)
        prompt = (
            "你是一個本地端 AI 代理，負責整理歌手從出道至今的歌曲資料。\n"
            f"歌手名稱：{artist_name}\n\n"
            "以下為系統已經搜尋到的資料：\n"
            f"歌手簡介：\n{biography or '無可用維基百科簡介。'}\n\n"
            "歌曲資料：\n"
            f"{song_text}\n\n"
            "請用繁體中文整理成回答格式，並輸出以下四個明確段落：\n"
            "1. 歌手簡介摘要\n"
            "2. 主要歌曲清單（標明歌名、發行年份、專輯／單曲、資料來源）\n"
            "3. 原文與中文翻譯（若有非中文原文，請先保留原文，再另外提供繁體中文翻譯）\n"
            "4. 來源說明與建議（若資料可能不完整，請說明採集方式和建議）\n\n"
            "請使用標題分隔，例如：\n"
            "歌手簡介摘要：\n...\n"
            "主要歌曲清單：\n...\n"
            "原文與中文翻譯：\n...\n"
            "來源說明與建議：\n...\n"
        )
        return prompt

    def search_artist_songs(self, artist_name: str) -> str:
        artist = search_musicbrainz_artist(artist_name)
        if not artist:
            return f"未能在 MusicBrainz 上找到歌手：{artist_name}。"

        artist_id = artist.get("id")
        biography = artist_summary_from_mb(artist)
        songs = fetch_recordings_for_artist(artist_id)

        if not songs:
            return f"已找到歌手 {artist_name}，但未能擷取歌曲資料。\n請檢查網路連線或稍後再試。"

        prompt = self.build_prompt(artist_name, biography, songs)
        try:
            text = self._generate_text(prompt)
        except Exception as exc:
            return f"AI 代理呼叫 Ollama 發生錯誤：{exc}"

        if not text:
            return "AI 代理未能產生回應，請確認 Ollama 模型與輸入是否正確。"

        return (text or "").strip()
