# 本地端 AI 代理：歌手歌曲資料搜尋器

## 創作理念
這個專案的目標是建立一個可在本地端執行的 AI 代理，用於搜尋指定歌手從出道至今的歌曲資料，並以繁體中文整理成回答。

本系統採用公開資料來源（以 MusicBrainz 為主要資料來源），先自動擷取歌手與歌曲資料，然後由本地模型生成結構化回應。本系統不使用維基百科。

## 專案內容
- `main.py`：CLI 入口程式，可輸入歌手名稱後啟動搜尋。
- `music_search.py`：透過 MusicBrainz API 搜尋歌手與歌曲列表，並使用 MusicBrainz 的元資料生成歌手摘要（不使用維基百科）。
- `agent.py`：本地 AI 代理核心，載入本地模型，整理資料並輸出繁體中文回答。
- `requirements.txt`：Python 相依套件。
- `.env.example`：本地模型路徑範例設定。

## 安裝步驟
1. 進入專案資料夾：

```powershell
cd "d:\saved download files\LLMFinal"
```

2. 建立 Python 虛擬環境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. 安裝必要套件：

```powershell
pip install -r requirements.txt
```

4. 安裝 Ollama 並設定模型

本專案使用 Ollama CLI 呼叫本地模型。請先安裝 Ollama，然後指定你要使用的模型名稱，例如 `llama2`。

```powershell
# 安裝 Ollama（依官方教學）
# https://ollama.com/docs/installation

ollama pull llama2
```

5. 建立 `.env` 設定檔（可選）：

```powershell
copy .env.example .env
```

若你安裝了 Ollama，預設會使用 `.env` 中的 `OLLAMA_MODEL`。若 Ollama CLI 非預設路徑，可設定 `OLLAMA_BINARY`。
## 執行方式

```powershell
python main.py "周杰倫"
```

或直接啟動互動模式：

```powershell
python main.py
```

若要啟動前端網頁介面：

```powershell
python web_app.py
```

開啟瀏覽器並前往 `http://127.0.0.1:5000`。

系統會要求輸入歌手名稱，並顯示 AI 代理整理後的回應。

## 注意事項
- 本程式需要網路連線，才能存取 MusicBrainz 資料。
- 由於 MusicBrainz API 會回傳較多錄音項目，系統只會整理前 50 筆歌曲摘要，並說明是否可能不完整。
- 若想使用其他本地模型或 Ollama 設定，請更新 `.env` 中的 `OLLAMA_MODEL` 或 `OLLAMA_BINARY` 設定。

## 建議
- 如果搜尋歌手結果不精確，可嘗試使用完整藝名或中英文混合名稱。
- 若要進一步擴充，可以加入 Spotify API、myMusic 等資料來源，或改善歌手資料清理邏輯。

## DISCLAIMER
- This whole thing was made by github copilot, expect some bugs.
- this was done for my university course project, It is not commercial.
- If there is any issue you are worried about, please contect me via my email  blacktea12ouo@gmail.com