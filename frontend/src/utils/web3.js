import Web3 from 'web3'
import { ethers } from 'ethers'

// Web3实例
let web3 = null

// 初始化Web3连接
export const initWeb3 = () => {
  if (!web3) {
    web3 = new Web3('http://localhost:8545')
  }
  return web3
}

// 获取Web3实例
export const getWeb3 = () => {
  if (!web3) {
    initWeb3()
  }
  return web3
}

// 创建新账户（使用ethers生成密钥对）
export const createNewAccount = async () => {
  try {
    // 使用ethers创建随机钱包
    const wallet = ethers.Wallet.createRandom()
    
    return {
      address: wallet.address,
      privateKey: wallet.privateKey,
      mnemonic: wallet.mnemonic?.phrase || ''
    }
  } catch (error) {
    console.error('创建账户失败:', error)
    throw error
  }
}

// 获取账户余额
export const getAccountBalance = async (address) => {
  try {
    const web3Instance = getWeb3()
    const balance = await web3Instance.eth.getBalance(address)
    return web3Instance.utils.fromWei(balance, 'ether')
  } catch (error) {
    console.error('获取余额失败:', error)
    return '0'
  }
}

// 从Treasury账户转账（需要后端API支持）
export const fundAccount = async (toAddress, amount = '1.0') => {
  try {
    // 调用后端API来执行转账
    const response = await fetch('/api/accounts/fund', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        to_address: toAddress,
        amount: amount
      })
    })
    
    if (!response.ok) {
      throw new Error('转账失败')
    }
    
    return await response.json()
  } catch (error) {
    console.error('资金转账失败:', error)
    throw error
  }
}

// 获取所有账户（从Ganache）
export const getAllAccounts = async () => {
  try {
    const web3Instance = getWeb3()
    const accounts = await web3Instance.eth.getAccounts()
    
    // 获取每个账户的余额
    const accountsWithBalance = await Promise.all(
      accounts.map(async (address) => {
        const balance = await getAccountBalance(address)
        return { address, balance }
      })
    )
    
    return accountsWithBalance
  } catch (error) {
    console.error('获取账户列表失败:', error)
    return []
  }
}

// 检查连接状态
export const checkConnection = async () => {
  try {
    const web3Instance = getWeb3()
    const blockNumber = await web3Instance.eth.getBlockNumber()
    return blockNumber >= 0
  } catch (error) {
    console.error('连接检查失败:', error)
    return false
  }
}