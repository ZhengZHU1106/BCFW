"""
区块链智能安防平台 - FastAPI 主应用
"""
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database.connection import init_database, get_db
from backend.blockchain.web3_manager import init_web3_manager
# AI模型已集成在服务层，无需单独初始化
from backend.app.services import ThreatDetectionService, ProposalService, SystemInfoService, RewardPoolService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("🚀 启动区块链智能安防平台...")
    
    try:
        # 初始化数据库
        logger.info("📊 初始化数据库...")
        init_database()
        
        # 初始化Web3管理器
        logger.info("🔗 初始化Web3连接...")
        init_web3_manager()
        
        # AI模型已集成在服务层，会在首次调用时自动加载
        logger.info("🤖 AI模型已集成在服务层，随时可用")
        
        # 初始化奖金池
        logger.info("💰 初始化奖金池...")
        try:
            from backend.app.services import RewardPoolService
            reward_pool_service = RewardPoolService()
            
            # 检查奖金池当前余额
            pool_info = reward_pool_service.get_reward_pool_info()
            if pool_info["success"] and pool_info["pool_info"]["balance"] < 50.0:
                # 如果奖金池余额低于50 ETH，则充值到100 ETH
                needed_amount = 100.0 - pool_info["pool_info"]["balance"]
                deposit_result = reward_pool_service.deposit_to_reward_pool("treasury", needed_amount)
                if deposit_result["success"]:
                    logger.info(f"✅ 奖金池初始化成功: 充值 {needed_amount} ETH，当前余额 100 ETH")
                else:
                    logger.error(f"❌ 奖金池初始化失败: {deposit_result.get('error')}")
            else:
                logger.info(f"✅ 奖金池已有足够余额: {pool_info['pool_info']['balance']} ETH")
        except Exception as e:
            logger.error(f"❌ 奖金池初始化异常: {e}")
        
        logger.info("✅ 系统初始化完成！")
        
        yield
        
    except Exception as e:
        logger.error(f"❌ 系统初始化失败: {e}")
        raise
    
    # 关闭时清理
    logger.info("🛑 关闭系统...")

