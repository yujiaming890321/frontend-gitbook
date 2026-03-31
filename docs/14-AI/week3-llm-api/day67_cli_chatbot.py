"""
Day 6-7: 综合练习 — 命令行聊天机器人

综合运用本周所有知识点：
- Day 1: Ollama 本地调用
- Day 2: 多 provider 支持
- Day 3: OpenAI 格式参数
- Day 4: 流式输出
- Day 5: 多轮对话管理

用法:
  python day67_cli_chatbot.py                    # 默认用 Ollama
  python day67_cli_chatbot.py --provider deepseek  # 用 DeepSeek
  python day67_cli_chatbot.py --model llama3.2    # 指定模型

命令:
  /clear    清空对话历史
  /history  查看对话历史
  /tokens   查看 token 用量
  /model    切换模型
  /system   修改 system prompt
  /save     保存对话到文件
  /exit     退出
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


# ============================================================
# Configuration
# ============================================================

@dataclass
class BotConfig:
    """Chatbot configuration"""
    provider: str = "ollama"
    model: str = ""
    system_prompt: str = "你是一个有用的 AI 助手，回答简洁精准。"
    temperature: float = 0.7
    max_tokens: int = 2000
    stream: bool = True
    max_history: int = 30

    PROVIDER_DEFAULTS = {
        "ollama": {"base_url": "http://localhost:11434/v1", "api_key": "ollama", "model": "qwen2.5:7b"},
        "deepseek": {"base_url": "https://api.deepseek.com", "api_key": "", "model": "deepseek-chat"},
        "dashscope": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "api_key": "", "model": "qwen-turbo"},
    }

    def get_client(self) -> OpenAI:
        """Create OpenAI client for the configured provider"""
        defaults = self.PROVIDER_DEFAULTS.get(self.provider, self.PROVIDER_DEFAULTS["ollama"])
        api_key = defaults["api_key"] or os.getenv(f"{self.provider.upper()}_API_KEY", "")
        return OpenAI(base_url=defaults["base_url"], api_key=api_key)

    def get_model(self) -> str:
        """Get model name, using provider default if not specified"""
        if self.model:
            return self.model
        return self.PROVIDER_DEFAULTS.get(self.provider, {}).get("model", "qwen2.5:7b")


# ============================================================
# Conversation Manager
# ============================================================

@dataclass
class ConversationManager:
    """Manage conversation history and token tracking"""
    config: BotConfig
    messages: list[dict] = field(default_factory=list)
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    turn_count: int = 0

    def __post_init__(self):
        self.messages = [{"role": "system", "content": self.config.system_prompt}]

    def add_user_message(self, content: str):
        self.messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content: str):
        self.messages.append({"role": "assistant", "content": content})
        self.turn_count += 1

    def _trim(self):
        """Keep messages within max_history limit"""
        if len(self.messages) > self.config.max_history:
            system = self.messages[0]
            recent = self.messages[-(self.config.max_history - 1):]
            self.messages = [system] + recent

    def clear(self):
        self.messages = [{"role": "system", "content": self.config.system_prompt}]
        self.turn_count = 0

    def update_system_prompt(self, new_prompt: str):
        self.config.system_prompt = new_prompt
        self.messages[0] = {"role": "system", "content": new_prompt}

    def save_to_file(self, path: str | None = None) -> str:
        """Save conversation to JSON file"""
        if path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            path = f"chat_history_{timestamp}.json"

        data = {
            "provider": self.config.provider,
            "model": self.config.get_model(),
            "turns": self.turn_count,
            "tokens": {
                "prompt": self.total_prompt_tokens,
                "completion": self.total_completion_tokens,
                "total": self.total_prompt_tokens + self.total_completion_tokens,
            },
            "messages": self.messages,
            "saved_at": datetime.now().isoformat(),
        }

        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return path

    def show_history(self):
        """Display conversation history"""
        for m in self.messages:
            role_label = {"system": "SYS", "user": "YOU", "assistant": "BOT"}[m["role"]]
            content = m["content"][:100] + ("..." if len(m["content"]) > 100 else "")
            print(f"  [{role_label}] {content}")

    def show_tokens(self):
        """Display token usage statistics"""
        print(f"  对话轮次: {self.turn_count}")
        print(f"  输入 tokens: {self.total_prompt_tokens}")
        print(f"  输出 tokens: {self.total_completion_tokens}")
        print(f"  总计 tokens: {self.total_prompt_tokens + self.total_completion_tokens}")


# ============================================================
# Chat Engine
# ============================================================

class ChatEngine:
    """Handle LLM API calls with streaming support"""

    def __init__(self, config: BotConfig):
        self.config = config
        self.client = config.get_client()

    def chat(self, conv: ConversationManager, user_input: str) -> str:
        """Send message and get response (streaming or non-streaming)"""
        conv.add_user_message(user_input)

        try:
            if self.config.stream:
                return self._stream_chat(conv)
            else:
                return self._sync_chat(conv)
        except Exception as e:
            error_msg = f"[错误: {e}]"
            print(error_msg)
            return error_msg

    def _stream_chat(self, conv: ConversationManager) -> str:
        """Streaming chat — print tokens as they arrive"""
        stream = self.client.chat.completions.create(
            model=self.config.get_model(),
            messages=conv.messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            stream=True,
        )

        full_response = ""
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                print(delta.content, end="", flush=True)
                full_response += delta.content

        print()  # newline after stream ends
        conv.add_assistant_message(full_response)
        return full_response

    def _sync_chat(self, conv: ConversationManager) -> str:
        """Non-streaming chat"""
        response = self.client.chat.completions.create(
            model=self.config.get_model(),
            messages=conv.messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        reply = response.choices[0].message.content
        conv.add_assistant_message(reply)

        if response.usage:
            conv.total_prompt_tokens += response.usage.prompt_tokens
            conv.total_completion_tokens += response.usage.completion_tokens

        print(reply)
        return reply


# ============================================================
# Command Handler
# ============================================================

def handle_command(command: str, conv: ConversationManager, engine: ChatEngine) -> bool:
    """
    Handle slash commands. Returns True to continue, False to exit.
    """
    cmd = command.strip().lower()

    if cmd == "/exit" or cmd == "/quit":
        print("再见！")
        return False

    elif cmd == "/clear":
        conv.clear()
        print("对话已清空。")

    elif cmd == "/history":
        print("--- 对话历史 ---")
        conv.show_history()

    elif cmd == "/tokens":
        print("--- Token 用量 ---")
        conv.show_tokens()

    elif cmd == "/save":
        path = conv.save_to_file()
        print(f"对话已保存到: {path}")

    elif cmd.startswith("/model"):
        parts = cmd.split(maxsplit=1)
        if len(parts) > 1:
            engine.config.model = parts[1]
            print(f"模型已切换为: {parts[1]}")
        else:
            print(f"当前模型: {engine.config.get_model()}")

    elif cmd.startswith("/system"):
        parts = cmd.split(maxsplit=1)
        if len(parts) > 1:
            conv.update_system_prompt(parts[1])
            print(f"System prompt 已更新。")
        else:
            print(f"当前 system prompt: {conv.config.system_prompt}")

    elif cmd == "/help":
        print("""
