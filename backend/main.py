"""
区块链智能安防平台 - FastAPI 主应用
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .database.connection import init_database, get_db
from .blockchain.web3_manager import init_web3_manager
from .ai_module.model_loader import init_threat_model
from .app.services import ThreatDetectionService, ProposalService, SystemInfoService

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
        from .database.models import ThreatDetectionLog
        
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
        from .database.models import ExecutionLog
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)