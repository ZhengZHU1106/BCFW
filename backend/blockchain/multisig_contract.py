"""
MultiSig Contract Integration Module - Real Web3.py Implementation
Integrates with deployed MultiSigProposal contract on DevLeChain
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import logging
from web3.exceptions import ContractLogicError

logger = logging.getLogger(__name__)

class MultiSigContract:
    """Real smart contract integration class"""

    def __init__(self, web3_manager, reward_pool_service=None):
        self.web3_manager = web3_manager
        self.reward_pool_service = reward_pool_service
        self.w3 = web3_manager.w3

        # Load deployed contract
        contract_info = self._load_deployed_contract()
        self.contract_address = contract_info["address"]
        self.contract_abi = contract_info["abi"]

        # Create contract instance
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.contract_abi
        )

        logger.info(f"✅ MultiSig contract loaded: {self.contract_address}")

    def _load_deployed_contract(self) -> Dict[str, Any]:
        """Load deployed contract info from JSON"""
        try:
            contract_path = os.path.join(
                os.path.dirname(__file__),
                '../assets/deployed_contract.json'
            )
            with open(contract_path, 'r') as f:
                contract_info = json.load(f)

            logger.info(f"✅ Deployed contract info loaded")
            return contract_info

        except Exception as e:
            logger.error(f"❌ Failed to load deployed contract: {e}")
            raise

    def create_proposal(self, target: str, amount: float, data: str = "0x", creator_role: str = None) -> Dict[str, Any]:
        """Create proposal on smart contract"""
        try:
            # Check creator authorization
            if creator_role and not self.is_authorized_creator(creator_role):
                raise ValueError(f"Role {creator_role} is not authorized to create proposals")

            # Convert amount to wei
            amount_wei = self.w3.to_wei(amount, 'ether')

            # Get creator account
            creator_address = self.web3_manager.accounts.get(creator_role or 'operator_0')
            creator_key = self.web3_manager.private_keys.get(creator_role or 'operator_0')

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(creator_address)
            gas_price = self.w3.eth.gas_price

            txn = self.contract.functions.createProposal(
                target,
                amount_wei,
                bytes.fromhex(data[2:]) if data.startswith('0x') else b''
            ).build_transaction({
                'from': creator_address,
                'nonce': nonce,
                'gas': 500000,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            })

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, creator_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                # Parse proposal ID from events
                proposal_id = self._get_proposal_id_from_receipt(receipt)

                logger.info(f"📝 Proposal created on-chain: ID-{proposal_id}, TX-{tx_hash.hex()}")

                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "target": target,
                    "amount": amount,
                    "amount_wei": amount_wei,
                    "contract_address": self.contract_address,
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "creator_role": creator_role,
                    "message": f"Proposal {proposal_id} created on blockchain"
                }
            else:
                raise Exception(f"Transaction failed with status {receipt.status}")

        except Exception as e:
            logger.error(f"❌ Create proposal failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def sign_proposal(self, proposal_id: int, signer_role: str) -> Dict[str, Any]:
        """Sign proposal on smart contract"""
        try:
            # Check signer authorization
            if not self.is_authorized_signer(signer_role):
                raise ValueError(f"Role {signer_role} is not authorized to sign proposals")

            # Get signer account
            signer_address = self.web3_manager.accounts.get(signer_role)
            signer_key = self.web3_manager.private_keys.get(signer_role)

            # Check if already signed
            has_signed = self.contract.functions.hasSigned(proposal_id, signer_address).call()
            if has_signed:
                raise ValueError(f"{signer_role} has already signed proposal {proposal_id}")

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(signer_address)
            gas_price = self.w3.eth.gas_price

            txn = self.contract.functions.signProposal(proposal_id).build_transaction({
                'from': signer_address,
                'nonce': nonce,
                'gas': 500000,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            })

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, signer_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                # Get updated proposal info
                proposal = self.get_proposal(proposal_id)

                logger.info(f"✅ Proposal {proposal_id} signed by {signer_role} on-chain")

                result = {
                    "success": True,
                    "proposal_id": proposal_id,
                    "signer": signer_address,
                    "signer_role": signer_role,
                    "signature_count": proposal["signature_count"] if proposal else 0,
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "signed_at": datetime.now().isoformat()
                }

                # Check if executed (from events)
                if proposal and proposal["executed"]:
                    result["executed"] = True
                    result["message"] = f"Proposal {proposal_id} signed and executed"

                return result
            else:
                raise Exception(f"Transaction failed with status {receipt.status}")

        except ContractLogicError as e:
            logger.error(f"❌ Contract logic error: {e}")
            return {
                "success": False,
                "error": f"Smart contract rejected: {str(e)}",
                "proposal_id": proposal_id,
                "signer_role": signer_role
            }
        except Exception as e:
            logger.error(f"❌ Sign proposal failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "proposal_id": proposal_id,
                "signer_role": signer_role
            }

    def get_proposal(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Get proposal from smart contract"""
        try:
            # Call getProposal function
            result = self.contract.functions.getProposal(proposal_id).call()

            # Parse result tuple: (id, target, amount, executed, signatureCount, creator, createdAt)
            # Check if result is valid (proposal ID >= 0 is valid)
            if result and result[1] != '0x0000000000000000000000000000000000000000':  # Check target address
                return {
                    "id": result[0],
                    "target": result[1],
                    "amount": self.w3.from_wei(result[2], 'ether'),
                    "amount_wei": result[2],
                    "executed": result[3],
                    "signature_count": result[4],
                    "creator": result[5],
                    "created_at": datetime.fromtimestamp(result[6]).isoformat() if result[6] > 0 else None,
                    "contract_address": self.contract_address
                }
            else:
                return None

        except Exception as e:
            logger.error(f"❌ Get proposal failed: {e}")
            return None

    def has_signed(self, proposal_id: int, signer_role: str) -> bool:
        """Check if signer has signed proposal"""
        try:
            signer_address = self.web3_manager.accounts.get(signer_role)
            return self.contract.functions.hasSigned(proposal_id, signer_address).call()
        except:
            return False

    def get_contract_info(self) -> Dict[str, Any]:
        """Get contract information"""
        try:
            owners = self.contract.functions.getOwners().call()
            threshold = self.contract.functions.threshold().call()
            proposal_count = self.contract.functions.proposalCount().call()

            return {
                "address": self.contract_address,
                "owners": owners,
                "threshold": threshold,
                "owner_count": len(owners),
                "chain_id": self.w3.eth.chain_id,
                "total_proposals": proposal_count
            }
        except Exception as e:
            logger.error(f"❌ Get contract info failed: {e}")
            return {
                "address": self.contract_address,
                "error": str(e)
            }

    def get_all_proposals(self) -> list:
        """Get all proposals from contract"""
        try:
            proposal_count = self.contract.functions.proposalCount().call()
            proposals = []

            # Proposal IDs start from 0
            for i in range(0, proposal_count):
                proposal = self.get_proposal(i)
                if proposal:
                    proposals.append(proposal)

            return proposals
        except Exception as e:
            logger.error(f"❌ Get all proposals failed: {e}")
            return []

    def get_pending_proposals(self) -> list:
        """Get pending (not executed) proposals"""
        all_proposals = self.get_all_proposals()
        return [p for p in all_proposals if not p.get("executed", False)]

    # ================================
    # Reward Pool Methods
    # ================================

    def deposit_to_reward_pool(self, from_role: str, amount_eth: float) -> Dict[str, Any]:
        """Deposit ETH to reward pool in smart contract"""
        try:
            depositor_address = self.web3_manager.accounts.get(from_role)
            depositor_key = self.web3_manager.private_keys.get(from_role)

            amount_wei = self.w3.to_wei(amount_eth, 'ether')

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(depositor_address)
            gas_price = self.w3.eth.gas_price

            txn = self.contract.functions.depositToRewardPool().build_transaction({
                'from': depositor_address,
                'value': amount_wei,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            })

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, depositor_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                pool_info = self.get_reward_pool_info()

                logger.info(f"💰 Deposited {amount_eth} ETH to reward pool")

                return {
                    "success": True,
                    "depositor_role": from_role,
                    "amount": amount_eth,
                    "new_balance": pool_info.get("balance", 0),
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "deposited_at": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Transaction failed with status {receipt.status}")

        except Exception as e:
            logger.error(f"❌ Deposit to reward pool failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_reward_pool_info(self) -> Dict[str, Any]:
        """Get reward pool info from contract"""
        try:
            result = self.contract.functions.getRewardPoolInfo().call()
            # Returns (balance, baseReward)

            return {
                "balance": self.w3.from_wei(result[0], 'ether'),
                "balance_wei": result[0],
                "base_reward": self.w3.from_wei(result[1], 'ether'),
                "base_reward_wei": result[1],
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Get reward pool info failed: {e}")
            return {
                "balance": 0,
                "balance_wei": 0,
                "base_reward": 0.01,
                "base_reward_wei": self.w3.to_wei(0.01, 'ether'),
                "error": str(e)
            }

    def get_contribution(self, manager_address: str) -> Dict[str, Any]:
        """Get manager contribution from contract"""
        try:
            result = self.contract.functions.getContribution(manager_address).call()
            # Returns (totalSignatures, avgResponseTime, qualityScore, lastSignatureTime)

            return {
                "total_signatures": result[0],
                "avg_response_time": result[1],
                "quality_score": result[2],
                "last_signature_time": datetime.fromtimestamp(result[3]).isoformat() if result[3] > 0 else None
            }
        except Exception as e:
            logger.error(f"❌ Get contribution failed: {e}")
            return {
                "total_signatures": 0,
                "avg_response_time": 0,
                "quality_score": 0,
                "last_signature_time": None
            }

    def distribute_contribution_rewards(self, admin_role: str) -> Dict[str, Any]:
        """Distribute rewards based on contributions"""
        try:
            admin_address = self.web3_manager.accounts.get(admin_role)
            admin_key = self.web3_manager.private_keys.get(admin_role)

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(admin_address)
            gas_price = self.w3.eth.gas_price

            txn = self.contract.functions.distributeContributionRewards().build_transaction({
                'from': admin_address,
                'nonce': nonce,
                'gas': 500000,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            })

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, admin_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                logger.info(f"🎁 Contribution rewards distributed")

                return {
                    "success": True,
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "distributed_at": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Transaction failed with status {receipt.status}")

        except Exception as e:
            logger.error(f"❌ Distribute rewards failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    # ================================
    # Role Authorization Methods
    # ================================

    def is_authorized_creator(self, role: str) -> bool:
        """Check if role can create proposals (Operator or Manager)"""
        try:
            address = self.web3_manager.accounts.get(role)
            if not address:
                return False

            # Check both operator and manager roles
            is_operator = self.contract.functions.isOperator(address).call()
            is_manager = self.contract.functions.isManager(address).call()

            return is_operator or is_manager
        except:
            # Fallback to local check
            return role in ["operator_0", "operator_1", "operator_2", "operator_3", "operator_4",
                           "manager_0", "manager_1", "manager_2"]

    def is_authorized_signer(self, role: str) -> bool:
        """Check if role can sign proposals (Manager only)"""
        try:
            address = self.web3_manager.accounts.get(role)
            if not address:
                return False

            return self.contract.functions.isManager(address).call()
        except:
            # Fallback to local check
            return role in ["manager_0", "manager_1", "manager_2"]

    def get_user_role(self, user_address: str) -> str:
        """Get user role from contract"""
        try:
            role_enum = self.contract.functions.getUserRole(user_address).call()
            # Role enum: 0=NONE, 1=OPERATOR, 2=MANAGER

            role_map = {0: "NONE", 1: "OPERATOR", 2: "MANAGER"}
            return role_map.get(role_enum, "NONE")
        except:
            return "NONE"

    def assign_role(self, user_address: str, role: int, admin_role: str) -> Dict[str, Any]:
        """Assign role to user (admin only)"""
        try:
            admin_address = self.web3_manager.accounts.get(admin_role)
            admin_key = self.web3_manager.private_keys.get(admin_role)

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(admin_address)
            gas_price = self.w3.eth.gas_price

            txn = self.contract.functions.assignRole(user_address, role).build_transaction({
                'from': admin_address,
                'nonce': nonce,
                'gas': 100000,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            })

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, admin_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                return {
                    "success": True,
                    "user_address": user_address,
                    "role": role,
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber
                }
            else:
                raise Exception(f"Transaction failed with status {receipt.status}")

        except Exception as e:
            logger.error(f"❌ Assign role failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _get_proposal_id_from_receipt(self, receipt) -> int:
        """Extract proposal ID from transaction receipt events"""
        try:
            # Get ProposalCreated event
            event_signature_hash = self.w3.keccak(text="ProposalCreated(uint256,address,address,uint256)")

            for log in receipt.logs:
                if log.topics[0] == event_signature_hash:
                    # First topic is proposal ID (indexed)
                    proposal_id = int(log.topics[1].hex(), 16)
                    return proposal_id

            # Fallback: get from proposalCount
            proposal_count = self.contract.functions.proposalCount().call()
            return proposal_count

        except Exception as e:
            logger.warning(f"⚠️  Could not extract proposal ID from receipt: {e}")
            # Return latest proposal count
            return self.contract.functions.proposalCount().call()
