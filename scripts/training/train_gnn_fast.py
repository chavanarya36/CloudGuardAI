"""
Fast GNN Training - Avoids slow torch_geometric imports
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'ml'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

import torch
import torch.nn as nn
import torch.optim as optim
from pathlib import Path
import json
from datetime import datetime

print("CloudGuard AI - GNN Training")
print("=" * 70)

# Import after basic setup
from ml.models.graph_neural_network import InfrastructureGNN

# Configuration
config = {
    'num_train_samples': 400,
    'num_val_samples': 100,
    'batch_size': 32,
    'learning_rate': 0.001,
    'num_epochs': 50,
    'device': 'cpu'
}

print(f"Device: {config['device']}\n")

# Create datasets
print("Creating datasets...")
from ml.models.attack_path_dataset import create_train_val_datasets

train_dataset, val_dataset = create_train_val_datasets(
    num_train=config['num_train_samples'],
    num_val=config['num_val_samples']
)

print(f"Train: {len(train_dataset)} samples")
print(f"Val: {len(val_dataset)} samples\n")

# Manual batching function
def create_batch(data_list):
    """Manually batch graph data"""
    from torch_geometric.data import Batch
    return Batch.from_data_list(data_list)

# Create model
print("Building model...")
model = InfrastructureGNN(
    num_node_features=15,  # Dataset uses 15 features
    hidden_channels=64
).to(config['device'])

total_params = sum(p.numel() for p in model.parameters())
print(f"Model parameters: {total_params:,}\n")

# Training setup
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=config['learning_rate'])

# Training function
def train_epoch(model, dataset, batch_size):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    # Process in batches
    for i in range(0, len(dataset), batch_size):
        batch_data = [dataset[j] for j in range(i, min(i + batch_size, len(dataset)))]
        batch = create_batch(batch_data)
        batch = batch.to(config['device'])
        
        optimizer.zero_grad()
        out = model(batch)  # Pass entire batch object
        if isinstance(out, tuple):
            out = out[0]  # Get risk scores if tuple returned
        out = out.squeeze()  # Remove extra dimension [32, 1] -> [32]
        loss = criterion(out, batch.y)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        pred = (out > 0.5).float()
        correct += (pred == batch.y).sum().item()
        total += batch.y.size(0)
    
    return total_loss / (len(dataset) / batch_size), correct / total

# Validation function
def validate(model, dataset, batch_size):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for i in range(0, len(dataset), batch_size):
            batch_data = [dataset[j] for j in range(i, min(i + batch_size, len(dataset)))]
            batch = create_batch(batch_data)
            batch = batch.to(config['device'])
            
            out = model(batch)  # Pass entire batch object
            if isinstance(out, tuple):
                out = out[0]  # Get risk scores if tuple returned
            out = out.squeeze()  # Remove extra dimension
            loss = criterion(out, batch.y)
            
            total_loss += loss.item()
            pred = (out > 0.5).float()
            correct += (pred == batch.y).sum().item()
            total += batch.y.size(0)
    
    return total_loss / (len(dataset) / batch_size), correct / total

# Training loop
print("Starting training...")
print("-" * 70)

best_val_acc = 0
training_history = []

for epoch in range(config['num_epochs']):
    train_loss, train_acc = train_epoch(model, train_dataset, config['batch_size'])
    val_loss, val_acc = validate(model, val_dataset, config['batch_size'])
    
    training_history.append({
        'epoch': epoch + 1,
        'train_loss': train_loss,
        'train_acc': train_acc,
        'val_loss': val_loss,
        'val_acc': val_acc
    })
    
    # Save best model
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        save_path = Path('ml/models_artifacts/gnn_attack_detector.pt')
        save_path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            'model_state_dict': model.state_dict(),
            'config': config,
            'val_acc': val_acc,
            'epoch': epoch + 1
        }, save_path)
    
    # Print progress every 5 epochs
    if (epoch + 1) % 5 == 0 or epoch == 0:
        print(f"Epoch {epoch+1:3d}/{config['num_epochs']}: "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.4f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.4f}")

print("-" * 70)
print(f"\nTraining complete!")
print(f"Best validation accuracy: {best_val_acc:.4f}")
print(f"Model saved to: ml/models_artifacts/gnn_attack_detector.pt")

# Save training history
history_path = Path('ml/models_artifacts/training_history.json')
with open(history_path, 'w') as f:
    json.dump({
        'config': config,
        'best_val_acc': best_val_acc,
        'history': training_history,
        'timestamp': datetime.now().isoformat()
    }, f, indent=2)

print(f"Training history saved to: {history_path}")
print("\nDone!")
