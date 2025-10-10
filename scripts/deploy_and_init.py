#!/usr/bin/env python3
"""
一键部署脚本 - DevLeChain智能合约部署与初始化
One-Click Deployment Script for DevLeChain Smart Contract

功能 / Features:
1. 编译并部署MultiSig智能合约 / Compile and deploy MultiSig contract
2. 自动初始化角色权限 / Automatically initialize roles
3. 自动充值合约奖金池 / Automatically fund contract reward pool
4. 验证部署成功 / Verify deployment success

使用方法 / Usage:
    python3 scripts/deploy_and_init.py
"""

import sys
import os
import json
from web3 import Web3
from eth_account import Account
import glob

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.config import DEVLECHAIN_CONFIG

# Color codes for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_info(msg):
    print(f"{BLUE}ℹ️  {msg}{RESET}")

def log_success(msg):
    print(f"{GREEN}✅ {msg}{RESET}")

def log_warning(msg):
    print(f"{YELLOW}⚠️  {msg}{RESET}")

def log_error(msg):
    print(f"{RED}❌ {msg}{RESET}")

def load_contract_artifacts():
    """加载智能合约ABI和字节码 / Load smart contract ABI and bytecode"""
    log_info("Step 1/4: Loading smart contract artifacts...")

    try:
        from solcx import compile_source, install_solc

        # Install solc if needed
        try:
            install_solc('0.8.19')
        except Exception:
            pass  # Already installed

        # Read and compile contract for bytecode
        contract_path = os.path.join(os.path.dirname(__file__), '../contracts/MultiSigProposal.sol')
        with open(contract_path, 'r') as f:
            contract_source = f.read()

        compiled_sol = compile_source(
            contract_source,
            output_values=['bin'],
            solc_version='0.8.19'
        )

        contract_id, contract_interface = compiled_sol.popitem()
        bytecode = contract_interface['bin']

        # Load complete ABI from existing file (includes all inherited methods)
        abi_path = os.path.join(os.path.dirname(__file__), '../backend/assets/multisig_abi.json')
        with open(abi_path, 'r') as f:
            abi = json.load(f)

        log_success("Contract artifacts loaded successfully")
        return abi, bytecode

    except Exception as e:
        log_error(f"Failed to load contract artifacts: {e}")
        sys.exit(1)

def connect_to_devlechain():
    """连接到DevLeChain / Connect to DevLeChain"""
    log_info("Connecting to DevLeChain...")

    w3 = Web3(Web3.HTTPProvider(DEVLECHAIN_CONFIG['rpc_url']))

    if not w3.is_connected():
        log_error(f"Cannot connect to DevLeChain: {DEVLECHAIN_CONFIG['rpc_url']}")
        log_error("Please ensure DevLeChain is running with: ./system.sh start")
        sys.exit(1)

    log_success(f"Connected to DevLeChain (Chain ID: {w3.eth.chain_id})")
    return w3

def load_deployer_account(w3):
    """加载部署账户 / Load deployer account (tries manager_0 first, then treasury)"""
    log_info("Loading deployer account from keystore...")

    keystore_dir = DEVLECHAIN_CONFIG['keystore_dir']
    password = DEVLECHAIN_CONFIG['password']

    # Try manager_0 first (usually has more balance), then treasury
    deployer_candidates = [
        ('manager_0', DEVLECHAIN_CONFIG['accounts']['manager_0']),
        ('treasury', DEVLECHAIN_CONFIG['accounts']['treasury'])
    ]

    for role, address in deployer_candidates:
        # Find keystore file
        pattern = os.path.join(keystore_dir, f"*--{address[2:].lower()}")
        keyfiles = glob.glob(pattern)

        if not keyfiles:
            log_warning(f"{role} keystore file not found: {address}")
            continue

        # Decrypt keystore
        with open(keyfiles[0], 'r') as f:
            encrypted_key = json.load(f)

        private_key = Account.decrypt(encrypted_key, password)
        account = Account.from_key(private_key)

        balance = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance, 'ether')

        # Check if this account has sufficient balance (need gas + 100 ETH funding)
        if balance >= w3.to_wei(110, 'ether'):  # 10 ETH for gas should be more than enough
            log_success(f"Deployer account loaded ({role}): {account.address} (Balance: {balance_eth} ETH)")
            return account, private_key
        else:
            log_warning(f"{role} has insufficient balance: {balance_eth} ETH (need at least 110 ETH)")

    log_error("No account with sufficient balance found for deployment!")
    log_error("Please ensure manager_0 or treasury has at least 110 ETH")
    sys.exit(1)

