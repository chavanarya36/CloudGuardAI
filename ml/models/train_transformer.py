"""
Training script for Transformer Secure Code Generator

Trains on synthetic vulnerable -> secure IaC code pairs.
Uses teacher forcing with next-token prediction.

Usage:
    python -u -m ml.models.train_transformer
"""
import sys
import os

# Force unbuffered output on Windows
os.environ["PYTHONUNBUFFERED"] = "1"

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from pathlib import Path
import json
from datetime import datetime
from typing import List, Tuple

def log(msg):
    """Print with immediate flush."""
    print(msg, flush=True)

try:
    from ml.models.transformer_code_gen import (
        SecureCodeGenerator, IaCVocabulary, IaCSecureCodeGenerator,
    )
    IMPORTS_OK = True
except ImportError:
    IMPORTS_OK = False
    log("ERROR: Import failed. Run from project root: python -u -m ml.models.train_transformer")


# ============================================================================
# TRAINING DATA — Vulnerable -> Secure IaC pairs
# ============================================================================

TRAINING_PAIRS: List[Tuple[str, str]] = [
    # --- S3 Bucket: Public ACL ---
    (
        'resource "aws_s3_bucket" "data" {\n  acl = "public-read"\n}',
        'resource "aws_s3_bucket" "data" {\n  acl = "private"\n}\nresource "aws_s3_bucket_server_side_encryption_configuration" "data" {\n  bucket = aws_s3_bucket.data.id\n  rule {\n    apply_server_side_encryption_by_default {\n      sse_algorithm = "AES256"\n    }\n  }\n}'
    ),
    # --- S3 Bucket: Public-read-write ---
    (
        'resource "aws_s3_bucket" "uploads" {\n  acl = "public-read-write"\n}',
        'resource "aws_s3_bucket" "uploads" {\n  acl = "private"\n}\nresource "aws_s3_bucket_public_access_block" "uploads" {\n  bucket = aws_s3_bucket.uploads.id\n  block_public_acls = true\n  block_public_policy = true\n  ignore_public_acls = true\n  restrict_public_buckets = true\n}'
    ),
    # --- S3 No versioning ---
    (
        'resource "aws_s3_bucket" "logs" {\n  acl = "private"\n}',
        'resource "aws_s3_bucket" "logs" {\n  acl = "private"\n}\nresource "aws_s3_bucket_versioning" "logs" {\n  bucket = aws_s3_bucket.logs.id\n  versioning_configuration {\n    status = "Enabled"\n  }\n}'
    ),
    # --- Security Group: Open all ports ---
    (
        'resource "aws_security_group" "allow_all" {\n  ingress {\n    from_port = 0\n    to_port = 65535\n    protocol = "tcp"\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}',
        'resource "aws_security_group" "allow_all" {\n  ingress {\n    from_port = 443\n    to_port = 443\n    protocol = "tcp"\n    cidr_blocks = ["10.0.0.0/8"]\n  }\n}'
    ),
    # --- Security Group: Open SSH ---
    (
        'resource "aws_security_group" "ssh" {\n  ingress {\n    from_port = 22\n    to_port = 22\n    protocol = "tcp"\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}',
        'resource "aws_security_group" "ssh" {\n  ingress {\n    from_port = 22\n    to_port = 22\n    protocol = "tcp"\n    cidr_blocks = ["10.0.0.0/8"]\n  }\n}'
    ),
    # --- RDS: Publicly accessible ---
    (
        'resource "aws_db_instance" "main" {\n  engine = "postgres"\n  publicly_accessible = true\n}',
        'resource "aws_db_instance" "main" {\n  engine = "postgres"\n  publicly_accessible = false\n  storage_encrypted = true\n  backup_retention_period = 7\n}'
    ),
    # --- RDS: No encryption ---
    (
        'resource "aws_db_instance" "db" {\n  engine = "mysql"\n  storage_encrypted = false\n}',
        'resource "aws_db_instance" "db" {\n  engine = "mysql"\n  storage_encrypted = true\n  kms_key_id = aws_kms_key.db.arn\n}'
    ),
    # --- EC2: Public IP ---
    (
        'resource "aws_instance" "web" {\n  ami = "ami-12345"\n  associate_public_ip_address = true\n}',
        'resource "aws_instance" "web" {\n  ami = "ami-12345"\n  associate_public_ip_address = false\n  subnet_id = aws_subnet.private.id\n}'
    ),
    # --- IAM: Wildcard ---
    (
        'resource "aws_iam_role_policy" "admin" {\n  policy = jsonencode({\n    Statement = [{\n      Action = "*"\n      Resource = "*"\n    }]\n  })\n}',
        'resource "aws_iam_role_policy" "admin" {\n  policy = jsonencode({\n    Statement = [{\n      Action = ["s3:GetObject"]\n      Resource = "arn:aws:s3:::bucket/*"\n    }]\n  })\n}'
    ),
    # --- KMS: No rotation ---
    (
        'resource "aws_kms_key" "data" {\n  description = "Key"\n}',
        'resource "aws_kms_key" "data" {\n  description = "Key"\n  enable_key_rotation = true\n  deletion_window_in_days = 30\n}'
    ),
    # --- EBS: Unencrypted ---
    (
        'resource "aws_ebs_volume" "data" {\n  size = 100\n}',
        'resource "aws_ebs_volume" "data" {\n  size = 100\n  encrypted = true\n}'
    ),
    # --- Security Group: Open MySQL ---
    (
        'resource "aws_security_group" "db" {\n  ingress {\n    from_port = 3306\n    to_port = 3306\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}',
        'resource "aws_security_group" "db" {\n  ingress {\n    from_port = 3306\n    to_port = 3306\n    security_groups = [aws_security_group.app.id]\n  }\n}'
    ),
    # --- S3: No encryption ---
    (
        'resource "aws_s3_bucket" "sensitive" {\n  bucket = "sensitive"\n  acl = "private"\n}',
        'resource "aws_s3_bucket" "sensitive" {\n  bucket = "sensitive"\n  acl = "private"\n}\nresource "aws_s3_bucket_server_side_encryption_configuration" "sensitive" {\n  bucket = aws_s3_bucket.sensitive.id\n  rule {\n    apply_server_side_encryption_by_default {\n      sse_algorithm = "aws:kms"\n    }\n  }\n}'
    ),
    # --- RDS: No backup ---
    (
        'resource "aws_db_instance" "analytics" {\n  engine = "postgres"\n  backup_retention_period = 0\n}',
        'resource "aws_db_instance" "analytics" {\n  engine = "postgres"\n  backup_retention_period = 7\n  storage_encrypted = true\n}'
    ),
    # --- Security Group: Open RDP ---
    (
        'resource "aws_security_group" "rdp" {\n  ingress {\n    from_port = 3389\n    to_port = 3389\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}',
        'resource "aws_security_group" "rdp" {\n  ingress {\n    from_port = 3389\n    to_port = 3389\n    cidr_blocks = ["10.0.0.0/8"]\n  }\n}'
    ),
    # --- Security Group: No egress restrict ---
    (
        'resource "aws_security_group" "web" {\n  egress {\n    from_port = 0\n    to_port = 0\n    protocol = "-1"\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}',
        'resource "aws_security_group" "web" {\n  egress {\n    from_port = 443\n    to_port = 443\n    protocol = "tcp"\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}'
    ),
    # --- EC2: No monitoring ---
    (
        'resource "aws_instance" "app" {\n  ami = "ami-67890"\n  instance_type = "t3.medium"\n}',
        'resource "aws_instance" "app" {\n  ami = "ami-67890"\n  instance_type = "t3.medium"\n  monitoring = true\n}'
    ),
    # --- RDS Cluster: Unencrypted ---
    (
        'resource "aws_rds_cluster" "main" {\n  engine = "aurora-postgresql"\n  storage_encrypted = false\n}',
        'resource "aws_rds_cluster" "main" {\n  engine = "aurora-postgresql"\n  storage_encrypted = true\n  backup_retention_period = 7\n}'
    ),
    # --- Security Group: Open PostgreSQL ---
    (
        'resource "aws_security_group" "pg" {\n  ingress {\n    from_port = 5432\n    to_port = 5432\n    cidr_blocks = ["0.0.0.0/0"]\n  }\n}',
        'resource "aws_security_group" "pg" {\n  ingress {\n    from_port = 5432\n    to_port = 5432\n    security_groups = [aws_security_group.app.id]\n  }\n}'
    ),
    # --- Lambda: No VPC ---
    (
        'resource "aws_lambda_function" "api" {\n  function_name = "api"\n  runtime = "python3.11"\n}',
        'resource "aws_lambda_function" "api" {\n  function_name = "api"\n  runtime = "python3.11"\n  vpc_config {\n    subnet_ids = var.private_subnet_ids\n    security_group_ids = [aws_security_group.lambda.id]\n  }\n}'
    ),
]


