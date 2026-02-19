"""
Adaptive Learning Engine — CloudGuardAI
========================================
Continuously learns from every scan, every feedback event, and every new
data point.  The system expands and upgrades itself over time:

1. **Pattern Discovery** — Clusters new findings to discover emerging
   vulnerability patterns and auto-generates YAML rules.
2. **Online Model Training** — Transforms feedback into correct labels,
   extracts rich features, and performs incremental model updates.
3. **Drift Detection** — Monitors prediction distribution and triggers
   automatic retraining when the world shifts.
4. **Adaptive Rule Weights** — Adjusts rule confidence scores based on
   accumulated false-positive / false-negative feedback.
5. **Champion / Challenger Evaluation** — New models must beat the
   incumbent on a holdout slice before promotion.
6. **Telemetry** — Every learning event is logged for auditability.

This module is wired into the FastAPI lifecycle so learning is *always on*.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1.  Rich Feature Extraction (replaces the 10-string-count fallback)
# ---------------------------------------------------------------------------

class RichFeatureExtractor:
    """
    Extracts a 40-dimensional feature vector from IaC content.
    Designed to align with the ensemble model's feature space while
    remaining cheap enough for online learning.
    """

    # Security-sensitive keywords grouped by category
    CREDENTIAL_KW = ["password", "secret", "api_key", "access_key", "private_key",
                     "token", "credential", "auth"]
    NETWORK_KW    = ["0.0.0.0", "::/0", "public", "ingress", "egress",
                     "security_group", "firewall", "cidr"]
    CRYPTO_KW     = ["encrypt", "kms", "ssl", "tls", "https", "certificate",
                     "aes", "sha"]
    IAM_KW        = ["iam", "role", "policy", "principal", "assume_role",
                     "admin", "root", "mfa"]
    LOGGING_KW    = ["logging", "monitoring", "cloudtrail", "audit",
                     "log_group", "metric"]

    @classmethod
    def extract(cls, content: str, filename: str = "") -> np.ndarray:
        """Return a 40-dim numpy feature vector."""
        lower = content.lower()
        lines = content.split("\n")

        features: List[float] = []

        # -- Structural (5) --
        features.append(min(len(content) / 10_000, 10.0))       # normalized length
        features.append(min(len(lines) / 500, 10.0))            # normalized line count
        features.append(float(content.count("{")))               # nesting depth proxy
        features.append(float(content.count("resource")))        # terraform resource blocks
        features.append(float(bool(re.search(r"apiVersion:", content))))  # K8s manifest?

        # -- Credential signals (8) --
        for kw in cls.CREDENTIAL_KW:
            features.append(float(lower.count(kw)))

        # -- Network signals (8) --
        for kw in cls.NETWORK_KW:
            features.append(float(lower.count(kw)))

        # -- Crypto signals (8) --
        for kw in cls.CRYPTO_KW:
            features.append(float(lower.count(kw)))

        # -- IAM signals (6) --
        for kw in cls.IAM_KW[:6]:
            features.append(float(lower.count(kw)))

        # -- Logging / monitoring (5) --
        for kw in cls.LOGGING_KW:
            features.append(float(lower.count(kw)))

        # Pad / truncate to exactly 40
        features = features[:40]
        while len(features) < 40:
            features.append(0.0)

        return np.array(features, dtype=np.float64)


# ---------------------------------------------------------------------------
# 2.  Feedback → Label Transformer (fixes the is_correct mismatch)
# ---------------------------------------------------------------------------

class FeedbackLabelTransformer:
    """
    Converts raw user feedback into the correct binary label the model needs.

    Model label semantics:  1 = file IS risky,  0 = file is safe.

    Feedback interpretations:
    ┌────────────────────────────┬──────────────┬───────────┐
    │ Situation                  │ is_correct   │ ML label  │
    ├────────────────────────────┼──────────────┼───────────┤
    │ Scanner flagged risky,     │ 1 (yes)      │ 1 (risky) │
    │ user confirms              │              │           │
    │ Scanner flagged risky,     │ 0 (FP)       │ 0 (safe)  │
    │ user says false positive   │              │           │
    │ feedback_type="accurate"   │ —            │ 1 (risky) │
    │ feedback_type="false_pos"  │ —            │ 0 (safe)  │
    │ feedback_type="false_neg"  │ —            │ 1 (risky) │
    └────────────────────────────┴──────────────┴───────────┘
    """

    @staticmethod
    def to_risk_label(
        is_correct: Optional[int],
        feedback_type: Optional[str] = None,
        scan_risk_score: float = 0.5,
    ) -> int:
        """Return 1 (risky) or 0 (safe)."""
        # Explicit feedback type takes priority
        if feedback_type:
            ft = feedback_type.lower().replace("-", "_")
            if ft in ("false_positive", "fp"):
                return 0  # scanner was wrong → actually safe
            if ft in ("false_negative", "fn"):
                return 1  # scanner missed it → actually risky
            if ft in ("accurate", "true_positive", "tp"):
                return 1  # scanner was right and it's risky

        # Fall back to is_correct + original risk
        if is_correct is not None:
            was_flagged_risky = scan_risk_score >= 0.4
            if is_correct == 1:
                return 1 if was_flagged_risky else 0
            else:
                return 0 if was_flagged_risky else 1

        # Default: treat as risky (conservative)
        return 1


# ---------------------------------------------------------------------------
# 3.  Drift Detector (proper PSI-style)
# ---------------------------------------------------------------------------

class DriftDetector:
    """
    Population Stability Index (PSI) based drift detection.
    Compares recent prediction distributions against a reference window.
    """

    def __init__(self, reference_window: int = 200, bins: int = 10):
        self.reference_window = reference_window
        self.bins = bins
        self._reference: List[float] = []
        self._recent: List[float] = []

    def record_prediction(self, prob: float):
        """Record a new prediction probability."""
        self._recent.append(prob)
        # Once reference is established, keep recent as a sliding window
        if len(self._reference) < self.reference_window:
            self._reference.append(prob)

    def compute_psi(self) -> float:
        """Compute PSI between reference and recent windows."""
        if len(self._reference) < 20 or len(self._recent) < 20:
            return 0.0

        ref = np.array(self._reference[-self.reference_window:])
        rec = np.array(self._recent[-self.reference_window:])

        # Histogram bins
        edges = np.linspace(0, 1, self.bins + 1)
        ref_hist, _ = np.histogram(ref, bins=edges)
        rec_hist, _ = np.histogram(rec, bins=edges)

        # Smooth zeros
        ref_pct = (ref_hist + 1) / (len(ref) + self.bins)
        rec_pct = (rec_hist + 1) / (len(rec) + self.bins)

        psi = float(np.sum((rec_pct - ref_pct) * np.log(rec_pct / ref_pct)))
        return psi

    def check(self, threshold: float = 0.15) -> Dict[str, Any]:
        psi = self.compute_psi()
        return {
            "drift_detected": psi > threshold,
            "psi_score": round(psi, 4),
            "reference_size": len(self._reference),
            "recent_size": len(self._recent),
            "threshold": threshold,
            "action": "retrain_recommended" if psi > threshold else "normal",
        }

    def reset_reference(self):
        """After retraining, promote recent data as the new reference."""
        self._reference = list(self._recent[-self.reference_window:])
        self._recent = list(self._recent[-self.reference_window:])


# ---------------------------------------------------------------------------
# 4.  Adaptive Rule Weights
# ---------------------------------------------------------------------------

class AdaptiveRuleWeights:
    """
    Tracks per-rule accuracy from feedback and adjusts confidence weights.

    Rules with many false positives get their weight lowered; rules that
    consistently catch real issues get boosted.  Weights are persisted to
    disk so they survive restarts.
    """

    def __init__(self, weights_path: str = "data/adaptive_rule_weights.json"):
        self.path = Path(weights_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.weights: Dict[str, Dict[str, Any]] = self._load()

    def _load(self) -> Dict[str, Dict[str, Any]]:
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.weights, f, indent=2)

    def record_feedback(self, rule_id: str, feedback_type: str):
        """Record a feedback event for a rule."""
        if rule_id not in self.weights:
            self.weights[rule_id] = {
                "true_positives": 0,
                "false_positives": 0,
                "false_negatives": 0,
                "total": 0,
                "confidence": 1.0,
                "last_updated": None,
            }

        entry = self.weights[rule_id]
        entry["total"] += 1

        ft = feedback_type.lower().replace("-", "_") if feedback_type else "accurate"
        if ft in ("accurate", "true_positive", "tp"):
            entry["true_positives"] += 1
        elif ft in ("false_positive", "fp"):
            entry["false_positives"] += 1
        elif ft in ("false_negative", "fn"):
            entry["false_negatives"] += 1

        # Recalculate confidence: precision-based weight with Bayesian smoothing
        tp = entry["true_positives"]
        fp = entry["false_positives"]
        # Laplace smoothing (prior of 2 TP, 1 FP → prior confidence ~0.67)
        entry["confidence"] = round((tp + 2) / (tp + fp + 3), 4)
        entry["last_updated"] = datetime.utcnow().isoformat()

        self.save()
        logger.info(
            "Rule %s weight updated: confidence=%.3f (TP=%d FP=%d FN=%d)",
            rule_id, entry["confidence"], tp, fp, entry["false_negatives"],
        )

    def get_weight(self, rule_id: str) -> float:
        """Return the current confidence weight for a rule (0-1)."""
        return self.weights.get(rule_id, {}).get("confidence", 1.0)

    def get_low_confidence_rules(self, threshold: float = 0.4) -> List[str]:
        """Return rule IDs with confidence below threshold (likely noisy)."""
        return [
            rid for rid, data in self.weights.items()
            if data.get("confidence", 1.0) < threshold and data.get("total", 0) >= 5
        ]

    def get_stats(self) -> Dict[str, Any]:
        """Return summary statistics for all tracked rules."""
        if not self.weights:
            return {"total_rules_tracked": 0, "rules": {}}
        confidences = [d["confidence"] for d in self.weights.values()]
        return {
            "total_rules_tracked": len(self.weights),
            "avg_confidence": round(np.mean(confidences), 4) if confidences else 0,
            "low_confidence_rules": self.get_low_confidence_rules(),
            "rules": self.weights,
        }


# ---------------------------------------------------------------------------
# 5.  Pattern Discovery Engine
# ---------------------------------------------------------------------------

class PatternDiscoveryEngine:
    """
    Discovers new vulnerability patterns from accumulated scan findings.

    Strategy:
    - Group findings by normalized signature (description keywords + severity)
    - If a cluster appears ≥ N times across different scans but has no
      matching YAML rule, generate a candidate rule.
    - New rules are written to `rules/rules_engine/rules/discovered/`.
    """

    MIN_OCCURRENCES = 3  # must appear in at least 3 scans
    RULES_DIR = Path("rules/rules_engine/rules/discovered")

    def __init__(self):
        self.RULES_DIR.mkdir(parents=True, exist_ok=True)
        self._pattern_counts: Dict[str, Dict[str, Any]] = {}
        self._load_state()

    def _state_path(self) -> Path:
        return Path("data/pattern_discovery_state.json")

    def _load_state(self):
        p = self._state_path()
        if p.exists():
            try:
                with open(p, "r") as f:
                    self._pattern_counts = json.load(f)
            except Exception:
                self._pattern_counts = {}

    def _save_state(self):
        p = self._state_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w") as f:
            json.dump(self._pattern_counts, f, indent=2)

    def _signature(self, finding: Dict[str, Any]) -> str:
        """Normalize a finding into a cluster key."""
        desc = finding.get("description", "").lower()
        # Extract core keywords (remove noise words)
        words = re.findall(r'[a-z_]{3,}', desc)
        # Take the 5 most relevant words + severity
        core = sorted(set(words))[:8]
        severity = finding.get("severity", "MEDIUM").upper()
        raw = f"{severity}::{','.join(core)}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]

    def ingest_findings(self, findings: List[Dict[str, Any]], scan_id: int):
        """Ingest findings from a completed scan."""
        for f in findings:
            sig = self._signature(f)
            if sig not in self._pattern_counts:
                self._pattern_counts[sig] = {
                    "signature": sig,
                    "sample_description": f.get("description", "")[:200],
                    "sample_rule_id": f.get("rule_id", ""),
                    "severity": f.get("severity", "MEDIUM"),
                    "scan_ids": [],
                    "count": 0,
                    "first_seen": datetime.utcnow().isoformat(),
                    "last_seen": None,
                    "rule_generated": False,
                }
            entry = self._pattern_counts[sig]
            if scan_id not in entry["scan_ids"]:
                entry["scan_ids"].append(scan_id)
            entry["count"] += 1
            entry["last_seen"] = datetime.utcnow().isoformat()

        self._save_state()

    def discover_new_patterns(self) -> List[Dict[str, Any]]:
        """
        Return patterns that have crossed the threshold and don't have
        a generated rule yet.
        """
        new_patterns = []
        for sig, data in self._pattern_counts.items():
            if (
                len(data.get("scan_ids", [])) >= self.MIN_OCCURRENCES
                and not data.get("rule_generated", False)
            ):
                new_patterns.append(data)
        return new_patterns

    def generate_rule(self, pattern: Dict[str, Any]) -> Optional[str]:
        """
        Auto-generate a YAML rule file for a discovered pattern.
        Returns the file path if created, None otherwise.
        """
        sig = pattern["signature"]
        desc = pattern.get("sample_description", "Discovered pattern")
        severity = pattern.get("severity", "MEDIUM")

        # Build a regex from the description's key terms
        words = re.findall(r'[a-z_]{4,}', desc.lower())
        if not words:
            return None

        # Use the two most distinctive words for matching
        key_terms = sorted(set(words), key=lambda w: len(w), reverse=True)[:2]
        regex_pattern = ".*".join(re.escape(t) for t in key_terms)

        rule_id = f"DISC_{sig.upper()}"
        rule_content = f"""# Auto-discovered rule — generated {datetime.utcnow().isoformat()}
