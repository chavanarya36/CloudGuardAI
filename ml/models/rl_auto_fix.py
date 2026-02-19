"""
Reinforcement Learning Auto-Remediation Agent

Novel AI Feature #2: Deep Q-Network (DQN) for automatic vulnerability fixing
- Learns optimal fix strategies through trial and error
- Maintains infrastructure functionality while fixing vulnerabilities
- Generalizes to unseen vulnerability patterns

This is a novel contribution that differentiates CloudGuard from:
- Checkov: No auto-fix, only detection
- TFSec: Manual fixes only
- Snyk: Template-based fixes (not learned)
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import random
import re
import json
from pathlib import Path


# ============================================================================
# STATE SPACE: Vulnerability representation
# ============================================================================

@dataclass
class VulnerabilityState:
    """
    State representation for RL agent
    
    Features:
    - Vulnerability type (one-hot encoded)
    - Severity level (0-1 normalized)
    - Resource type (one-hot encoded)
    - File format (terraform, yaml, json)
    - Context features (public exposure, encryption, IAM, etc.)
    """
    vuln_type: str  # e.g., "unencrypted_storage", "public_access", "weak_iam"
    severity: float  # 0.0 (low) to 1.0 (critical)
    resource_type: str  # e.g., "aws_s3_bucket", "aws_db_instance"
    file_format: str  # "terraform", "yaml", "json"
    is_public: bool
    has_encryption: bool
    has_backup: bool
    has_logging: bool
    has_mfa: bool
    code_snippet: str  # The vulnerable code block
    
    def to_vector(self) -> np.ndarray:
        """Convert state to feature vector for neural network"""
        
        # Vulnerability type encoding (20 common types)
        vuln_types = [
            "unencrypted_storage", "public_access", "weak_iam", 
            "missing_logging", "no_backup", "insecure_protocol",
            "hardcoded_secrets", "open_security_group", "missing_mfa",
            "outdated_version", "excessive_permissions", "no_encryption_transit",
            "missing_tags", "public_bucket", "weak_password",
            "missing_vpc", "internet_gateway", "unrestricted_egress",
            "missing_waf", "cors_misconfiguration"
        ]
        vuln_encoding = [1.0 if self.vuln_type == vt else 0.0 for vt in vuln_types]
        
        # Resource type encoding (15 common resources)
        resource_types = [
            "aws_s3_bucket", "aws_db_instance", "aws_instance", 
            "aws_security_group", "aws_iam_role", "aws_iam_policy",
            "aws_lambda_function", "aws_rds_cluster", "aws_ebs_volume",
            "aws_kms_key", "aws_cloudfront_distribution", "aws_alb",
            "aws_ecs_task_definition", "kubernetes_deployment", "azurerm_storage_account"
        ]
        resource_encoding = [1.0 if self.resource_type == rt else 0.0 for rt in resource_types]
        
        # File format encoding
        format_encoding = [
            1.0 if self.file_format == "terraform" else 0.0,
            1.0 if self.file_format == "yaml" else 0.0,
            1.0 if self.file_format == "json" else 0.0
        ]
        
        # Context features
        context = [
            self.severity,
            1.0 if self.is_public else 0.0,
            1.0 if self.has_encryption else 0.0,
            1.0 if self.has_backup else 0.0,
            1.0 if self.has_logging else 0.0,
            1.0 if self.has_mfa else 0.0
        ]
        
        # Concatenate all features
        return np.array(vuln_encoding + resource_encoding + format_encoding + context, dtype=np.float32)
    
    @property
    def state_dim(self) -> int:
        """Dimension of state vector"""
        return 20 + 15 + 3 + 6  # 44 features


# ============================================================================
# ACTION SPACE: Fix strategies
# ============================================================================

class FixAction:
    """
    Available fix actions for different vulnerability types
    
    Actions are defined as code transformations:
    - Add encryption
    - Restrict access
    - Enable logging
    - Add backup
    - Enable MFA
    - Update version
    - Remove public access
    - Add VPC
    - Enable WAF
    - etc.
    """
    
    # Action IDs
    ADD_ENCRYPTION = 0
    RESTRICT_ACCESS = 1
    ENABLE_LOGGING = 2
    ADD_BACKUP = 3
    ENABLE_MFA = 4
    UPDATE_VERSION = 5
    REMOVE_PUBLIC_ACCESS = 6
    ADD_VPC = 7
    ENABLE_WAF = 8
    ADD_TAGS = 9
    STRENGTHEN_IAM = 10
    ENABLE_HTTPS = 11
    ADD_KMS = 12
    RESTRICT_EGRESS = 13
    ADD_MONITORING = 14
    
    # Total number of actions
    NUM_ACTIONS = 15
    
    @staticmethod
    def apply_fix(state: VulnerabilityState, action_id: int) -> Tuple[str, bool]:
        """
        Apply fix action to vulnerable code
        
        Args:
            state: Current vulnerability state
            action_id: Action to apply
        
        Returns:
            (fixed_code, success): Fixed code and whether fix was successful
        """
        code = state.code_snippet
        
        if action_id == FixAction.ADD_ENCRYPTION:
            return FixAction._add_encryption(code, state)
        elif action_id == FixAction.RESTRICT_ACCESS:
            return FixAction._restrict_access(code, state)
        elif action_id == FixAction.ENABLE_LOGGING:
            return FixAction._enable_logging(code, state)
        elif action_id == FixAction.ADD_BACKUP:
            return FixAction._add_backup(code, state)
        elif action_id == FixAction.ENABLE_MFA:
            return FixAction._enable_mfa(code, state)
        elif action_id == FixAction.UPDATE_VERSION:
            return FixAction._update_version(code, state)
        elif action_id == FixAction.REMOVE_PUBLIC_ACCESS:
            return FixAction._remove_public_access(code, state)
        elif action_id == FixAction.ADD_VPC:
            return FixAction._add_vpc(code, state)
        elif action_id == FixAction.ENABLE_WAF:
            return FixAction._enable_waf(code, state)
        elif action_id == FixAction.ADD_TAGS:
            return FixAction._add_tags(code, state)
        elif action_id == FixAction.STRENGTHEN_IAM:
            return FixAction._strengthen_iam(code, state)
        elif action_id == FixAction.ENABLE_HTTPS:
            return FixAction._enable_https(code, state)
        elif action_id == FixAction.ADD_KMS:
            return FixAction._add_kms(code, state)
        elif action_id == FixAction.RESTRICT_EGRESS:
            return FixAction._restrict_egress(code, state)
        elif action_id == FixAction.ADD_MONITORING:
            return FixAction._add_monitoring(code, state)
        else:
            return code, False
    
    @staticmethod
    def _add_encryption(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Add encryption to resource"""
        if "terraform" in state.file_format:
            # S3 bucket encryption
            if "aws_s3_bucket" in code and "server_side_encryption_configuration" not in code:
                fixed = code.rstrip()
                if fixed.endswith("}"):
                    fixed = fixed[:-1]
                fixed += """
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
}"""
                return fixed, True
            
            # RDS encryption
            if "aws_db_instance" in code and "storage_encrypted" not in code:
                fixed = re.sub(r'(resource\s+"aws_db_instance"[^{]+\{)', r'\1\n  storage_encrypted = true', code)
                return fixed, True
            
            # EBS encryption
            if "aws_ebs_volume" in code and "encrypted" not in code:
                fixed = re.sub(r'(resource\s+"aws_ebs_volume"[^{]+\{)', r'\1\n  encrypted = true', code)
                return fixed, True
        
        return code, False
    
    @staticmethod
    def _restrict_access(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Restrict overly permissive access"""
        if "0.0.0.0/0" in code:
            # Replace with private network
            fixed = code.replace("0.0.0.0/0", "10.0.0.0/16")
            return fixed, True
        
        if '"*"' in code and "Action" in code:
            # Restrict IAM wildcard actions
            fixed = code.replace('"*"', '"s3:GetObject"')
            return fixed, True
        
        return code, False
    
    @staticmethod
    def _enable_logging(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Enable logging for resource"""
        if "terraform" in state.file_format:
            if "aws_s3_bucket" in code and "logging" not in code:
                fixed = code.rstrip()
                if fixed.endswith("}"):
                    fixed = fixed[:-1]
                fixed += """
  logging {
    target_bucket = aws_s3_bucket.log_bucket.id
    target_prefix = "log/"
  }
}"""
                return fixed, True
        
        return code, False
    
    @staticmethod
    def _add_backup(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Add backup configuration"""
        if "aws_db_instance" in code and "backup_retention_period" not in code:
            fixed = re.sub(r'(resource\s+"aws_db_instance"[^{]+\{)', r'\1\n  backup_retention_period = 7', code)
            return fixed, True
        
        return code, False
    
    @staticmethod
    def _remove_public_access(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Remove public access"""
        if "publicly_accessible" in code:
            fixed = code.replace("publicly_accessible = true", "publicly_accessible = false")
            return fixed, True
        
        if "acl" in code and "public-read" in code:
            fixed = code.replace('"public-read"', '"private"')
            return fixed, True
        
        return code, False
    
    @staticmethod
    def _add_kms(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Add KMS encryption key"""
        if "terraform" in state.file_format and "kms_key_id" not in code:
            fixed = re.sub(
                r'(storage_encrypted\s*=\s*true)',
                r'\1\n  kms_key_id = aws_kms_key.main.arn',
                code
            )
            if fixed != code:
                return fixed, True
        
        return code, False
    
    @staticmethod
    def _restrict_egress(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Restrict egress rules"""
        if "egress" in code and "0.0.0.0/0" in code:
            # Keep HTTPS egress, remove all others
            fixed = re.sub(
                r'egress\s*\{[^}]+0\.0\.0\.0/0[^}]+\}',
                '''egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }''',
                code
            )
            if fixed != code:
                return fixed, True
        
        return code, False
    
    @staticmethod
    def _enable_https(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Enforce HTTPS/TLS"""
        if "protocol" in code and '"http"' in code:
            fixed = code.replace('"http"', '"https"')
            return fixed, True
        
        if "ssl_policy" not in code and "aws_lb_listener" in code:
            fixed = re.sub(
                r'(resource\s+"aws_lb_listener"[^{]+\{)',
                r'\1\n  ssl_policy = "ELBSecurityPolicy-TLS-1-2-2017-01"',
                code
            )
            if fixed != code:
                return fixed, True
        
        return code, False

    @staticmethod
    def _enable_mfa(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Enable MFA / multi-factor authentication on IAM resources"""
        if "terraform" in state.file_format:
            # Add MFA delete protection on S3 buckets
            if "aws_s3_bucket" in code and "mfa_delete" not in code:
                fixed = code.rstrip()
                if fixed.endswith("}"):
                    fixed = fixed[:-1]
                fixed += """
  versioning {
    enabled    = true
    mfa_delete = true
  }
}"""
                return fixed, True

            # Add MFA condition to IAM policy
            if "aws_iam" in code and "Condition" not in code and "Action" in code:
                fixed = re.sub(
                    r'("Effect"\s*:\s*"Allow")',
                    r'\1,\n      "Condition": {"Bool": {"aws:MultiFactorAuthPresent": "true"}}',
                    code,
                )
                if fixed != code:
                    return fixed, True

        return code, False

    @staticmethod
    def _update_version(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Update deprecated / vulnerable version references"""
        updated = False
        fixed = code

        # Terraform provider version bumps
        version_upgrades = {
            '"~> 2.0"': '"~> 5.0"',
            '"~> 3.0"': '"~> 5.0"',
            '"= 2.0.0"': '"~> 5.0"',
            'engine_version = "5.6"': 'engine_version = "8.0"',
            'engine_version = "9.6"': 'engine_version = "15.4"',
            'engine_version = "11"': 'engine_version = "15.4"',
            '"tls1.0"': '"tls1.2"',
            '"TLSv1"': '"TLSv1.2"',
            '"SSLv3"': '"TLSv1.2"',
        }

        for old_ver, new_ver in version_upgrades.items():
            if old_ver in fixed:
                fixed = fixed.replace(old_ver, new_ver)
                updated = True

        return fixed, updated

    @staticmethod
    def _add_vpc(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Place resources inside a VPC / private subnet"""
        if "terraform" in state.file_format:
            # Lambda: add VPC config
            if "aws_lambda_function" in code and "vpc_config" not in code:
                fixed = code.rstrip()
                if fixed.endswith("}"):
                    fixed = fixed[:-1]
                fixed += """
  vpc_config {
    subnet_ids         = var.private_subnet_ids
    security_group_ids = [var.lambda_sg_id]
  }
}"""
                return fixed, True

            # RDS: ensure not publicly accessible
            if "aws_db_instance" in code and "db_subnet_group_name" not in code:
                fixed = re.sub(
                    r'(resource\s+"aws_db_instance"[^{]+\{)',
                    r'\1\n  db_subnet_group_name = var.db_subnet_group\n  publicly_accessible  = false',
                    code,
                )
                if fixed != code:
                    return fixed, True

        return code, False

    @staticmethod
    def _enable_waf(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Add WAF (Web Application Firewall) association"""
        if "terraform" in state.file_format:
            # ALB → WAF association
            if ("aws_alb" in code or "aws_lb" in code) and "aws_wafv2" not in code:
                fixed = code.rstrip()
                if fixed.endswith("}"):
                    fixed = fixed[:-1]
                fixed += """
}

resource "aws_wafv2_web_acl_association" "main" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = var.waf_acl_arn
}"""
                return fixed, True

            # CloudFront → WAF
            if "aws_cloudfront_distribution" in code and "web_acl_id" not in code:
                fixed = re.sub(
                    r'(resource\s+"aws_cloudfront_distribution"[^{]+\{)',
                    r'\1\n  web_acl_id = var.waf_acl_arn',
                    code,
                )
                if fixed != code:
                    return fixed, True

        return code, False

    @staticmethod
    def _add_tags(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Add mandatory resource tags for compliance"""
        if "terraform" in state.file_format and "tags" not in code:
            # Add standard tag block before the closing brace
            fixed = code.rstrip()
            if fixed.endswith("}"):
                fixed = fixed[:-1]
            fixed += """
  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
    Project     = "cloudguard"
    Owner       = var.owner
  }
}"""
            return fixed, True

        return code, False

    @staticmethod
    def _strengthen_iam(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Tighten IAM policies — remove wildcards, add conditions"""
        modified = False
        fixed = code

        # Replace Action: "*" with least-privilege patterns
        if '"Action": "*"' in fixed or '"Action": ["*"]' in fixed:
            fixed = fixed.replace('"Action": "*"', '"Action": ["s3:GetObject", "s3:ListBucket"]')
            fixed = fixed.replace('"Action": ["*"]', '"Action": ["s3:GetObject", "s3:ListBucket"]')
            modified = True

        # Replace Resource: "*" with specific ARN pattern
        if '"Resource": "*"' in fixed:
            fixed = fixed.replace('"Resource": "*"', '"Resource": "arn:aws:s3:::${var.bucket_name}/*"')
            modified = True

        # Restrict assume-role to specific services
        if "assume_role_policy" in fixed and '"Service": "*"' in fixed:
            fixed = fixed.replace('"Service": "*"', '"Service": "ec2.amazonaws.com"')
            modified = True

        return fixed, modified

    @staticmethod
    def _add_monitoring(code: str, state: VulnerabilityState) -> Tuple[str, bool]:
        """Add CloudWatch monitoring / alerting for the resource"""
        if "terraform" in state.file_format:
            # RDS monitoring
            if "aws_db_instance" in code and "monitoring_interval" not in code:
                fixed = re.sub(
                    r'(resource\s+"aws_db_instance"[^{]+\{)',
                    r'\1\n  monitoring_interval = 60\n  monitoring_role_arn = var.rds_monitoring_role_arn\n  performance_insights_enabled = true',
                    code,
                )
                if fixed != code:
                    return fixed, True

            # ECS / Lambda — add CloudWatch alarms block
            if ("aws_lambda_function" in code or "aws_ecs_service" in code) and "aws_cloudwatch_metric_alarm" not in code:
                resource_type = "lambda" if "aws_lambda_function" in code else "ecs"
                fixed = code.rstrip()
                if fixed.endswith("}"):
                    fixed = fixed[:-1]
                fixed += """
}

resource "aws_cloudwatch_metric_alarm" "%s_errors" {
  alarm_name          = "${var.project}-%s-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/%s"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert on elevated error rate"
  alarm_actions       = [var.sns_topic_arn]
}""" % (resource_type, resource_type, "Lambda" if resource_type == "lambda" else "ECS")
                return fixed, True

        return code, False


# ============================================================================
# REWARD FUNCTION
# ============================================================================

class RewardCalculator:
    """
    Calculate reward for RL agent
    
    Reward components:
    1. Vulnerability fixed: +10
    2. Functionality maintained: +5
    3. Minimal code changes: +2
    4. Introduced new vulnerability: -15
    5. Broke functionality: -10
    6. Excessive changes: -3
    """
    
    @staticmethod
    def calculate_reward(
        original_code: str,
        fixed_code: str,
        original_vulnerabilities: int,
        fixed_vulnerabilities: int,
        syntax_valid: bool,
        functionality_maintained: bool
    ) -> float:
        """
        Calculate reward for a fix action
        
        Args:
            original_code: Original vulnerable code
            fixed_code: Code after applying fix
            original_vulnerabilities: Number of vulnerabilities before fix
            fixed_vulnerabilities: Number of vulnerabilities after fix
            syntax_valid: Whether fixed code has valid syntax
            functionality_maintained: Whether code still works
        
        Returns:
            Reward value (higher is better)
        """
        reward = 0.0
        
        # 1. Vulnerability reduction
        vulns_fixed = original_vulnerabilities - fixed_vulnerabilities
        if vulns_fixed > 0:
            reward += 10.0 * vulns_fixed
        elif vulns_fixed < 0:
            # Introduced new vulnerabilities
            reward -= 15.0 * abs(vulns_fixed)
        
        # 2. Syntax validity
        if not syntax_valid:
            reward -= 10.0
        
        # 3. Functionality maintained
        if functionality_maintained:
            reward += 5.0
        else:
            reward -= 10.0
        
        # 4. Code change size (prefer minimal changes)
        code_diff = len(fixed_code) - len(original_code)
        if abs(code_diff) > 500:  # Large changes
            reward -= 3.0
        elif abs(code_diff) < 100:  # Minimal changes
            reward += 2.0
        
        return reward


# ============================================================================
# DEEP Q-NETWORK
# ============================================================================

class DQN(nn.Module):
    """
    Deep Q-Network for learning optimal fix strategies
    
    Architecture:
    - Input: State vector (44 features)
    - Hidden layers: 128 -> 128 -> 64
    - Output: Q-values for each action (15 actions)
    """
    
    def __init__(self, state_dim: int = 44, action_dim: int = 15):
        super(DQN, self).__init__()
        
        self.network = nn.Sequential(
            nn.Linear(state_dim, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, action_dim)
        )
    
    def forward(self, state: torch.Tensor) -> torch.Tensor:
        """
        Forward pass: state -> Q-values
        
        Args:
            state: Batch of state vectors [batch_size, state_dim]
        
        Returns:
            Q-values for each action [batch_size, action_dim]
        """
        return self.network(state)


# ============================================================================
# EXPERIENCE REPLAY BUFFER
# ============================================================================

@dataclass
class Experience:
    """Single experience tuple for replay buffer"""
    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    """
    Experience replay buffer for DQN training
    
    Stores past experiences and samples random batches for training
    to break correlations between consecutive experiences
    """
    
    def __init__(self, capacity: int = 10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, experience: Experience):
        """Add experience to buffer"""
        self.buffer.append(experience)
    
    def sample(self, batch_size: int) -> List[Experience]:
        """Sample random batch of experiences"""
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))
    
    def __len__(self) -> int:
        return len(self.buffer)


# ============================================================================
# RL AUTO-FIX AGENT
# ============================================================================

class RLAutoFixAgent:
    """
    Reinforcement Learning agent for automatic vulnerability fixing
    
    Uses Deep Q-Network (DQN) with:
    - Experience replay
    - Target network
    - Epsilon-greedy exploration
    """
    
    def __init__(
        self,
        state_dim: int = 44,
        action_dim: int = 15,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
        buffer_capacity: int = 10000,
        batch_size: int = 64,
        target_update_freq: int = 10
    ):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Q-networks
        self.policy_net = DQN(state_dim, action_dim).to(self.device)
        self.target_net = DQN(state_dim, action_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Training components
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=learning_rate)
        self.criterion = nn.MSELoss()
        self.replay_buffer = ReplayBuffer(buffer_capacity)
        
        # Hyperparameters
        self.gamma = gamma
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay
        self.batch_size = batch_size
        self.target_update_freq = target_update_freq
        self.steps_done = 0
        
        # Statistics
        self.total_reward = 0.0
        self.episode_rewards = []
    
    def select_action(self, state: VulnerabilityState, training: bool = True) -> int:
        """
        Select action using epsilon-greedy policy
        
        Args:
            state: Current vulnerability state
            training: Whether in training mode (enables exploration)
        
        Returns:
            Action ID to take
        """
        if training and random.random() < self.epsilon:
            # Explore: random action
            return random.randint(0, FixAction.NUM_ACTIONS - 1)
        else:
            # Exploit: best action from Q-network
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state.to_vector()).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                return q_values.argmax(dim=1).item()
    
    def train_step(self):
        """
        Perform one training step using experience replay
        """
        if len(self.replay_buffer) < self.batch_size:
            return
        
        # Sample batch
        experiences = self.replay_buffer.sample(self.batch_size)
        
        # Prepare tensors
        states = torch.FloatTensor([e.state for e in experiences]).to(self.device)
        actions = torch.LongTensor([e.action for e in experiences]).to(self.device)
        rewards = torch.FloatTensor([e.reward for e in experiences]).to(self.device)
        next_states = torch.FloatTensor([e.next_state for e in experiences]).to(self.device)
        dones = torch.FloatTensor([e.done for e in experiences]).to(self.device)
        
        # Current Q-values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        
        # Target Q-values
        with torch.no_grad():
            next_q = self.target_net(next_states).max(dim=1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Compute loss and update
        loss = self.criterion(current_q, target_q)
        
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # Update target network periodically
        self.steps_done += 1
        if self.steps_done % self.target_update_freq == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())
        
        # Decay epsilon
        self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)
        
        return loss.item()
    
    def save(self, path: str):
        """Save model checkpoint"""
        torch.save({
            'policy_net_state_dict': self.policy_net.state_dict(),
            'target_net_state_dict': self.target_net.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'epsilon': self.epsilon,
            'steps_done': self.steps_done,
            'episode_rewards': self.episode_rewards
        }, path)
        print(f"✅ RL agent saved to {path}")
    
    def load(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.policy_net.load_state_dict(checkpoint['policy_net_state_dict'])
        self.target_net.load_state_dict(checkpoint['target_net_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.epsilon = checkpoint['epsilon']
        self.steps_done = checkpoint['steps_done']
        self.episode_rewards = checkpoint.get('episode_rewards', [])
        print(f"✅ RL agent loaded from {path}")


if __name__ == "__main__":
    print("RL Auto-Remediation Agent")
    print("=" * 70)
    print("Novel AI Feature #2: Deep Q-Network for vulnerability fixing")
    print()
    print("Components:")
    print("  ✓ State Space: 44-dimensional vulnerability representation")
    print("  ✓ Action Space: 15 fix strategies")
    print("  ✓ DQN: 3-layer neural network with experience replay")
    print("  ✓ Reward: Balances fix quality, functionality, code changes")
    print()
    print("Ready to train RL agent on vulnerability fixing tasks!")
