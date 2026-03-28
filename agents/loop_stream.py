from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from agents.tools import TOOLS, TOOL_MAPPER

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)


def agent_loop(messages: list):
    while True:
        print("\033[92m思考中...\033[0m")
        response = client.chat.completions.create(
            model="deepseek-chat",
            tools=TOOLS,
            messages=messages,
            max_tokens=8000,
            stream=True,
        )

        content_chunks = []
        tool_calls_chunks = {}
        tool_call_printed = set()

        for chunk in response:
            delta = chunk.choices[0].delta

            if delta.content:
                print(delta.content, end="", flush=True)
                content_chunks.append(delta.content)

            if delta.tool_calls:
                for tool_call_delta in delta.tool_calls:
                    idx = tool_call_delta.index
                    if idx not in tool_calls_chunks:
                        tool_calls_chunks[idx] = {
                            "id": "",
                            "type": "function",
                            "function": {"name": "", "arguments": ""},
                        }
                    if tool_call_delta.id:
                        tool_calls_chunks[idx]["id"] = tool_call_delta.id
                    if tool_call_delta.function:
                        if tool_call_delta.function.name:
                            tool_calls_chunks[idx]["function"]["name"] = (
                                tool_call_delta.function.name
                            )
                            if idx not in tool_call_printed:
                                print(
                                    f"\n\033[33m🛠️ [调用工具] {tool_call_delta.function.name}\033[0m"
                                )
                                print("\033[90m   参数: \033[0m", end="", flush=True)
                                tool_call_printed.add(idx)
                        if tool_call_delta.function.arguments:
                            tool_calls_chunks[idx]["function"]["arguments"] += (
                                tool_call_delta.function.arguments
                            )
                            print(
                                tool_call_delta.function.arguments,
                                end="",
                                flush=True,
                            )

        print()

        full_content = "".join(content_chunks) if content_chunks else None

        tool_calls = None
        if tool_calls_chunks:
            tool_calls = []
            for idx in sorted(tool_calls_chunks.keys()):
                tc = tool_calls_chunks[idx]
                tool_calls.append(
                    {
                        "id": tc["id"],
                        "type": tc["type"],
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                )

        messages.append(
            {"role": "assistant", "content": full_content, "tool_calls": tool_calls}
        )

        if not tool_calls:
            return

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            args = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call["id"]
            if tool_name not in TOOL_MAPPER:
                result = f"工具 {tool_name} 不存在"
            else:
                result = TOOL_MAPPER[tool_name](**args)
            out = result if len(result) < 500 else result[:500] + "\n... (输出已截断)"
            print(f"\033[32m   执行结果: {out}\033[0m")
            messages.append(
                {"role": "tool", "tool_call_id": tool_call_id, "content": result}
            )

        print()