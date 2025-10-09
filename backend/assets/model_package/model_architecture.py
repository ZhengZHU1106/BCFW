"""
Hierarchical Transformer-Enhanced Network Intrusion Detection System
Model Architecture Definition
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class MultiScaleAttention(nn.Module):
    """多尺度注意力机制：结合类别、时间、空间注意力"""
    def __init__(self, input_dim, num_classes):
        super().__init__()
        self.num_classes = num_classes
        self.input_dim = input_dim
        
        # 类别特定注意力
        self.class_attention = nn.ModuleList([
            nn.Sequential(
                nn.Linear(input_dim, input_dim // 4),
                nn.ReLU(),
                nn.Dropout(0.1),
                nn.Linear(input_dim // 4, input_dim),
                nn.Sigmoid()
            ) for _ in range(num_classes)
        ])
        
        # 时间序列注意力
        self.temporal_attention = nn.MultiheadAttention(
            input_dim, num_heads=4, dropout=0.1, batch_first=True
        )
        
        # 空间特征注意力
        self.spatial_attention = nn.Sequential(
            nn.Linear(input_dim, input_dim // 8),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(input_dim // 8, input_dim),
            nn.Sigmoid()
        )
        
        # 注意力融合权重
        self.fusion_weights = nn.Parameter(torch.ones(3) / 3)
    
    def forward(self, x):
        batch_size = x.size(0)
        
        # 1. 类别特定注意力
        class_features = []
        for i in range(self.num_classes):
            attention_weights = self.class_attention[i](x)
            attended_features = attention_weights * x
            class_features.append(attended_features)
        class_attended = torch.stack(class_features, dim=1)
        
        # 2. 时间序列注意力
        x_temporal = x.unsqueeze(1)
        temporal_attended, _ = self.temporal_attention(x_temporal, x_temporal, x_temporal)
        temporal_attended = temporal_attended.squeeze(1)
        
        # 3. 空间特征注意力
        spatial_weights = self.spatial_attention(x)
        spatial_attended = spatial_weights * x
        
        # 4. 多尺度融合
        weights = F.softmax(self.fusion_weights, dim=0)
        class_attended_mean = class_attended.mean(dim=1)
        
        fused_features = (weights[0] * class_attended_mean + 
                         weights[1] * temporal_attended + 
                         weights[2] * spatial_attended)
        
        return class_attended, fused_features

class TransformerEnhancedEnsembleModel(nn.Module):
    """Transformer增强的集成模型：支持层次化检测架构"""
    def __init__(self, input_dim, num_classes, dropout_rate=0.3, use_pretrained=False):
        super().__init__()
        self.num_classes = num_classes
        self.use_pretrained = use_pretrained
        
        # 共享编码器
        self.shared_encoder = nn.Sequential(
            nn.Linear(input_dim, 512),
            nn.BatchNorm1d(512),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(dropout_rate / 2)
        )
        
        # Transformer编码器
        self.feature_dim = 256
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.feature_dim,
            nhead=8,
            dim_feedforward=512,
            dropout=0.1,
            batch_first=True,
            activation='gelu'
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=2)
        
        # 位置编码
        self.pos_encoding = nn.Parameter(torch.randn(1, 1, self.feature_dim) * 0.1)
        
        # 多尺度注意力机制
        self.multi_scale_attention = MultiScaleAttention(256, num_classes)
        
        # 类别特定分类头
        self.class_specific_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(256, 128),
                nn.BatchNorm1d(128),
                nn.ReLU(),
                nn.Dropout(dropout_rate),
                nn.Linear(128, 64),
                nn.ReLU(),
                nn.Linear(64, 1)
            ) for _ in range(num_classes)
        ])
        
        # 全局分类器
        self.global_classifier = nn.Sequential(
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(128, num_classes)
        )
        
        # 自适应融合网络
        self.fusion_network = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 2),
            nn.Softmax(dim=-1)
        )
        
        # 特征提取器
        self.feature_extractor = nn.Identity()
        
        # 不确定性估计头
        self.uncertainty_head = nn.Sequential(
            nn.Linear(256, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid()
        )
        
    def forward(self, x, return_features=False, return_uncertainty=False):
        # 共享特征提取
        shared_features = self.shared_encoder(x)
        
        if return_features:
            return shared_features
        
        # Transformer处理
        transformer_input = shared_features.unsqueeze(1) + self.pos_encoding
        transformer_features = self.transformer_encoder(transformer_input)
        transformer_features = transformer_features.squeeze(1)
        
        # 残差连接 + Layer Normalization
        enhanced_features = F.layer_norm(
            shared_features + transformer_features, 
            normalized_shape=[self.feature_dim]
        )
        
        # 多尺度注意力处理
        class_attended_features, fused_attention_features = self.multi_scale_attention(enhanced_features)
        
        # 类别特定输出
        class_specific_outputs = []
        for i in range(self.num_classes):
            output = self.class_specific_heads[i](class_attended_features[:, i, :])
            class_specific_outputs.append(output)
        class_specific_logits = torch.cat(class_specific_outputs, dim=1)
        
        # 全局输出
        global_logits = self.global_classifier(fused_attention_features)
        
        # 自适应融合
        fusion_weights = self.fusion_network(enhanced_features)
        final_logits = (fusion_weights[:, 0:1] * class_specific_logits + 
                       fusion_weights[:, 1:2] * global_logits)
        
        # 不确定性估计
        if return_uncertainty:
            uncertainty = self.uncertainty_head(enhanced_features)
            return final_logits, uncertainty
        
        return final_logits
    
    def load_pretrained_encoder(self, pretrained_model_path):
        """加载预训练的编码器权重"""
        import os
        if os.path.exists(pretrained_model_path):
            pretrained_state = torch.load(pretrained_model_path, map_location='cpu')
            encoder_state = {}
            for key, value in pretrained_state.items():
                if key.startswith('shared_encoder'):
                    encoder_state[key] = value
            
            self.load_state_dict(encoder_state, strict=False)
