"""
Formatting helpers for Part 9 signal history.

Produces readable text and JSON from real SignalRecord objects.
No order execution and no probability claims.
"""

import json

from core.signal_history import SignalRecord


class SignalFormatter:
    @staticmethod
    def to_text(record: SignalRecord) -> str:
        lines = []

        lines.append("NeuroTrade AI Signal Record")
        lines.append(f"Record ID: {record.record_id}")
        lines.append(f"Created at (local): {record.created_at}")
        lines.append(f"Engine: {record.engine} ({record.engine_version})")
        lines.append("")

        lines.append(
            f"Symbol: {record.symbol} | Timeframe: {record.timeframe}"
        )
        lines.append(f"Decision candle time: {record.decision_time}")
        lines.append(
            f"Rows used: {record.rows_used} | "
            f"Exclude latest candle: {'Yes' if record.exclude_latest else 'No'}"
        )
        lines.append("")

        lines.append(f"Action: {record.action}")
        lines.append(f"Heuristic score: {record.score:.2f}")
        lines.append(f"Heuristic confidence: {record.confidence:.1f}/100")
        lines.append(
            "Confidence is a weighted rule score, NOT a win probability."
        )
        lines.append("")

        lines.append("Rule contributions:")
        if record.reasons:
            for reason in record.reasons:
                lines.append(f"  {reason}")
        else:
            lines.append("  No valid rule contributions.")

        if record.warnings:
            lines.append("")
            lines.append("Warnings:")
            for warning in record.warnings:
                lines.append(f"  {warning}")

        if record.weights:
            lines.append("")
            lines.append("Rule weights:")
            for name, weight in record.weights.items():
                lines.append(f"  {name:<24} {float(weight):8.3f}")

        if record.inputs:
            lines.append("")
            lines.append("Decision inputs:")
            for name, value in record.inputs.items():
                lines.append(f"  {name}: {value}")

        lines.append("")
        lines.append(
            "Heuristic decision record only. No order was sent by this module."
        )

        return "\n".join(lines)

    @staticmethod
    def to_json(record: SignalRecord) -> str:
        return json.dumps(
            {
                "record_id": record.record_id,
                "created_at": record.created_at,
                "engine": record.engine,
                "engine_version": record.engine_version,
                "symbol": record.symbol,
                "timeframe": record.timeframe,
                "decision_time": record.decision_time,
                "action": record.action,
                "score": record.score,
                "confidence": record.confidence,
                "confidence_is_probability": False,
                "rows_used": record.rows_used,
                "exclude_latest": record.exclude_latest,
                "inputs": record.inputs,
                "reasons": record.reasons,
                "warnings": record.warnings,
                "weights": record.weights,
                "order_sent": False,
            },
            indent=2,
            ensure_ascii=True,
        )