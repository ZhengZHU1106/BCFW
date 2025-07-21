"""
API 统一异常处理机制
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


# ================== 自定义异常类 ==================

class APIException(Exception):
    """API异常基类"""
    def __init__(
        self, 
        message: str, 
        error_code: str = "API_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(APIException):
    """验证异常"""
    def __init__(self, message: str = "数据验证失败", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=details
        )


class BusinessException(APIException):
    """业务逻辑异常"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_ERROR",
            status_code=400,
            details=details
        )


class ResourceNotFoundException(APIException):
    """资源未找到异常"""
    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource}未找到"
        if resource_id:
            message += f": {resource_id}"
        
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            status_code=404,
            details={"resource": resource, "resource_id": resource_id}
        )


class AuthorizationException(APIException):
    """权限异常"""
    def __init__(self, message: str = "权限不足", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            details=details
        )


class SystemException(APIException):
    """系统异常"""
    def __init__(self, message: str = "系统内部错误", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SYSTEM_ERROR",
            status_code=500,
            details=details
        )


class ExternalServiceException(APIException):
    """外部服务异常"""
    def __init__(self, service: str, message: str = "外部服务调用失败"):
        super().__init__(
            message=f"{service}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service}
        )


# ================== 异常处理器 ==================

def create_error_response(
    success: bool = False,
    message: str = "操作失败",
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> JSONResponse:
    """创建标准错误响应"""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "message": message,
            "error_code": error_code,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
    )


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """API异常处理器"""
    logger.error(f"API异常: {exc.error_code} - {exc.message}")
    if exc.details:
        logger.error(f"异常详情: {exc.details}")
    
    return create_error_response(
        message=exc.message,
        error_code=exc.error_code,
        details=exc.details,
        status_code=exc.status_code
    )


async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Pydantic验证异常处理器"""
    logger.error(f"数据验证失败: {exc}")
    
    # 格式化验证错误详情
    details = {
        "validation_errors": []
    }
    
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        details["validation_errors"].append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    return create_error_response(
        message="请求数据验证失败",
        error_code="VALIDATION_ERROR",
        details=details,
        status_code=422
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""
    logger.error(f"HTTP异常: {exc.status_code} - {exc.detail}")
    
    # 根据状态码确定错误类型
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR"
    }
    
    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")
    
    return create_error_response(
        message=str(exc.detail),
        error_code=error_code,
        status_code=exc.status_code
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""
    logger.exception(f"未处理的异常: {type(exc).__name__} - {str(exc)}")
    
    return create_error_response(
        message="系统内部错误",
        error_code="INTERNAL_ERROR",
        details={"exception_type": type(exc).__name__},
        status_code=500
    )


# ================== 异常处理工具函数 ==================

def handle_service_exception(func):
    """服务层异常处理装饰器"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            raise BusinessException(str(e))
        except KeyError as e:
            raise ResourceNotFoundException("资源", str(e))
        except Exception as e:
            logger.exception(f"服务层异常: {func.__name__}")
            raise SystemException(f"服务执行失败: {str(e)}")
    
    return wrapper


def validate_role(role: str, valid_roles: list) -> None:
    """验证角色有效性"""
    if role not in valid_roles:
        raise ValidationException(
            f"无效的角色: {role}",
            details={"valid_roles": valid_roles, "provided_role": role}
        )


def validate_positive_number(value: Any, field_name: str) -> None:
    """验证正数"""
    if not isinstance(value, (int, float)) or value <= 0:
        raise ValidationException(
            f"{field_name}必须是正数",
            details={"field": field_name, "value": value}
        )


def validate_ethereum_address(address: str) -> None:
    """验证以太坊地址格式"""
    if not address or not address.startswith('0x') or len(address) != 42:
        raise ValidationException(
            "无效的以太坊地址格式",
            details={"address": address, "expected_format": "0x + 40位十六进制字符"}
        )