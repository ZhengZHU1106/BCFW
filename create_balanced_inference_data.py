#!/usr/bin/env python3
"""
创建包含所有7个威胁类型的均衡推理数据集
从inference_data_7class.pt中采样生成平衡的测试数据
"""

import torch
import numpy as np
from collections import defaultdict
import random

def create_balanced_inference_data():
    # 加载原始数据
    print("🔄 加载原始推理数据...")
    data = torch.load('/Users/zane/Desktop/BCFW/backend/assets/data/inference_data_7class.pt')
    
    features = data['features']
    labels = data['labels']
    class_names = data['class_names']
    
    print(f"📊 原始数据总计: {features.shape[0]} 样本")
    print(f"🏷️  类别: {class_names}")
    
    # 统计各类型数量
    unique_labels, counts = torch.unique(labels, return_counts=True)
    print("\n原始数据分布:")
    for label, count in zip(unique_labels, counts):
        print(f"  {class_names[label]}: {count} 样本")
    
    # 按类别分组索引
    class_indices = defaultdict(list)
    for i, label in enumerate(labels):
        class_indices[label.item()].append(i)
    
    # 每个类别采样50个样本（如果不足50个则全部采用）
    samples_per_class = 50
    selected_indices = []
    
    print(f"\n🎯 每个类别采样 {samples_per_class} 个样本:")
    for class_id in range(len(class_names)):
        if class_id in class_indices:
            available_samples = len(class_indices[class_id])
            num_to_sample = min(samples_per_class, available_samples)
            
            # 随机采样
            sampled_indices = random.sample(class_indices[class_id], num_to_sample)
            selected_indices.extend(sampled_indices)
            
            print(f"  {class_names[class_id]}: 采样 {num_to_sample}/{available_samples}")
        else:
            print(f"  {class_names[class_id]}: 无数据")
    
    # 打乱顺序
    random.shuffle(selected_indices)
    
    # 提取选中的样本
    selected_features = features[selected_indices]
    selected_labels = labels[selected_indices]
    
    # 创建新的数据字典
    balanced_data = {
        'features': selected_features,
        'labels': selected_labels,
        'class_names': class_names,
        'metadata': {
            'total_samples': len(selected_indices),
            'feature_count': selected_features.shape[1],
            'data_format': 'raw_features',
            'preprocessing_required': True,
            'description': 'Balanced dataset with all 7 threat types from CIC-IDS2017',
            'samples_per_class': samples_per_class
        }
    }
    
    # 保存新数据
    output_file = '/Users/zane/Desktop/BCFW/backend/assets/data/inference_data_balanced.pt'
    torch.save(balanced_data, output_file)
    
    print(f"\n✅ 已保存均衡数据集: {output_file}")
    print(f"📈 总样本数: {len(selected_indices)}")
    
    # 验证新数据集
    print("\n🔍 新数据集威胁类型分布:")
    unique_new, counts_new = torch.unique(selected_labels, return_counts=True)
    for label, count in zip(unique_new, counts_new):
        print(f"  {class_names[label]}: {count} 样本")
    
    return output_file

def update_config():
    """更新配置文件以使用新的均衡数据集"""
    config_file = '/Users/zane/Desktop/BCFW/backend/config.py'
    
    # 读取配置文件
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换推理数据文件路径
    old_line = '"inference_data_file": DATA_DIR / "inference_data_fixed.pt",'
    new_line = '"inference_data_file": DATA_DIR / "inference_data_balanced.pt",'
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # 写回文件
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ 已更新配置文件: {config_file}")
        return True
    else:
        print(f"⚠️  未找到配置行，请手动更新配置文件")
        return False

if __name__ == "__main__":
    print("🚀 创建包含所有7个威胁类型的均衡推理数据集")
    print("=" * 60)
    
    # 设置随机种子
    random.seed(42)
    torch.manual_seed(42)
    
    # 创建均衡数据集
    output_file = create_balanced_inference_data()
    
    # 更新配置
    if update_config():
        print("\n🎉 完成！请重启系统以使用新的数据集:")
        print("   ./system.sh restart")
    else:
        print("\n⚠️  请手动更新 backend/config.py 中的 inference_data_file 配置")
        print(f"   修改为: DATA_DIR / \"inference_data_balanced.pt\"")