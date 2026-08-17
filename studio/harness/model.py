"""harness/model.py — the LangChain chat-model adapter over models.py.

Every harness model call routes through the EXISTING adapter layer:
  - provider chain: models.active_providers(role) — keys activate via the
    environment exactly as models.py has always done;
  - transport: models.chat_completions — the one OpenAI-compatible client
    (base_url, headers, extra body params from the providers.json entry);
  - caps: the role's max_tokens_in/out from providers.json, enforced per call;
  - ledger: ledger.log_call per request — tokens + cost land in
    state/events.jsonl like any brain-era call.

Only the "openai" family supports tool-calling here; other families are
skipped with a provider_error event, same fall-through semantics as
ModelAdapter.complete(). Credentials are never touched, logged, or stored.
"""

from __future__ import annotations

import json
import time
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ToolMessage,
)
from langchain_core.messages.ai import UsageMetadata
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.utils.function_calling import convert_to_openai_tool

from ledger import log_call, log_event
from models import (
    AllProvidersExhausted,
    BudgetExceeded,
    active_providers,
    chat_completions,
    load_routing,
)


def _content_to_text(content: object) -> str:
    """Flatten LangChain content (str or block list) to plain text."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text", ""))
        return "\n".join(p for p in parts if p)
    return ""


def _to_openai_message(msg: BaseMessage) -> dict:
    role = {
        "system": "system",
        "human": "user",
        "ai": "assistant",
        "tool": "tool",
    }.get(msg.type, "user")
    out: dict[str, Any] = {"role": role, "content": _content_to_text(msg.content)}
    if isinstance(msg, AIMessage) and msg.tool_calls:
        out["tool_calls"] = [
            {
                "id": tc["id"],
                "type": "function",
                "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])},
            }
            for tc in msg.tool_calls
        ]
    if isinstance(msg, ToolMessage):
        out["tool_call_id"] = msg.tool_call_id
    return out


class HarnessChatModel(BaseChatModel):
    """A BaseChatModel that speaks through studio/models.py.

    Instantiated per (role, task) so caps, chain, and ledger attribution are
    the role's own. Tool schemas are bound via bind_tools and forwarded in
    OpenAI `tools` format; tool_calls in the reply become AIMessage tool
    calls, which is what the Deep Agents loop drives on.
    """

    role: str
    task_id: str
    escalation_level: int = 0

    @property
    def _llm_type(self) -> str:
        return "jotbeat-harness"

    def bind_tools(self, tools, *, tool_choice=None, **kwargs):
        formatted = [convert_to_openai_tool(t) for t in tools]
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
        return self.bind(tools=formatted, **kwargs)

    def _generate(self, messages, stop=None, run_manager=None, **kwargs) -> ChatResult:
        routing = load_routing()
        role_cfg = routing["roles"][self.role]
        cap_in = role_cfg["max_tokens_in"]
        cap_out = role_cfg["max_tokens_out"]

        body: dict[str, Any] = {
            "messages": [_to_openai_message(m) for m in messages],
            "max_tokens": cap_out,
        }
        if kwargs.get("tools"):
            body["tools"] = kwargs["tools"]
        if kwargs.get("tool_choice"):
            body["tool_choice"] = kwargs["tool_choice"]

        # Same rough estimate as ModelAdapter.complete — caps are hard limits.
        est_in = len(json.dumps(body["messages"]) + json.dumps(body.get("tools", []))) // 4
        if est_in > cap_in:
            raise BudgetExceeded(
                f"[{self.role}] ~{est_in} input tokens exceeds cap {cap_in}. "
                "Shrink context — do NOT raise the cap mid-task."
            )

        chain = active_providers(self.role)
        if self.escalation_level > 0:
            chain = [p for p in chain if p.get("tier") == "escalation"] or chain

        last_err = None
        for provider in chain:
            t0 = time.time()
            try:
                data = chat_completions(provider, {**body, "model": provider["model"]})
            except Exception as e:  # noqa: BLE001 — chain fall-through, mirroring ModelAdapter.complete
                last_err = e
                log_event(
                    "provider_error",
                    task=self.task_id,
                    role=self.role,
                    provider=provider["name"],
                    error=str(e)[:300],
                )
                continue

            latency_ms = int((time.time() - t0) * 1000)
            try:
                generation = self._parse_response(provider, data)
            except Exception as e:  # noqa: BLE001 — a malformed reply is a failed call; fall through
                last_err = e
                log_event(
                    "provider_error",
                    task=self.task_id,
                    role=self.role,
                    provider=provider["name"],
                    error=f"malformed completion: {e}"[:300],
                )
                continue

            usage = data.get("usage", {}) or {}
            log_call(
                task_id=self.task_id,
                role=self.role,
                provider=provider["name"],
                model=provider["model"],
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0),
                cached_in=usage.get("prompt_cache_hit_tokens", 0),
                retry=0,
                escalated=self.escalation_level > 0,
                latency_ms=latency_ms,
            )
            return ChatResult(generations=[generation])

        raise AllProvidersExhausted(f"[{self.role}] all providers failed: {last_err}")

    @staticmethod
    def _parse_response(provider: dict, data: dict) -> ChatGeneration:
        ch0 = data["choices"][0]
        msg = ch0.get("message", {})
        content = msg.get("content")
        if isinstance(content, list):
            content = "".join(
                p.get("text", "") for p in content if isinstance(p, dict)
            )
        tool_calls = []
        for tc in msg.get("tool_calls") or []:
            fn = tc.get("function", {})
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {"__unparsed_arguments__": fn.get("arguments", "")}
            tool_calls.append(
                {"name": fn.get("name", ""), "args": args, "id": tc.get("id"), "type": "tool_call"}
            )
        if not content and not tool_calls:
            raise AllProvidersExhausted(
                f"{provider['name']}: empty completion "
                f"(finish_reason={ch0.get('finish_reason')})"
            )
        usage = data.get("usage", {}) or {}
        usage_md = UsageMetadata(
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
        )
        ai = AIMessage(
            content=content or "",
            tool_calls=tool_calls,
            usage_metadata=usage_md,
            response_metadata={
                "provider": provider["name"],
                "model": provider["model"],
                "finish_reason": ch0.get("finish_reason"),
            },
        )
        return ChatGeneration(message=ai)
