import os
import json
from typing import Any
from groq import Groq
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

class CustomLogger:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def log_message(self, title: str, content: Any, style: str = "bold green"):
        if not self.verbose:
            return

        if isinstance(content, str):
            if content.strip().startswith("{") or content.strip().startswith("["):
                try:
                    parsed_content = json.loads(content)
                    formatted_content = json.dumps(parsed_content, indent=2)
                    syntax = Syntax(formatted_content, "json", theme="monokai", line_numbers=True)
                    console.print(Panel(syntax, title=title, expand=False, border_style=style))
                except json.JSONDecodeError:
                    console.print(Panel(content, title=title, expand=False, border_style=style))
            elif "\n" in content:
                syntax = Syntax(content, "python", theme="monokai", line_numbers=True)
                console.print(Panel(syntax, title=title, expand=False, border_style=style))
            else:
                console.print(Panel(content, title=title, expand=False, border_style=style))
        elif isinstance(content, (dict, list)):
            formatted_content = json.dumps(content, indent=2)
            syntax = Syntax(formatted_content, "json", theme="monokai", line_numbers=True)
            console.print(Panel(syntax, title=title, expand=False, border_style=style))
        else:
            console.print(Panel(str(content), title=title, expand=False, border_style=style))

class GroqLLM:
    def __init__(self, api_key: str, verbose: bool = False):
        self.client = Groq(api_key=api_key)
        self.logger = CustomLogger(verbose=verbose)

    def generate(self, prompt: str) -> str:
        self.logger.log_message("PROMPT", prompt, style="bold cyan")
        
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-70b-versatile",
        )

        response = chat_completion.choices[0].message.content
        
        self.logger.log_message("RESPONSE", response, style="bold magenta")

        return response
    