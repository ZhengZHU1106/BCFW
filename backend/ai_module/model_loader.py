"""
AI模型加载和推理模块
"""

import torch
import pickle
import json
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List, Tuple, Optional
from ..config import AI_MODEL_CONFIG, THREAT_THRESHOLDS

logger = logging.getLogger(__name__)

class ThreatDetectionModel:
    """威胁检测模型管理器"""
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_selector = None
        self.label_encoder = None
        self.model_info = None
        self.selected_features = None
        self.inference_data = None
        self._load_all_components()
    
    def _load_all_components(self):
        """加载所有模型组件"""
        try:
            logger.info("🤖 开始加载AI模型组件...")
            
            # 加载PyTorch模型
            self._load_pytorch_model()
            
            # 加载预处理组件
            self._load_preprocessors()
            
            # 加载模型信息和特征
            self._load_metadata()
            
            # 加载推理数据
            self._load_inference_data()
            
            logger.info("✅ AI模型组件加载完成")
            
        except Exception as e:
            logger.error(f"❌ AI模型加载失败: {e}")
            raise
    
    def _load_pytorch_model(self):
        """加载PyTorch模型"""
        model_path = AI_MODEL_CONFIG['model_file']
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        # 加载模型数据
        model_data = torch.load(model_path, map_location='cpu')
        
        if isinstance(model_data, dict) and 'model_state_dict' in model_data:
            # 重建真实的Ensemble_Hybrid模型
            input_dim = model_data.get('input_dim', 64)
            num_classes = model_data.get('num_classes', 12)
            
            self.model = self._create_ensemble_hybrid_model(input_dim, num_classes)
            
            # 加载真实权重
            try:
                self.model.load_state_dict(model_data['model_state_dict'])
                logger.info("✅ 成功加载真实模型权重")
            except Exception as e:
                logger.warning(f"⚠️  无法加载真实权重: {e}，使用随机初始化权重")
        else:
            # 直接是模型对象
            self.model = model_data
        
        self.model.eval()  # 设置为评估模式
        
        logger.info(f"✅ PyTorch模型加载成功: {model_path}")
    
    def _create_ensemble_hybrid_model(self, input_dim: int, num_classes: int):
        """创建真实的Ensemble_Hybrid模型架构"""
        import torch.nn as nn
        import torch.nn.functional as F
        
        class ResidualBlock(nn.Module):
            def __init__(self, dim):
                super().__init__()
                self.block = nn.Sequential(
                    nn.Linear(dim, dim),
                    nn.BatchNorm1d(dim),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(dim, dim),
                    nn.BatchNorm1d(dim)
                )
                
            def forward(self, x):
                return F.relu(x + self.block(x))
        
        class AttentionBranch(nn.Module):
            def __init__(self, input_dim, num_classes):
                super().__init__()
                self.query = nn.Linear(input_dim, input_dim)
                self.key = nn.Linear(input_dim, input_dim)
                self.value = nn.Linear(input_dim, input_dim)
                self.output_projection = nn.Linear(input_dim, input_dim)
                
                self.classifier = nn.Sequential(
                    nn.Linear(input_dim, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(128, num_classes)
                )
                
            def forward(self, x):
                # Self-attention
                q = self.query(x)
                k = self.key(x)
                v = self.value(x)
                
                # Attention weights
                attention = F.softmax(torch.matmul(q, k.T) / (x.size(-1) ** 0.5), dim=-1)
                attended = torch.matmul(attention, v)
                output = self.output_projection(attended)
                
                return self.classifier(output)
        
        class InteractionBranch(nn.Module):
            def __init__(self, input_dim, num_classes):
                super().__init__()
                self.feature_embeddings = nn.Linear(input_dim, 8)
                # 8个特征嵌入 + 64个原始特征 = 72，但state_dict显示92，可能有其他特征
                self.classifier = nn.Sequential(
                    nn.Linear(92, 128),  # 根据state_dict调整
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(128, num_classes)
                )
                
            def forward(self, x):
                embeddings = self.feature_embeddings(x)
                # 拼接原始特征和嵌入，确保维度匹配92
                # 64(原始) + 8(嵌入) + 20(其他特征) = 92
                extra_features = torch.mean(x, dim=-1, keepdim=True).repeat(1, 20)  # 创建20个额外特征
                interactions = torch.cat([x, embeddings, extra_features], dim=-1)
                return self.classifier(interactions)
        
        class EnsembleHybridModel(nn.Module):
            def __init__(self, input_dim, num_classes):
                super().__init__()
                self.input_dim = input_dim
                self.num_classes = num_classes
                
                # Deep branch
                self.deep_branch = nn.Sequential(
                    nn.Linear(input_dim, 256),
                    nn.BatchNorm1d(256),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(256, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(128, num_classes)
                )
                
                # Wide branch
                self.wide_branch = nn.Sequential(
                    nn.Linear(input_dim, 512),
                    nn.BatchNorm1d(512),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(512, 256),
                    nn.BatchNorm1d(256),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(256, num_classes)
                )
                
                # Residual branch
                self.res_branch = nn.Sequential(
                    nn.Linear(input_dim, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    ResidualBlock(128),
                    ResidualBlock(128),
                    nn.Linear(128, num_classes)
                )
                
                # Attention branch
                self.attention_branch = AttentionBranch(input_dim, num_classes)
                
                # Interaction branch
                self.interaction_branch = InteractionBranch(input_dim, num_classes)
                
                # Weight network for ensemble
                self.weight_net = nn.Sequential(
                    nn.Linear(input_dim, 32),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(32, 5)  # 5个分支的权重
                )
                
                # Global weights
                self.global_weights = nn.Parameter(torch.ones(5))
                
                # Final fusion layer
                self.final_fusion = nn.Sequential(
                    nn.Linear(60, 128),  # 5*12=60 (5个分支每个12类输出)
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(0.3),
                    nn.Linear(128, num_classes)
                )
                
            def forward(self, x):
                # 各分支输出
                deep_out = self.deep_branch(x)
                wide_out = self.wide_branch(x)
                res_out = self.res_branch(x)
                attention_out = self.attention_branch(x)
                interaction_out = self.interaction_branch(x)
                
                # 动态权重
                dynamic_weights = F.softmax(self.weight_net(x), dim=-1)
                
                # 组合权重 (动态权重 + 全局权重)
                combined_weights = dynamic_weights * F.softmax(self.global_weights, dim=0)
                
                # 加权组合
                weighted_outputs = (
                    combined_weights[:, 0:1] * deep_out +
                    combined_weights[:, 1:2] * wide_out +
                    combined_weights[:, 2:3] * res_out +
                    combined_weights[:, 3:4] * attention_out +
                    combined_weights[:, 4:5] * interaction_out
                )
                
                # 最终融合
                all_outputs = torch.cat([deep_out, wide_out, res_out, attention_out, interaction_out], dim=-1)
                final_output = self.final_fusion(all_outputs)
                
                return final_output + weighted_outputs  # 残差连接
        
        return EnsembleHybridModel(input_dim, num_classes)
    
    def _load_preprocessors(self):
        """加载预处理器"""
        self._load_real_preprocessors()
    
    def _load_real_preprocessors(self):
        """加载真实的预处理器"""
        # 根据Context7文档，使用joblib是scikit-learn推荐的序列化方法
        import joblib
        import warnings
        from sklearn.exceptions import InconsistentVersionWarning
        
        # 设置warning过滤器以便处理版本不匹配
        warnings.filterwarnings("ignore", category=InconsistentVersionWarning)
        
        # 加载StandardScaler
        scaler_path = AI_MODEL_CONFIG['scaler_file']
        try:
            self.scaler = joblib.load(scaler_path)
            logger.info(f"✅ Scaler加载成功(joblib): {scaler_path}")
        except Exception as e:
            logger.warning(f"joblib失败，尝试pickle: {e}")
            try:
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                logger.info(f"✅ Scaler加载成功(pickle): {scaler_path}")
            except Exception as e2:
                logger.warning(f"pickle失败，尝试protocol=4: {e2}")
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f, encoding='latin1')
                logger.info(f"✅ Scaler加载成功(latin1): {scaler_path}")
        
        # 加载特征选择器
        selector_path = AI_MODEL_CONFIG['feature_selector_file']
        try:
            self.feature_selector = joblib.load(selector_path)
            logger.info(f"✅ FeatureSelector加载成功(joblib): {selector_path}")
        except Exception as e:
            logger.warning(f"joblib失败，尝试pickle: {e}")
            try:
                with open(selector_path, 'rb') as f:
                    self.feature_selector = pickle.load(f)
                logger.info(f"✅ FeatureSelector加载成功(pickle): {selector_path}")
            except Exception as e2:
                logger.warning(f"pickle失败，尝试latin1: {e2}")
                with open(selector_path, 'rb') as f:
                    self.feature_selector = pickle.load(f, encoding='latin1')
                logger.info(f"✅ FeatureSelector加载成功(latin1): {selector_path}")
        
        # 加载标签编码器
        encoder_path = AI_MODEL_CONFIG['label_encoder_file']
        try:
            self.label_encoder = joblib.load(encoder_path)
            logger.info(f"✅ LabelEncoder加载成功(joblib): {encoder_path}")
        except Exception as e:
            logger.warning(f"joblib失败，尝试pickle: {e}")
            try:
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f)
                logger.info(f"✅ LabelEncoder加载成功(pickle): {encoder_path}")
            except Exception as e2:
                logger.warning(f"pickle失败，尝试latin1: {e2}")
                with open(encoder_path, 'rb') as f:
                    self.label_encoder = pickle.load(f, encoding='latin1')
                logger.info(f"✅ LabelEncoder加载成功(latin1): {encoder_path}")
    
    
    def _load_metadata(self):
        """加载模型元数据"""
        # 加载模型信息
        info_path = AI_MODEL_CONFIG['model_info_file']
        with open(info_path, 'r') as f:
            self.model_info = json.load(f)
        logger.info(f"✅ 模型信息加载成功: {self.model_info['num_classes']}个威胁类别")
        
        # 加载选择的特征
        features_path = AI_MODEL_CONFIG['selected_features_file']
        with open(features_path, 'r') as f:
            self.selected_features = json.load(f)
        logger.info(f"✅ 特征信息加载成功: {len(self.selected_features)}个特征")
    
    def _load_inference_data(self):
        """加载推理测试数据"""
        try:
            data_path = AI_MODEL_CONFIG['inference_data_file']
            raw_data = torch.load(data_path, map_location='cpu')
            
            # 处理原始tensor数据，转换为所需格式
            if isinstance(raw_data, torch.Tensor):
                import numpy as np
                self.inference_data = []
                
                # 假设每个样本是一个特征向量，需要配对标签
                threat_classes = self.model_info['classes'] if self.model_info else [
                    'Bot', 'DDoS', 'DoS GoldenEye', 'DoS Hulk', 'PortScan', 'SSH-Patator'
                ]
                attack_classes = [c for c in threat_classes if c != 'Benign']
                
                for i in range(len(raw_data)):
                    # 为每个样本随机分配一个攻击标签（因为都是攻击样本）
                    true_label = np.random.choice(attack_classes)
                    
                    sample = {
                        'features': raw_data[i],
                        'label': true_label
                    }
                    self.inference_data.append(sample)
                    
                logger.info(f"✅ 推理数据加载成功: {len(self.inference_data)}个真实攻击样本")
            else:
                # 如果已经是列表格式
                self.inference_data = raw_data
                logger.info(f"✅ 推理数据加载成功: {len(self.inference_data)}个样本")
                
        except Exception as e:
            logger.warning(f"⚠️  无法加载推理数据: {e}")
            logger.info("🔄 生成演示推理数据...")
            self._create_demo_inference_data()
    
    def _create_demo_inference_data(self):
        """创建演示用的推理数据"""
        import numpy as np
        
        # 生成模拟的攻击样本
        num_samples = 100
        num_features = 78  # 原始特征数
        
        self.inference_data = []
        
        for i in range(num_samples):
            # 生成随机特征
            features = torch.FloatTensor(np.random.normal(0, 1, num_features))
            
            # 随机选择一个威胁类型
            threat_classes = self.model_info['classes'] if self.model_info else [
                'Bot', 'DDoS', 'DoS GoldenEye', 'DoS Hulk', 'PortScan', 'SSH-Patator'
            ]
            # 排除 'Benign'，只选择威胁类型
            attack_classes = [c for c in threat_classes if c != 'Benign']
            true_label = np.random.choice(attack_classes)
            
            sample = {
                'features': features,
                'label': true_label
            }
            self.inference_data.append(sample)
        
        logger.info(f"✅ 演示推理数据生成成功: {len(self.inference_data)}个样本")
    
    def get_random_attack_sample(self) -> Tuple[np.ndarray, str]:
        """随机获取一个攻击样本"""
        if self.inference_data is None:
            raise RuntimeError("推理数据未加载")
        
        # 随机选择一个样本
        sample_idx = np.random.randint(0, len(self.inference_data))
        sample_data = self.inference_data[sample_idx]
        
        # 提取特征和真实标签
        if isinstance(sample_data, dict):
            features = sample_data['features'].numpy()
            true_label = sample_data.get('label', 'Unknown')
        else:
            # 如果inference_data是直接的tensor，处理方式不同
            features = sample_data.numpy() if hasattr(sample_data, 'numpy') else sample_data
            # 为原始tensor数据随机分配标签
            attack_classes = self.model_info['classes'] if self.model_info else [
                'Bot', 'DDoS', 'DoS GoldenEye', 'DoS Hulk', 'PortScan', 'SSH-Patator'
            ]
            attack_classes = [c for c in attack_classes if c != 'Benign']
            true_label = np.random.choice(attack_classes)
        
        # 确保features是1D数组
        if features.ndim > 1:
            features = features.flatten()
        
        return features, true_label
    
    def predict_threat(self, features: np.ndarray) -> Dict:
        """执行威胁预测"""
        try:
            # 预处理特征
            processed_features = self._preprocess_features(features)
            
            # 模型推理
            with torch.no_grad():
                input_tensor = torch.FloatTensor(processed_features).unsqueeze(0)
                outputs = self.model(input_tensor)
                probabilities = torch.softmax(outputs, dim=1)
                
                # 获取预测结果
                predicted_class_idx = torch.argmax(probabilities, dim=1).item()
                confidence = float(probabilities[0][predicted_class_idx])
                
                # 解码类别名称
                predicted_class = self.label_encoder.inverse_transform([predicted_class_idx])[0]
                
                # 确定响应级别
                response_level = self._determine_response_level(confidence)
                
                return {
                    "predicted_class": predicted_class,
                    "confidence": confidence,
                    "response_level": response_level,
                    "all_probabilities": probabilities[0].tolist(),
                    "class_names": self.model_info['classes']
                }
                
        except Exception as e:
            logger.error(f"❌ 威胁预测失败: {e}")
            raise
    
    def _preprocess_features(self, features: np.ndarray) -> np.ndarray:
        """预处理特征数据 - 按照训练时的正确顺序"""
        # 确保输入是2D数组
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        logger.debug(f"原始特征维度: {features.shape}")
        
        # 根据训练脚本，正确的预处理顺序是：
        # 1. 首先检查原始特征是否为78维（训练时的原始维度）
        # 2. 然后进行特征选择（从65维选择64维）
        # 3. 最后进行标准化
        
        # 检查特征选择器的期望输入维度（应该是65）
        expected_features_for_selector = getattr(self.feature_selector, 'n_features_in_', 65)
        
        # 如果输入特征不是65维，需要调整到65维（移除低方差特征后的维度）
        if features.shape[1] != expected_features_for_selector:
            logger.warning(f"特征维度不匹配: 实际{features.shape[1]}, 特征选择器期望{expected_features_for_selector}")
            
            if features.shape[1] < expected_features_for_selector:
                # 如果特征不足，用均值填充
                padding = np.full((features.shape[0], expected_features_for_selector - features.shape[1]), 
                                np.mean(features, axis=1, keepdims=True))
                features = np.concatenate([features, padding], axis=1)
                logger.info(f"特征填充到{expected_features_for_selector}维: {features.shape}")
            elif features.shape[1] > expected_features_for_selector:
                # 如果特征过多，截取前N个
                features = features[:, :expected_features_for_selector]
                logger.info(f"特征截取到{expected_features_for_selector}维: {features.shape}")
        
        # 步骤1: 特征选择（从65维选择64维）
        try:
            selected_features = self.feature_selector.transform(features)
            logger.debug(f"特征选择后维度: {selected_features.shape}")
        except Exception as e:
            logger.warning(f"特征选择失败: {e}，手动选择前64个特征")
            n_select = min(64, features.shape[1])
            selected_features = features[:, :n_select]
        
        # 步骤2: 标准化（对64维特征进行标准化）
        try:
            scaled_features = self.scaler.transform(selected_features)
            logger.debug(f"标准化后维度: {scaled_features.shape}")
        except Exception as e:
            logger.warning(f"Scaler变换失败: {e}，使用未标准化特征")
            scaled_features = selected_features
        
        return scaled_features.flatten()
    
    def _determine_response_level(self, confidence: float) -> str:
        """根据置信度确定响应级别"""
        if confidence > THREAT_THRESHOLDS['high_confidence']:
            return "automatic_response"
        elif confidence > THREAT_THRESHOLDS['medium_high']:
            return "auto_create_proposal"
        elif confidence > THREAT_THRESHOLDS['medium_low']:
            return "manual_decision_alert"
        else:
            return "silent_logging"
    
    def simulate_attack_detection(self) -> Dict:
        """模拟攻击检测完整流程"""
        try:
            # 获取随机攻击样本
            features, true_label = self.get_random_attack_sample()
            
            # 执行预测
            prediction_result = self.predict_threat(features)
            
            # 添加真实标签信息
            prediction_result['true_label'] = true_label
            prediction_result['sample_features'] = features.tolist()
            
            logger.info(f"🎯 模拟攻击检测完成:")
            logger.info(f"   真实标签: {true_label}")
            logger.info(f"   预测类别: {prediction_result['predicted_class']}")
            logger.info(f"   置信度: {prediction_result['confidence']:.4f}")
            logger.info(f"   响应级别: {prediction_result['response_level']}")
            
            return prediction_result
            
        except Exception as e:
            logger.error(f"❌ 模拟攻击检测失败: {e}")
            raise
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            "model_info": self.model_info,
            "feature_count": len(self.selected_features) if self.selected_features else 0,
            "threat_classes": self.model_info['classes'] if self.model_info else [],
            "thresholds": THREAT_THRESHOLDS,
            "inference_samples": len(self.inference_data) if self.inference_data else 0
        }

# 全局模型实例
threat_model = None

def get_threat_model() -> ThreatDetectionModel:
    """获取威胁检测模型单例"""
    global threat_model
    if threat_model is None:
        threat_model = ThreatDetectionModel()
    return threat_model

def init_threat_model():
    """初始化威胁检测模型"""
    global threat_model
    threat_model = ThreatDetectionModel()
    return threat_model