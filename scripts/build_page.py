"""讀取 results.json，產生 GitHub Pages 作品頁（site/index.html）。

只用標準函式庫，所以 GitHub Actions 上不需要安裝任何套件，也不需要金鑰。
用法：python scripts/build_page.py [results.json] [輸出資料夾]
"""

import html
import json
import sys
from pathlib import Path

# ====== 請依照你自己的實際情況修改這一區（作業要求：寫出用了什麼工具、用在哪裡、自己修改或驗證了什麼）======
AI_USAGE = [
    {
        "tool": "Claude（Anthropic）",
        "where": "協助規劃專案結構、產生 main.py / build_page.py / workflow 的初版程式碼與 README 草稿",
        "mine": "在自己的電腦實際執行並除錯：預設模型 gemini-2.5-flash 回傳 404，查官方文件後改用 gemini-3.5-flash-lite 才成功；金鑰只放在 .env，並確認 .env 不會進 repo。",
    },
    {
        "tool": "Google Gemini API（模型名稱見下方執行結果）",
        "where": "程式執行時，由模型決定呼叫 get_weather 並根據結果產生穿搭建議",
        "mine": "逐題檢查 5 筆執行結果：每題都有先呼叫 get_weather，且建議內容與回傳的氣溫、降雨機率一致，例如台北 18 度、降雨 80% 時建議攜帶雨具。",
    },
]
# =====================================================================================================

e = html.escape


def render(data: dict) -> str:
    rows = []
    for i, r in enumerate(data["results"], start=1):
        calls = "<br>".join(
            f"<code>{e(c['name'])}({e(json.dumps(c['arguments'], ensure_ascii=False))})</code><br>"
            f"<small>{e(json.dumps(c['result'], ensure_ascii=False))}</small>"
            for c in r["tool_calls"]
        ) or "<em>（模型沒有呼叫工具）</em>"
        rows.append(
            f"<tr><td>{i}</td><td>{e(r['question'])}</td><td>{calls}</td><td>{e(r['answer'])}</td></tr>"
        )

    usage_items = "".join(
        f"<li><strong>{e(u['tool'])}</strong><br>用在哪裡：{e(u['where'])}<br>我自己做的修改／驗證：{e(u['mine'])}</li>"
        for u in AI_USAGE
    )

    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>天氣穿搭建議</title>
<style>
  body {{ font-family: system-ui, "Noto Sans TC", sans-serif; max-width: 960px; margin: 0 auto; padding: 24px 16px; line-height: 1.7; color: #222; }}
  h1 {{ border-bottom: 3px solid #b31500; padding-bottom: 8px; }}
  h2 {{ color: #b31500; margin-top: 2em; }}
  pre {{ background: #f4f4f4; padding: 12px; overflow-x: auto; border-radius: 6px; }}
  code {{ background: #f4f4f4; padding: 1px 4px; border-radius: 4px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  th, td {{ border: 1px solid #ccc; padding: 8px; vertical-align: top; text-align: left; }}
  th {{ background: #b31500; color: #fff; }}
  tr:nth-child(even) td {{ background: #faf0ec; }}
  .meta {{ color: #666; font-size: 0.9em; }}
</style>
</head>
<body>
<h1>天氣穿搭建議</h1>

<h2>1. 做了什麼</h2>
<p>這是一支用 Python（uv）呼叫雲端模型（Google Gemini API）的小程式，使用的 LLM 能力是<strong>工具呼叫（tool calling）</strong>：
使用者輸入「我要去某城市，怎麼穿？」，模型會自己判斷需要先呼叫 <code>get_weather(city)</code> 查詢天氣，
程式執行該函式後把氣溫、天氣狀況與降雨機率回傳給模型，模型再據此用繁體中文給出穿搭建議。
天氣資料為自己編寫的示範資料，沒有串接外部 API。</p>

<h2>2. 怎麼執行</h2>
<pre>uv sync
# 複製 .env.example 為 .env，填入自己的 LLM_API_KEY（.env 不會進 repo）
uv run python main.py          # 產生 results.json
python scripts/build_page.py   # 產生 site/index.html（Actions 也會自動執行）</pre>
<p>為了避免把金鑰放到 GitHub，<code>main.py</code> 只在本機執行；<code>results.json</code> 由本機產生後 commit，
GitHub Actions 只負責把它轉成這個網頁並部署到 GitHub Pages，過程中不會呼叫模型，也不需要金鑰。</p>

<h2>3. 執行結果</h2>
<p class="meta">模型：{e(data['model'])}　產生時間：{e(data['generated_at'])}</p>
<table>
<thead><tr><th>#</th><th>使用者問題</th><th>工具呼叫與回傳</th><th>模型的穿搭建議</th></tr></thead>
<tbody>
{''.join(rows)}
</tbody>
</table>

<h2>4. AI 使用說明</h2>
<ul>{usage_items}</ul>
</body>
</html>
"""


def main() -> None:
    results_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("results.json")
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("site")

    if not results_path.exists():
        sys.exit(f"找不到 {results_path}，請先在本機執行 main.py 並把 results.json commit 進 repo")

    data = json.loads(results_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(render(data), encoding="utf-8")
    print(f"已產生 {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
