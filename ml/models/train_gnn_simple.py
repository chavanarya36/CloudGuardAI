"""
Quick GNN training script (simplified, no visualization)
"""

import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import json
from datetime import datetime

from ml.models.graph_neural_network import InfrastructureGNN
from ml.models.attack_path_dataset import create_train_val_datasets

# Import DataLoader directly to avoid slow transformers import
from torch.utils.data import DataLoader as TorchDataLoader

print("CloudGuard AI - GNN Training (Simplified)")
print("=" * 70)

# Configuration
config = {
    'num_train_samples': 400,
    'num_val_samples': 100,
    'batch_size': 32,
    'num_epochs': 50,  # Reduced for quick training
    'learning_rate': 0.001
}

print(f"Config: {json.dumps(config, indent=2)}\n")

# Device
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Device: {device}\n")

# Create datasets
print("Creating datasets...")
train_dataset, val_dataset = create_train_val_datasets(
    num_train=config['num_train_samples'],
    num_val=config['num_val_samples']
)

# Use custom collate function for graph batching
def collate_fn(batch):
    from torch_geometric.data import Batch
    return Batch.from_data_list(batch)

train_loader = TorchDataLoader(train_dataset, batch_size=config['batch_size'], shuffle=True, collate_fn=collate_fn)
val_loader = TorchDataLoader(val_dataset, batch_size=config['batch_size'], shuffle=False, collate_fn=collate_fn)

print(f"Train: {len(train_dataset)} samples")
print(f"Val: {len(val_dataset)} samples\n")

# Create model
print("Building model...")
model = InfrastructureGNN(num_node_features=15, hidden_channels=64, num_heads=4).to(device)
print(f"Parameters: {sum(p.numel() for p in model.parameters()):,}\n")

# Training
optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])
criterion = nn.BCELoss()

best_val_acc = 0
model_path = 'ml/models/saved/gnn_attack_detector.pt'

print("Training...\n")
for epoch in range(1, config['num_epochs'] + 1):
    # Train
    model.train()
    train_loss = 0
    train_correct = 0
    train_total = 0
    
    for batch in train_loader:
        batch = batch.to(device)
        optimizer.zero_grad()
        
        risk_scores, _ = model(batch)
        loss = criterion(risk_scores.squeeze(), batch.y)
        
        loss.backward()
        optimizer.step()
        
        train_loss += loss.item() * batch.num_graphs
        predictions = (risk_scores.squeeze() > 0.5).float()
        train_correct += (predictions == batch.y).sum().item()
        train_total += batch.num_graphs
    
    train_loss /= train_total
    train_acc = train_correct / train_total
    
    # Validate
    model.eval()
    val_loss = 0
    val_correct = 0
    val_total = 0
    
    with torch.no_grad():
        for batch in val_loader:
            batch = batch.to(device)
            risk_scores, _ = model(batch)
            loss = criterion(risk_scores.squeeze(), batch.y)
            
            val_loss += loss.item() * batch.num_graphs
            predictions = (risk_scores.squeeze() > 0.5).float()
            val_correct += (predictions == batch.y).sum().item()
            val_total += batch.num_graphs
    
    val_loss /= val_total
    val_acc = val_correct / val_total
    
    if epoch % 10 == 0 or epoch == 1:
        print(f"Epoch {epoch:2d}/{config['num_epochs']}")
        print(f"  Train - Loss: {train_loss:.4f}, Acc: {train_acc:.4f}")
        print(f"  Val   - Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")
        print()
    
    # Save best model
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'val_accuracy': val_acc,
            'val_loss': val_loss
        }, model_path)

print(f"\n✅ Training complete!")
print(f"   Best Val Accuracy: {best_val_acc:.4f}")
print(f"   Model saved to: {model_path}")

# Test prediction
print(f"\n🧪 Testing model...")
from ml.models.graph_neural_network import AttackPathPredictor

predictor = AttackPathPredictor(model_path=model_path)

vulnerable_tf = """
resource "aws_instance" "web" {
    associate_public_ip_address = true
}
resource "aws_security_group" "sg" {
    ingress {
        from_port = 0
        to_port = 65535
        cidr_blocks = ["0.0.0.0/0"]
    }
}
resource "aws_db_instance" "db" {
    publicly_accessible = true
    storage_encrypted = false
}
"""

result = predictor.predict_attack_risk(vulnerable_tf)
print(f"\n📊 Test Result:")
print(f"   Risk: {result['risk_level']}")
print(f"   Score: {result['risk_score']:.2%}")
print(f"   Critical Nodes: {', '.join(result['critical_nodes'])}")

print(f"\n" + "=" * 70)
print(f"✅ GNN training successful!")
print(f"   Ready for integration into CloudGuard AI")
