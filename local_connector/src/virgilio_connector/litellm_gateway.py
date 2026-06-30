"""Mock-only LiteLLM gateway for future classification flows."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Callable, Mapping


class LiteLLMGatewayError(RuntimeError):
    """Safe failure for the future LiteLLM adapter."""


class LiteLLMBudgetError(LiteLLMGatewayError):
    """Raised when a request exceeds the configured local budget."""


@dataclass(frozen=True, slots=True)
class LiteLLMGatewayConfig:
    provider: str = "mock"
    model: str = "gpt-4o-mini"
    max_total_tokens: int = 2000
    max_output_tokens: int = 400
    max_prompt_chars: int = 12000
    max_cost_eur: float = 0.5
    estimated_cost_per_1k_tokens_eur: float = 0.002

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("provider is required")
        if not self.model.strip():
            raise ValueError("model is required")
        if self.max_total_tokens <= 0:
            raise ValueError("max_total_tokens must be positive")
        if self.max_output_tokens <= 0:
            raise ValueError("max_output_tokens must be positive")
        if self.max_output_tokens > self.max_total_tokens:
            raise ValueError("max_output_tokens cannot exceed max_total_tokens")
        if self.max_prompt_chars <= 0:
            raise ValueError("max_prompt_chars must be positive")
        if self.max_cost_eur <= 0:
            raise ValueError("max_cost_eur must be positive")
        if self.estimated_cost_per_1k_tokens_eur <= 0:
            raise ValueError("estimated_cost_per_1k_tokens_eur must be positive")


@dataclass(frozen=True, slots=True)
class LiteLLMRequest:
    prompt: str
    system_prompt: str = ""
    metadata: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not self.prompt.strip():
            raise ValueError("prompt is required")
        if self.metadata is not None:
            for key, value in self.metadata.items():
                if not str(key).strip() or not str(value).strip():
                    raise ValueError("metadata keys and values must be non-empty strings")


@dataclass(frozen=True, slots=True)
class LiteLLMResponse:
    provider: str
    model: str
    dry_run: bool
    output_text: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost_eur: float
    finish_reason: str
    warnings: tuple[str, ...] = ()


class MockLiteLLMProvider:
    """Provider stub that never performs network calls."""

    def __call__(self, request: LiteLLMRequest, config: LiteLLMGatewayConfig) -> dict[str, Any]:
        metadata_summary = ", ".join(
            f"{key}={value}" for key, value in sorted((request.metadata or {}).items())
        )
        suffix = f" [{metadata_summary}]" if metadata_summary else ""
        preview = request.prompt.strip().replace("\r", " ").replace("\n", " ")
        if len(preview) > 80:
            preview = preview[:77] + "..."
        return {
            "output_text": f"Mock LiteLLM response for {config.model}: {preview}{suffix}",
            "completion_tokens": min(64, config.max_output_tokens),
            "finish_reason": "stop",
            "warnings": ("mock_provider_only",),
        }


class LiteLLMGateway:
    def __init__(self, config: LiteLLMGatewayConfig, *,
                 provider: Callable[[LiteLLMRequest, LiteLLMGatewayConfig], Mapping[str, Any]] | None = None) -> None:
        self.config = config
        self.provider = provider or MockLiteLLMProvider()

    def run(self, request: LiteLLMRequest) -> LiteLLMResponse:
        prompt_chars = len(request.prompt) + len(request.system_prompt)
        if prompt_chars > self.config.max_prompt_chars:
            raise LiteLLMBudgetError(
                f"prompt exceeds local limit: {prompt_chars}>{self.config.max_prompt_chars} chars"
            )
        prompt_tokens = _estimate_tokens(request.prompt) + _estimate_tokens(request.system_prompt)
        estimated_total_tokens = prompt_tokens + self.config.max_output_tokens
        self._assert_budget(estimated_total_tokens)
        raw_response = dict(self.provider(request, self.config))
        completion_tokens = raw_response.get("completion_tokens")
        output_text = raw_response.get("output_text")
        finish_reason = raw_response.get("finish_reason", "stop")
        warnings = tuple(str(item) for item in raw_response.get("warnings", ()))
        if isinstance(completion_tokens, bool) or not isinstance(completion_tokens, int) or completion_tokens < 0:
            raise LiteLLMGatewayError("provider returned invalid completion_tokens")
        if not isinstance(output_text, str) or not output_text.strip():
            raise LiteLLMGatewayError("provider returned invalid output_text")
        if not isinstance(finish_reason, str) or not finish_reason.strip():
            raise LiteLLMGatewayError("provider returned invalid finish_reason")
        total_tokens = prompt_tokens + completion_tokens
        self._assert_budget(total_tokens)
        return LiteLLMResponse(
            provider=self.config.provider,
            model=self.config.model,
            dry_run=True,
            output_text=output_text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_eur=_estimate_cost(total_tokens, self.config.estimated_cost_per_1k_tokens_eur),
            finish_reason=finish_reason,
            warnings=warnings,
        )

    def _assert_budget(self, total_tokens: int) -> None:
        if total_tokens > self.config.max_total_tokens:
            raise LiteLLMBudgetError(
                f"token budget exceeded: {total_tokens}>{self.config.max_total_tokens}"
            )
        estimated_cost = _estimate_cost(total_tokens, self.config.estimated_cost_per_1k_tokens_eur)
        if estimated_cost > self.config.max_cost_eur:
            raise LiteLLMBudgetError(
                f"cost budget exceeded: {estimated_cost:.6f}>{self.config.max_cost_eur:.6f} EUR"
            )


def _estimate_tokens(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return max(1, math.ceil(len(stripped) / 4))


def _estimate_cost(total_tokens: int, rate_per_1k_tokens_eur: float) -> float:
    return round((total_tokens / 1000) * rate_per_1k_tokens_eur, 6)