可用命令:
  /clear    清空对话历史
  /history  查看对话历史
  /tokens   查看 token 用量
  /model    查看/切换模型
  /system   查看/修改 system prompt
  /save     保存对话到文件
  /help     显示帮助
  /exit     退出
""")
    else:
        print(f"未知命令: {cmd}，输入 /help 查看帮助")

    return True


# ============================================================
# Main Loop
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="CLI Chatbot")
    parser.add_argument("--provider", default="ollama", choices=["ollama", "deepseek", "dashscope"])
    parser.add_argument("--model", default="")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--no-stream", action="store_true")
    args = parser.parse_args()

    config = BotConfig(
        provider=args.provider,
        model=args.model,
        temperature=args.temperature,
        stream=not args.no_stream,
    )

    conv = ConversationManager(config)
    engine = ChatEngine(config)

    print(f"AI 聊天机器人 (provider={config.provider}, model={config.get_model()})")
    print("输入消息开始对话，输入 /help 查看命令，输入 /exit 退出\n")

    while True:
        try:
            user_input = input("你: ").strip()
            if not user_input:
                continue

            if user_input.startswith("/"):
                should_continue = handle_command(user_input, conv, engine)
                if not should_continue:
                    break
            else:
                print("AI: ", end="")
                engine.chat(conv, user_input)
                print()

        except KeyboardInterrupt:
            print("\n再见！")
            break
        except EOFError:
            print("\n再见！")
            break


if __name__ == "__main__":
    main()


# ============================================================
# 扩展练习
# ============================================================

# TODO 1: 添加 /export 命令
# 把对话导出为 Markdown 格式，方便阅读和分享

# TODO 2: 添加对话自动总结
# 每 10 轮自动生成一次对话摘要
# 显示在 /history 的开头

# TODO 3: 添加 /persona 命令
# 预设几个角色模板：code_reviewer, teacher, translator
# /persona code_reviewer → 自动设置对应的 system prompt

# TODO 4: 添加输入历史
# 用 readline 或 prompt_toolkit 实现上下箭头翻历史