def deploy_contract(w3, abi, bytecode, deployer_account, private_key):
    """部署智能合约 / Deploy smart contract"""
    log_info("Step 2/4: Deploying MultiSig contract to DevLeChain...")

    try:
        # Get manager addresses as owners
        owners = [
            DEVLECHAIN_CONFIG['accounts']['manager_0'],
            DEVLECHAIN_CONFIG['accounts']['manager_1'],
            DEVLECHAIN_CONFIG['accounts']['manager_2']
        ]
        threshold = 2  # 2/3 signatures required

        # Create contract object
        Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

        # Build deployment transaction
        nonce = w3.eth.get_transaction_count(deployer_account.address)

        transaction = Contract.constructor(owners, threshold).build_transaction({
            'from': deployer_account.address,
            'nonce': nonce,
            'gas': 5000000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id
        })

        # Sign and send transaction
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)

        log_info(f"Transaction sent: {tx_hash.hex()}")
        log_info("Waiting for transaction confirmation...")

        # Wait for receipt
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt.status != 1:
            log_error("Contract deployment failed!")
            sys.exit(1)

        contract_address = receipt.contractAddress
        log_success(f"Contract deployed at: {contract_address}")
        log_success(f"Block number: {receipt.blockNumber}")
        log_success(f"Gas used: {receipt.gasUsed}")

        # Save deployment info
        deployment_info = {
            'address': contract_address,
            'deployer': deployer_account.address,
            'tx_hash': tx_hash.hex(),
            'block_number': receipt.blockNumber,
            'gas_used': receipt.gasUsed,
            'owners': owners,
            'threshold': threshold,
            'abi': abi
        }

        config_path = os.path.join(os.path.dirname(__file__), '../backend/assets/deployed_contract.json')
        with open(config_path, 'w') as f:
            json.dump(deployment_info, f, indent=2)

        log_success(f"Deployment info saved to: {config_path}")

        return contract_address, abi

    except Exception as e:
        log_error(f"Contract deployment failed: {e}")
        sys.exit(1)

def initialize_roles(w3, contract_address, abi, admin_account, private_key):
    """初始化角色权限 / Initialize roles"""
    log_info("Step 3/4: Initializing roles in smart contract...")

    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # Role enum values in the contract
        MANAGER_ROLE = 1
        OPERATOR_ROLE = 2

        operators = [
            DEVLECHAIN_CONFIG['accounts']['operator_0'],
            DEVLECHAIN_CONFIG['accounts']['operator_1']
        ]

        managers = [
            DEVLECHAIN_CONFIG['accounts']['manager_0'],
            DEVLECHAIN_CONFIG['accounts']['manager_1'],
            DEVLECHAIN_CONFIG['accounts']['manager_2']
        ]

        # Assign OPERATOR role
        for operator in operators:
            if not contract.functions.isOperator(operator).call():
                tx = contract.functions.assignRole(operator, OPERATOR_ROLE).build_transaction({
                    'from': admin_account.address,
                    'nonce': w3.eth.get_transaction_count(admin_account.address),
                    'gas': 150000,
                    'gasPrice': w3.eth.gas_price,
                    'chainId': w3.eth.chain_id
                })

                signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status == 1:
                    log_success(f"Assigned OPERATOR role to: {operator}")
                else:
                    log_error(f"Failed to assign OPERATOR role to: {operator}")
            else:
                log_info(f"OPERATOR role already assigned: {operator}")

        # Assign MANAGER role
        for manager in managers:
            if not contract.functions.isManager(manager).call():
                tx = contract.functions.assignRole(manager, MANAGER_ROLE).build_transaction({
                    'from': admin_account.address,
                    'nonce': w3.eth.get_transaction_count(admin_account.address),
                    'gas': 150000,
                    'gasPrice': w3.eth.gas_price,
                    'chainId': w3.eth.chain_id
                })

                signed_tx = w3.eth.account.sign_transaction(tx, private_key)
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
                receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

                if receipt.status == 1:
                    log_success(f"Assigned MANAGER role to: {manager}")
                else:
                    log_error(f"Failed to assign MANAGER role to: {manager}")
            else:
                log_info(f"MANAGER role already assigned: {manager}")

        log_success("All roles initialized successfully!")

    except Exception as e:
        log_error(f"Role initialization failed: {e}")
        sys.exit(1)

