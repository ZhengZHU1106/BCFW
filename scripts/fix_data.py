#!/usr/bin/env python3
"""
Data migration script to fix existing proposal reward data and manager contributions
"""

import sqlite3
import json
import os
from datetime import datetime

# 路径配置
DB_PATH = "/Users/zane/Desktop/BCFW/backend/security_platform.db"
CONTRIBUTIONS_FILE = "/Users/zane/Desktop/BCFW/backend/assets/manager_contributions_state.json"

def fix_proposal_rewards():
    """修复提案奖励数据"""
    print("开始修复提案奖励数据...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 查找已批准但没有奖励接收者的提案
        cursor.execute("""
            SELECT id, signed_by FROM proposals 
            WHERE status = 'approved' AND (reward_recipient IS NULL OR reward_recipient = '')
        """)
        
        proposals = cursor.fetchall()
        fixed_count = 0
        
        for proposal_id, signed_by_json in proposals:
            try:
                # 解析签名者列表
                signed_by = json.loads(signed_by_json) if signed_by_json else []
                
                if signed_by:
                    # 使用第一个签名者作为奖励接收者（符合原始逻辑）
                    final_signer = signed_by[0]
                    
                    # 更新奖励接收者
                    cursor.execute("""
                        UPDATE proposals 
                        SET reward_recipient = ? 
                        WHERE id = ?
                    """, (final_signer, proposal_id))
                    
                    print(f"✅ 修复提案 #{proposal_id}: 奖励接收者设为 {final_signer}")
                    fixed_count += 1
                else:
                    print(f"⚠️  提案 #{proposal_id}: 没有签名者数据")
                    
            except json.JSONDecodeError as e:
                print(f"❌ 提案 #{proposal_id}: JSON解析错误 - {e}")
                continue
        
        conn.commit()
        print(f"✅ 成功修复 {fixed_count} 个提案的奖励数据")
        
    except Exception as e:
        print(f"❌ 修复奖励数据失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def calculate_manager_contributions():
    """从历史数据计算管理员贡献"""
    print("开始计算管理员贡献...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 统计每个管理员的签名次数
        cursor.execute("""
            SELECT id, signed_by, created_at FROM proposals 
            WHERE status IN ('approved', 'rejected') AND signed_by IS NOT NULL
        """)
        
        proposals = cursor.fetchall()
        contributions = {}
        
        for proposal_id, signed_by_json, created_at in proposals:
            try:
                signed_by = json.loads(signed_by_json) if signed_by_json else []
                
                for signer in signed_by:
                    if signer not in contributions:
                        contributions[signer] = {
                            "signature_count": 0,
                            "quality_score": 85,  # 默认质量分数
                            "total_rewards": 0,
                            "last_activity": created_at or "2024-01-01T00:00:00Z"
                        }
                    
                    contributions[signer]["signature_count"] += 1
                    # 更新最后活动时间为最新的签名时间
                    if created_at and created_at > contributions[signer]["last_activity"]:
                        contributions[signer]["last_activity"] = created_at
                        
            except json.JSONDecodeError as e:
                print(f"⚠️  提案 #{proposal_id}: JSON解析错误 - {e}")
                continue
        
        # 保存贡献数据
        os.makedirs(os.path.dirname(CONTRIBUTIONS_FILE), exist_ok=True)
        with open(CONTRIBUTIONS_FILE, 'w') as f:
            json.dump(contributions, f, indent=2)
        
        print("✅ 管理员贡献统计:")
        for manager, data in contributions.items():
            print(f"   {manager}: {data['signature_count']} 次签名")
        
        print(f"✅ 贡献数据已保存至: {CONTRIBUTIONS_FILE}")
        
    except Exception as e:
        print(f"❌ 计算贡献失败: {e}")
    finally:
        conn.close()

def main():
    """主函数"""
    print("🔧 开始数据修复...")
    print("=" * 50)
    
    # 检查数据库文件是否存在
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return
    
    # 1. 修复提案奖励数据
    fix_proposal_rewards()
    print()
    
    # 2. 计算管理员贡献
    calculate_manager_contributions()
    print()
    
    print("✅ 数据修复完成!")
    print("=" * 50)

if __name__ == "__main__":
    main()