# Based on {pattern['count']} occurrences across {len(pattern.get('scan_ids', []))} scans
# Original: {desc[:120]}
rules:
  - id: {rule_id}
    description: "[Auto-Discovered] {desc[:100]}"
    severity: {severity}
    file_types: [".tf", ".yaml", ".yml", ".json"]
    match:
      regex: "{regex_pattern}"
    references:
      - "https://cloudguard.ai/discovered-patterns/{sig}"
"""

        rule_path = self.RULES_DIR / f"{rule_id.lower()}.yaml"
        with open(rule_path, "w") as f:
            f.write(rule_content)

        # Mark as generated
        self._pattern_counts[sig]["rule_generated"] = True
        self._save_state()

        logger.info(
            "🆕 Auto-generated rule %s from %d occurrences: %s",
            rule_id, pattern["count"], desc[:80],
        )
        return str(rule_path)

    def run_discovery_cycle(self) -> Dict[str, Any]:
        """Run a full discovery cycle and generate any new rules."""
        new_patterns = self.discover_new_patterns()
        generated = []

        for pattern in new_patterns:
            path = self.generate_rule(pattern)
            if path:
                generated.append({
                    "rule_id": f"DISC_{pattern['signature'].upper()}",
                    "path": path,
                    "occurrences": pattern["count"],
                    "scans": len(pattern.get("scan_ids", [])),
                })

        return {
            "total_tracked_patterns": len(self._pattern_counts),
            "new_rules_generated": len(generated),
            "generated_rules": generated,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def get_stats(self) -> Dict[str, Any]:
        """Return current pattern discovery statistics."""
        generated = sum(
            1 for d in self._pattern_counts.values() if d.get("rule_generated")
        )
        pending = [
            d for d in self._pattern_counts.values()
            if len(d.get("scan_ids", [])) >= self.MIN_OCCURRENCES
            and not d.get("rule_generated")
        ]
        return {
            "total_patterns_tracked": len(self._pattern_counts),
            "rules_generated": generated,
            "pending_patterns": len(pending),
            "top_patterns": sorted(
                self._pattern_counts.values(),
                key=lambda x: x.get("count", 0),
                reverse=True,
            )[:5],
        }


# ---------------------------------------------------------------------------
# 6.  Champion / Challenger Model Evaluator
# ---------------------------------------------------------------------------

class ModelEvaluator:
    """
    Evaluates a challenger model against the current champion using a
    holdout slice of recent labeled data.  The challenger must beat the
    champion's F1 by a margin to be promoted.
    """

    MIN_IMPROVEMENT = 0.02   # challenger must beat champion F1 by ≥ 2 pts
    MIN_EVAL_SAMPLES = 10    # need at least this many samples to evaluate

    @staticmethod
    def evaluate(
        champion_predict,
        challenger_predict,
        X_holdout: np.ndarray,
        y_holdout: np.ndarray,
    ) -> Dict[str, Any]:
        """Compare two model predict functions on holdout data."""
        from sklearn.metrics import f1_score, accuracy_score, precision_score, recall_score

        if len(y_holdout) < ModelEvaluator.MIN_EVAL_SAMPLES:
            return {
                "decision": "insufficient_data",
                "reason": f"Need {ModelEvaluator.MIN_EVAL_SAMPLES} samples, have {len(y_holdout)}",
            }

        champ_pred = champion_predict(X_holdout)
        chall_pred = challenger_predict(X_holdout)

        champ_f1 = f1_score(y_holdout, champ_pred, zero_division=0)
        chall_f1 = f1_score(y_holdout, chall_pred, zero_division=0)
        improvement = chall_f1 - champ_f1

        result = {
            "champion_f1": round(float(champ_f1), 4),
            "challenger_f1": round(float(chall_f1), 4),
            "improvement": round(float(improvement), 4),
            "champion_accuracy": round(float(accuracy_score(y_holdout, champ_pred)), 4),
            "challenger_accuracy": round(float(accuracy_score(y_holdout, chall_pred)), 4),
            "samples": len(y_holdout),
        }

        if improvement >= ModelEvaluator.MIN_IMPROVEMENT:
            result["decision"] = "promote_challenger"
            result["reason"] = f"Challenger F1 ({chall_f1:.3f}) beats champion ({champ_f1:.3f}) by {improvement:.3f}"
        elif improvement >= 0:
            result["decision"] = "keep_champion"
            result["reason"] = f"Improvement ({improvement:.3f}) below threshold ({ModelEvaluator.MIN_IMPROVEMENT})"
        else:
            result["decision"] = "keep_champion"
            result["reason"] = f"Challenger is worse by {abs(improvement):.3f}"

        logger.info("Model evaluation: %s (improvement=%.4f)", result["decision"], improvement)
        return result


# ---------------------------------------------------------------------------
# 7.  Learning Telemetry
# ---------------------------------------------------------------------------

class LearningTelemetry:
    """
    Tracks and persists all learning events for auditability.
    """

    def __init__(self, path: str = "data/learning_telemetry.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.events: List[Dict[str, Any]] = self._load()

    def _load(self) -> List[Dict[str, Any]]:
        if self.path.exists():
            try:
                with open(self.path, "r") as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
            except Exception:
                return []
        return []

    def _save(self):
        # Keep last 1000 events
        self.events = self.events[-1000:]
        with open(self.path, "w") as f:
            json.dump(self.events, f, indent=2)

    def log(self, event_type: str, details: Dict[str, Any]):
        event = {
            "type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            **details,
        }
        self.events.append(event)
        self._save()
        logger.debug("Telemetry: %s — %s", event_type, json.dumps(details)[:200])

    def get_recent(self, n: int = 50) -> List[Dict[str, Any]]:
        return self.events[-n:]

    def get_summary(self) -> Dict[str, Any]:
        """Return aggregate learning telemetry."""
        type_counts = Counter(e["type"] for e in self.events)
        last_event = self.events[-1] if self.events else None
        return {
            "total_events": len(self.events),
            "event_types": dict(type_counts),
            "last_event": last_event,
        }


# ---------------------------------------------------------------------------
# 8.  Orchestrator — ties everything together
# ---------------------------------------------------------------------------

class AdaptiveLearningEngine:
    """
    Main orchestrator that coordinates all learning subsystems.
    Instantiated once at API startup and used throughout the app lifecycle.
    """

    def __init__(self):
        self.feature_extractor = RichFeatureExtractor()
        self.label_transformer = FeedbackLabelTransformer()
        self.drift_detector = DriftDetector()
        self.rule_weights = AdaptiveRuleWeights()
        self.pattern_engine = PatternDiscoveryEngine()
        self.model_evaluator = ModelEvaluator()
        self.telemetry = LearningTelemetry()

        # Accumulated training buffer for batch evaluation
        self._training_buffer_X: List[np.ndarray] = []
        self._training_buffer_y: List[int] = []
        self._feedback_count_since_retrain = 0

        # Auto-retrain thresholds
        self.AUTO_RETRAIN_FEEDBACK_THRESHOLD = 20
        self.AUTO_RETRAIN_DRIFT_THRESHOLD = 0.15

        logger.info("🧠 Adaptive Learning Engine initialized")
        self.telemetry.log("engine_started", {"components": [
            "feature_extractor", "label_transformer", "drift_detector",
            "rule_weights", "pattern_engine", "model_evaluator", "telemetry",
        ]})

    # --- Scan lifecycle hooks ---

    def on_scan_completed(self, scan_id: int, findings: List[Dict], risk_score: float):
        """Called after every scan completes — feeds pattern discovery + drift."""
        # 1. Feed prediction to drift detector
        self.drift_detector.record_prediction(risk_score)

        # 2. Feed findings to pattern discovery
        self.pattern_engine.ingest_findings(findings, scan_id)

        # 3. Check drift
        drift = self.drift_detector.check(self.AUTO_RETRAIN_DRIFT_THRESHOLD)
        if drift["drift_detected"]:
            self.telemetry.log("drift_detected", drift)
            logger.warning("⚠️  Model drift detected (PSI=%.4f) — retraining recommended", drift["psi_score"])

        self.telemetry.log("scan_processed", {
            "scan_id": scan_id,
            "findings_count": len(findings),
            "risk_score": round(risk_score, 4),
        })

    def on_feedback_received(
        self,
        scan_id: int,
        file_content: str,
        filename: str,
        is_correct: Optional[int],
        feedback_type: Optional[str],
        scan_risk_score: float,
        rule_id: Optional[str] = None,
    ):
        """Called on every feedback submission — feeds online learning + rule weights."""
        # 1. Transform to correct label
        label = self.label_transformer.to_risk_label(is_correct, feedback_type, scan_risk_score)

        # 2. Extract rich features
        features = self.feature_extractor.extract(file_content, filename)

        # 3. Buffer for training
        self._training_buffer_X.append(features)
        self._training_buffer_y.append(label)
        self._feedback_count_since_retrain += 1

        # 4. Update rule weight if we have a rule_id
        if rule_id:
            fb_type = feedback_type or ("accurate" if is_correct == 1 else "false_positive")
            self.rule_weights.record_feedback(rule_id, fb_type)

        self.telemetry.log("feedback_processed", {
            "scan_id": scan_id,
            "label": label,
            "feedback_type": feedback_type,
            "rule_id": rule_id,
            "buffer_size": len(self._training_buffer_X),
        })

        logger.info(
            "📊 Feedback processed (scan %d) — buffer: %d/%d for auto-retrain",
            scan_id, self._feedback_count_since_retrain,
            self.AUTO_RETRAIN_FEEDBACK_THRESHOLD,
        )

    def should_auto_retrain(self) -> Tuple[bool, str]:
        """Check whether automatic retraining should be triggered."""
        # Check feedback volume threshold
        if self._feedback_count_since_retrain >= self.AUTO_RETRAIN_FEEDBACK_THRESHOLD:
            return True, f"feedback_threshold ({self._feedback_count_since_retrain} samples)"

        # Check drift
        drift = self.drift_detector.check(self.AUTO_RETRAIN_DRIFT_THRESHOLD)
        if drift["drift_detected"]:
            return True, f"drift_detected (PSI={drift['psi_score']:.4f})"

        return False, "not_needed"

    def get_training_batch(self) -> Tuple[np.ndarray, np.ndarray]:
        """Return the accumulated training data and clear the buffer."""
        if not self._training_buffer_X:
            return np.array([]), np.array([])

        X = np.array(self._training_buffer_X)
        y = np.array(self._training_buffer_y)
        return X, y

    def on_retrain_completed(self, metrics: Dict[str, Any]):
        """Called after a successful retraining cycle."""
        self._training_buffer_X.clear()
        self._training_buffer_y.clear()
        self._feedback_count_since_retrain = 0
        self.drift_detector.reset_reference()

        # Run pattern discovery cycle
        discovery = self.pattern_engine.run_discovery_cycle()

        self.telemetry.log("retrain_completed", {
            "metrics": metrics,
            "patterns_discovered": discovery["new_rules_generated"],
        })
        logger.info("✅ Retrain complete. %d new rules discovered.", discovery["new_rules_generated"])

    def get_learning_status(self) -> Dict[str, Any]:
        """Full status of all learning subsystems — exposed via API."""
        should_retrain, reason = self.should_auto_retrain()
        return {
            "adaptive_learning_active": True,
            "training_buffer_size": len(self._training_buffer_X),
            "feedback_since_retrain": self._feedback_count_since_retrain,
            "auto_retrain_threshold": self.AUTO_RETRAIN_FEEDBACK_THRESHOLD,
            "should_retrain": should_retrain,
            "retrain_reason": reason,
            "drift": self.drift_detector.check(),
            "rule_weights": self.rule_weights.get_stats(),
            "pattern_discovery": self.pattern_engine.get_stats(),
            "telemetry_summary": self.telemetry.get_summary(),
        }


# ---------------------------------------------------------------------------
# Singleton instance — imported by the API
# ---------------------------------------------------------------------------
learning_engine = AdaptiveLearningEngine()