def fund_contract(w3, contract_address, abi, funder_account, private_key):
    """充值合约奖金池 / Fund contract reward pool"""
    log_info("Step 4/4: Funding contract reward pool...")

    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # Deposit 100 ETH to reward pool
        amount_wei = w3.to_wei(100, 'ether')

        tx = contract.functions.depositToRewardPool().build_transaction({
            'from': funder_account.address,
            'value': amount_wei,
            'nonce': w3.eth.get_transaction_count(funder_account.address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id
        })

        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

        log_info(f"Funding transaction sent: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt.status != 1:
            log_error("Funding transaction failed!")
            sys.exit(1)

        # Verify contract balance
        pool_info = contract.functions.getRewardPoolInfo().call()
        pool_balance_eth = w3.from_wei(pool_info[0], 'ether')

        log_success(f"Contract funded successfully! Reward pool balance: {pool_balance_eth} ETH")

    except Exception as e:
        log_error(f"Contract funding failed: {e}")
        sys.exit(1)

def verify_deployment(w3, contract_address, abi):
    """验证部署 / Verify deployment"""
    log_info("Verifying deployment...")

    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # Check contract info
        contract_info = contract.functions.getContractInfo().call()
        owners = contract_info[0]
        threshold = contract_info[1]
        proposal_count = contract_info[2]

        log_success(f"Contract owners: {len(owners)} accounts")
        log_success(f"Signature threshold: {threshold}")
        log_success(f"Current proposals: {proposal_count}")

        # Check reward pool
        pool_info = contract.functions.getRewardPoolInfo().call()
        pool_balance = w3.from_wei(pool_info[0], 'ether')

        log_success(f"Reward pool balance: {pool_balance} ETH")

        # Check roles
        OPERATOR_ROLE = w3.keccak(text="OPERATOR_ROLE")
        operator_0 = DEVLECHAIN_CONFIG['accounts']['operator_0']
        is_operator = contract.functions.hasRole(OPERATOR_ROLE, operator_0).call()

        log_success(f"Operator role check: {'✓' if is_operator else '✗'}")

        log_success("Deployment verification complete!")

        return True

    except Exception as e:
        log_error(f"Deployment verification failed: {e}")
        return False

def main():
    """主函数 / Main function"""
    print("\n" + "="*60)
    print(f"{GREEN}DevLeChain Smart Contract Deployment Script{RESET}")
    print("="*60 + "\n")

    # Step 1: Load contract artifacts
    abi, bytecode = load_contract_artifacts()

    # Connect to DevLeChain
    w3 = connect_to_devlechain()

    # Load deployer account
    deployer_account, deployer_private_key = load_deployer_account(w3)

    # Step 2: Deploy contract
    contract_address, abi = deploy_contract(w3, abi, bytecode, deployer_account, deployer_private_key)

    # Step 3: Initialize roles
    initialize_roles(w3, contract_address, abi, deployer_account, deployer_private_key)

    # Step 4: Fund contract
    fund_contract(w3, contract_address, abi, deployer_account, deployer_private_key)

    # Verify deployment
    success = verify_deployment(w3, contract_address, abi)

    if success:
        print("\n" + "="*60)
        log_success("All deployment steps completed successfully!")
        log_success(f"Contract address: {contract_address}")
        log_info("You can now start the backend with: ./system.sh start")
        print("="*60 + "\n")
    else:
        log_error("Deployment verification failed. Please check the logs.")
        sys.exit(1)

if __name__ == "__main__":
    main()
