"""天氣穿搭建議：用雲端模型（Google Gemini API）的「工具呼叫（tool calling）」，
讓模型自己查天氣再給穿搭建議。

流程：
1. 使用者問「我明天要去某城市，穿什麼？」
2. 模型決定呼叫 get_weather(city)（工具呼叫）
3. 程式執行假天氣函式，把結果回傳給模型
4. 模型根據天氣資料，用繁體中文給出穿搭建議
5. 全部結果存成 results.json，之後由 build_page.py 產生作品頁

金鑰只從環境變數 / .env 讀取，絕對不要寫在程式碼裡，也不要 commit .env。
"""

import json
import os
import sys
import time
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()  # 讀取 .env（已被 .gitignore 排除）

API_KEY = os.getenv("LLM_API_KEY")
# Gemini 提供 OpenAI 相容的介面，所以可以用 openai 套件呼叫
BASE_URL = os.getenv("LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
MODEL = os.getenv("LLM_MODEL", "gemini-3.5-flash-lite")

# ---- 假的天氣資料（自己編的，沒有串任何外部 API）----
FAKE_WEATHER = {
    "台北": {"temp_c": 18, "condition": "陰雨", "rain_chance": 80, "wind": "東北風 4 級"},
    "台中": {"temp_c": 24, "condition": "多雲", "rain_chance": 20, "wind": "微風"},
    "高雄": {"temp_c": 30, "condition": "晴朗", "rain_chance": 5, "wind": "微風"},
    "東京": {"temp_c": 9, "condition": "晴朗", "rain_chance": 10, "wind": "北風 3 級"},
    "首爾": {"temp_c": -2, "condition": "下雪", "rain_chance": 70, "wind": "強風"},
}

QUESTIONS = [
    "我明天要去台北，應該怎麼穿？",
    "我週末要去台中逛街，穿什麼比較好？",
    "下週去高雄衝浪，要怎麼穿搭？",
    "我要去東京出差，需要帶什麼外套？",
    "我去首爾旅行，穿搭要注意什麼？",
]

SYSTEM_PROMPT = (
    "你是一位穿搭顧問。使用者提到城市時，一定要先呼叫 get_weather 工具查詢天氣，"
    "再根據查到的氣溫、天氣狀況與降雨機率，用繁體中文給出具體穿搭建議（上衣、下身、外套、配件），"
    "有需要時提醒帶傘。回答請控制在 120 字以內。"
)

# 告訴模型有哪些工具可以用（工具呼叫的「說明書」）
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查詢指定城市的天氣（示範用的假資料）",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名稱，例如 台北、台中、高雄、東京、首爾",
                    }
                },
                "required": ["city"],
            },
        },
    }
]


def get_weather(city: str) -> dict:
    """查詢指定城市的天氣（示範用的假資料）。"""
    data = FAKE_WEATHER.get(city)
    if data is None:
        return {"error": f"查無 {city} 的天氣資料", "available": list(FAKE_WEATHER)}
    return {"city": city, **data}


AVAILABLE_FUNCTIONS = {"get_weather": get_weather}


def ask(client: OpenAI, question: str) -> dict:
    """問一個問題，處理工具呼叫迴圈，回傳這一題的完整紀錄。"""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tool_calls_log = []

    # 最多跑 3 輪，避免模型一直重複呼叫工具
    for _ in range(3):
        response = client.chat.completions.create(model=MODEL, messages=messages, tools=TOOLS)
        message = response.choices[0].message
        messages.append(message.model_dump(exclude_none=True))

        if not message.tool_calls:
            return {
                "question": question,
                "tool_calls": tool_calls_log,
                "answer": (message.content or "").strip(),
            }

        for call in message.tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            func = AVAILABLE_FUNCTIONS.get(name)
            result = func(**args) if func else {"error": f"未知工具 {name}"}
            tool_calls_log.append({"name": name, "arguments": args, "result": result})
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return {"question": question, "tool_calls": tool_calls_log, "answer": "（模型未能在限定輪數內完成回答）"}


def main() -> None:
    if not API_KEY:
        sys.exit("找不到 LLM_API_KEY。請複製 .env.example 成 .env，並把你的金鑰填進去。")

    # timeout：最多等 60 秒；max_retries：失敗時最多自動重試 1 次（避免畫面卡很久沒反應）
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=60.0, max_retries=1)
    print(f"使用模型：{MODEL}\n", flush=True)
    results = []
    try:
        for i, q in enumerate(QUESTIONS, start=1):
            print(f"[{i}/{len(QUESTIONS)}] {q}")
            record = ask(client, q)
            for tc in record["tool_calls"]:
                print(f"    工具呼叫：{tc['name']}({tc['arguments']}) -> {tc['result']}")
            print(f"    建議：{record['answer']}\n")
            results.append(record)
            time.sleep(2)  # 放慢一點，避免免費額度的每分鐘限制
    except OpenAIError as err:
        status = getattr(err, "status_code", None)
        detail = getattr(err, "body", None) or str(err)
        sys.exit(
            f"呼叫模型失敗：{type(err).__name__}（狀態碼：{status}）\n詳細訊息：{detail}\n"
            "請檢查金鑰、模型名稱（LLM_MODEL）是否正確，或稍後再試。"
        )

    output = {
        "model": MODEL,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "results": results,
    }
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print("已儲存 results.json")


if __name__ == "__main__":
    main()
