"""
Training script for GNN Attack Path Detector

Trains the model on synthetic infrastructure graphs to learn attack patterns.
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.loader import DataLoader
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List
import matplotlib.pyplot as plt

try:
    from ml.models.graph_neural_network import InfrastructureGNN, AttackPathPredictor
    from ml.models.attack_path_dataset import create_train_val_datasets
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("⚠️  Import error. Run from project root: python -m ml.models.train_gnn")


class GNNTrainer:
    """Trains and evaluates GNN model for attack path detection"""
    
    def __init__(
        self,
        model: InfrastructureGNN,
        device: torch.device,
        lr: float = 0.001,
        weight_decay: float = 5e-4
    ):
        self.model = model.to(device)
        self.device = device
        self.optimizer = optim.Adam(
            model.parameters(),
            lr=lr,
            weight_decay=weight_decay
        )
        self.criterion = nn.BCELoss()
        
        self.train_losses = []
        self.val_losses = []
        self.train_accuracies = []
        self.val_accuracies = []
        
    def train_epoch(self, train_loader: DataLoader) -> tuple[float, float]:
        """Train for one epoch"""
        self.model.train()
        total_loss = 0
        correct = 0
        total = 0
        
        for batch in train_loader:
            batch = batch.to(self.device)
            
            # Forward pass
            self.optimizer.zero_grad()
            risk_scores, _ = self.model(batch)
            loss = self.criterion(risk_scores.squeeze(), batch.y)
            
            # Backward pass
            loss.backward()
            self.optimizer.step()
            
            # Metrics
            total_loss += loss.item() * batch.num_graphs
            predictions = (risk_scores.squeeze() > 0.5).float()
            correct += (predictions == batch.y).sum().item()
            total += batch.num_graphs
        
        avg_loss = total_loss / total
        accuracy = correct / total
        
        return avg_loss, accuracy
    
    @torch.no_grad()
    def evaluate(self, val_loader: DataLoader) -> tuple[float, float, Dict]:
        """Evaluate model on validation set"""
        self.model.eval()
        total_loss = 0
        correct = 0
        total = 0
        
        true_positives = 0
        false_positives = 0
        true_negatives = 0
        false_negatives = 0
        
        for batch in val_loader:
            batch = batch.to(self.device)
            
            # Forward pass
            risk_scores, _ = self.model(batch)
            loss = self.criterion(risk_scores.squeeze(), batch.y)
            
            # Metrics
            total_loss += loss.item() * batch.num_graphs
            predictions = (risk_scores.squeeze() > 0.5).float()
            correct += (predictions == batch.y).sum().item()
            total += batch.num_graphs
            
            # Confusion matrix
            for pred, label in zip(predictions, batch.y):
                if pred == 1 and label == 1:
                    true_positives += 1
                elif pred == 1 and label == 0:
                    false_positives += 1
                elif pred == 0 and label == 0:
                    true_negatives += 1
                else:
                    false_negatives += 1
        
        avg_loss = total_loss / total
        accuracy = correct / total
        
        # Additional metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'true_negatives': true_negatives,
            'false_negatives': false_negatives
        }
        
        return avg_loss, accuracy, metrics
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        num_epochs: int = 100,
        early_stopping_patience: int = 15,
        model_save_path: str = 'ml/models/saved/gnn_attack_detector.pt'
    ):
        """Full training loop with early stopping"""
        
        print("🚀 Starting GNN training...")
        print(f"   Device: {self.device}")
        print(f"   Epochs: {num_epochs}")
        print(f"   Batch size: {train_loader.batch_size}")
        print()
        
        best_val_loss = float('inf')
        best_val_accuracy = 0
        patience_counter = 0
        
        for epoch in range(1, num_epochs + 1):
            # Train
            train_loss, train_acc = self.train_epoch(train_loader)
            
            # Validate
            val_loss, val_acc, val_metrics = self.evaluate(val_loader)
            
            # Track history
            self.train_losses.append(train_loss)
            self.val_losses.append(val_loss)
            self.train_accuracies.append(train_acc)
            self.val_accuracies.append(val_acc)
            
            # Print progress
            if epoch % 10 == 0 or epoch == 1:
                print(f"Epoch {epoch:3d}/{num_epochs}")
                print(f"  Train - Loss: {train_loss:.4f}, Acc: {train_acc:.4f}")
                print(f"  Val   - Loss: {val_loss:.4f}, Acc: {val_acc:.4f}")
                print(f"  Val   - Precision: {val_metrics['precision']:.4f}, Recall: {val_metrics['recall']:.4f}, F1: {val_metrics['f1_score']:.4f}")
                print()
            
            # Save best model
            if val_acc > best_val_accuracy:
                best_val_accuracy = val_acc
                best_val_loss = val_loss
                patience_counter = 0
                
                # Save checkpoint
                Path(model_save_path).parent.mkdir(parents=True, exist_ok=True)
                torch.save({
                    'epoch': epoch,
                    'model_state_dict': self.model.state_dict(),
                    'optimizer_state_dict': self.optimizer.state_dict(),
                    'train_loss': train_loss,
                    'val_loss': val_loss,
                    'val_accuracy': val_acc,
                    'val_metrics': val_metrics,
                    'num_features': self.model.num_node_features,
                    'hidden_channels': self.model.hidden_channels
                }, model_save_path)
                
                print(f"💾 Saved best model (Val Acc: {val_acc:.4f})")
            else:
                patience_counter += 1
            
            # Early stopping
            if patience_counter >= early_stopping_patience:
                print(f"\n⏹️  Early stopping triggered (patience={early_stopping_patience})")
                break
        
        print(f"\n✅ Training complete!")
        print(f"   Best Val Accuracy: {best_val_accuracy:.4f}")
        print(f"   Best Val Loss: {best_val_loss:.4f}")
        print(f"   Model saved to: {model_save_path}")
        
        return {
            'best_val_accuracy': best_val_accuracy,
            'best_val_loss': best_val_loss,
            'final_epoch': epoch,
            'train_losses': self.train_losses,
            'val_losses': self.val_losses,
            'train_accuracies': self.train_accuracies,
            'val_accuracies': self.val_accuracies
        }
    
    def plot_training_curves(self, save_path: str = 'ml/models/saved/training_curves.png'):
        """Plot training and validation curves"""
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
        
        # Loss curves
        epochs = range(1, len(self.train_losses) + 1)
        ax1.plot(epochs, self.train_losses, 'b-', label='Train Loss')
        ax1.plot(epochs, self.val_losses, 'r-', label='Val Loss')
        ax1.set_xlabel('Epoch')
        ax1.set_ylabel('Loss')
        ax1.set_title('Training and Validation Loss')
        ax1.legend()
        ax1.grid(True)
        
        # Accuracy curves
        ax2.plot(epochs, self.train_accuracies, 'b-', label='Train Accuracy')
        ax2.plot(epochs, self.val_accuracies, 'r-', label='Val Accuracy')
        ax2.set_xlabel('Epoch')
        ax2.set_ylabel('Accuracy')
        ax2.set_title('Training and Validation Accuracy')
        ax2.legend()
        ax2.grid(True)
        
        plt.tight_layout()
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=150)
        print(f"📊 Saved training curves to {save_path}")


def main():
    """Main training function"""
    
    if not IMPORTS_AVAILABLE:
        return
    
    # Configuration
    config = {
        'num_train_samples': 400,
        'num_val_samples': 100,
        'batch_size': 32,
        'num_epochs': 100,
        'learning_rate': 0.001,
        'hidden_channels': 64,
        'num_heads': 4,
        'dropout': 0.3,
        'early_stopping_patience': 15
    }
    
    print("🧠 CloudGuard AI - GNN Attack Path Detector Training")
    print("=" * 70)
    print(f"Configuration: {json.dumps(config, indent=2)}")
    print()
    
    # Device
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"🖥️  Using device: {device}")
    print()
    
    # Create datasets
    print("📚 Creating datasets...")
    train_dataset, val_dataset = create_train_val_datasets(
        num_train=config['num_train_samples'],
        num_val=config['num_val_samples']
    )
    
    train_loader = DataLoader(
        train_dataset,
        batch_size=config['batch_size'],
        shuffle=True
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=config['batch_size'],
        shuffle=False
    )
    
    print(f"✅ Train: {len(train_dataset)} samples, {len(train_loader)} batches")
    print(f"✅ Val: {len(val_dataset)} samples, {len(val_loader)} batches")
    print()
    
    # Create model
    print("🏗️  Building GNN model...")
    model = InfrastructureGNN(
        num_node_features=15,
        hidden_channels=config['hidden_channels'],
        num_heads=config['num_heads'],
        dropout=config['dropout']
    )
    
    num_params = sum(p.numel() for p in model.parameters())
    print(f"✅ Model created with {num_params:,} parameters")
    print()
    
    # Create trainer
    trainer = GNNTrainer(
        model=model,
        device=device,
        lr=config['learning_rate']
    )
    
    # Train
    results = trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        num_epochs=config['num_epochs'],
        early_stopping_patience=config['early_stopping_patience']
    )
    
    # Plot results
    trainer.plot_training_curves()
    
    # Save training summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'config': config,
        'results': {
            'best_val_accuracy': results['best_val_accuracy'],
            'best_val_loss': results['best_val_loss'],
            'final_epoch': results['final_epoch']
        },
        'device': str(device),
        'num_parameters': num_params
    }
    
    summary_path = 'ml/models/saved/training_summary.json'
    Path(summary_path).parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n📄 Training summary saved to {summary_path}")
    
    # Test prediction
    print("\n🧪 Testing trained model...")
    predictor = AttackPathPredictor(model_path='ml/models/saved/gnn_attack_detector.pt')
    
    # Vulnerable infrastructure example
    vulnerable_tf = """
    resource "aws_instance" "web" {
        ami = "ami-12345"
        instance_type = "t2.micro"
        associate_public_ip_address = true
    }
    
    resource "aws_security_group" "allow_all" {
        ingress {
            from_port = 0
            to_port = 65535
            protocol = "tcp"
            cidr_blocks = ["0.0.0.0/0"]
        }
    }
    
    resource "aws_db_instance" "database" {
        engine = "postgres"
        instance_class = "db.t2.micro"
        publicly_accessible = true
        storage_encrypted = false
    }
    """
    
    result = predictor.predict_attack_risk(vulnerable_tf)
    print(f"\n📊 Test Prediction:")
    print(f"   Risk Score: {result['risk_score']:.2%}")
    print(f"   Risk Level: {result['risk_level']}")
    print(f"   Critical Nodes: {', '.join(result['critical_nodes'])}")
    print(f"\n💡 {result['explanation']}")
    
    print("\n" + "=" * 70)
    print("✅ GNN training completed successfully!")
    print(f"   Model: ml/models/saved/gnn_attack_detector.pt")
    print(f"   Accuracy: {results['best_val_accuracy']:.2%}")
    print(f"   Ready for integration into CloudGuard AI")


if __name__ == '__main__':
    main()
