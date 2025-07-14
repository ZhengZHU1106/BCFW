#!/usr/bin/env python3
"""
测试Ganache连接和账户配置
"""

import sys
import json
from pathlib import Path

# 添加后端路径
sys.path.append(str(Path(__file__).parent.parent / "backend"))

def test_ganache_connection():
    """测试Ganache连接"""
    print("🔍 测试Ganache连接...")
    
    try:
        from web3 import Web3
        import config
        
        # 连接到Ganache
        w3 = Web3(Web3.HTTPProvider(config.GANACHE_CONFIG['rpc_url']))
        
        if not w3.is_connected():
            print("❌ 无法连接到Ganache")
            print(f"   请确保Ganache运行在 {config.GANACHE_CONFIG['rpc_url']}")
            return False
        
        print("✅ Ganache连接成功")
        
        # 检查网络信息
        chain_id = w3.eth.chain_id
        block_number = w3.eth.block_number
        print(f"   网络ID: {chain_id}")
        print(f"   当前区块: {block_number}")
        
        # 检查账户
        accounts = w3.eth.accounts
        print(f"   可用账户数: {len(accounts)}")
        
        if len(accounts) < 4:
            print("❌ 账户数量不足，需要至少4个账户")
            return False
        
        # 验证账户配置
        ganache_accounts = config.GANACHE_CONFIG['accounts']
        print("\n📋 账户配置验证:")
        
        for role, index in ganache_accounts.items():
            if index < len(accounts):
                account = accounts[index]
                balance = w3.eth.get_balance(account)
                balance_eth = w3.from_wei(balance, 'ether')
                print(f"   {role}: {account} (余额: {balance_eth} ETH)")
            else:
                print(f"   ❌ {role}: 账户索引 {index} 不存在")
                return False
        
        return True
        
    except ImportError:
        print("❌ 缺少web3依赖，请运行: pip install web3")
        return False
    except Exception as e:
        print(f"❌ 连接测试失败: {e}")
        return False

def test_account_deterministic():
    """测试账户地址的确定性"""
    print("\n🔍 测试账户地址确定性...")
    
    try:
        from web3 import Web3
        from eth_account import Account
        import config
        
        mnemonic = config.GANACHE_CONFIG['mnemonic']
        print(f"   使用助记词: {mnemonic}")
        
        # 预期的账户地址（通过助记词生成）
        Account.enable_unaudited_hdwallet_features()
        
        expected_accounts = []
        for i in range(4):
            account = Account.from_mnemonic(mnemonic, account_path=f"m/44'/60'/0'/0/{i}")
            expected_accounts.append(account.address)
        
        print("\n   预期账户地址:")
        ganache_accounts = config.GANACHE_CONFIG['accounts']
        for role, index in ganache_accounts.items():
            print(f"   {role}: {expected_accounts[index]}")
        
        return True
        
    except ImportError:
        print("❌ 缺少eth-account依赖，请运行: pip install eth-account")
        return False
    except Exception as e:
        print(f"❌ 地址生成失败: {e}")
        return False

def main():
    """运行Ganache连接测试"""
    print("🚀 Ganache连接测试\n")
    print("=" * 50)
    
    # 首先检查配置
    try:
        import config
        print("✅ 配置文件加载成功")
    except ImportError:
        print("❌ 无法加载配置文件")
        return False
    
    # 测试账户确定性
    result1 = test_account_deterministic()
    
    # 测试实际连接
    result2 = test_ganache_connection()
    
    print("\n" + "=" * 50)
    if result1 and result2:
        print("🎉 Ganache连接测试全部通过！")
        print("\n💡 提示:")
        print("   - 使用 CLI: npm run start-chain")
        print("   - 使用桌面端: npm run start-chain-desktop")
        return True
    else:
        print("⚠️  测试失败，请检查Ganache是否正常运行")
        print("\n🔧 启动Ganache:")
        print("   npm run start-chain")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)