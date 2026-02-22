"""
Attack Path Analyzer — Content-Based Graph Analysis
=====================================================
Builds an infrastructure dependency graph from IaC content and detects
multi-hop attack paths by analyzing resource relationships, security
misconfigurations, and data flows.

Unlike the PyTorch Geometric GNN scanner, this works purely on parsed
content — no external ML libraries required. It produces:
  - Concrete attack path chains (e.g., Open SG → Public EC2 → S3 Bucket)
  - Graph data (nodes + edges) for frontend visualization
  - Specific resource names, types, and the vulnerabilities at each hop
"""

from __future__ import annotations

import re
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ── Vulnerability signatures per resource type ─────────────────────────────
_VULN_SIGNATURES: Dict[str, List[Dict[str, Any]]] = {
    "aws_security_group": [
        {"pattern": r'cidr_blocks\s*=\s*\[\s*"0\.0\.0\.0/0"\s*\]',
         "vuln": "Unrestricted ingress (0.0.0.0/0)", "severity": "HIGH",
         "remediation": "Restrict CIDR blocks to specific IP ranges"},
        {"pattern": r'from_port\s*=\s*0[\s\S]*?to_port\s*=\s*(0|65535)',
         "vuln": "All ports open", "severity": "CRITICAL",
         "remediation": "Limit port ranges to necessary services only"},
        {"pattern": r'protocol\s*=\s*"-1"',
         "vuln": "All protocols allowed", "severity": "HIGH",
         "remediation": "Restrict to specific protocols (tcp, udp)"},
    ],
    "aws_instance": [
        {"pattern": r'associate_public_ip_address\s*=\s*true',
         "vuln": "Public IP assigned", "severity": "MEDIUM",
         "remediation": "Place instance behind a load balancer or NAT gateway"},
        {"pattern": r'user_data\s*=.*(?:password|secret|key)',
         "vuln": "Secrets in user_data", "severity": "CRITICAL",
         "remediation": "Use AWS Secrets Manager or Parameter Store for credentials"},
    ],
    "aws_db_instance": [
        {"pattern": r'publicly_accessible\s*=\s*true',
         "vuln": "Database publicly accessible", "severity": "CRITICAL",
         "remediation": "Set publicly_accessible = false and use VPC peering"},
        {"pattern": r'storage_encrypted\s*=\s*false',
         "vuln": "Database storage not encrypted", "severity": "HIGH",
         "remediation": "Enable storage_encrypted = true with KMS key"},
        {"pattern": r'password\s*=\s*"[^"]*"',
         "vuln": "Hardcoded database password", "severity": "CRITICAL",
         "remediation": "Use aws_secretsmanager_secret or variable references"},
    ],
    "aws_s3_bucket": [
        {"pattern": r'acl\s*=\s*"public-read"',
         "vuln": "S3 bucket publicly readable", "severity": "CRITICAL",
         "remediation": "Remove public ACL; use bucket policies for access control"},
        {"pattern": r'acl\s*=\s*"public-read-write"',
         "vuln": "S3 bucket publicly writable", "severity": "CRITICAL",
         "remediation": "Never allow public-read-write; restrict to specific principals"},
    ],
    "aws_iam_role": [
        {"pattern": r'"Action"\s*:\s*"\*"',
         "vuln": "Wildcard IAM action (full admin)", "severity": "CRITICAL",
         "remediation": "Follow least-privilege: specify only needed actions"},
        {"pattern": r'"Resource"\s*:\s*"\*"',
         "vuln": "Wildcard IAM resource", "severity": "HIGH",
         "remediation": "Scope Resource to specific ARNs"},
    ],
    "aws_iam_policy": [
        {"pattern": r'"Effect"\s*:\s*"Allow"[\s\S]*?"Action"\s*:\s*"\*"',
         "vuln": "Allow all actions policy", "severity": "CRITICAL",
         "remediation": "Use specific action lists instead of '*'"},
    ],
    "aws_lambda_function": [
        {"pattern": r'environment\s*\{[\s\S]*?(password|secret|key)\s*=',
         "vuln": "Secrets in Lambda environment variables", "severity": "HIGH",
         "remediation": "Use AWS Secrets Manager and grant Lambda IAM access"},
    ],
    "aws_ecs_task_definition": [
        {"pattern": r'"environment"\s*:\s*\[[\s\S]*?(password|secret)',
         "vuln": "Secrets in ECS task environment", "severity": "HIGH",
         "remediation": "Use secretsArn with AWS Secrets Manager"},
    ],
    "aws_lb": [
        {"pattern": r'internal\s*=\s*false',
         "vuln": "Internet-facing load balancer", "severity": "MEDIUM",
         "remediation": "Ensure WAF and security groups are properly configured"},
    ],
    "aws_rds_cluster": [
        {"pattern": r'storage_encrypted\s*=\s*false',
         "vuln": "RDS cluster not encrypted", "severity": "HIGH",
         "remediation": "Enable storage_encrypted = true"},
    ],
}

