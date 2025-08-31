"""
业务逻辑服务层
"""

import random
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
import logging
import pandas as pd
import numpy as np
import torch
import os
import sys

from ..database.models import Proposal, ExecutionLog, ThreatDetectionLog
from ..blockchain.web3_manager import get_web3_manager
from ..config import AI_MODEL_CONFIG, THREAT_THRESHOLDS, INCENTIVE_CONFIG

# 添加 model_package 到 Python 路径，确保 predictor.py 能正确导入 model_architecture
model_package_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'assets', 'model_package')
if model_package_dir not in sys.path:
    sys.path.insert(0, model_package_dir)
from predictor import HierarchicalPredictor

logger = logging.getLogger(__name__)

# 全局模型实例
_threat_model = None

def get_threat_model():
    """获取威胁检测模型单例 - 直接使用 HierarchicalPredictor"""
    global _threat_model
    if _threat_model is None:
        # 使用config中定义的路径
        model_package_path = str(AI_MODEL_CONFIG['model_package_dir'])
        
        logger.info(f"正在从以下路径加载模型包: {model_package_path}")
        _threat_model = HierarchicalPredictor(model_package_path, device='cpu', debug=False)
        
        # 为模型加载推理数据
        _load_inference_data(_threat_model)
        # 为向后兼容性添加方法
        _add_compatibility_methods(_threat_model)
    return _threat_model

def _load_inference_data(model):
    """为模型加载推理测试数据"""
    try:
        if AI_MODEL_CONFIG.get('use_original_data', False):
            # 使用原始parquet数据
            _load_original_data(model)
        else:
            # 使用预处理数据 - 现在有正确的quantile阈值处理，效果完美
            _load_preprocessed_data(model)
            
    except Exception as e:
        logger.error(f"❌ 无法加载推理数据: {e}")
        model.inference_data = None
        model.inference_labels = None
        model.inference_class_names = None

def _load_preprocessed_data(model):
    """加载预处理的inference_data.pt文件"""
    data_path = AI_MODEL_CONFIG['inference_data_file']
    loaded_data = torch.load(data_path, map_location='cpu')
    
    if isinstance(loaded_data, dict) and 'features' in loaded_data:
        model.inference_data = loaded_data['features']
        model.inference_labels = loaded_data['labels'] 
        model.inference_class_names = loaded_data['class_names']
        logger.info(f"✅ 预处理推理数据加载成功: {len(model.inference_data)}个样本")
    else:
        # 兼容旧格式
        model.inference_data = loaded_data
        model.inference_labels = None
        model.inference_class_names = None
        logger.info(f"✅ 旧格式推理数据加载成功: {len(model.inference_data)}个样本")


def _load_original_data(model):
    """加载原始parquet数据文件"""
    import pandas as pd
    from pathlib import Path
    
    original_data_dir = Path(AI_MODEL_CONFIG['original_data_dir'])
    
    # 定义文件到类别的映射
    file_mappings = {
        'Benign-Monday-no-metadata.parquet': 'Benign',
        'Botnet-Friday-no-metadata.parquet': 'Bot',
        'Bruteforce-Tuesday-no-metadata.parquet': 'Brute_Force',
        'DDoS-Friday-no-metadata.parquet': 'DDoS',
        'DoS-Wednesday-no-metadata.parquet': 'DoS',
        'Portscan-Friday-no-metadata.parquet': 'PortScan',
        'WebAttacks-Thursday-no-metadata.parquet': 'Web_Attack'
    }
    
    all_features = []
    all_labels = []
    class_names = ['Benign', 'Bot', 'Brute_Force', 'DDoS', 'DoS', 'PortScan', 'Web_Attack']
    
    # 每个类别采样一定数量的样本 (避免内存问题)
    samples_per_class = 10000
    
    for filename, class_name in file_mappings.items():
        file_path = original_data_dir / filename
        if file_path.exists():
            df = pd.read_parquet(file_path)
            
            # 随机采样
            if len(df) > samples_per_class:
                df = df.sample(n=samples_per_class, random_state=42)
            
            # 确保特征顺序与训练时一致
            if hasattr(model, 'feature_names'):
                # 检查特征是否匹配
                available_features = set(df.columns)
                required_features = set(model.feature_names)
                missing_features = required_features - available_features
                
                if missing_features:
                    logger.warning(f"缺少特征 {missing_features}，用0填充")
                    for feature in missing_features:
                        df[feature] = 0
                
                # 重新排序特征
                df = df[model.feature_names]
            
            # 转换为tensor
            features_tensor = torch.from_numpy(df.values).float()
            class_label = class_names.index(class_name)
            labels_tensor = torch.full((len(df),), class_label, dtype=torch.long)
            
            all_features.append(features_tensor)
            all_labels.append(labels_tensor)
            
            logger.info(f"✅ 加载 {class_name}: {len(df)} 个样本")
    
    if all_features:
        model.inference_data = torch.cat(all_features, dim=0)
        model.inference_labels = torch.cat(all_labels, dim=0)
        model.inference_class_names = class_names
        total_samples = len(model.inference_data)
        logger.info(f"✅ 原始数据加载完成: 总共 {total_samples} 个样本")
    else:
        raise Exception("没有找到任何原始数据文件")

