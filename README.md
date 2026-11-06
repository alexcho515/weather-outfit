# 天氣穿搭建議

用 Python（uv）呼叫雲端模型（Google Gemini API）的小程式。使用的 LLM 能力：**工具呼叫（tool calling）**。

使用者輸入「我要去某城市，怎麼穿？」，模型會自己決定先呼叫 `get_weather(city)` 查詢天氣，
程式執行函式並把結果回傳給模型，模型再根據氣溫、天氣狀況、降雨機率，用繁體中文給出穿搭建議。
天氣資料是自己編寫的示範資料，沒有串接外部天氣 API。

作品頁：`https://<你的帳號>.github.io/<repo 名稱>/`（部署後請替換成實際網址）

## 專案結構

```
.
├── main.py                      # 主程式：雲端模型工具呼叫，輸出 results.json
├── results.json                 # 本機執行結果（commit 進 repo，供作品頁使用）
├── scripts/build_page.py        # 讀 results.json，產生 site/index.html
├── .github/workflows/pages.yml  # GitHub Actions：自動部署 GitHub Pages
├── pyproject.toml               # uv 專案設定
├── .env.example                 # 環境變數範例（真正的 .env 不進 repo）
└── .gitignore
```

## 執行步驟

1. 安裝 [uv](https://docs.astral.sh/uv/)，並到 [Google AI Studio](https://aistudio.google.com/apikey) 申請 API 金鑰。
2. 安裝套件：
   ```bash
   uv sync
   ```
3. 複製 `.env.example` 為 `.env`，把 `LLM_API_KEY` 換成你自己的金鑰。
   若模型名稱失效，可在 `.env` 設定 `LLM_MODEL`。
4. 執行程式，會在終端機印出每題的工具呼叫與建議，並寫入 `results.json`：
   ```bash
   uv run python main.py
   ```
5. 在本機預覽作品頁：
   ```bash
   python scripts/build_page.py   # 產生 site/index.html
   ```

## GitHub Actions 與 Pages

為了不讓金鑰離開本機，流程是：**本機執行 `main.py` → commit `results.json` → push 到 `main`**，
workflow 會用 `results.json` 產生網頁並自動部署，過程中不會呼叫模型，也不需要金鑰。

第一次使用請到 repo 的 **Settings → Pages → Source** 選擇 **GitHub Actions**，
之後每次 push 都會自動部署，可在 Actions 分頁確認綠燈。

## 安全注意

- 金鑰只放 `.env`，且 `.env` 已列在 `.gitignore`（請在第一次 commit 前確認）。
- `.env.example` 只放假的範例值，不要把真的金鑰貼進去。

## AI 使用說明

請見作品頁第 4 節；內容在 `scripts/build_page.py` 的 `AI_USAGE` 區塊，請改成你自己的實際使用與驗證情況。
