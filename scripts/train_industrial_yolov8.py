import os
import argparse
import logging
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aeromind.training")

def train_industrial_model(dataset_yaml: str, epochs: int, batch_size: int, weights: str = "yolov8m.pt"):
    """
    Fine-tunes a YOLOv8 model on custom industrial datasets (e.g. PPE, Forklifts).
    """
    logger.info(f"Starting YOLOv8 training using base weights: {weights}")
    logger.info(f"Dataset config: {dataset_yaml}, Epochs: {epochs}, Batch size: {batch_size}")
    
    try:
        model = YOLO(weights)
        
        # Start training
        results = model.train(
            data=dataset_yaml,
            epochs=epochs,
            batch=batch_size,
            imgsz=640,
            device='auto',  # Automatically choose GPU if available
            project='runs/train',
            name='aeromind_industrial_v1'
        )
        
        logger.info(f"Training completed successfully. Best weights saved to: {results.save_dir}/weights/best.pt")
        return results.save_dir
        
    except Exception as e:
        logger.error(f"Training failed: {e}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AeroMind Industrial YOLOv8 Trainer")
    parser.add_argument("--data", type=str, required=True, help="Path to data.yaml file")
    parser.add_argument("--epochs", type=int, default=100, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--weights", type=str, default="yolov8m.pt", help="Base model weights")
    
    args = parser.parse_args()
    train_industrial_model(args.data, args.epochs, args.batch, args.weights)