# ============================================================================
# DATASET
# ============================================================================

class VulnSecurePairDataset(Dataset):
    """Dataset of (vulnerable_code, secure_code) pairs for teacher forcing."""

    def __init__(self, pairs: List[Tuple[str, str]], vocab: IaCVocabulary, max_len: int = 64):
        self.vocab = vocab
        self.max_len = max_len
        self.samples: List[Tuple[List[int], List[int]]] = []
        for vuln, secure in pairs:
            input_text = f"<VULN> {vuln} <SECURE>"
            target_text = f"{secure}"
            input_ids = vocab.encode(input_text, max_length=max_len)
            target_ids = vocab.encode(target_text, max_length=max_len)
            self.samples.append((
                vocab.pad_sequence(input_ids, max_len),
                vocab.pad_sequence(target_ids, max_len),
            ))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        inp, tgt = self.samples[idx]
        return torch.LongTensor(inp), torch.LongTensor(tgt)


# ============================================================================
# TRAINING
# ============================================================================

def train_model():
    """Main training function."""
    if not IMPORTS_OK:
        return

    log("=" * 60)
    log("CloudGuard AI — Transformer Training")
    log("=" * 60)

    device = torch.device("cpu")  # CPU only for portability
    log(f"Device: {device}")

    vocab = IaCVocabulary()
    log(f"Vocabulary: {vocab.vocab_size} tokens")

    # Augment data with name/resource substitutions
    all_pairs = list(TRAINING_PAIRS)
    name_swaps = [
        ('"data"', '"backup"'), ('"main"', '"primary"'),
        ('"data"', '"archive"'), ('"main"', '"replica"'),
        ('"uploads"', '"assets"'), ('"logs"', '"audit"'),
        ('"web"', '"frontend"'), ('"app"', '"service"'),
        ('"db"', '"database"'), ('"test"', '"staging"'),
    ]
    for vuln, secure in TRAINING_PAIRS:
        for old_name, new_name in name_swaps:
            v2 = vuln.replace(old_name, new_name)
            s2 = secure.replace(old_name, new_name)
            if v2 != vuln:
                all_pairs.append((v2, s2))

    log(f"Training pairs: {len(all_pairs)}")

    # Split 80/20
    split = int(len(all_pairs) * 0.8)
    train_pairs = all_pairs[:split]
    val_pairs = all_pairs[split:]

    MAX_LEN = 96
    train_ds = VulnSecurePairDataset(train_pairs, vocab, max_len=MAX_LEN)
    val_ds = VulnSecurePairDataset(val_pairs, vocab, max_len=MAX_LEN)

    train_loader = DataLoader(train_ds, batch_size=4, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=4, shuffle=False)

    log(f"Train: {len(train_ds)} samples, Val: {len(val_ds)} samples")

    # Tiny model for fast CPU training (~150K params)
    model = SecureCodeGenerator(
        vocab_size=vocab.vocab_size,
        d_model=64,
        num_heads=4,
        num_layers=2,
        d_ff=256,
        max_seq_length=MAX_LEN * 2,
        dropout=0.15,
        eos_idx=vocab.eos_idx,
    ).to(device)

    n_params = sum(p.numel() for p in model.parameters())
    log(f"Model: {n_params:,} parameters")

    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    criterion = nn.CrossEntropyLoss(ignore_index=vocab.pad_idx)

    EPOCHS = 60
    best_val = float("inf")
    save_path = "ml/models_artifacts/transformer_secure_codegen.pt"
    Path(save_path).parent.mkdir(parents=True, exist_ok=True)

    log(f"\nTraining for {EPOCHS} epochs...")
    log("-" * 40)

    for epoch in range(1, EPOCHS + 1):
        # --- Train ---
        model.train()
        train_loss = 0.0
        n_train = 0
        for inp, tgt in train_loader:
            inp, tgt = inp.to(device), tgt.to(device)
            optimizer.zero_grad()

            # Teacher forcing: concat input + shifted target
            combined = torch.cat([inp, tgt[:, :-1]], dim=1)
            logits = model(combined)

            # Loss on target portion only
            pred = logits[:, inp.size(1):, :]
            labels = tgt[:, 1:]
            loss = criterion(
                pred.contiguous().view(-1, vocab.vocab_size),
                labels.contiguous().view(-1),
            )
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            train_loss += loss.item() * inp.size(0)
            n_train += inp.size(0)

        train_loss /= max(n_train, 1)

        # --- Val ---
        model.eval()
        val_loss = 0.0
        n_val = 0
        with torch.no_grad():
            for inp, tgt in val_loader:
                inp, tgt = inp.to(device), tgt.to(device)
                combined = torch.cat([inp, tgt[:, :-1]], dim=1)
                logits = model(combined)
                pred = logits[:, inp.size(1):, :]
                labels = tgt[:, 1:]
                loss = criterion(
                    pred.contiguous().view(-1, vocab.vocab_size),
                    labels.contiguous().view(-1),
                )
                val_loss += loss.item() * inp.size(0)
                n_val += inp.size(0)
        val_loss /= max(n_val, 1)

        saved = ""
        if val_loss < best_val:
            best_val = val_loss
            torch.save({
                "model_state_dict": model.state_dict(),
                "vocab_size": vocab.vocab_size,
                "d_model": 64,
                "num_heads": 4,
                "num_layers": 2,
                "d_ff": 256,
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
            }, save_path)
            saved = " *saved*"

        log(f"Epoch {epoch:2d}/{EPOCHS}  train={train_loss:.4f}  val={val_loss:.4f}{saved}")

    log("-" * 40)
    log(f"Best val loss: {best_val:.4f}")
    log(f"Model saved to: {save_path}")

    # Save summary
    summary = {
        "timestamp": datetime.now().isoformat(),
        "vocab_size": vocab.vocab_size,
        "num_parameters": n_params,
        "d_model": 64,
        "num_layers": 2,
        "num_heads": 4,
        "training_pairs": len(all_pairs),
        "best_val_loss": best_val,
        "epochs": EPOCHS,
    }
    summary_path = Path(save_path).parent / "transformer_training_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    # Quick sanity check
    log("\n--- Sanity Check ---")
    gen = IaCSecureCodeGenerator(model_path=save_path)
    test = 'resource "aws_s3_bucket" "x" {\n  acl = "public-read"\n}'
    out = gen.generate_secure_code(test, max_length=64, temperature=0.7)
    log(f"Input:  {test}")
    log(f"Output: {out}")
    log("Done!")


if __name__ == "__main__":
    train_model()
