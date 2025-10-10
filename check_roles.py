#!/usr/bin/env python3
"""Check roles assigned in MultiSig contract"""
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.blockchain.web3_manager import get_web3_manager

def main():
    print("🔍 Checking Contract Roles...")
    web3_manager = get_web3_manager()
    contract = web3_manager.multisig_contract.contract

    roles_to_check = [
        ("operator_0", "OPERATOR"),
        ("operator_1", "OPERATOR"),
        ("manager_0", "MANAGER"),
        ("manager_1", "MANAGER"),
        ("manager_2", "MANAGER"),
    ]

    role_names = {0: "NONE", 1: "OPERATOR", 2: "MANAGER"}

    print("\nCurrent Role Assignments:")
    print("-" * 60)
    for role_name, expected_role in roles_to_check:
        user_address = web3_manager.accounts.get(role_name)
        if user_address:
            current_role = contract.functions.getUserRole(user_address).call()
            status = "✅" if role_names[current_role] == expected_role else "❌"
            print(f"{status} {role_name:12} ({user_address[:10]}...): {role_names[current_role]}")

if __name__ == "__main__":
    main()