# Relationship patterns: how resources reference each other
_REF_PATTERNS = [
    # Security group references
    (r'vpc_security_group_ids\s*=\s*\[([^\]]+)\]', "protected_by"),
    (r'security_groups\s*=\s*\[([^\]]+)\]', "protected_by"),
    # Subnet / VPC references
    (r'subnet_id\s*=\s*(\S+)', "in_subnet"),
    (r'vpc_id\s*=\s*(\S+)', "in_vpc"),
    # IAM references
    (r'role\s*=\s*(\S+)', "assumes_role"),
    (r'execution_role_arn\s*=\s*(\S+)', "uses_role"),
    (r'task_role_arn\s*=\s*(\S+)', "uses_role"),
    # Data flow references
    (r'bucket\s*=\s*(\S+)', "accesses_bucket"),
    (r'source_arn\s*=\s*(\S+)', "triggered_by"),
    (r'target_group_arn\s*=\s*(\S+)', "routes_to"),
    # DB references
    (r'db_instance_identifier\s*=\s*(\S+)', "connects_to_db"),
    # Generic name reference
    (r'(\w+\.\w+\.\w+)', "references"),
]


def _parse_terraform_resources(content: str) -> List[Dict[str, Any]]:
    """Parse Terraform content into structured resource blocks."""
    resources = []
    # Match resource "type" "name" { ... }
    # Use a simple brace-matching approach
    pattern = re.compile(
        r'resource\s+"([^"]+)"\s+"([^"]+)"\s*\{', re.MULTILINE
    )
    for m in pattern.finditer(content):
        res_type = m.group(1)
        res_name = m.group(2)
        start = m.end()
        # Find matching closing brace
        depth = 1
        pos = start
        while pos < len(content) and depth > 0:
            if content[pos] == '{':
                depth += 1
            elif content[pos] == '}':
                depth -= 1
            pos += 1
        block = content[start:pos - 1] if pos > start else ""
        resources.append({
            "type": res_type,
            "name": res_name,
            "full_name": f"{res_type}.{res_name}",
            "block": block,
            "start_line": content[:m.start()].count('\n') + 1,
        })
    return resources


