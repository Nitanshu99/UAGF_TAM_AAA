"""Zero-cost end-to-end check of the observability wiring.

``python -m scripts.obs_probe`` makes ONE LLM call through the same seam
every agent uses — ``BaseAgent.acompletion`` → ``flex_acompletion`` →
``write_audit`` — with LiteLLM's ``mock_response``, so no provider is
contacted and nothing is billed. It then verifies the call surfaced in each
sink: ``logs/audit/llm_audit.jsonl``, the shared Prometheus directory, the
API's ``/metrics``, Loki (through Grafana's datasource proxy) and Langfuse's
public API. Sinks whose service is not running are reported as skipped, not
failed, so the probe is usable on a partial stack.
"""
