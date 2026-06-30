from __future__ import annotations

import json
from pathlib import Path
import sys

import pytest

from virgilio_connector.litellm_gateway import (LiteLLMBudgetError,
                                                LiteLLMGateway,
                                                LiteLLMGatewayConfig,
                                                LiteLLMRequest)


def test_gateway_returns_mock_response_with_budget_metadata():
    result = LiteLLMGateway(LiteLLMGatewayConfig(
        model="gpt-4o-mini", max_total_tokens=500, max_output_tokens=80,
        max_cost_eur=0.1, estimated_cost_per_1k_tokens_eur=0.002,
    )).run(LiteLLMRequest(
        prompt="Classifica questo allegato in modo prudente.",
        metadata={"account_alias": "demo_box"},
    ))
    assert result.dry_run is True
    assert result.provider == "mock"
    assert result.total_tokens <= 500
    assert result.estimated_cost_eur <= 0.1
    assert "Mock LiteLLM response" in result.output_text
    assert result.warnings == ("mock_provider_only",)


def test_gateway_blocks_prompt_over_token_budget_before_provider_is_called():
    calls = []
    gateway = LiteLLMGateway(
        LiteLLMGatewayConfig(max_total_tokens=20, max_output_tokens=10, max_cost_eur=1.0),
        provider=lambda request, config: calls.append("called"),
    )
    with pytest.raises(LiteLLMBudgetError, match="token budget exceeded"):
        gateway.run(LiteLLMRequest(prompt="x" * 80))
    assert calls == []


def test_gateway_blocks_prompt_over_character_budget():
    gateway = LiteLLMGateway(LiteLLMGatewayConfig(max_prompt_chars=12, max_cost_eur=1.0))
    with pytest.raises(LiteLLMBudgetError, match="prompt exceeds local limit"):
        gateway.run(LiteLLMRequest(prompt="questo prompt supera il limite"))


def test_gateway_blocks_provider_result_over_cost_budget():
    gateway = LiteLLMGateway(
        LiteLLMGatewayConfig(
            max_total_tokens=500,
            max_output_tokens=400,
            max_cost_eur=0.001,
            estimated_cost_per_1k_tokens_eur=0.01,
        ),
        provider=lambda request, config: {
            "output_text": "mock answer",
            "completion_tokens": 300,
            "finish_reason": "stop",
        },
    )
    with pytest.raises(LiteLLMBudgetError, match="cost budget exceeded"):
        gateway.run(LiteLLMRequest(prompt="prompt breve"))


def test_cli_litellm_gateway_dry_run_returns_json(tmp_path, monkeypatch, capsys):
    from virgilio_connector.__main__ import main

    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Classifica senza azioni automatiche.", encoding="utf-8")
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "litellm-gateway-dry-run",
        "--prompt-file", str(prompt),
        "--budget-tokens", "300",
        "--max-cost-eur", "0.02",
    ])
    assert main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["dry_run"] is True
    assert payload["provider"] == "mock"
    assert payload["total_tokens"] <= 300


def test_cli_litellm_gateway_command_is_registered(tmp_path, monkeypatch):
    from virgilio_connector.__main__ import main

    missing = tmp_path / "missing.txt"
    monkeypatch.setattr(sys, "argv", [
        "virgilio", "litellm-gateway-dry-run",
        "--prompt-file", str(missing),
    ])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
