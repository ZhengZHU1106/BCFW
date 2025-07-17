"""
区块链智能安防平台 - FastAPI 主应用
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.database.connection import init_database, get_db
from backend.blockchain.web3_manager import init_web3_manager
from backend.ai_module.model_loader import init_threat_model
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
        
        # 初始化AI模型
        logger.info("🤖 初始化AI模型...")
        init_threat_model()
        
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
        history = proposal_service.get_proposal_history(db, limit=20)
        
        return {
            "success": True,
            "data": {
                "pending": pending,
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
        
        result = proposal_service.sign_proposal(db, proposal_id, manager_role)
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

@app.post("/api/proposals/create")
async def create_manual_proposal(detection_id: int, action: str = "block", db: Session = Depends(get_db)):
    """创建手动提案（Operator操作）"""
    try:
        result = proposal_service.create_manual_proposal(db, detection_id, action)
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
async def fund_account(to_address: str, amount: float = 1.0):
    """从Treasury账户向新账户转账"""
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
        treasury_private_key = web3_manager.accounts['treasury']['private_key']
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)