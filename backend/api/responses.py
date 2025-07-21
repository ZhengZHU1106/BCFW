"""
API 标准化响应工具函数
"""
from typing import Any, Dict, Optional
from datetime import datetime
from fastapi.responses import JSONResponse

from .schemas import APISuccessResponse, APIErrorResponse


def create_success_response(
    data: Any,
    message: str = "操作成功",
    status_code: int = 200
) -> JSONResponse:
    """创建成功响应"""
    response_data = {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_error_response(
    message: str = "操作失败",
    error_code: str = "UNKNOWN_ERROR",
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> JSONResponse:
    """创建错误响应"""
    response_data = {
        "success": False,
        "message": message,
        "error_code": error_code,
        "details": details,
        "timestamp": datetime.now().isoformat()
    }
    
    return JSONResponse(
        status_code=status_code,
        content=response_data
    )


def create_health_response(
    status: str = "healthy",
    message: str = "系统运行正常"
) -> JSONResponse:
    """创建健康检查响应"""
    response_data = {
        "status": status,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    return JSONResponse(
        status_code=200,
        content=response_data
    )


def success_response(data: Any, message: str = "操作成功"):
    """返回成功响应数据结构（用于路由函数返回）"""
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }


def paginated_response(
    items: list,
    total: int,
    page: int = 1,
    page_size: int = 50,
    message: str = "数据获取成功"
):
    """返回分页响应"""
    return success_response(
        data={
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size,
                "has_next": page * page_size < total,
                "has_prev": page > 1
            }
        },
        message=message
    )