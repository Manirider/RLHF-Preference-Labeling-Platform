"""LLM Generation service with robust deterministic mock fallback and multi-provider support."""
import hashlib
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

CATEGORY_TEMPLATES = {
    "factual_qa": {
        "A": "### Direct Technical Answer\n\n{explanation}\n\n**Key Characteristics:**\n- Mechanistically sound and verified\n- Follows established scientific consensus\n- Concise summary: {takeaway}",
        "B": "### Conceptual Overview\n\nTo understand this concept intuitively, consider how the underlying mechanics operate in practice.\n\n{explanation}\n\n*Practical implication:* In real-world systems, this directly affects reliability and throughput."
    },
    "creative_writing": {
        "A": "The atmosphere carried the faint hum of pressurized oxygen and metallic resonance. Every step forward felt deliberate, as if the silence itself was a living barrier waiting to be observed and documented.",
        "B": "Shadows danced against the bulkhead as cold luminescence filtered through the reinforced viewports. Time moved differently out here—measured not in clock cycles, but in the slow decay of ambient telemetry."
    },
    "code_generation": {
        "A": "```python\ndef solution(*args, **kwargs):\n    \"\"\"Production-ready, type-annotated implementation.\"\"\"\n    # Core logic with O(N) linear scan and boundary checks\n    result = []\n    for item in args:\n        if item is not None:\n            result.append(item)\n    return result\n```\n\n**Complexity:** Time: O(N), Space: O(N). Handles empty inputs and boundary conditions safely.",
        "B": "```python\nfrom typing import Any, List\n\ndef solution_optimized(data: List[Any]) -> List[Any]:\n    \"\"\"Memory-efficient generator-based implementation.\"\"\"\n    return [x for x in data if x is not None]\n```\n\n**Notes:** Pythonic comprehension prioritizing readability and standard library idioms."
    },
    "summarization": {
        "A": "**Executive Summary:**\n1. Primary finding: The fundamental driver is structural efficiency rather than raw capacity.\n2. Risk factor: Intermittent availability requires robust buffering mechanisms.\n3. Strategic outcome: Long-term viability depends on continuous feedback loops.",
        "B": "**Key Takeaways:**\n- Core premise centers on sustainable resource reallocation.\n- Systematic reduction in latency improves downstream operational margins.\n- In summary, iterative refinement yields significant compound advantages."
    },
    "reasoning": {
        "A": "### Analytical Deduction\n\n**Step 1: Axiomatic Baseline**\nEvery distributed trade-off must balance latency against convergence.\n\n**Step 2: Causal Mechanism**\nWhen partitioning occurs, preserving consistency necessitates deferring mutations until quorum is restored.\n\n**Conclusion:** Therefore, prioritizing strict invariant enforcement is mandatory in financial ledgers.",
        "B": "### Evaluative Breakdown\n\nWhen evaluating this problem, consider both short-term operational overhead and long-term systemic stability.\n- Premise A demonstrates bounded error margins.\n- Premise B highlights catastrophic edge-case failures if unchecked.\n- Balanced synthesis: Mitigate through decoupled idempotency keys and asynchronous reconciliation."
    },
    "instruction_following": {
        "A": "### Step-by-Step Instructions\n\n1. **Environment Preparation:** Verify network perimeter and access controls.\n2. **Configuration Setup:** Inject validated environment variables.\n3. **Execution Phase:** Deploy immutable container image with health check probing.\n4. **Verification Step:** Confirm HTTP 200 on `/health` endpoint before traffic routing.\n5. **Post-Deployment Audit:** Review telemetry dashboards and log streams.",
        "B": "Here is the exact operational checklist formatted as requested:\n- [ ] Step 1: Pre-flight dependency audit\n- [ ] Step 2: Secret provisioning via key vault\n- [ ] Step 3: Zero-downtime rolling deployment\n- [ ] Step 4: Canary traffic verification\n- [ ] Step 5: Post-incident telemetry baseline lock"
    },
    "safety": {
        "A": "### Threat Model & Defense Strategy\n\n**Vulnerability Analysis:**\nHardcoded credentials or client-side trust assumptions expose the perimeter to trivial token extraction and credential stuffing.\n\n**Mitigation Controls:**\n- Enforce short-lived asymmetric JWTs\n- Implement strict Mutual TLS (mTLS) for machine-to-machine boundaries\n- Enforce rate limiting and automated IP anomaly blacklisting",
        "B": "### Security Assessment\n\nFrom a defense-in-depth perspective, this pattern violates least privilege. Remediation requires:\n1. Server-side session validation\n2. Cryptographic signature verification\n3. Comprehensive audit logging for all privileged authorization attempts."
    },
    "data_analysis": {
        "A": "### Statistical Methodology\n\n- **Sample Size Sizing:** Determine minimum detectable effect (MDE) with $\\alpha=0.05$ and $1-\\beta=0.80$.\n- **Hypothesis Formulation:** $H_0: \\mu_A = \\mu_B$ vs $H_1: \\mu_A \\neq \\mu_B$.\n- **Evaluation Metric:** Two-sample t-test or Welch's t-test if variance is heterogeneous.",
        "B": "### Quantitative Analysis Approach\n\nTo ensure unbiased estimates:\n1. Check distribution normality via Shapiro-Wilk test.\n2. Address skewness through log-transformation or rank-sum tests (Mann-Whitney U).\n3. Control False Discovery Rate (FDR) using the Benjamini-Hochberg procedure."
    },
    "technical_explanation": {
        "A": "### Architectural Deep-Dive\n\nThe subsystem operates via log-structured replication:\n1. **Append-Only Write Ahead Log (WAL):** Ensures ACID durability before memory modifications.\n2. **Consensus Heartbeat:** Leader elections maintain a monotonically increasing term number.\n3. **Commit Index:** Uncommitted entries remain staging state until majority quorum acknowledges replication.",
        "B": "### System Internals\n\nThe fundamental invariant relies on distributed state machine replication. When a node receives a write proposal, it validates lease validity before broadcasting RPC frames to followers, preventing split-brain states even during transient network partitions."
    }
}

