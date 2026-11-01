import torch
from PIL import Image
from transformers import pipeline

from app.schemas import BBox, Detection, DetectionResponse


def load_model(name: str, device=1):
    return pipeline("object-detection", model=name, device=-1)  # CPU


def run_inference(model, image: Image.Image, threshold: float = 0.5) -> list[dict]:
    results = model(image.convert("RGB"), threshold=threshold)
    return [
        {
            "class": r["label"],
            "confidence": round(float(r["score"]), 3),
            "bbox": [
                r["box"]["xmin"],
                r["box"]["ymin"],
                r["box"]["xmax"],
                r["box"]["ymax"],
            ],
        }
        for r in results
    ]


class YOLOInferenceService:
    def __init__(self, yolo_model_path):
        self.model = YOLO(yolo_model_path)
        if torch.cuda.is_available():
            self.device = "cuda"
        elif torch.backends.mps.is_available():
            self.device = "mps"
        else:
            self.device = "cpu"
        self.model.to(self.device)

    def predict(self, image: Image.Image) -> DetectionResponse:
        """
        image: PIL Image object
        Returns: DetectionResponse with typed detections, count, and image dimensions
        """

        results = self.model(image)
        boxes = results[0].boxes

        detections = [
            Detection(
                bbox=BBox(
                    x1=float(box.xyxy[0][0]),
                    y1=float(box.xyxy[0][1]),
                    x2=float(box.xyxy[0][2]),
                    y2=float(box.xyxy[0][3]),
                ),
                confidence=round(float(box.conf[0]), 3),
                class_id=int(box.cls[0]),
                class_name=self.model.names[int(box.cls[0])],
            )
            for box in boxes
        ]

        return DetectionResponse(
            detections=detections,
            count=len(detections),
            image_width=image.width,
            image_height=image.height,
        )
