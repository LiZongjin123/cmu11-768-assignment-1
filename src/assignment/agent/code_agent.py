"""The Part 1 coding agent: fix a software issue and submit a git patch."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from assignment.agent.base import (
    DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
    DEFAULT_COMPACTION_MAX_TOKENS,
    Agent,
    format_tool_output,
)
from assignment.agent.tools import EXECUTE_TOOL, SEND_MESSAGE_TOOL
from assignment.env import Environment
from jsonschema import validate, ValidationError

class CodeAgent(Agent):
    """An agent that fixes a software issue and submits a git patch."""

    def __init__(
        self,
        task: str,
        environment: Environment,
        model: str | None = None,
        logs_save_path: str | None = None,
        step_limit: int = 100,
        skills_path: str | None = None,
        auto_stop_environment: bool = True,
        compact_threshold_tokens: int | None = None,
        compaction_keep_recent_steps: int = DEFAULT_COMPACTION_KEEP_RECENT_STEPS,
        compaction_max_tokens: int = DEFAULT_COMPACTION_MAX_TOKENS,
    ):
        super().__init__(
            environment=environment,
            model=model,
            logs_save_path=logs_save_path,
            step_limit=step_limit,
            skills_path=skills_path,
            auto_stop_environment=auto_stop_environment,
            compact_threshold_tokens=compact_threshold_tokens,
            compaction_keep_recent_steps=compaction_keep_recent_steps,
            compaction_max_tokens=compaction_max_tokens,
        )
        self.task = task
        self.submitted_patch = ""

        # TODO(Part 1.3): Make the `execute` and `send_message` tools available
        # to the agent.

        # TODO(1.1.b): Construct the system prompt and task_prompt. These
        # should be usable by the `Agent.build_prompt` method.
        self.system_prompt = (
            "<system_information>\n"
            "{\n"
            f"  \"machine\": {self.env.machine},\n"
            f"  \"release\": {self.env.release},\n"
            f"  \"system\": {self.env.system},\n"
            f"  \"version\": {self.env.version}\n"
            "}\n"
            "</system_information>"
        )
        self.task_prompt = task

        # TODO(1.4): If any skills are available to the agent, make their
        # descriptions/metadata available to the agent in the prompt.
        skills_list = ""
        for value in self.skills.values():
            skills_list += (
                "{\n"
                f"  {value["metadata"]}\n"
                "},\n"
            )
        skills_prompt = (
            "<available_skills>\n"
            f"{skills_list}"
            "<available_skills>"
        )
        self.system_prompt += f"\n{skills_prompt}"

    def execute_tool_calls(
        self, tool_calls: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Execute ``execute`` and ``send_message`` calls in the code sandbox."""

        # TODO(Part 1.3): Parse each call, execute recognized tools, and return
        # one message per call (there may be multiple tool calls in one agent
        # response!). Malformed JSON and unknown tools must become recoverable
        # observations relayed to the agent instead of exceptions.
        
        output = []
        for tool_call in tool_calls:
            result = {
                "role": "tool",
                "tool_call_id": tool_call["id"],
            }
            if tool_call["type"] == "function":
                if tool_call["function"]["name"] == "execute":
                    result["content"] = self.__handle_execute_tool_calling(tool_call["function"]["arguments"])
                elif tool_call["function"]["name"] == "send_message":
                    result["content"] = self.__handle_send_message_tool_calling(tool_call["function"]["arguments"])
            output.append(result)
        return output
                    
    def __send_message(self, summary:str) -> str:
        print(summary)
        return "success"

    def __handle_execute_tool_calling(self, arguments: str) -> str:
        schema = EXECUTE_TOOL["function"]["parameters"]
        try:
            args = json.loads(arguments)
            validate(args, schema)
        except json.JSONDecodeError:
            return "Arguments error: invalid JSON."
        except ValidationError as exc:
            return f"Arguments error: {exc.message}"
        else:
            return format_tool_output(self.env.execute(**args))

    def __handle_send_message_tool_calling(self, arguments: str) -> str:
        schema = SEND_MESSAGE_TOOL["function"]["parameters"]
        try:
            args = json.loads(arguments)
            validate(args, schema)
        except json.JSONDecodeError:
            return "Arguments error: invalid JSON."
        except ValidationError as exc:
            return f"Arguments error: {exc.message}"
        else:
            return self.__send_message(**args)