def _detect_vulnerabilities(resource: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check a resource block against known vulnerability signatures."""
    vulns = []
    res_type = resource["type"]
    signatures = _VULN_SIGNATURES.get(res_type, [])
    for sig in signatures:
        if re.search(sig["pattern"], resource["block"], re.IGNORECASE | re.DOTALL):
            vulns.append({
                "vuln": sig["vuln"],
                "severity": sig["severity"],
                "remediation": sig["remediation"],
                "resource": resource["full_name"],
                "resource_type": res_type,
                "resource_name": resource["name"],
            })
    return vulns


def _build_reference_edges(
    resources: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Extract edges between resources based on reference patterns and inferred relationships."""
    edges = []
    name_map = {r["full_name"]: r for r in resources}
    # Also map by just the name (e.g., "web_sg" -> "aws_security_group.web_sg")
    short_map: Dict[str, str] = {}
    for r in resources:
        short_map[r["name"]] = r["full_name"]
        short_map[f'{r["type"]}.{r["name"]}'] = r["full_name"]

    # ── Explicit reference edges ────────────────────────────────
    for resource in resources:
        block = resource["block"]
        for pattern, rel_type in _REF_PATTERNS:
            for m in re.finditer(pattern, block):
                ref_str = m.group(1)
                ref_str = ref_str.strip().strip('"').strip("'")
                # Handle aws_security_group.web_sg.id → aws_security_group.web_sg
                parts = ref_str.split(".")
                candidates = [
                    ref_str,
                    ".".join(parts[:2]) if len(parts) >= 2 else ref_str,
                    parts[-2] if len(parts) >= 2 else "",
                    parts[0] if parts else "",
                ]
                target = None
                for c in candidates:
                    if c in name_map:
                        target = c
                        break
                    if c in short_map:
                        target = short_map[c]
                        break
                if target and target != resource["full_name"]:
                    edges.append({
                        "source": resource["full_name"],
                        "target": target,
                        "relationship": rel_type,
                    })

    # ── Inferred deployment-level edges ─────────────────────────
    # Resources in the same file share a deployment context.
    # Add implicit network / access edges based on common patterns.
    by_type: Dict[str, List[Dict]] = defaultdict(list)
    for r in resources:
        by_type[r["type"]].append(r)

    # Security groups that protect a compute resource also govern network reach
    # Build map: resource → security groups it uses
    sg_users: Dict[str, Set[str]] = defaultdict(set)  # full_name → set of SG full_names
    for e in edges:
        if e["relationship"] == "protected_by":
            sg_users[e["source"]].add(e["target"])

    # If two compute/data resources share a security group, they can reach each other
    all_sg_user_items = list(sg_users.items())
    for i in range(len(all_sg_user_items)):
        for j in range(i + 1, len(all_sg_user_items)):
            r1, sgs1 = all_sg_user_items[i]
            r2, sgs2 = all_sg_user_items[j]
            if sgs1 & sgs2:  # shared SG
                edges.append({"source": r1, "target": r2, "relationship": "shared_network"})
                edges.append({"source": r2, "target": r1, "relationship": "shared_network"})

    # Compute → data-store access patterns (same deployment)
    compute_types = {"aws_instance", "aws_ecs_task_definition", "aws_lambda_function",
                     "aws_ecs_service", "aws_eks_node_group"}
    db_types = {"aws_db_instance", "aws_rds_cluster", "aws_dynamodb_table"}
    storage_types = {"aws_s3_bucket"}
    iam_types = {"aws_iam_role", "aws_iam_policy"}

    computes = [r for r in resources if r["type"] in compute_types]
    dbs = [r for r in resources if r["type"] in db_types]
    buckets = [r for r in resources if r["type"] in storage_types]
    iam_res = [r for r in resources if r["type"] in iam_types]

    # Explicit edge set for dedup
    explicit = {(e["source"], e["target"]) for e in edges}

    for comp in computes:
        # Compute instances commonly access databases in same deployment
        for db in dbs:
            key = (comp["full_name"], db["full_name"])
            if key not in explicit:
                edges.append({"source": comp["full_name"], "target": db["full_name"],
                              "relationship": "network_access"})
                explicit.add(key)
        # Compute instances commonly access S3 buckets
        for bkt in buckets:
            key = (comp["full_name"], bkt["full_name"])
            if key not in explicit:
                edges.append({"source": comp["full_name"], "target": bkt["full_name"],
                              "relationship": "data_access"})
                explicit.add(key)
        # Compute instances may assume IAM roles
        for iam in iam_res:
            if iam["type"] == "aws_iam_role":
                key = (comp["full_name"], iam["full_name"])
                if key not in explicit:
                    edges.append({"source": comp["full_name"], "target": iam["full_name"],
                                  "relationship": "assumes_role"})
                    explicit.add(key)

    # IAM policy attached to role (same deployment heuristic)
    roles = [r for r in resources if r["type"] == "aws_iam_role"]
    policies = [r for r in resources if r["type"] == "aws_iam_policy"]
    for role in roles:
        for pol in policies:
            key = (role["full_name"], pol["full_name"])
            if key not in explicit:
                edges.append({"source": role["full_name"], "target": pol["full_name"],
                              "relationship": "policy_attachment"})
                explicit.add(key)

    # S3 bucket objects → bucket (already covered by explicit refs usually)
    # Security groups → the resources they protect (reverse edge for graph traversal)
    for e in list(edges):
        if e["relationship"] == "protected_by":
            rev = (e["target"], e["source"])
            if rev not in explicit:
                edges.append({"source": e["target"], "target": e["source"],
                              "relationship": "exposes"})
                explicit.add(rev)

    # Deduplicate
    seen: Set[Tuple[str, str, str]] = set()
    unique_edges = []
    for e in edges:
        key = (e["source"], e["target"], e["relationship"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(e)
    return unique_edges


def _find_attack_paths(
    resources: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    vulns_by_resource: Dict[str, List[Dict]],
) -> List[Dict[str, Any]]:
    """
    Detect multi-hop attack paths through the infrastructure graph.
    A path is a chain of resources where vulnerabilities enable traversal.
    """
    # Build adjacency list (bidirectional — attacks can flow either way)
    adj: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
    for e in edges:
        adj[e["source"]].append((e["target"], e["relationship"]))
        adj[e["target"]].append((e["source"], e["relationship"]))

    # Entry points: resources with public exposure or open ingress
    entry_keywords = ["public", "0.0.0.0", "internet", "ingress"]
    entry_resources: Set[str] = set()
    for r in resources:
        block_lower = r["block"].lower()
        if any(kw in block_lower for kw in entry_keywords):
            entry_resources.add(r["full_name"])
        # Resources with vulnerabilities related to public access
        for v in vulns_by_resource.get(r["full_name"], []):
            if any(kw in v["vuln"].lower() for kw in ["public", "unrestricted", "all ports"]):
                entry_resources.add(r["full_name"])

    # High-value targets: databases, S3 buckets, secrets, IAM
    target_types = {"aws_db_instance", "aws_s3_bucket", "aws_rds_cluster",
                    "aws_iam_role", "aws_iam_policy", "aws_secretsmanager_secret",
                    "aws_dynamodb_table", "aws_kms_key"}
    target_resources: Set[str] = set()
    for r in resources:
        if r["type"] in target_types:
            target_resources.add(r["full_name"])

    # BFS from each entry point to find paths to targets
    attack_paths = []

    for entry in entry_resources:
        visited: Set[str] = set()
        queue: List[List[Tuple[str, str]]] = [[(entry, "entry_point")]]

        while queue:
            path = queue.pop(0)
            current = path[-1][0]

            if current in visited:
                continue
            visited.add(current)

            # Check if we reached a target
            if current in target_resources and len(path) > 1:
                # Build the attack path
                path_chain = []
                total_severity_score = 0
                severity_weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}

                for node_name, relationship in path:
                    node_vulns = vulns_by_resource.get(node_name, [])
                    node_resource = next((r for r in resources if r["full_name"] == node_name), None)
                    for v in node_vulns:
                        total_severity_score += severity_weights.get(v["severity"], 1)
                    path_chain.append({
                        "resource": node_name,
                        "resource_type": node_resource["type"] if node_resource else "",
                        "resource_name": node_resource["name"] if node_resource else "",
                        "relationship": relationship,
                        "vulnerabilities": node_vulns,
                        "is_entry": node_name == entry,
                        "is_target": node_name in target_resources,
                    })

                # Determine overall path severity
                if total_severity_score >= 8:
                    path_severity = "CRITICAL"
                elif total_severity_score >= 5:
                    path_severity = "HIGH"
                elif total_severity_score >= 2:
                    path_severity = "MEDIUM"
                else:
                    path_severity = "LOW"

                # Build human-readable attack narrative
                narrative_parts = []
                for i, node in enumerate(path_chain):
                    if i == 0:
                        narrative_parts.append(f"Attacker enters via **{node['resource']}**")
                        for v in node["vulnerabilities"]:
                            narrative_parts.append(f"  ↳ {v['vuln']}")
                    else:
                        narrative_parts.append(f"→ Traverses to **{node['resource']}** ({node['relationship']})")
                        for v in node["vulnerabilities"]:
                            narrative_parts.append(f"  ↳ {v['vuln']}")
                    if node["is_target"]:
                        narrative_parts.append(f"  🎯 **HIGH-VALUE TARGET REACHED**")

                attack_paths.append({
                    "path_id": f"AP-{len(attack_paths)+1:03d}",
                    "entry_point": entry,
                    "target": current,
                    "hops": len(path_chain),
                    "severity": path_severity,
                    "severity_score": total_severity_score,
                    "chain": path_chain,
                    "narrative": "\n".join(narrative_parts),
                    "path_string": " → ".join(
                        n["resource_name"] or n["resource"] for n in path_chain
                    ),
                    "remediation": _generate_path_remediation(path_chain),
                })

            # Continue exploring
            for neighbor, rel in adj.get(current, []):
                if neighbor not in visited:
                    queue.append(path + [(neighbor, rel)])

    # Sort by severity_score descending and limit to top 10 most critical
    attack_paths.sort(key=lambda p: p["severity_score"], reverse=True)

    # Deduplicate equivalent paths (same entry type + same target)
    # Keep only unique entry→target pairs, preferring shortest path for same pair
    seen_pairs: Set[Tuple[str, str]] = set()
    unique_paths = []
    for p in attack_paths:
        pair = (p["entry_point"], p["target"])
        if pair not in seen_pairs:
            seen_pairs.add(pair)
            unique_paths.append(p)

    # Re-number and cap at 10
    for i, p in enumerate(unique_paths[:10]):
        p["path_id"] = f"AP-{i+1:03d}"

    return unique_paths[:10]


def _generate_path_remediation(chain: List[Dict]) -> List[str]:
    """Generate specific remediation steps to break an attack path."""
    steps = []
    for node in chain:
        for v in node.get("vulnerabilities", []):
            steps.append(
                f"[{node['resource']}] {v['remediation']}"
            )
    if not steps:
        steps.append("Review resource relationships and apply network segmentation.")
    steps.append("Apply principle of least privilege across all connected resources.")
    steps.append("Add monitoring and alerting for the identified attack path.")
    return steps


def analyze_attack_paths(content: str, filename: str = "") -> Dict[str, Any]:
    """
    Main entry point: analyze IaC content for attack paths.

    Returns a dict with:
      - attack_paths: list of detected paths with full details
      - graph: {nodes, edges} for visualization
      - summary: statistics
      - findings: list of Finding-compatible dicts for the scan pipeline
    """
    resources = _parse_terraform_resources(content)
    if not resources:
        return {
            "attack_paths": [],
            "graph": {"nodes": [], "edges": []},
            "summary": {"total_paths": 0, "total_resources": 0, "total_vulnerabilities": 0},
            "findings": [],
        }

    # Detect vulnerabilities per resource
    vulns_by_resource: Dict[str, List[Dict]] = {}
    all_vulns = []
    for r in resources:
        rv = _detect_vulnerabilities(r)
        vulns_by_resource[r["full_name"]] = rv
        all_vulns.extend(rv)

    # Build edges
    edges = _build_reference_edges(resources)

    # Find attack paths
    attack_paths = _find_attack_paths(resources, edges, vulns_by_resource)

    # Build sets of entry points and targets for graph marking
    # Use vulnerability-based detection (not just path-based) so all risky nodes are marked
    entry_keywords = ["public", "0.0.0.0", "internet", "ingress"]
    target_types = {"aws_db_instance", "aws_s3_bucket", "aws_rds_cluster",
                    "aws_iam_role", "aws_iam_policy", "aws_secretsmanager_secret",
                    "aws_dynamodb_table", "aws_kms_key"}
    vuln_entry_kws = ["public", "unrestricted", "all ports", "internet-facing"]
    vuln_target_kws = ["database", "bucket", "secret", "admin", "wildcard"]

    all_entry_points: Set[str] = set()
    all_targets: Set[str] = set()
    for r in resources:
        block_lower = r["block"].lower()
        # Entry: has public exposure keywords
        if any(kw in block_lower for kw in entry_keywords):
            all_entry_points.add(r["full_name"])
        for v in vulns_by_resource.get(r["full_name"], []):
            if any(kw in v["vuln"].lower() for kw in vuln_entry_kws):
                all_entry_points.add(r["full_name"])
        # Target: is a high-value resource type or has target-type vulns
        if r["type"] in target_types:
            all_targets.add(r["full_name"])
        for v in vulns_by_resource.get(r["full_name"], []):
            if any(kw in v["vuln"].lower() for kw in vuln_target_kws):
                all_targets.add(r["full_name"])

    # Build graph data for frontend visualization
    node_ids = set()
    graph_nodes = []
    for r in resources:
        vulns = vulns_by_resource.get(r["full_name"], [])
        max_sev = "NONE"
        for v in vulns:
            if v["severity"] == "CRITICAL":
                max_sev = "CRITICAL"
            elif v["severity"] == "HIGH" and max_sev != "CRITICAL":
                max_sev = "HIGH"
            elif v["severity"] == "MEDIUM" and max_sev not in ("CRITICAL", "HIGH"):
                max_sev = "MEDIUM"

        is_entry = r["full_name"] in all_entry_points
        is_target = r["full_name"] in all_targets

        graph_nodes.append({
            "id": r["full_name"],
            "label": r["name"],
            "type": r["type"],
            "vulnerabilities": len(vulns),
            "max_severity": max_sev,
            "is_entry_point": is_entry,
            "is_target": is_target,
            "details": vulns,
        })
        node_ids.add(r["full_name"])

    graph_edges = []
    for e in edges:
        if e["source"] in node_ids and e["target"] in node_ids:
            # Check if this edge is part of an attack path
            is_attack_edge = any(
                any(
                    n["resource"] == e["source"] for n in p["chain"]
                ) and any(
                    n["resource"] == e["target"] for n in p["chain"]
                )
                for p in attack_paths
            )
            graph_edges.append({
                "source": e["source"],
                "target": e["target"],
                "relationship": e["relationship"],
                "is_attack_path": is_attack_edge,
            })

    # Convert attack paths to scan findings
    findings = []
    for path in attack_paths:
        findings.append({
            "scanner": "gnn",
            "category": "gnn",
            "type": "attack_path",
            "severity": path["severity"],
            "confidence": 0.85 if path["severity_score"] >= 5 else 0.7,
            "title": f"Attack Path: {path['path_string']}",
            "description": (
                f"Detected a {path['hops']}-hop attack path from "
                f"{path['entry_point']} to {path['target']}.\n\n"
                f"**Attack Chain:** {path['path_string']}\n\n"
                f"{path['narrative']}"
            ),
            "rule_id": path["path_id"],
            "resource": path["entry_point"],
            "remediation_steps": path["remediation"],
            "metadata": {
                "path_id": path["path_id"],
                "hops": path["hops"],
                "severity_score": path["severity_score"],
                "entry_point": path["entry_point"],
                "target": path["target"],
                "chain": path["chain"],
            },
        })

    # Also add per-vulnerability findings for critical nodes
    for r in resources:
        for v in vulns_by_resource.get(r["full_name"], []):
            findings.append({
                "scanner": "gnn",
                "category": "gnn",
                "type": "critical_resource",
                "severity": v["severity"],
                "confidence": 0.9,
                "title": f"[{r['name']}] {v['vuln']}",
                "description": (
                    f"Resource **{r['full_name']}** has vulnerability: {v['vuln']}. "
                    f"This resource is part of the infrastructure attack graph and "
                    f"may enable lateral movement or data exfiltration."
                ),
                "rule_id": f"GNN_{r['type'].upper()}_{r['name'].upper()}",
                "resource": r["full_name"],
                "remediation_steps": [v["remediation"]],
                "line_number": r.get("start_line"),
            })

    summary = {
        "total_paths": len(attack_paths),
        "total_resources": len(resources),
        "total_edges": len(edges),
        "total_vulnerabilities": len(all_vulns),
        "critical_paths": sum(1 for p in attack_paths if p["severity"] == "CRITICAL"),
        "high_paths": sum(1 for p in attack_paths if p["severity"] == "HIGH"),
        "entry_points": sorted(all_entry_points),
        "targets_reached": sorted(all_targets),
    }

    logger.info(
        "🔍 Attack Path Analysis: %d resources, %d edges, %d paths (%d critical)",
        len(resources), len(edges), len(attack_paths),
        summary["critical_paths"],
    )

    return {
        "attack_paths": attack_paths,
        "graph": {"nodes": graph_nodes, "edges": graph_edges},
        "summary": summary,
        "findings": findings,
    }