def _add_compatibility_methods(model):
    """为 HierarchicalPredictor 添加兼容方法以适应旧的Service层调用"""
    
    def simulate_attack_detection():
        """模拟攻击检测 - 兼容旧接口"""
        if not hasattr(model, 'inference_data') or model.inference_data is None:
            return _generate_random_prediction()
        
        # 随机选择一个样本
        sample_idx = np.random.randint(0, len(model.inference_data))
        sample_tensor = model.inference_data[sample_idx:sample_idx+1]
        
        # 转换为 DataFrame (使用模型内部加载的特征名)
        sample_df = pd.DataFrame(sample_tensor.numpy(), columns=model.feature_names)
        
        # 使用新的预测器进行预测（暂时使用原预处理，等待新数据）
        results = model.predict(sample_df)
        result = results[0]
        
        # 获取真实标签
        true_label = "Unknown" # 默认值
        if hasattr(model, 'inference_labels') and model.inference_labels is not None and hasattr(model, 'inference_class_names') and model.inference_class_names is not None:
            true_label_idx = int(model.inference_labels[sample_idx])
            if true_label_idx < len(model.inference_class_names):
                true_label = model.inference_class_names[true_label_idx]
        
        # 转换为兼容格式
        predicted_class = result['multi_prediction'] if result['multi_prediction'] else result['binary_prediction']
        confidence = result['confidence']
        
        # 确定响应级别
        if predicted_class == 'Benign':
            # Benign流量始终是日志记录级别，不需要响应
            response_level = "log_only"
        elif confidence >= THREAT_THRESHOLDS["high_confidence"]:
            response_level = "automatic_response"
        elif confidence >= THREAT_THRESHOLDS["medium_high"]:
            response_level = "auto_create_proposal"
        elif confidence >= THREAT_THRESHOLDS["medium_low"]:
            response_level = "manual_decision_alert"
        else:
            response_level = "log_only"

        return {
            'sample_index': sample_idx,
            'predicted_class': predicted_class,
            'confidence': confidence,
            'true_label': true_label,
            'response_level': response_level
        }
    
    def get_model_info():
        """获取模型信息 - 兼容旧接口"""
        model_info = model.model_info.copy()
        
        inference_samples = 0
        if hasattr(model, 'inference_data') and model.inference_data is not None:
            inference_samples = len(model.inference_data)
        
        model_info.update({
            'inference_samples': inference_samples,
            'classes': ['Benign'] + model.multi_classes,
            'num_classes': len(['Benign'] + model.multi_classes),
            'architecture': 'HierarchicalPredictor',
            'device': str(model.device)
        })
        
        return model_info
    
    def _generate_random_prediction():
        classes = ['Benign', 'Bot', 'Brute_Force', 'DDoS', 'DoS', 'PortScan', 'Web_Attack']
        predicted_class = np.random.choice(classes)
        confidence = np.random.uniform(0.5, 0.95)
        
        # ... (response_level logic) ...

        return {
            'predicted_class': predicted_class,
            'confidence': confidence,
            'true_label': 'Unknown',
            'response_level': 'log_only'
        }
    
    # 将方法绑定到模型实例
    model.simulate_attack_detection = simulate_attack_detection
    model.get_model_info = get_model_info

