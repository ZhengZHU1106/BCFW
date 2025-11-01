import json
import os
import pickle
import threading

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F

from model_architecture import TransformerEnhancedEnsembleModel

class HierarchicalPredictor:
    def __init__(self, model_package_path: str, device: str = 'cpu', debug: bool = False):
        self.model_package_path = model_package_path
        self.device = torch.device(device)
        self.debug = debug
        self._model_initialized = False
        self._model_lock = threading.Lock()

        # Attributes populated after the first load
        self.model_info = {}
        self.scaler = None
        self.label_encoders = {}
        self.feature_names = []
        self.quantile_thresholds = {}
        self.binary_model = None
        self.multi_model = None
        self.binary_classes = []
        self.multi_classes = []

    def _load_model(self):
        if self._model_initialized:
            return

        if self.debug:
            print(f"[Predictor] Loading model from: {self.model_package_path}")

        # Load model info
        with open(os.path.join(self.model_package_path, 'model_info.json'), 'r') as f:
            self.model_info = json.load(f)
        
        # Load scaler
        with open(os.path.join(self.model_package_path, 'scaler.pkl'), 'rb') as f:
            self.scaler = pickle.load(f)

        # Load label encoders
        with open(os.path.join(self.model_package_path, 'label_encoder.pkl'), 'rb') as f:
            self.label_encoders = pickle.load(f)
        
        # Load feature names
        with open(os.path.join(self.model_package_path, 'selected_features.json'), 'r') as f:
            self.feature_names = json.load(f)['features']

        # Load quantile thresholds - 关键新增：加载训练时的固定分位数阈值
        with open(os.path.join(self.model_package_path, 'quantile_thresholds.pkl'), 'rb') as f:
            self.quantile_thresholds = pickle.load(f)

        # Load model weights
        model_checkpoint = torch.load(os.path.join(self.model_package_path, 'model.pth'), map_location=self.device)
        arch_info = self.model_info['architecture']

        # Initialize models
        self.binary_model = TransformerEnhancedEnsembleModel(
            input_dim=arch_info['input_features'], 
            num_classes=arch_info['binary_classes'],
            dropout_rate=arch_info['dropout_rate']
        ).to(self.device)

        self.multi_model = TransformerEnhancedEnsembleModel(
            input_dim=arch_info['input_features'], 
            num_classes=arch_info['multi_classes'],
            dropout_rate=arch_info['dropout_rate']
        ).to(self.device)

        # Load state dicts
        self.binary_model.load_state_dict(model_checkpoint['binary_model_state'])
        self.multi_model.load_state_dict(model_checkpoint['multi_model_state'])
        self.binary_model.eval()
        self.multi_model.eval()

        self.binary_classes = self.label_encoders['binary_classes']
        self.multi_classes = self.label_encoders['multi_classes']

        if self.debug:
            print("[Predictor] Model loaded successfully.")

        self._model_initialized = True

    def _ensure_model_loaded(self):
        if self._model_initialized:
            return

        with self._model_lock:
            if self._model_initialized:
                return
            self._load_model()

    def _preprocess(self, df: pd.DataFrame) -> torch.Tensor:
        self._ensure_model_loaded()

        # Validate and prepare features
        df = df.copy()
        df.columns = [col.strip() for col in df.columns]
        missing_features = set(self.feature_names) - set(df.columns)
        if missing_features:
            for feature in missing_features:
                df[feature] = 0
        df = df[self.feature_names]

        # Handle inf/nan values
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.fillna(0, inplace=True)
        
        # 关键修复：使用训练时保存的固定分位数阈值进行异常值裁剪
        # 这确保了与训练时完全一致的预处理流程
        for col in self.feature_names:
            if col in self.quantile_thresholds:
                q01 = self.quantile_thresholds[col]['q01']
                q99 = self.quantile_thresholds[col]['q99']
                df[col] = df[col].clip(lower=q01, upper=q99)
        
        if self.debug:
            print(f"[Predictor] Preprocessing {len(df)} samples with {len(df.columns)} features")
            print(f"[Predictor] Applied fixed quantile clipping (1%-99%) for {len(self.quantile_thresholds)} features")
        
        # 使用训练好的scaler进行标准化
        scaled_data = self.scaler.transform(df)
        return torch.from_numpy(scaled_data).float().to(self.device)

    def predict(self, dataframe: pd.DataFrame):
        self._ensure_model_loaded()

        input_tensor = self._preprocess(dataframe)

        with torch.no_grad():
            # Binary prediction
            binary_logits = self.binary_model(input_tensor)
            binary_probs = F.softmax(binary_logits, dim=1)
            binary_preds = torch.argmax(binary_probs, dim=1)

            # Multi-class prediction for all
            multi_logits = self.multi_model(input_tensor)
            multi_probs = F.softmax(multi_logits, dim=1)
            multi_preds = torch.argmax(multi_probs, dim=1)

        # Process results
        results = []
        for i in range(len(dataframe)):
            is_malicious = binary_preds[i].item() == 1
            binary_label = self.binary_classes[binary_preds[i].item()]
            binary_confidence = binary_probs[i].max().item()

            multi_label = self.multi_classes[multi_preds[i].item()]
            multi_confidence = multi_probs[i].max().item()

            # Final decision logic - 修正：严格按照训练时的层次化架构
            if is_malicious:
                # 如果二分类判定为恶意，使用多分类结果进行具体分类
                final_prediction = multi_label
                final_confidence = multi_confidence
            else:
                # 如果二分类判定为正常，直接采用二分类结果
                final_prediction = "Benign"
                final_confidence = binary_probs[i][0].item()  # 正常流量的置信度

            results.append({
                'binary_prediction': binary_label,
                'binary_confidence': binary_confidence,
                'multi_prediction': multi_label if is_malicious else None,
                'multi_confidence': multi_confidence if is_malicious else None,
                'final_prediction': final_prediction,
                'confidence': final_confidence
            })
        return results
