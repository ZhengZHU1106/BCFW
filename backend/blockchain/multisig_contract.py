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

from ..config import get_deployed_contract

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
            contract_info = get_deployed_contract()

            # 部署信息可能不包含 ABI，此处兜底加载
            if "abi" not in contract_info or not contract_info["abi"]:
                abi_path = os.path.join(
                    os.path.dirname(__file__),
                    '../assets/multisig_abi.json'
                )
                with open(abi_path, 'r', encoding='utf-8') as abi_file:
                    contract_info["abi"] = json.load(abi_file)

            logger.info(
                "✅ Deployed contract info loaded\n"
                f"   Address: {contract_info.get('address')}\n"
                f"   Mode: {contract_info.get('mode', 'poa')}"
            )
            return contract_info

        except FileNotFoundError as exc:
            raise FileNotFoundError(
                f"Contract configuration not found for PoA demo: {exc}"
            ) from exc
        except Exception as exc:
            logger.error(f"❌ Failed to load deployed contract: {exc}")
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

    def reject_proposal(self, proposal_id: int, rejector_role: str) -> Dict[str, Any]:
        """Reject proposal on smart contract (1-vote veto)"""
        try:
            # Check rejector authorization
            if not self.is_authorized_signer(rejector_role):
                raise ValueError(f"Role {rejector_role} is not authorized to reject proposals")

            # Get rejector account
            rejector_address = self.web3_manager.accounts.get(rejector_role)
            rejector_key = self.web3_manager.private_keys.get(rejector_role)

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(rejector_address)
            gas_price = self.w3.eth.gas_price

            txn = self.contract.functions.rejectProposal(proposal_id).build_transaction({
                'from': rejector_address,
                'nonce': nonce,
                'gas': 200000,
                'gasPrice': gas_price,
                'chainId': self.w3.eth.chain_id
            })

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(txn, rejector_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                # Get updated proposal info
                proposal = self.get_proposal(proposal_id)

                logger.info(f"❌ Proposal {proposal_id} rejected by {rejector_role} on-chain")

                return {
                    "success": True,
                    "proposal_id": proposal_id,
                    "rejector": rejector_address,
                    "rejector_role": rejector_role,
                    "rejected": proposal["rejected"] if proposal else True,
                    "rejected_by": proposal["rejected_by"] if proposal else rejector_address,
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "rejected_at": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Transaction failed with status {receipt.status}")

        except ContractLogicError as e:
            logger.error(f"❌ Contract logic error: {e}")
            return {
                "success": False,
                "error": f"Smart contract rejected: {str(e)}",
                "proposal_id": proposal_id,
                "rejector_role": rejector_role
            }
        except Exception as e:
            logger.error(f"❌ Reject proposal failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "proposal_id": proposal_id,
                "rejector_role": rejector_role
            }

    def get_proposal(self, proposal_id: int) -> Optional[Dict[str, Any]]:
        """Get proposal from smart contract"""
        try:
            # Call getProposal function
            result = self.contract.functions.getProposal(proposal_id).call()

            if result and len(result) >= 4:
                target = result[1]
                if target == '0x0000000000000000000000000000000000000000':
                    return None

                if len(result) >= 9:
                    _, _, amount_wei, executed, rejected, rejected_by, signature_count, creator, created_at = result
                else:
                    # Legacy contract with 7 fields (id, target, amount, executed, signatureCount, creator, createdAt)
                    _, _, amount_wei, executed, signature_count, creator, created_at = result[:7]
                    rejected = False
                    rejected_by = None

                return {
                    "id": result[0],
                    "target": target,
                    "amount": self.w3.from_wei(amount_wei, 'ether'),
                    "amount_wei": amount_wei,
                    "executed": executed,
                    "rejected": rejected,
                    "rejected_by": rejected_by if rejected_by and rejected_by != '0x0000000000000000000000000000000000000000' else None,
                    "signature_count": signature_count,
                    "creator": creator,
                    "created_at": datetime.fromtimestamp(created_at).isoformat() if created_at and created_at > 0 else None,
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

    def withdraw_from_reward_pool(self, to_role: str, amount_eth: float) -> Dict[str, Any]:
        """Withdraw ETH from reward pool - using treasury as intermediary"""
        try:
            # Get reward pool current balance first
            pool_info = self.get_reward_pool_info()
            current_balance = float(pool_info.get("balance", 0))  # Convert to float

            if current_balance < amount_eth:
                raise ValueError(f"Insufficient balance in reward pool. Available: {current_balance} ETH")

            # Use treasury account to send ETH from reward pool
            treasury_address = self.web3_manager.accounts.get("treasury")
            treasury_key = self.web3_manager.private_keys.get("treasury")
            recipient_address = self.web3_manager.accounts.get(to_role)

            amount_wei = self.w3.to_wei(amount_eth, 'ether')

            # Build transaction
            nonce = self.w3.eth.get_transaction_count(treasury_address)
            gas_price = self.w3.eth.gas_price

            transaction = {
                'to': recipient_address,
                'value': amount_wei,
                'gas': 21000,
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': self.w3.eth.chain_id
            }

            # Sign and send
            signed_txn = self.w3.eth.account.sign_transaction(transaction, treasury_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            if receipt.status == 1:
                logger.info(f"💸 Withdrew {amount_eth} ETH from reward pool to {to_role}")

                return {
                    "success": True,
                    "recipient_role": to_role,
                    "amount": amount_eth,
                    "new_balance": current_balance - amount_eth,  # Approximate
                    "tx_hash": tx_hash.hex(),
                    "block_number": receipt.blockNumber,
                    "withdrawn_at": datetime.now().isoformat()
                }
            else:
                raise Exception(f"Transaction failed with status {receipt.status}")

        except Exception as e:
            logger.error(f"❌ Withdraw from reward pool failed: {e}")
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
            events = self.contract.events.ProposalCreated().process_receipt(receipt)
            if events:
                return int(events[0]['args']['proposalId'])

            # Fallback: use latest proposalCount (count is total proposals)
            proposal_count = self.contract.functions.proposalCount().call()
            if proposal_count == 0:
                raise ValueError("No proposals found on-chain after creation receipt")
            return proposal_count - 1

        except Exception as e:
            logger.warning(f"⚠️  Could not extract proposal ID from receipt: {e}")
            # Return latest proposal count
            proposal_count = self.contract.functions.proposalCount().call()
            return proposal_count - 1 if proposal_count else 0
