"""Tests for the local log analyzer parsing helpers."""

import sys
from pathlib import Path

# Allow running the file directly with `python tests/test_local_analyzer.py`
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.llm.local_analyzer import LocalLogAnalyzer


def _parse(text: str):
    analyzer = LocalLogAnalyzer.__new__(LocalLogAnalyzer)
    analyzer.model = "test-model"
    return LocalLogAnalyzer._parse_analysis_result(analyzer, text, [])


def test_parse_handles_parenthetical_numbering():
    analysis_text = """SUMMARY: Overall system health is degraded but stable.

KEY INSIGHTS:
1) Database connection pool exhaustion created request queueing.
2) Payment gateway timeouts are retrying and hitting the retry cap.
3) Suspicious activity from IP 203.0.113.45 continues despite rate limiting.

RECOMMENDATIONS:
1) Increase database pool capacity or add a read replica immediately.
2) Engage the payment vendor and implement exponential backoff on retries.
3) Block the malicious IP and tighten API authentication monitoring.

CONFIDENCE: 0.82"""

    result = _parse(analysis_text)

    assert result.summary.startswith("Overall system health")
    assert result.key_insights == [
        "Database connection pool exhaustion created request queueing.",
        "Payment gateway timeouts are retrying and hitting the retry cap.",
        "Suspicious activity from IP 203.0.113.45 continues despite rate limiting.",
    ]
    assert result.recommendations == [
        "Increase database pool capacity or add a read replica immediately.",
        "Engage the payment vendor and implement exponential backoff on retries.",
        "Block the malicious IP and tighten API authentication monitoring.",
    ]
    assert result.confidence_score == 0.82


def test_parse_cleans_markdown_bullets():
    analysis_text = """SUMMARY: Incidents resolved but some risk remains.

KEY INSIGHTS:
- **Critical** database saturation recovered after scaling web-server-01.
- **Security** repeated credential stuffing attempts detected overnight.

RECOMMENDATIONS:
- **Immediate** add proactive database autoscaling runbooks.
- **Follow-up** tighten rate limits and extend security monitoring to partner APIs.

CONFIDENCE: high"""

    result = _parse(analysis_text)

    assert result.key_insights == [
        "Critical database saturation recovered after scaling web-server-01.",
        "Security repeated credential stuffing attempts detected overnight.",
    ]
    assert result.recommendations == [
        "Immediate add proactive database autoscaling runbooks.",
        "Follow-up tighten rate limits and extend security monitoring to partner APIs.",
    ]
    assert result.confidence_score == 0.9