class ThreatDetectionService:
    """威胁检测服务"""
    
    def __init__(self):
        self.threat_model = get_threat_model()
        self.web3_manager = get_web3_manager()
    
    def simulate_attack(self, db: Session) -> Dict:
        """模拟攻击检测"""
        try:
            detection_result = self.threat_model.simulate_attack_detection()
            
            source_ip = self._generate_random_ip()
            target_ip = self._generate_random_ip()
            
            detection_log = ThreatDetectionLog(
                threat_type=detection_result['predicted_class'],
                confidence=detection_result['confidence'],
                true_label=detection_result['true_label'],
                response_level=detection_result['response_level'],
                source_ip=source_ip,
                target_ip=target_ip,
                detection_data=detection_result
            )
            
            response_action = self._handle_detection_response(
                db, detection_result, detection_log, target_ip
            )
            
            detection_log.action_taken = response_action['action_taken']
            detection_log.proposal_id = response_action.get('proposal_id')
            detection_log.execution_log_id = response_action.get('execution_log_id')
            
            db.add(detection_log)
            db.commit()
            
            result = {
                "detection_id": detection_log.id,
                "threat_info": {
                    "predicted_class": detection_result['predicted_class'],
                    "confidence": detection_result['confidence'],
                    "true_label": detection_result['true_label'],
                    "response_level": detection_result['response_level']
                },
                "network_info": {
                    "source_ip": source_ip,
                    "target_ip": target_ip
                },
                "response_action": response_action,
                "timestamp": detection_log.detected_at.isoformat()
            }
            
            logger.info(f"🎯 攻击模拟完成: 真实标签: {detection_result['true_label']} "
                       f"(置信度: {detection_result['confidence']:.4f}, 预测: {detection_result['predicted_class']})")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 攻击模拟失败: {e}", exc_info=True)
            db.rollback()
            raise
    
    def _handle_detection_response(self, db: Session, detection_result: Dict, 
                                 detection_log: ThreatDetectionLog, target_ip: str) -> Dict:
        # ... (rest of the class is unchanged) ...
        response_level = detection_result['response_level']
        
        if response_level == "automatic_response":
            execution_log = self._execute_automatic_response(db, detection_result, target_ip)
            return {"action_taken": "automatic_block", "execution_log_id": execution_log.id, "description": "高置信度威胁，自动执行封锁"}
        elif response_level == "auto_create_proposal":
            proposal = self._create_auto_proposal(db, detection_result, target_ip)
            return {"action_taken": "auto_proposal_created", "proposal_id": proposal.id, "description": "中高置信度威胁，已自动创建提案等待Manager审批"}
        elif response_level == "manual_decision_alert":
            return {"action_taken": "manual_alert", "description": "中低置信度威胁，已生成告警等待Operator手动决策"}
        else:
            return {"action_taken": "silent_logging", "description": "低置信度事件，已静默记录"}

    def _execute_automatic_response(self, db: Session, detection_result: Dict, target_ip: str) -> ExecutionLog:
        execution_log = ExecutionLog(
            action_type="auto_block",
            execution_type="auto",
            target_ip=target_ip,
            threat_type=detection_result['predicted_class'],
            confidence=detection_result['confidence'],
            execution_status="success",
            execution_details=f"自动封锁IP {target_ip}，威胁类型: {detection_result['predicted_class']}",
            execution_data=detection_result
        )
        db.add(execution_log)
        db.flush()
        logger.info(f"🚫 自动执行封锁: {target_ip}")
        return execution_log

    def _create_auto_proposal(self, db: Session, detection_result: Dict, target_ip: str) -> Proposal:
        proposal = Proposal(
            threat_type=detection_result['predicted_class'],
            confidence=detection_result['confidence'],
            true_label=detection_result['true_label'],
            proposal_type="auto",
            target_ip=target_ip,
            action_type="block",
            detection_data=detection_result
        )
        db.add(proposal)
        db.flush()
        multisig_result = self.web3_manager.create_multisig_proposal(
            target_role="manager_0",
            amount_eth=INCENTIVE_CONFIG['proposal_reward'],
            data="0x",
            creator_role="system"
        )
        if multisig_result["success"]:
            proposal.contract_proposal_id = multisig_result["proposal_id"]
            proposal.contract_address = multisig_result["contract_address"]
            logger.info(f"📝 自动创建MultiSig提案: DB-ID-{proposal.id}, Contract-ID-{multisig_result['proposal_id']}")
        else:
            logger.error(f"❌ MultiSig提案创建失败: {multisig_result['error']}")
            proposal.contract_proposal_id = None
        return proposal

    def _generate_random_ip(self) -> str:
        return f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"

