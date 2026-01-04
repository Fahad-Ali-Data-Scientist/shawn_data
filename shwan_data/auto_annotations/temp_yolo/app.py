from ultralytics import YOLO
from pathlib import Path

# Path to the merged dataset from the previous cell
DATASET_YAML = Path("all_dataset_singleclass/data.yaml")

# Create and train the YOLOv11-large model
model = model = YOLO("yolo11l-seg.pt")

model.train(
    data=str(DATASET_YAML),  # dataset.yaml path
    epochs=300,              # number of training epochs
    imgsz=640,               # image size
    batch=16,                # batch size (adjust per GPU)
    workers=8,               # number of dataloader workers
    project="runs/train",    # folder to save training results
    name="all_dataset_singleclass_sam",  # experiment name
    device=0,                # GPU id (use 'cpu' if no GPU)
    save=True
)

print("\n✅ Training started on YOLOv11-large seg model using merged dataset!")