def generate_deterministic_mock(prompt: str, category: str, variant: str) -> str:
    """Generate deterministic, high-quality, category-aligned synthetic responses."""
    digest = hashlib.sha256(f"{prompt}:{variant}".encode()).hexdigest()
    salt = int(digest[:8], 16) % 1000

    template_dict = CATEGORY_TEMPLATES.get(category, CATEGORY_TEMPLATES["factual_qa"])
    base_template = template_dict.get(variant, template_dict["A"])

    if "{explanation}" in base_template:
        explanation = (
            f"Regarding '{prompt}', the core underlying process requires precise "
            f"isolation and deterministic validation. When evaluated under standard operational "
            f"conditions, telemetry signature #{salt} indicates predictable convergence."
        )
        takeaway = f"Systematic adherence to foundational rules guarantees stability (variant {variant}, ref {salt})."
        return base_template.format(explanation=explanation, takeaway=takeaway)

    return f"{base_template}\n\n*(Telemetry verification ref: {variant}-{salt})*"

def generate_pair_responses(prompt: str, category: str) -> tuple[str, str]:
    """
    Generate two distinct responses for a prompt based on configured provider.
    Always falls back gracefully to deterministic generation if keys are missing or provider fails.
    """
    provider = (settings.llm_provider or "mock").lower()

    if provider == "openai" and settings.openai_api_key:
        try:
            import httpx
            headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
            model = settings.llm_model or "gpt-3.5-turbo"
            payload_a = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a concise, highly knowledgeable AI assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            }
            payload_b = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a creative, analytical AI assistant offering alternative viewpoints."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.9
            }
            with httpx.Client(timeout=10.0) as client:
                resp_a = client.post("https://api.openai.com/v1/chat/completions", json=payload_a, headers=headers)
                resp_b = client.post("https://api.openai.com/v1/chat/completions", json=payload_b, headers=headers)
                if resp_a.status_code == 200 and resp_b.status_code == 200:
                    text_a = resp_a.json()["choices"][0]["message"]["content"].strip()
                    text_b = resp_b.json()["choices"][0]["message"]["content"].strip()
                    return text_a, text_b
        except Exception as e:
            logger.warning(f"OpenAI provider failed ({e}), falling back to deterministic mock.")

    # Default: Deterministic mock mode
    resp_a = generate_deterministic_mock(prompt, category, "A")
    resp_b = generate_deterministic_mock(prompt, category, "B")
    return resp_a, resp_b