# ... (rest of the file is unchanged) ...
class ProposalService:
    def __init__(self):
        self.web3_manager = get_web3_manager()
    
    def get_pending_proposals(self, db: Session) -> List[Dict]:
        """获取待处理的提案列表"""
        proposals = db.query(Proposal).filter(Proposal.status == "pending").all()
        return [proposal.to_dict() for proposal in proposals]
    
    def get_approved_proposals(self, db: Session) -> List[Dict]:
        """获取已批准的提案列表"""
        proposals = db.query(Proposal).filter(Proposal.status == "approved").all()
        return [proposal.to_dict() for proposal in proposals]
    
    def get_rejected_proposals(self, db: Session) -> List[Dict]:
        """获取已拒绝的提案列表"""
        proposals = db.query(Proposal).filter(Proposal.status == "rejected").all()
        return [proposal.to_dict() for proposal in proposals]
    
    def get_proposal_history(self, db: Session, limit: int = 50) -> List[Dict]:
        """获取历史提案记录"""
        proposals = db.query(Proposal).order_by(Proposal.created_at.desc()).limit(limit).all()
        return [proposal.to_dict() for proposal in proposals]
    
    def sign_proposal(self, db: Session, proposal_id: int, signer_role: str) -> Dict:
        """签名提案"""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        
        # 模拟签名实现 - 正确处理JSON字段
        from sqlalchemy.orm.attributes import flag_modified
        
        signed_by_list = proposal.signed_by if proposal.signed_by else []
        
        if signer_role not in signed_by_list:
            signed_by_list.append(signer_role)
            proposal.signed_by = signed_by_list
            flag_modified(proposal, 'signed_by')  # 告诉SQLAlchemy JSON字段已修改
            proposal.signatures_count = len(signed_by_list)
            
            # 如果达到阈值，自动批准
            if proposal.signatures_count >= proposal.signatures_required:
                proposal.status = "approved"
                proposal.approved_at = datetime.utcnow()
        
        db.commit()
        return {"success": True, "message": "Proposal signed successfully"}
    
    def reject_proposal(self, db: Session, proposal_id: int, manager_role: str) -> Dict:
        """拒绝提案"""
        proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
        if not proposal:
            return {"success": False, "error": "Proposal not found"}
        
        if proposal.status != "pending":
            return {"success": False, "error": "Proposal is not in pending status"}
        
        # 1-vote veto - 任何Manager都可以立即拒绝提案
        proposal.status = "rejected"
        proposal.rejected_at = datetime.utcnow()
        proposal.rejected_by = manager_role
        
        db.commit()
        return {"success": True, "message": "Proposal rejected successfully"}

class SystemInfoService:
    def __init__(self):
        self.web3_manager = get_web3_manager()
        self.threat_model = get_threat_model()
    
    def get_system_status(self, db: Session) -> Dict:
        """获取系统状态信息"""
        try:
            # 检查各个组件状态
            ganache_connected = self.web3_manager.is_connected()
            database_connected = True  # 如果到这里说明数据库连接正常
            
            # 检查AI模型是否加载
            ai_model_loaded = False
            try:
                from ..app.services import get_threat_model
                model = get_threat_model()
                ai_model_loaded = model is not None
            except:
                ai_model_loaded = False
            
            # 获取账户余额
            accounts_info = self.web3_manager.get_all_accounts_info()
            account_balances = {acc['role']: acc['balance_eth'] for acc in accounts_info}
            
            return {
                "status": "operational" if ganache_connected and database_connected else "degraded",
                "ganache_connected": ganache_connected,
                "database_connected": database_connected, 
                "ai_model_loaded": ai_model_loaded,
                "account_balances": account_balances,
                "blockchain": {"status": "connected" if ganache_connected else "disconnected"},
                "accounts": accounts_info,
                "network": self.web3_manager.get_network_info()
            }
        except Exception as e:
            logger.error(f"获取系统状态失败: {e}")
            return {
                "status": "error",
                "ganache_connected": False,
                "database_connected": False,
                "ai_model_loaded": False,
                "error": str(e)
            }
class RewardPoolService:
    def __init__(self):
        self.web3_manager = get_web3_manager()
    
    def get_reward_pool_info(self) -> Dict:
        """获取奖金池信息"""
        return {"success": True, "pool_info": {"balance": 85.1, "status": "Active"}}
