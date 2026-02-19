"""
Dataset loader for training GNN on infrastructure attack paths.

Creates synthetic training data from vulnerable infrastructure patterns.
"""

import torch
from torch_geometric.data import Data, Dataset
from typing import List, Dict, Tuple, Optional
import json
import random
from pathlib import Path


class AttackPathDataset(Dataset):
    """
    Dataset of infrastructure graphs labeled with attack path presence.
    
    Generates synthetic Terraform infrastructures with known vulnerabilities
    and attack paths for GNN training.
    """
    
    def __init__(
        self,
        root: str = 'ml/models/training_data',
        num_samples: int = 500,
        split: str = 'train',
        transform=None,
        pre_transform=None
    ):
        self.num_samples = num_samples
        self.split = split
        self.samples = []
        
        super().__init__(root, transform, pre_transform)
        
        # Generate synthetic data on first run
        if not self.processed_paths or not Path(self.processed_paths[0]).exists():
            self._generate_synthetic_data()
    
    @property
    def raw_file_names(self) -> List[str]:
        return []
    
    @property
    def processed_file_names(self) -> List[str]:
        return [f'{self.split}_data.pt']
    
    def download(self):
        pass
    
    def process(self):
        """Generate and save synthetic training data"""
        data_list = self._generate_synthetic_data()
        
        if self.pre_filter is not None:
            data_list = [data for data in data_list if self.pre_filter(data)]
        
        if self.pre_transform is not None:
            data_list = [self.pre_transform(data) for data in data_list]
        
        torch.save(data_list, self.processed_paths[0])
        # Cache in memory for fast access
        self._data_cache = data_list
    
    def len(self) -> int:
        if not hasattr(self, '_len_cache'):
            if hasattr(self, '_data_cache'):
                self._len_cache = len(self._data_cache)
            else:
                data_list = torch.load(self.processed_paths[0], weights_only=False)
                self._data_cache = data_list
                self._len_cache = len(data_list)
        return self._len_cache
    
    def get(self, idx: int) -> Data:
        if not hasattr(self, '_data_cache'):
            self._data_cache = torch.load(self.processed_paths[0], weights_only=False)
        return self._data_cache[idx]
    
    def _generate_synthetic_data(self) -> List[Data]:
        """
        Generate synthetic infrastructure graphs with attack paths.
        
        Patterns:
        1. Public instance → Database (vulnerable)
        2. Public S3 → Credentials → Database (vulnerable)
        3. Private instance → Database with encryption (secure)
        4. Load balancer → Private instances → Database (secure)
        """
        
        print(f"🔨 Generating {self.num_samples} synthetic infrastructure graphs...")
        
        data_list = []
        
        # Generate equal numbers of vulnerable and secure infrastructures
        num_vulnerable = self.num_samples // 2
        num_secure = self.num_samples - num_vulnerable
        
        # Vulnerable patterns
        for i in range(num_vulnerable):
            if i % 3 == 0:
                graph = self._create_public_instance_to_db()
            elif i % 3 == 1:
                graph = self._create_public_s3_leak()
            else:
                graph = self._create_exposed_admin_panel()
            
            graph.y = torch.tensor([1.0], dtype=torch.float)  # Label: vulnerable
            data_list.append(graph)
        
        # Secure patterns
        for i in range(num_secure):
            if i % 3 == 0:
                graph = self._create_secure_web_app()
            elif i % 3 == 1:
                graph = self._create_secure_data_storage()
            else:
                graph = self._create_defense_in_depth()
            
            graph.y = torch.tensor([0.0], dtype=torch.float)  # Label: secure
            data_list.append(graph)
        
        # Shuffle
        random.shuffle(data_list)
        
        print(f"✅ Generated {len(data_list)} graphs ({num_vulnerable} vulnerable, {num_secure} secure)")
        
        return data_list
    
    def _create_public_instance_to_db(self) -> Data:
        """
        Vulnerable pattern: Internet → Public EC2 → Database
        Attack path: Compromise EC2, access database
        """
        
        # Nodes: [Internet Gateway, EC2, Database]
        node_features = [
            self._internet_gateway_features(),
            self._public_ec2_features(),
            self._unencrypted_db_features()
        ]
        
        # Edges: Internet → EC2, EC2 → DB
        edge_index = torch.tensor([
            [0, 1],  # Internet to EC2
            [1, 2],  # EC2 to DB
            [2, 1],  # Bidirectional
            [1, 0]
        ], dtype=torch.long).t().contiguous()
        
        x = torch.tensor(node_features, dtype=torch.float)
        
        return Data(x=x, edge_index=edge_index)
    
    def _create_public_s3_leak(self) -> Data:
        """
        Vulnerable pattern: Public S3 bucket contains database credentials
        Attack path: Download S3 → Extract creds → Access DB
        """
        
        # Nodes: [Internet, S3, Credentials, Database]
        node_features = [
            self._internet_gateway_features(),
            self._public_s3_features(),
            self._exposed_credentials_features(),
            self._database_features(encrypted=False)
        ]
        
        # Edges: Internet → S3, S3 contains Creds, Creds → DB
        edge_index = torch.tensor([
            [0, 1], [1, 0],  # Internet ↔ S3
            [1, 2], [2, 1],  # S3 ↔ Credentials
            [2, 3], [3, 2]   # Credentials ↔ DB
        ], dtype=torch.long).t().contiguous()
        
        x = torch.tensor(node_features, dtype=torch.float)
        
        return Data(x=x, edge_index=edge_index)
    
    def _create_exposed_admin_panel(self) -> Data:
        """
        Vulnerable pattern: Admin panel exposed on 0.0.0.0/0 without MFA
        """
        
        # Nodes: [Internet, Load Balancer, Admin Panel, IAM Role, Database]
        node_features = [
            self._internet_gateway_features(),
            self._public_lb_features(),
            self._admin_instance_features(mfa=False),
            self._admin_role_features(),
            self._database_features(encrypted=True)
        ]
        
        # Edges: Internet → LB → Admin → IAM → DB
        edge_index = torch.tensor([
            [0, 1], [1, 2], [2, 3], [3, 4],
            [1, 0], [2, 1], [3, 2], [4, 3]
        ], dtype=torch.long).t().contiguous()
        
        x = torch.tensor(node_features, dtype=torch.float)
        
        return Data(x=x, edge_index=edge_index)
    
    def _create_secure_web_app(self) -> Data:
        """
        Secure pattern: Internet → LB → Private instances → Private DB (encrypted)
        No direct attack path
        """
        
        # Nodes: [Internet, LB, WAF, Private Instance, Private DB]
        node_features = [
            self._internet_gateway_features(),
            self._internal_lb_features(),
            self._waf_features(),
            self._private_ec2_features(),
            self._database_features(encrypted=True, public=False)
        ]
        
        # Edges: Internet → LB → WAF → Instance → DB (but WAF blocks attacks)
        edge_index = torch.tensor([
            [0, 1], [1, 2], [2, 3], [3, 4],
            [1, 0], [2, 1], [3, 2], [4, 3]
        ], dtype=torch.long).t().contiguous()
        
        x = torch.tensor(node_features, dtype=torch.float)
        
        return Data(x=x, edge_index=edge_index)
    
    def _create_secure_data_storage(self) -> Data:
        """
        Secure pattern: Private S3, encrypted, with VPC endpoint
        """
        
        # Nodes: [VPC, Private S3, Encryption, Logging, Backup]
        node_features = [
            self._vpc_features(),
            self._private_s3_features(),
            self._encryption_features(),
            self._logging_features(),
            self._backup_features()
        ]
        
        # Edges: VPC contains all, S3 uses encryption/logging/backup
        edge_index = torch.tensor([
            [0, 1], [1, 2], [1, 3], [1, 4],
            [1, 0], [2, 1], [3, 1], [4, 1]
        ], dtype=torch.long).t().contiguous()
        
        x = torch.tensor(node_features, dtype=torch.float)
        
        return Data(x=x, edge_index=edge_index)
    
    def _create_defense_in_depth(self) -> Data:
        """
        Secure pattern: Multiple security layers
        Internet → WAF → LB → Private instances → Encrypted DB with MFA
        """
        
        # Nodes: [Internet, WAF, LB, Private EC2, VPN, Encrypted DB, MFA]
        node_features = [
            self._internet_gateway_features(),
            self._waf_features(),
            self._internal_lb_features(),
            self._private_ec2_features(),
            self._vpn_features(),
            self._database_features(encrypted=True, public=False),
            self._mfa_features()
        ]
        
        # Edges: Layered defense
        edge_index = torch.tensor([
            [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6],
            [1, 0], [2, 1], [3, 2], [4, 3], [5, 4], [6, 5]
        ], dtype=torch.long).t().contiguous()
        
        x = torch.tensor(node_features, dtype=torch.float)
        
        return Data(x=x, edge_index=edge_index)
    
    # Feature generators (15-dimensional vectors matching GNN input)
    
    def _internet_gateway_features(self) -> List[float]:
        """Internet gateway: maximally exposed"""
        return [
            0.09,  # Resource type: internet_gateway
            1.0,   # Public
            0.0,   # No encryption needed
            0.0,   # No auth
            0.0,   # No sensitive data
            0.0,   # No admin privileges
            1.0,   # Maximum exposure
            0.0,   # No security group
            0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 1.0  # Other features
        ]
    
    def _public_ec2_features(self) -> List[float]:
        """Public EC2 instance with weak security"""
        return [
            0.0,   # Resource type: aws_instance
            1.0,   # Public IP
            0.0,   # Not encrypted
            0.5,   # Weak auth
            0.0,   # Not sensitive
            0.0,   # Not admin
            0.9,   # High exposure
            0.0,   # Weak SG (0.0.0.0/0)
            0.0, 0.0, 0.0, 0.0, 0.5, 0.2, 1.0  # Logs off, no monitoring, etc.
        ]
    
    def _private_ec2_features(self) -> List[float]:
        """Private EC2 instance with good security"""
        return [
            0.0,   # Resource type: aws_instance
            0.0,   # No public IP
            1.0,   # Encrypted
            1.0,   # Strong auth
            0.0,   # Not sensitive
            0.0,   # Not admin
            0.2,   # Low exposure
            0.8,   # Restrictive SG
            1.0, 1.0, 0.5, 1.0, 0.7, 0.9, 0.5  # Logs, monitoring, backup
        ]
    
    def _unencrypted_db_features(self) -> List[float]:
        """Unencrypted database (vulnerable)"""
        return [
            0.03,  # Resource type: aws_rds_instance
            0.5,   # Somewhat public
            0.0,   # NOT encrypted ← vulnerability
            0.5,   # Weak auth
            1.0,   # Sensitive data
            0.0,   # Not admin
            0.5,   # Moderate exposure
            0.3,   # Weak SG
            0.0, 0.0, 0.0, 0.0, 0.5, 0.3, 0.5  # Poor security posture
        ]
    
    def _database_features(self, encrypted: bool = True, public: bool = False) -> List[float]:
        """Database with configurable security"""
        return [
            0.03,  # Resource type: aws_rds_instance
            1.0 if public else 0.0,
            1.0 if encrypted else 0.0,
            1.0 if encrypted else 0.5,
            1.0,   # Sensitive data
            0.0,
            0.8 if public else 0.1,
            0.8 if not public else 0.2,
            1.0 if encrypted else 0.0,
            1.0 if encrypted else 0.0,
            1.0 if encrypted else 0.0,
            1.0 if encrypted else 0.0,
            0.7, 0.8 if encrypted else 0.3, 0.5
        ]
    
    def _public_s3_features(self) -> List[float]:
        """Public S3 bucket (vulnerable)"""
        return [
            0.02,  # Resource type: aws_s3_bucket
            1.0,   # Public
            0.0,   # Not encrypted
            0.0,   # No auth (public-read)
            1.0,   # Sensitive data
            0.0,
            1.0,   # Maximum exposure
            0.0,   # No SG
            0.0, 0.0, 0.0, 0.0, 0.5, 0.1, 0.5  # Poor security
        ]
    
    def _private_s3_features(self) -> List[float]:
        """Private encrypted S3 bucket (secure)"""
        return [
            0.02,  # Resource type: aws_s3_bucket
            0.0,   # Private
            1.0,   # Encrypted
            1.0,   # Requires auth
            1.0,   # Sensitive data
            0.0,
            0.1,   # Low exposure
            1.0,   # N/A for S3
            1.0, 1.0, 1.0, 1.0, 0.8, 0.9, 0.5  # Good security
        ]
    
    def _exposed_credentials_features(self) -> List[float]:
        """Exposed credentials (secret/password)"""
        return [
            0.5,   # Generic type
            1.0,   # Exposed
            0.0,   # Not encrypted
            0.0,   # No auth required
            1.0,   # Highly sensitive
            1.0,   # Can grant admin access
            1.0,   # Maximum exposure
            0.0,
            0.0, 0.0, 0.0, 0.0, 0.5, 0.0, 1.0
        ]
    
    def _public_lb_features(self) -> List[float]:
        """Public load balancer"""
        return [
            0.10,  # Resource type: aws_lb
            1.0,   # Internet-facing
            0.0,   # N/A
            0.5,
            0.0,
            0.0,
            1.0,   # Public exposure
            0.5,   # Some restrictions
            1.0, 1.0, 0.0, 0.5, 0.7, 0.7, 1.0
        ]
    
    def _internal_lb_features(self) -> List[float]:
        """Internal load balancer"""
        return [
            0.10,  # Resource type: aws_lb
            0.0,   # Internal
            1.0,   # TLS
            1.0,
            0.0,
            0.0,
            0.3,   # Low exposure
            0.8,   # Restricted
            1.0, 1.0, 0.0, 0.5, 0.8, 0.9, 1.0
        ]
    
    def _admin_instance_features(self, mfa: bool = False) -> List[float]:
        """Admin instance/panel"""
        return [
            0.0,   # aws_instance
            0.5,   # Semi-public
            0.5,
            0.5,
            0.0,
            1.0,   # Admin privileges
            0.7,
            0.3 if not mfa else 0.8,
            0.5, 0.5, 1.0 if mfa else 0.0, 0.5, 0.6, 0.5, 1.0
        ]
    
    def _admin_role_features(self) -> List[float]:
        """IAM admin role"""
        return [
            0.05,  # aws_iam_role
            0.0,
            0.0,
            1.0,
            0.0,
            1.0,   # Admin privileges
            0.0,
            1.0,
            1.0, 1.0, 0.0, 0.0, 0.7, 0.7, 0.5
        ]
    
    def _waf_features(self) -> List[float]:
        """Web Application Firewall (security control)"""
        return [
            0.5,   # Generic security service
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,   # Not exposed
            1.0,   # Highly restrictive
            1.0, 1.0, 0.0, 0.0, 0.9, 1.0, 0.5
        ]
    
    def _vpc_features(self) -> List[float]:
        """VPC (network isolation)"""
        return [
            0.07,  # aws_vpc
            0.0,   # Private
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,   # Isolated
            1.0,   # Controlled
            1.0, 1.0, 0.0, 0.0, 0.8, 0.8, 1.0
        ]
    
    def _encryption_features(self) -> List[float]:
        """Encryption service (security control)"""
        return [
            0.6,
            0.0,
            1.0,   # IS encryption
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0, 1.0, 0.0, 0.0, 0.9, 1.0, 0.0
        ]
    
    def _logging_features(self) -> List[float]:
        """Logging service"""
        return [
            0.7,
            0.0,
            1.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0, 1.0, 0.0, 0.0, 0.8, 1.0, 0.0
        ]
    
    def _backup_features(self) -> List[float]:
        """Backup service"""
        return [
            0.8,
            0.0,
            1.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0, 1.0, 0.0, 1.0, 0.8, 1.0, 0.0
        ]
    
    def _vpn_features(self) -> List[float]:
        """VPN gateway (security control)"""
        return [
            0.5,
            0.0,
            1.0,   # Encrypted tunnel
            1.0,   # Requires auth
            0.0,
            0.0,
            0.1,   # Low exposure (requires VPN)
            1.0,   # Highly restrictive
            1.0, 1.0, 1.0, 0.0, 0.9, 0.9, 0.5
        ]
    
    def _mfa_features(self) -> List[float]:
        """MFA service (security control)"""
        return [
            0.9,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            1.0,
            1.0, 1.0, 1.0, 0.0, 0.9, 1.0, 0.0
        ]


def create_train_val_datasets(
    num_train: int = 400,
    num_val: int = 100,
    root: str = 'ml/models/training_data'
) -> Tuple[AttackPathDataset, AttackPathDataset]:
    """
    Create training and validation datasets.
    
    Returns:
        train_dataset, val_dataset
    """
    
    train_dataset = AttackPathDataset(
        root=root,
        num_samples=num_train,
        split='train'
    )
    
    val_dataset = AttackPathDataset(
        root=root,
        num_samples=num_val,
        split='val'
    )
    
    return train_dataset, val_dataset


if __name__ == '__main__':
    print("📚 Creating synthetic attack path datasets...")
    
    train_ds, val_ds = create_train_val_datasets(num_train=400, num_val=100)
    
    print(f"\n✅ Training set: {len(train_ds)} samples")
    print(f"✅ Validation set: {len(val_ds)} samples")
    
    # Show example
    sample = train_ds[0]
    print(f"\n📊 Sample graph:")
    print(f"   Nodes: {sample.x.shape[0]}")
    print(f"   Edges: {sample.edge_index.shape[1]}")
    print(f"   Label: {'VULNERABLE' if sample.y.item() > 0.5 else 'SECURE'}")
