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
try:
    from ..config import AI_MODEL_CONFIG, THREAT_THRESHOLDS
except ImportError:
    # 处理直接运行时的导入问题
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from config import AI_MODEL_CONFIG, THREAT_THRESHOLDS

# 导入新的分层Transformer模型
import sys
sys.path.append(str(AI_MODEL_CONFIG['new_model_package_dir']))
from model_loader import HierarchicalTransformerIDSLoader

logger = logging.getLogger(__name__)

class ThreatDetectionModel:
    """威胁检测模型管理器 - 使用新的分层Transformer模型"""
    
    def __init__(self):
        # 新模型相关属性
        self.transformer_loader = None
        self.new_model_info = None
        
        # 兼容性属性（保持接口一致）
        self.model = None
        self.scaler = None
        self.feature_selector = None
        self.label_encoder = None
        self.model_info = None
        self.selected_features = None
        self.inference_data = None
        
        self._load_new_transformer_model()
    
    def _load_new_transformer_model(self):
        """加载新的分层Transformer模型"""
        try:
            logger.info("🤖 开始加载新的分层Transformer模型...")
            
            # 加载新的Transformer模型
            model_package_path = str(AI_MODEL_CONFIG['new_model_package_dir'])
            self.transformer_loader = HierarchicalTransformerIDSLoader(model_package_path)
            
            # 获取模型信息
            self.new_model_info = self.transformer_loader.get_model_info()
            
            # 为了兼容性，设置旧的接口属性
            self._setup_compatibility_attributes()
            
            # 加载推理数据（可能需要转换维度）
            self._load_inference_data()
            
            logger.info("✅ 新的分层Transformer模型加载完成")
            logger.info(f"   模型: {self.new_model_info['model_name']} v{self.new_model_info['model_version']}")
            logger.info(f"   二分类准确率: {self.new_model_info['performance']['binary_stage']['accuracy']:.4f}")
            logger.info(f"   多分类准确率: {self.new_model_info['performance']['multi_stage']['accuracy']:.4f}")
            
        except Exception as e:
            logger.error(f"❌ 分层Transformer模型加载失败: {e}")
            raise
    
    def _setup_compatibility_attributes(self):
        """设置兼容性属性以保持现有接口"""
        # 构造兼容的model_info
        self.model_info = {
            'classes': (['Benign'] + self.new_model_info['classes']['multi']),  # 7类系统
            'num_classes': 7,
            'model_name': self.new_model_info['model_name'],
            'architecture': 'HierarchicalTransformer'
        }
        
        # 构造兼容的selected_features（使用新模型的77个特征）
        self.selected_features = self.new_model_info['features']['feature_names']
        
        logger.info(f"✅ 设置兼容性接口: {len(self.model_info['classes'])}类系统")
        logger.info(f"   威胁类别: {', '.join(self.model_info['classes'])}")
    
    def _load_pytorch_model(self):
        """加载PyTorch模型并验证权重加载"""
        model_path = AI_MODEL_CONFIG['model_file']
        if not model_path.exists():
            raise FileNotFoundError(f"模型文件不存在: {model_path}")
        
        # 加载模型数据
        model_data = torch.load(model_path, map_location='cpu')
        
        if isinstance(model_data, dict) and 'model_state_dict' in model_data:
            # 重建真实的Ensemble_Hybrid模型
            input_dim = model_data.get('input_dim', 64)
            num_classes = model_data.get('num_classes', 12)
            
            logger.info(f"正在创建模型: input_dim={input_dim}, num_classes={num_classes}")
            self.model = self._create_ensemble_hybrid_model(input_dim, num_classes)
            
            # 计算模型参数数量
            model_params = sum(p.numel() for p in self.model.parameters())
            logger.info(f"模型参数数量: {model_params:,}")
            
            # 加载真实权重
            try:
                self.model.load_state_dict(model_data['model_state_dict'], strict=True)
                logger.info("✅ 成功加载真实模型权重")
                
                # 验证权重加载成功
                self._verify_model_weights()
                
            except Exception as e:
                logger.error(f"❌ 权重加载失败: {e}")
                logger.error("这将导致模型使用随机权重，预测结果不准确！")
                raise RuntimeError(f"模型权重加载失败: {e}")
        else:
            # 直接是模型对象
            self.model = model_data
        
        self.model.eval()  # 设置为评估模式
        
        logger.info(f"✅ PyTorch模型加载成功: {model_path}")
    
    def _create_ensemble_hybrid_model(self, input_dim: int, num_classes: int):
        """创建真实的Ensemble_Hybrid模型架构（完全匹配training.ipynb）"""
        import torch.nn as nn
        import torch.nn.functional as F
        
        class ResidualBlock(nn.Module):
            """残差块 - 改善梯度流动"""
            def __init__(self, dim, dropout_rate=0.2):
                super().__init__()
                self.block = nn.Sequential(
                    nn.Linear(dim, dim),
                    nn.BatchNorm1d(dim),
                    nn.ReLU(),
                    nn.Dropout(dropout_rate),
                    nn.Linear(dim, dim),
                    nn.BatchNorm1d(dim)
                )
                self.dropout = nn.Dropout(dropout_rate)
                
            def forward(self, x):
                residual = x
                out = self.block(x)
                out = out + residual
                return F.relu(self.dropout(out))
        
        class SelfAttentionBranch(nn.Module):
            """自注意力分支"""
            def __init__(self, input_dim, num_classes, dropout_rate=0.2):
                super().__init__()
                self.attention_dim = min(64, input_dim)
                self.query = nn.Linear(input_dim, self.attention_dim)
                self.key = nn.Linear(input_dim, self.attention_dim)
                self.value = nn.Linear(input_dim, self.attention_dim)
                self.output_projection = nn.Linear(self.attention_dim, input_dim)
                self.classifier = nn.Sequential(
                    nn.Linear(input_dim, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(dropout_rate),
                    nn.Linear(128, num_classes)
                )
                self._init_weights()
            
            def _init_weights(self):
                for module in self.modules():
                    if isinstance(module, nn.Linear):
                        nn.init.xavier_uniform_(module.weight)
                        if module.bias is not None:
                            nn.init.constant_(module.bias, 0)
            
            def forward(self, x):
                q = self.query(x)
                k = self.key(x)
                v = self.value(x)
                attention_scores = torch.sum(q * k, dim=1, keepdim=True)
                attention_weights = torch.sigmoid(attention_scores)
                attention_weights = torch.clamp(attention_weights, min=1e-8, max=1.0)
                attended = attention_weights * v
                projected = self.output_projection(attended)
                return self.classifier(projected)
        
        class FeatureInteractionBranch(nn.Module):
            """特徵交互分支"""
            def __init__(self, input_dim, num_classes, dropout_rate=0.2):
                super().__init__()
                self.interaction_dim = min(8, input_dim // 8)
                self.feature_embeddings = nn.Linear(input_dim, self.interaction_dim)
                self.interaction_output_dim = (self.interaction_dim * (self.interaction_dim - 1)) // 2
                if self.interaction_output_dim == 0:
                    self.interaction_output_dim = 1
                self.classifier = nn.Sequential(
                    nn.Linear(input_dim + self.interaction_output_dim, 128),
                    nn.BatchNorm1d(128),
                    nn.ReLU(),
                    nn.Dropout(dropout_rate),
                    nn.Linear(128, num_classes)
                )
                self._init_weights()
            
            def _init_weights(self):
                for module in self.modules():
                    if isinstance(module, nn.Linear):
                        nn.init.xavier_uniform_(module.weight)
                        if module.bias is not None:
                            nn.init.constant_(module.bias, 0)
            
            def forward(self, x):
                embeddings = torch.tanh(self.feature_embeddings(x))
                interactions = []
                if self.interaction_dim > 1:
                    for i in range(self.interaction_dim):
                        for j in range(i + 1, self.interaction_dim):
                            interaction = embeddings[:, i] * embeddings[:, j]
                            interactions.append(interaction.unsqueeze(1))
                
                if interactions:
                    interaction_features = torch.cat(interactions, dim=1)
                else:
                    interaction_features = torch.zeros(x.size(0), 1, device=x.device)
                
                combined_features = torch.cat([x, interaction_features], dim=1)
                return self.classifier(combined_features)
        
        class Ensemble_Hybrid(nn.Module):
            """集成混合網絡 - 完全匹配training.ipynb"""
            def __init__(self, input_dim, num_classes=12, dropout_rate=0.2):
                super().__init__()
                self.input_dim = input_dim
                self.num_classes = num_classes
                
                self.deep_branch = nn.Sequential(
                    nn.Linear(input_dim, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(dropout_rate),
                    nn.Linear(256, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(dropout_rate),
                    nn.Linear(128, num_classes)
                )
                self.wide_branch = nn.Sequential(
                    nn.Linear(input_dim, 512), nn.BatchNorm1d(512), nn.ReLU(), nn.Dropout(dropout_rate),
                    nn.Linear(512, 256), nn.BatchNorm1d(256), nn.ReLU(), nn.Dropout(dropout_rate),
                    nn.Linear(256, num_classes)
                )
                self.res_branch = nn.Sequential(
                    nn.Linear(input_dim, 128), nn.BatchNorm1d(128), nn.ReLU(),
                    ResidualBlock(128, dropout_rate),
                    ResidualBlock(128, dropout_rate),
                    nn.Linear(128, num_classes)
                )
                self.attention_branch = SelfAttentionBranch(input_dim, num_classes, dropout_rate)
                self.interaction_branch = FeatureInteractionBranch(input_dim, num_classes, dropout_rate)
                
                self.weight_net = nn.Sequential(
                    nn.Linear(input_dim, 32), nn.ReLU(), nn.Dropout(dropout_rate),
                    nn.Linear(32, 5), nn.Softmax(dim=1)
                )
                self.final_fusion = nn.Sequential(
                    nn.Linear(num_classes * 5, 128), nn.BatchNorm1d(128), nn.ReLU(), nn.Dropout(dropout_rate),
                    nn.Linear(128, num_classes)
                )
                self.global_weights = nn.Parameter(torch.ones(5) / 5)
                self._init_weights()
            
            def _init_weights(self):
                for module in self.modules():
                    if isinstance(module, nn.Linear):
                        nn.init.xavier_uniform_(module.weight)
                        if module.bias is not None: nn.init.constant_(module.bias, 0)
                    elif isinstance(module, nn.BatchNorm1d):
                        nn.init.constant_(module.weight, 1)
                        nn.init.constant_(module.bias, 0)
            
            def forward(self, x, return_intermediate=False):
                if torch.isnan(x).any() or torch.isinf(x).any():
                    x = torch.nan_to_num(x, nan=0.0, posinf=1.0, neginf=-1.0)
                
                outputs = [
                    self.deep_branch(x), self.wide_branch(x), self.res_branch(x),
                    self.attention_branch(x), self.interaction_branch(x)
                ]
                
                for i, out in enumerate(outputs):
                    if torch.isnan(out).any() or torch.isinf(out).any():
                        outputs[i] = torch.nan_to_num(out, nan=0.0, posinf=1.0, neginf=-1.0)
                
                deep_out, wide_out, res_out, att_out, inter_out = outputs
                
                adaptive_weights = torch.clamp(self.weight_net(x), min=1e-8, max=1.0)
                global_weights = torch.clamp(F.softmax(self.global_weights, dim=0), min=1e-8, max=1.0)
                
                outputs_stack = torch.stack(outputs, dim=2)
                
                weighted_output_adaptive = torch.sum(outputs_stack * adaptive_weights.unsqueeze(1), dim=2)
                weighted_output_global = torch.sum(outputs_stack * global_weights.unsqueeze(0).unsqueeze(0), dim=2)
                weighted_output = 0.6 * weighted_output_adaptive + 0.4 * weighted_output_global
                
                concatenated = torch.cat(outputs, dim=1)
                final_output = self.final_fusion(concatenated)
                
                ensemble_output = 0.7 * final_output + 0.3 * weighted_output
                
                if torch.isnan(ensemble_output).any() or torch.isinf(ensemble_output).any():
                    ensemble_output = torch.nan_to_num(ensemble_output, nan=0.0, posinf=1.0, neginf=-1.0)
                    
                if return_intermediate:
                    return {
                        'ensemble': ensemble_output, 'final_fusion': final_output,
                        'weighted': weighted_output, 'branches': tuple(outputs),
                        'weights': (adaptive_weights, global_weights)
                    }
                return ensemble_output
        
        return Ensemble_Hybrid(input_dim, num_classes)
    
    def _verify_model_weights(self):
        """验证模型权重是否正确加载"""
        try:
            # 创建一个测试输入（使用批大小=2来防止BatchNorm问题）
            test_input = torch.randn(2, 64)  # 模拟64个特征的输入，批大小=2
            
            with torch.no_grad():
                # 执行前向传播
                output = self.model(test_input)
                
                # 检查输出是否合理
                if torch.isnan(output).any() or torch.isinf(output).any():
                    logger.error("模型输出包含NaN或Inf值")
                    return False
                
                # 检查输出维度
                if output.shape != (2, 12):
                    logger.error(f"模型输出维度不正确: {output.shape}, 期望: (2, 12)")
                    return False
                
                # 检查输出是否为全零或全相同值（随机权重的特征）
                if torch.allclose(output, torch.zeros_like(output), atol=1e-6):
                    logger.warning("模型输出全为零，可能权重加载失败")
                    return False
                
                # 检查输出是否具有合理的变化范围
                output_std = torch.std(output)
                if output_std < 1e-6:
                    logger.warning(f"模型输出方差过小: {output_std}, 可能权重加载失败")
                    return False
                
                # 检查两个样本的输出是否不同（避免固定输出）
                if torch.allclose(output[0], output[1], atol=1e-4):
                    logger.warning("模型输出固定不变，可能权重加载失败")
                    return False
                
                logger.info(f"✅ 模型权重验证成功: 输出维度={output.shape}, 方差={output_std:.6f}")
                return True
                
        except Exception as e:
            logger.error(f"模型权重验证失败: {e}")
            return False
    
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
            loaded_data = torch.load(data_path, map_location='cpu')
            
            # 检查数据格式
            if isinstance(loaded_data, dict) and 'features' in loaded_data:
                # 新格式：包含features, labels, class_names
                self.inference_data = loaded_data['features']
                self.inference_labels = loaded_data['labels'] 
                self.inference_class_names = loaded_data['class_names']
                logger.info(f"✅ 新格式推理数据加载成功: {len(self.inference_data)}个样本")
                logger.info(f"   类别: {', '.join(self.inference_class_names)}")
            else:
                # 旧格式：直接是tensor
                self.inference_data = loaded_data
                self.inference_labels = None
                self.inference_class_names = None
                logger.info(f"✅ 旧格式推理数据加载成功: {len(self.inference_data)}个样本")
                
        except Exception as e:
            logger.error(f"❌ 无法加载推理数据: {e}")
            raise RuntimeError(f"无法加载必需的推理数据文件: {data_path}")
    
    
    def _get_true_labels(self) -> List[str]:
        """重建真实标签映射（基于抽样脚本的shuffle逻辑）"""
        # 重建标签列表（与所有分析脚本中使用的逻辑一致）
        labels = []
        labels.extend(['Benign'] * 120)  # 前120个是Benign
        threat_classes = ['Bot', 'DDoS', 'DoS GoldenEye', 'DoS Hulk', 'DoS Slowhttptest', 
                         'DoS slowloris', 'FTP-Patator', 'PortScan', 'Rare_Attack', 'SSH-Patator', 'Web Attack  Brute Force']
        for class_name in threat_classes:  # 其余类别每个10个
            labels.extend([class_name] * 10)
        
        # 使用固定种子应用shuffle（与抽样脚本一致）
        # 注意：这里需要保存随机状态，避免每次调用都重置随机种子
        random_state = np.random.get_state()
        np.random.seed(42)
        shuffled_indices = np.random.permutation(len(labels))
        shuffled_labels = [labels[i] for i in shuffled_indices]
        np.random.set_state(random_state)  # 恢复随机状态
        
        return shuffled_labels
    
    def get_random_attack_sample(self) -> Tuple[np.ndarray, str]:
        """随机获取一个攻击样本 - 使用新的推理数据格式"""
        if self.inference_data is None:
            raise RuntimeError("推理数据未加载")
        
        if self.inference_labels is not None and self.inference_class_names is not None:
            # 新格式数据：使用真实标签
            # 找到所有非Benign的攻击样本
            attack_indices = []
            for i, label_idx in enumerate(self.inference_labels):
                class_name = self.inference_class_names[label_idx]
                if class_name != 'Benign':
                    attack_indices.append(i)
            
            if not attack_indices:
                raise RuntimeError("没有找到攻击样本")
            
            # 随机选择一个攻击样本
            sample_idx = np.random.choice(attack_indices)
            true_label_idx = self.inference_labels[sample_idx].item()
            true_label = self.inference_class_names[true_label_idx]
            
            # 映射到新的7类系统
            label_mapping = {
                'Bot': 'Bot',
                'Brute_Force': 'Brute_Force', 
                'DDoS': 'DDoS',
                'DoS': 'DoS',
                'PortScan': 'PortScan',
                'Web Attack  Brute Force': 'Web_Attack',
                'Web Attack  Sql Injection': 'Web_Attack', 
                'Web Attack  XSS': 'Web_Attack'
            }
            mapped_label = label_mapping.get(true_label, 'Web_Attack')
            
        else:
            # 旧格式数据：使用旧的标签重建逻辑
            true_labels = self._get_true_labels_new_system()
            attack_indices = [i for i, label in enumerate(true_labels) if label != 'Benign']
            
            if not attack_indices:
                raise RuntimeError("没有找到攻击样本")
            
            sample_idx = np.random.choice(attack_indices)
            mapped_label = true_labels[sample_idx]
        
        # 提取特征
        features = self.inference_data[sample_idx].numpy()
        
        # 确保features是1D数组
        if features.ndim > 1:
            features = features.flatten()
        
        return features, mapped_label
    
    def _get_true_labels_new_system(self) -> List[str]:
        """获取真实标签映射，转换到新的7类系统"""
        # 原来的12类标签映射
        old_labels = self._get_true_labels()
        
        # 12类到7类的映射关系
        label_mapping = {
            'Benign': 'Benign',
            'Bot': 'Bot',
            'DDoS': 'DDoS',
            'DoS GoldenEye': 'DoS',
            'DoS Hulk': 'DoS', 
            'DoS Slowhttptest': 'DoS',
            'DoS slowloris': 'DoS',
            'FTP-Patator': 'Brute_Force',
            'SSH-Patator': 'Brute_Force',
            'PortScan': 'PortScan',
            'Web Attack  Brute Force': 'Web_Attack',
            'Rare_Attack': 'Web_Attack'  # 归类为Web攻击
        }
        
        # 转换标签
        new_labels = [label_mapping.get(label, 'Web_Attack') for label in old_labels]
        return new_labels
    
    def predict_threat(self, features: np.ndarray, is_preprocessed: bool = False, strategy: str = "original") -> Dict:
        """执行威胁预测 - 使用分层Transformer模型"""
        try:
            # 检查数据是否已预处理
            if is_preprocessed and features.shape[-1] == 77:
                # 新的77维已预处理数据，直接转换为tensor，跳过模型内部预处理
                processed_features = features
                logger.debug("使用77维已预处理数据，跳过模型预处理")
                
                # 确保是2D数组格式
                if processed_features.ndim == 1:
                    processed_features = processed_features.reshape(1, -1)
                    
                logger.debug(f"输入特征维度: {processed_features.shape}")
                
                # 直接调用模型，跳过预处理步骤
                import torch
                with torch.no_grad():
                    input_tensor = torch.FloatTensor(processed_features).to(self.transformer_loader.device)
                    
                    # 二分类预测
                    binary_logits, binary_uncertainty = self.transformer_loader.binary_model(input_tensor, return_uncertainty=True)
                    binary_probs = torch.nn.functional.softmax(binary_logits, dim=1)
                    binary_preds = torch.argmax(binary_probs, dim=1)
                    
                    # 多分类预测（仅恶意流量）
                    multi_probs = torch.zeros(len(processed_features), len(self.new_model_info['classes']['multi']))
                    multi_uncertainty = torch.zeros(len(processed_features), 1)
                    
                    malicious_mask = binary_preds == 1
                    if malicious_mask.sum() > 0:
                        malicious_data = input_tensor[malicious_mask]
                        multi_logits, multi_unc = self.transformer_loader.multi_model(malicious_data, return_uncertainty=True)
                        multi_probs[malicious_mask] = torch.nn.functional.softmax(multi_logits, dim=1)
                        multi_uncertainty[malicious_mask] = multi_unc
                    
                    prediction_result = {
                        'binary': {
                            'predictions': binary_preds.cpu().numpy(),
                            'probabilities': binary_probs.cpu().numpy(),
                            'uncertainty': binary_uncertainty.cpu().numpy(),
                            'classes': self.new_model_info['classes']['binary']
                        },
                        'multi': {
                            'probabilities': multi_probs.cpu().numpy(),
                            'uncertainty': multi_uncertainty.cpu().numpy(),
                            'classes': self.new_model_info['classes']['multi']
                        },
                        'metadata': {
                            'model_name': self.new_model_info['model_name'],
                            'num_samples': len(processed_features)
                        }
                    }
            else:
                # 旧的64维数据或需要维度适配的数据
                processed_features = self._adapt_feature_dimensions(features)
                logger.debug("应用维度适配和预处理")
                
                # 确保是2D数组格式
                if processed_features.ndim == 1:
                    processed_features = processed_features.reshape(1, -1)
                    
                logger.debug(f"输入特征维度: {processed_features.shape}")
                
                # 使用新的分层模型进行预测（包含内部预处理）
                prediction_result = self.transformer_loader.predict(processed_features)
            
            # 分层预测逻辑
            binary_pred = prediction_result['binary']['predictions'][0]  # 0=Benign, 1=Malicious
            binary_probs = prediction_result['binary']['probabilities'][0]  # [benign_prob, malicious_prob]
            binary_confidence = max(binary_probs)
            
            if binary_pred == 0:  # Benign
                predicted_class = "Benign"
                confidence = binary_probs[0]  # Benign的概率
                all_probs = [binary_probs[0]] + [0.0] * 6  # Benign + 6个攻击类型都是0
            else:  # Malicious
                # 多分类阶段：获取最可能的攻击类型
                multi_probs = prediction_result['multi']['probabilities'][0]  # 6类攻击概率
                max_attack_idx = np.argmax(multi_probs)
                predicted_class = self.new_model_info['classes']['multi'][max_attack_idx]
                confidence = multi_probs[max_attack_idx] * binary_probs[1]  # 组合置信度
                
                # 构造完整概率分布 [Benign=0, Attack1, Attack2, ...]
                all_probs = [0.0] + multi_probs.tolist()
            
            # 确定响应级别
            response_level = self._determine_response_level(confidence)
            
            logger.debug(f"分层预测结果: 二分类={binary_pred}, 最终类别={predicted_class}, 置信度={confidence:.4f}")
            
            return {
                "predicted_class": predicted_class,
                "confidence": float(confidence),  # 转换为Python float
                "response_level": response_level,
                "all_probabilities": [float(p) for p in all_probs],  # 转换为Python float列表
                "class_names": self.model_info['classes'],
                "hierarchical_info": {
                    "binary_prediction": "Malicious" if binary_pred == 1 else "Benign",
                    "binary_confidence": float(binary_confidence),  # 转换为Python float
                    "attack_type": predicted_class if binary_pred == 1 else None
                }
            }
                
        except Exception as e:
            logger.error(f"❌ 威胁预测失败: {e}")
            raise
    
    def _adapt_feature_dimensions(self, features: np.ndarray) -> np.ndarray:
        """将64维特征适配为77维特征"""
        if features.shape[-1] == 77:
            return features  # 已经是77维
        elif features.shape[-1] == 64:
            # 从64维扩展到77维：添加13个零值特征
            if features.ndim == 1:
                padding = np.zeros(13)
                return np.concatenate([features, padding])
            else:
                padding = np.zeros((features.shape[0], 13))
                return np.concatenate([features, padding], axis=1)
        else:
            # 其他维度：截断或填充到77维
            target_dim = 77
            if features.ndim == 1:
                if features.shape[0] > target_dim:
                    return features[:target_dim]
                else:
                    padding = np.zeros(target_dim - features.shape[0])
                    return np.concatenate([features, padding])
            else:
                if features.shape[1] > target_dim:
                    return features[:, :target_dim]
                else:
                    padding = np.zeros((features.shape[0], target_dim - features.shape[1]))
                    return np.concatenate([features, padding], axis=1)
    
    def _preprocess_features(self, features: np.ndarray) -> np.ndarray:
        """预处理特征数据 - 修复维度不匹配问题"""
        # 确保输入是2D数组
        if features.ndim == 1:
            features = features.reshape(1, -1)
        
        logger.debug(f"原始特征维度: {features.shape}")
        
        # 检查特征选择器的期望输入维度
        expected_features_for_selector = getattr(self.feature_selector, 'n_features_in_', 65)
        
        # 关键修复：如果我们的数据只有64维，但特征选择器期望65维输入
        if features.shape[1] == 64 and expected_features_for_selector == 65:
            # 添加一个额外特征（使用均值或零值）
            # 这里使用零值，因为它不会影响特征选择的结果
            extra_feature = np.zeros((features.shape[0], 1))
            features = np.concatenate([features, extra_feature], axis=1)
            logger.info(f"添加一个零值特征以匹配特征选择器: {features.shape}")
        
        # 其他维度不匹配情况的处理
        elif features.shape[1] != expected_features_for_selector:
            logger.warning(f"特征维度不匹配: 实际{features.shape[1]}, 特征选择器期望{expected_features_for_selector}")
            
            if features.shape[1] < expected_features_for_selector:
                # 如果特征不足，用零值填充
                padding = np.zeros((features.shape[0], expected_features_for_selector - features.shape[1]))
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
    
    def _apply_improved_decision_strategy(self, probabilities: torch.Tensor, strategy: str = "original") -> tuple:
        """应用改进的决策策略来提高攻击检测准确率"""
        # 获取所有类别名称
        class_names = self.model_info['classes']
        
        # 按概率排序
        sorted_indices = torch.argsort(probabilities, descending=True)
        
        # 获取Benign类别的索引和概率
        benign_idx = class_names.index('Benign')
        benign_prob = probabilities[benign_idx].item()
        
        if strategy == "original":
            # 策略2：直接使用模型的原始预测结果
            predicted_class_idx = sorted_indices[0].item()
            confidence = probabilities[predicted_class_idx].item()
            predicted_class = self.label_encoder.inverse_transform([predicted_class_idx])[0]
            return predicted_class_idx, confidence, predicted_class
            
        elif strategy == "attack_vs_benign":
            # 策略3：比较攻击类别总概率 vs Benign概率
            # 计算所有攻击类别的概率总和
            attack_prob_sum = 0.0
            for i, class_name in enumerate(class_names):
                if class_name != 'Benign':
                    attack_prob_sum += probabilities[i].item()
            
            if attack_prob_sum > benign_prob:
                # 攻击概率总和更高，选择概率最高的攻击类别
                for idx in sorted_indices:
                    if class_names[idx] != 'Benign':
                        predicted_class_idx = idx.item()
                        confidence = probabilities[predicted_class_idx].item()
                        predicted_class = self.label_encoder.inverse_transform([predicted_class_idx])[0]
                        return predicted_class_idx, confidence, predicted_class
            else:
                # Benign概率更高，选择Benign
                predicted_class_idx = benign_idx
                confidence = benign_prob
                predicted_class = 'Benign'
                return predicted_class_idx, confidence, predicted_class
        
        else:
            # 默认使用原始策略
            predicted_class_idx = sorted_indices[0].item()
            confidence = probabilities[predicted_class_idx].item()
            predicted_class = self.label_encoder.inverse_transform([predicted_class_idx])[0]
            return predicted_class_idx, confidence, predicted_class
    
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
            
            # 执行预测（inference_data中的数据已预处理）
            prediction_result = self.predict_threat(features, is_preprocessed=True)
            
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
        """获取模型信息 - 返回新的7类系统信息"""
        # 处理 inference_data 的长度计算
        inference_samples = 0
        if self.inference_data is not None:
            if hasattr(self.inference_data, 'shape'):
                # 如果是 tensor，使用 shape[0]
                inference_samples = self.inference_data.shape[0]
            elif hasattr(self.inference_data, '__len__'):
                # 如果是列表或其他可迭代对象
                inference_samples = len(self.inference_data)
        
        return {
            "model_info": self.model_info,
            "feature_count": len(self.selected_features) if self.selected_features else 0,
            "threat_classes": self.model_info['classes'] if self.model_info else [],
            "thresholds": THREAT_THRESHOLDS,
            "inference_samples": inference_samples,
            "new_model_details": {
                "architecture": "HierarchicalTransformer",
                "binary_accuracy": self.new_model_info['performance']['binary_stage']['accuracy'],
                "multi_accuracy": self.new_model_info['performance']['multi_stage']['accuracy'],
                "input_features": self.new_model_info['architecture']['input_features'],
                "hierarchical_classes": {
                    "binary": self.new_model_info['classes']['binary'],
                    "multi": self.new_model_info['classes']['multi']
                }
            }
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