app = FastAPI(
    title="区块链智能安防平台",
    description="基于AI威胁检测和区块链多重签名的安防平台演示原型",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化服务
threat_service = ThreatDetectionService()
proposal_service = ProposalService()
system_service = SystemInfoService()
reward_pool_service = RewardPoolService()


@app.get("/")
async def root():
    """根路径，返回API状态信息"""
    return {
        "message": "区块链智能安防平台 API",
        "status": "运行中",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "simulate_attack": "/api/attack/simulate",
            "system_status": "/api/system/status",
            "proposals": "/api/proposals",
            "network_topology": "/api/network/topology",
            "node_details": "/api/network/nodes/{node_id}/details",
            "attack_flow": "/api/network/simulate-attack-flow",
            "health": "/health"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "message": "系统运行正常"}

# API路由

@app.post("/api/attack/simulate")
async def simulate_attack(db: Session = Depends(get_db)):
    """模拟攻击检测"""
    try:
        result = threat_service.simulate_attack(db)
        return {
            "success": True,
            "data": result,
            "message": "攻击模拟执行成功"
        }
    except Exception as e:
        logger.error(f"攻击模拟失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/status")
async def get_system_status(db: Session = Depends(get_db)):
    """获取系统状态"""
    try:
        status = system_service.get_system_status(db)
        return {
            "success": True,
            "data": status,
            "message": "系统状态获取成功"
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/proposals")
async def get_proposals(db: Session = Depends(get_db)):
    """获取提案列表"""
    try:
        pending = proposal_service.get_pending_proposals(db)
        approved = proposal_service.get_approved_proposals(db)
        rejected = proposal_service.get_rejected_proposals(db)
        history = proposal_service.get_proposal_history(db, limit=20)
        
        return {
            "success": True,
            "data": {
                "pending": pending,
                "approved": approved,
                "rejected": rejected,
                "history": history,
                "latest_pending_id": pending[0]["id"] if pending else None
            },
            "message": "提案列表获取成功"
        }
    except Exception as e:
        logger.error(f"获取提案列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/proposals/{proposal_id}/sign")
async def sign_proposal(proposal_id: int, manager_role: str, db: Session = Depends(get_db)):
    """Manager签名提案"""
    try:
        # 验证manager_role
        valid_managers = ["manager_0", "manager_1", "manager_2"]
        if manager_role not in valid_managers:
            raise HTTPException(status_code=400, detail=f"无效的Manager角色: {manager_role}")
        
        # 使用ProposalService处理签名
        result = proposal_service.sign_proposal(db, proposal_id, manager_role)
        
        # 检查ProposalService的返回结果
        if not result.get("success", False):
            raise ValueError(result.get("error", "签名失败"))
        
        return {
            "success": True,
            "data": result,
            "message": "提案签名成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"提案签名失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: int, request: dict, db: Session = Depends(get_db)):
    """Manager拒绝提案"""
    try:
        manager_role = request.get("manager_role")
        if not manager_role:
            raise HTTPException(status_code=400, detail="manager_role is required")
        
        # 验证manager_role
        valid_managers = ["manager_0", "manager_1", "manager_2"]
        if manager_role not in valid_managers:
            raise HTTPException(status_code=400, detail=f"无效的Manager角色: {manager_role}")
        
        # 使用ProposalService处理拒绝
        result = proposal_service.reject_proposal(db, proposal_id, manager_role)
        return {
            "success": True,
            "data": result,
            "message": "提案拒绝成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"提案拒绝失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/proposals/create")
async def create_manual_proposal(
    request: dict,
    db: Session = Depends(get_db)
):
    """创建手动提案（Operator操作）"""
    try:
        detection_id = request.get("detection_id")
        action = request.get("action", "block")
        operator_role = request.get("operator_role")
        
        if not detection_id:
            raise ValueError("detection_id is required")
        
        result = proposal_service.create_manual_proposal(
            db, detection_id, action, operator_role
        )
        return {
            "success": True,
            "data": result,
            "message": "手动提案创建成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建手动提案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/proposals/{proposal_id}/withdraw")
async def withdraw_proposal(proposal_id: int, request: dict, db: Session = Depends(get_db)):
    """撤回提案（Operator操作）"""
    try:
        operator_role = request.get("operator_role")
        
        if not operator_role:
            raise ValueError("operator_role is required")
        
        result = proposal_service.withdraw_proposal(db, proposal_id, operator_role)
        return {
            "success": True,
            "data": result,
            "message": "Proposal withdrawn successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Withdraw proposal failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/detections")
async def get_detection_logs(limit: int = 50, db: Session = Depends(get_db)):
    """获取检测日志"""
    try:
        from backend.database.models import ThreatDetectionLog
        
        logs = db.query(ThreatDetectionLog).order_by(
            ThreatDetectionLog.detected_at.desc()
        ).limit(limit).all()
        
        return {
            "success": True,
            "data": [log.to_dict() for log in logs],
            "message": "检测日志获取成功"
        }
    except Exception as e:
        logger.error(f"获取检测日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs/executions")
async def get_execution_logs(limit: int = 50, db: Session = Depends(get_db)):
    """获取执行日志"""
    try:
        from backend.database.models import ExecutionLog
        
        logs = db.query(ExecutionLog).order_by(
            ExecutionLog.executed_at.desc()
        ).limit(limit).all()
        
        return {
            "success": True,
            "data": [log.to_dict() for log in logs],
            "message": "执行日志获取成功"
        }
    except Exception as e:
        logger.error(f"获取执行日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/accounts/fund")
async def fund_account(request: dict):
    """从Treasury账户向新账户转账"""
    to_address = request.get("to_address")
    amount = request.get("amount", 1.0)
    
    if not to_address:
        raise HTTPException(status_code=400, detail="缺少 to_address 参数")
    try:
        from backend.blockchain.web3_manager import get_web3_manager
        web3_manager = get_web3_manager()
        
        # 验证地址格式
        if not to_address.startswith('0x') or len(to_address) != 42:
            raise HTTPException(status_code=400, detail="无效的以太坊地址")
        
        # 检查Treasury余额
        treasury_info = web3_manager.get_account_info('treasury')
        if treasury_info['balance_eth'] < amount:
            raise HTTPException(status_code=400, detail="Treasury账户余额不足")
        
        # 执行转账
        treasury_account = treasury_info['address']
        treasury_private_key = web3_manager.private_keys['treasury']
        
        # 构建交易
        nonce = web3_manager.w3.eth.get_transaction_count(treasury_account)
        transaction = {
            'nonce': nonce,
            'to': to_address,
            'value': web3_manager.w3.to_wei(amount, 'ether'),
            'gas': 21000,
            'gasPrice': web3_manager.w3.to_wei('1', 'gwei')
        }
        
        # 签名并发送交易
        signed_txn = web3_manager.w3.eth.account.sign_transaction(
            transaction, 
            private_key=treasury_private_key
        )
        tx_hash = web3_manager.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # 等待交易确认
        receipt = web3_manager.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # 获取新余额
        new_balance = web3_manager.w3.eth.get_balance(to_address)
        
        return {
            "success": True,
            "data": {
                "transaction_hash": tx_hash.hex(),
                "from_address": treasury_account,
                "to_address": to_address,
                "amount": amount,
                "new_balance": float(web3_manager.w3.from_wei(new_balance, 'ether'))
            },
            "message": f"成功向 {to_address} 转账 {amount} ETH"
        }
    except Exception as e:
        logger.error(f"账户资金转账失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/test/reward")
async def test_reward_sending(from_role: str = "treasury", to_role: str = "manager_0"):
    """测试奖励发送功能"""
    try:
        web3_manager = system_service.web3_manager
        
        # 检查账户余额
        from_balance = web3_manager.get_account_info(from_role)["balance_eth"]
        to_balance_before = web3_manager.get_account_info(to_role)["balance_eth"]
        
        if from_balance < 0.01:
            raise HTTPException(status_code=400, detail=f"{from_role}账户余额不足")
        
        # 发送测试奖励
        result = web3_manager.send_reward(from_role, to_role, 0.01)
        
        # 检查发送后余额
        to_balance_after = web3_manager.get_account_info(to_role)["balance_eth"]
        
        return {
            "success": True,
            "data": {
                "reward_result": result,
                "balance_changes": {
                    "from_role": from_role,
                    "to_role": to_role,
                    "to_balance_before": to_balance_before,
                    "to_balance_after": to_balance_after,
                    "balance_increase": to_balance_after - to_balance_before
                }
            },
            "message": "奖励发送测试完成"
        }
    except Exception as e:
        logger.error(f"奖励发送测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 奖金池管理API
@app.get("/api/reward-pool/info")
async def get_reward_pool_info():
    """获取奖金池信息"""
    try:
        result = reward_pool_service.get_reward_pool_info()
        return {
            "success": result["success"],
            "pool_info": result.get("pool_info", {}),
            "error": result.get("error"),
            "message": "奖金池信息获取成功" if result["success"] else "奖金池信息获取失败"
        }
    except Exception as e:
        logger.error(f"获取奖金池信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reward-pool/contributions")
async def get_manager_contributions():
    """获取Manager贡献记录"""
    try:
        result = reward_pool_service.get_manager_contributions()
        return {
            "success": result["success"],
            "contributions": result.get("contributions", {}),
            "error": result.get("error"),
            "message": "Manager贡献记录获取成功" if result["success"] else "Manager贡献记录获取失败"
        }
    except Exception as e:
        logger.error(f"获取Manager贡献记录失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reward-pool/deposit")
async def deposit_to_reward_pool(request_data: dict):
    """向奖金池充值"""
    try:
        from_role = request_data.get("from_role", "treasury")
        amount = request_data.get("amount", 0.1)
        
        if amount <= 0:
            raise HTTPException(status_code=400, detail="充值金额必须大于0")
        
        result = reward_pool_service.deposit_to_reward_pool(from_role, amount)
        return {
            "success": result["success"],
            "message": result.get("message", "奖金池充值操作完成"),
            "data": {
                "depositor_role": result.get("depositor_role"),
                "amount": result.get("amount"),
                "new_balance": result.get("new_balance"),
                "tx_hash": result.get("tx_hash")
            },
            "error": result.get("error")
        }
    except Exception as e:
        logger.error(f"奖金池充值失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 手动分配API已移除 - 现在使用自动分配机制

@app.post("/api/test/auto-distribute")
async def test_auto_distribute():
    """测试自动分配机制"""
    try:
        result = reward_pool_service._auto_distribute_on_execution()
        return {
            "success": True,
            "auto_distribution_result": result,
            "message": "自动分配测试完成"
        }
    except Exception as e:
        logger.error(f"自动分配测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 网络可视化API
@app.get("/api/network/topology")
async def get_network_topology():
    """获取网络拓扑信息"""
    try:
        from backend.config import NETWORK_CONFIG, GANACHE_CONFIG
        
        # 获取所有账户信息
        accounts_info = system_service.web3_manager.get_all_accounts_info()
        
        # 转换为网络节点格式
        nodes = []
        for account in accounts_info:
            role = account["role"]
            node_type = "manager" if role.startswith("manager") else \
                       "treasury" if role == "treasury" else "operator"
            
            nodes.append({
                "id": role,
                "address": account["address"],
                "balance": account["balance_eth"],
                "type": node_type,
                "role": NETWORK_CONFIG["node_types"][node_type]["role"],
                "color": NETWORK_CONFIG["node_types"][node_type]["color"],
                "size": NETWORK_CONFIG["node_types"][node_type]["size"],
                "status": "online" if account["balance_eth"] > 0 else "offline"
            })
        
        return {
            "success": True,
            "data": {
                "nodes": nodes,
                "config": NETWORK_CONFIG,
                "total_nodes": len(nodes)
            },
            "message": "网络拓扑获取成功"
        }
    except Exception as e:
        logger.error(f"获取网络拓扑失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/network/nodes/{node_id}/details")
async def get_node_details(node_id: str, db: Session = Depends(get_db)):
    """获取节点详细信息"""
    try:
        # 尝试获取账户基本信息来验证节点是否存在
        # 这支持静态配置的节点和动态创建的节点
        try:
            account_info = system_service.web3_manager.get_account_info(node_id)
        except Exception as e:
            logger.error(f"Node {node_id} not found in blockchain: {e}")
            raise HTTPException(status_code=404, detail=f"节点不存在: {node_id}")
        
        # 获取相关的提案信息（如果是Manager）
        proposals_signed = []
        if node_id.startswith("manager"):
            from backend.database.models import Proposal
            proposals = db.query(Proposal).all()
            for proposal in proposals:
                # 检查signed_by字段中是否包含当前manager的地址
                if (proposal.signed_by and isinstance(proposal.signed_by, list) and 
                    account_info["address"] in [signer.get("address") if isinstance(signer, dict) else signer 
                                              for signer in proposal.signed_by]):
                    proposals_signed.append({
                        "id": proposal.id,
                        "threat_type": proposal.threat_type,
                        "created_at": proposal.created_at.isoformat(),
                        "status": proposal.status
                    })
        
        # 获取威胁检测记录（如果是Operator）
        threat_detections = []
        if node_id.startswith("operator"):
            from backend.database.models import ThreatDetectionLog
            detections = db.query(ThreatDetectionLog).limit(10).all()
            threat_detections = [{
                "id": detection.id,
                "threat_type": detection.threat_type,
                "confidence": detection.confidence,
                "detected_at": detection.detected_at.isoformat()
            } for detection in detections]
        
        return {
            "success": True,
            "data": {
                "node_info": account_info,
                "proposals_signed": proposals_signed,
                "threat_detections": threat_detections,
                "node_type": "manager" if node_id.startswith("manager") else 
                           "treasury" if node_id == "treasury" else "operator"
            },
            "message": f"节点 {node_id} 详细信息获取成功"
        }
    except Exception as e:
        logger.error(f"获取节点详细信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/network/simulate-attack-flow")
async def simulate_attack_flow(request_data: dict, db: Session = Depends(get_db)):
    """模拟攻击流程的可视化"""
    try:
        attack_type = request_data.get("attack_type", "random")
        confidence = request_data.get("confidence", 0.85)
        
        # 执行攻击检测
        attack_result = threat_service.simulate_attack(db)
        
        # 创建攻击流程步骤
        flow_steps = [
            {
                "step": 1,
                "action": "threat_detected",
                "node": "operator_0",
                "description": f"Threat Detected: {attack_result.get('threat_info', {}).get('predicted_class', 'Unknown')}",
                "confidence": attack_result.get('threat_info', {}).get('confidence', 0.0),
                "timestamp": attack_result.get('timestamp')
            }
        ]
        
        # 根据置信度决定后续步骤
        confidence = attack_result.get('threat_info', {}).get('confidence', 0.0)
        if confidence >= 0.80:
            flow_steps.append({
                "step": 2,
                "action": "proposal_created",
                "node": "manager_0",
                "description": "Auto-Created Proposal",
                "timestamp": attack_result.get('timestamp')
            })
            
            flow_steps.append({
                "step": 3,
                "action": "awaiting_signatures",
                "nodes": ["manager_1", "manager_2"],
                "description": "Awaiting Manager Signatures",
                "required_signatures": 2
            })
        
        return {
            "success": True,
            "data": {
                "attack_result": attack_result,
                "flow_steps": flow_steps,
                "total_steps": len(flow_steps)
            },
            "message": "攻击流程模拟成功"
        }
    except Exception as e:
        logger.error(f"攻击流程模拟失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/network/nodes/available-indices")
async def get_available_node_indices():
    """获取可用的节点索引"""
    try:
        from backend.config import GANACHE_CONFIG
        
        # 获取当前已配置的账户索引
        used_indices = set(GANACHE_CONFIG["accounts"].values())
        
        # 返回下一个可用的索引（Ganache通常支持更多账户）
        max_accounts = 20  # Ganache可以支持更多账户
        available_indices = []
        
        for i in range(max_accounts):
            if i not in used_indices:
                available_indices.append(i)
        
        return {
            "success": True,
            "data": {
                "available_indices": available_indices[:10],  # 返回前10个可用索引
                "next_manager_index": min([i for i in available_indices if i not in used_indices]),
                "next_operator_index": min([i for i in available_indices if i not in used_indices]),
                "max_accounts": max_accounts
            },
            "message": "可用索引获取成功"
        }
    except Exception as e:
        logger.error(f"获取可用索引失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/network/nodes/create")
async def create_network_node(request_data: dict):
    """创建新的网络节点 - DEPRECATED

    注意：此API已废弃，因为DevLeChain使用预定义的keystore账户，不支持动态创建节点。
    所有账户在系统启动时从keystore加载，无法在运行时创建新账户。
    """
    raise HTTPException(
        status_code=501,
        detail="Dynamic node creation is not supported with DevLeChain keystore mode. "
               "All accounts are pre-defined in the blockchain keystore."
    )

    # 以下代码已废弃，仅保留用于参考
    try:
        from backend.config import GANACHE_CONFIG
        from eth_account import Account

        node_type = request_data.get("type")  # "manager" or "operator"
        node_name = request_data.get("name", "")
        
        if node_type not in ["manager", "operator"]:
            raise HTTPException(status_code=400, detail="节点类型必须是 'manager' 或 'operator'")
        
        # 启用HD钱包功能
        Account.enable_unaudited_hdwallet_features()
        
        # 获取下一个可用的索引
        used_indices = set(GANACHE_CONFIG["accounts"].values())
        next_index = None
        for i in range(20):  # 搜索前20个索引
            if i not in used_indices:
                next_index = i
                break
        
        if next_index is None:
            raise HTTPException(status_code=400, detail="没有可用的账户索引")
        
        # 生成新账户
        mnemonic = GANACHE_CONFIG['mnemonic']
        new_account = Account.from_mnemonic(
            mnemonic, 
            account_path=f"m/44'/60'/0'/0/{next_index}"
        )
        
        # 创建节点ID
        existing_nodes = [k for k in GANACHE_CONFIG["accounts"].keys() if k.startswith(node_type)]
        node_count = len(existing_nodes)
        node_id = f"{node_type}_{node_count}"
        
        # 如果提供了自定义名称，使用自定义名称
        if node_name:
            node_id = f"{node_type}_{node_name}"
        
        # 从Treasury转账激活新账户
        web3_manager = system_service.web3_manager
        treasury_info = web3_manager.get_account_info('treasury')
        
        if treasury_info['balance_eth'] < 100:
            raise HTTPException(status_code=400, detail="Treasury余额不足，无法激活新账户")
        
        # 构建转账交易
        nonce = web3_manager.w3.eth.get_transaction_count(treasury_info['address'])
        transaction = {
            'nonce': nonce,
            'to': new_account.address,
            'value': web3_manager.w3.to_wei(100, 'ether'),  # 转账100 ETH
            'gas': 21000,
            'gasPrice': web3_manager.w3.to_wei('1', 'gwei')
        }
        
        # 签名并发送交易
        treasury_private_key = web3_manager.private_keys['treasury']
        signed_txn = web3_manager.w3.eth.account.sign_transaction(
            transaction, 
            private_key=treasury_private_key
        )
        tx_hash = web3_manager.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # 等待交易确认
        receipt = web3_manager.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # 更新配置（运行时添加，重启后需要手动持久化）
        web3_manager.accounts[node_id] = new_account.address
        web3_manager.private_keys[node_id] = new_account.key.hex()
        
        # 获取新账户余额确认
        new_balance = web3_manager.w3.eth.get_balance(new_account.address)
        
        return {
            "success": True,
            "data": {
                "node_id": node_id,
                "node_type": node_type,
                "address": new_account.address,
                "private_key": new_account.key.hex(),  # 注意：生产环境中不应返回私钥
                "balance": float(web3_manager.w3.from_wei(new_balance, 'ether')),
                "transaction_hash": tx_hash.hex(),
                "account_index": next_index
            },
            "message": f"节点 {node_id} 创建成功"
        }
    except Exception as e:
        logger.error(f"节点创建失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/network/nodes/{node_id}/remove")
async def remove_network_node(node_id: str):
    """删除网络节点（将余额转回Treasury并停用）"""
    try:
        from backend.config import GANACHE_CONFIG
        
        # 检查节点是否存在
        web3_manager = system_service.web3_manager
        if node_id not in web3_manager.accounts:
            raise HTTPException(status_code=404, detail=f"节点 {node_id} 不存在")
        
        # 检查是否为核心节点（不可删除）
        core_nodes = ["treasury", "manager_0", "manager_1", "manager_2"]
        if node_id in core_nodes:
            raise HTTPException(status_code=400, detail=f"核心节点 {node_id} 不可删除")
        
        # 获取节点信息
        node_info = web3_manager.get_account_info(node_id)
        treasury_info = web3_manager.get_account_info('treasury')
        
        transfer_tx_hash = None
        
        # 如果节点有余额，转回Treasury
        if node_info['balance_eth'] > 0.01:  # 保留少量gas费
            # 计算转账金额（保留0.01 ETH作为gas费）
            transfer_amount = node_info['balance_eth'] - 0.01
            
            # 构建转账交易
            nonce = web3_manager.w3.eth.get_transaction_count(node_info['address'])
            transaction = {
                'nonce': nonce,
                'to': treasury_info['address'],
                'value': web3_manager.w3.to_wei(transfer_amount, 'ether'),
                'gas': 21000,
                'gasPrice': web3_manager.w3.to_wei('1', 'gwei')
            }
            
            # 签名并发送交易
            node_private_key = web3_manager.private_keys[node_id]
            signed_txn = web3_manager.w3.eth.account.sign_transaction(
                transaction, 
                private_key=node_private_key
            )
            transfer_tx_hash = web3_manager.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # 等待交易确认
            receipt = web3_manager.w3.eth.wait_for_transaction_receipt(transfer_tx_hash)
            transfer_tx_hash = transfer_tx_hash.hex()
        
        # 从运行时配置中移除节点
        removed_address = web3_manager.accounts.pop(node_id, None)
        removed_key = web3_manager.private_keys.pop(node_id, None)
        
        # 获取最终余额
        final_balance = web3_manager.w3.eth.get_balance(removed_address or node_info['address'])
        
        return {
            "success": True,
            "data": {
                "node_id": node_id,
                "removed_address": removed_address,
                "transfer_amount": transfer_amount if 'transfer_amount' in locals() else 0,
                "transfer_tx_hash": transfer_tx_hash,
                "final_balance": float(web3_manager.w3.from_wei(final_balance, 'ether')),
                "treasury_address": treasury_info['address']
            },
            "message": f"节点 {node_id} 已停用，余额已转回Treasury"
        }
    except Exception as e:
        logger.error(f"节点删除失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)