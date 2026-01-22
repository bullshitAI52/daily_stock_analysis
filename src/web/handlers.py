# -*- coding: utf-8 -*-
"""
===================================
Web 处理器层 - 请求处理
===================================

职责：
1. 处理各类 HTTP 请求
2. 调用服务层执行业务逻辑
3. 返回响应数据

处理器分类：
- PageHandler: 页面请求处理
- ApiHandler: API 接口处理
"""

from __future__ import annotations

import json
import re
import logging
from http import HTTPStatus
from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING

from web.services import get_config_service, get_analysis_service
from web.templates import render_config_page
from enums import ReportType

if TYPE_CHECKING:
    from http.server import BaseHTTPRequestHandler

logger = logging.getLogger(__name__)


# ============================================================
# 响应辅助类
# ============================================================

class Response:
    """HTTP 响应封装"""
    
    def __init__(
        self,
        body: bytes,
        status: HTTPStatus = HTTPStatus.OK,
        content_type: str = "text/html; charset=utf-8"
    ):
        self.body = body
        self.status = status
        self.content_type = content_type
    
    def send(self, handler: 'BaseHTTPRequestHandler') -> None:
        """发送响应到客户端"""
        handler.send_response(self.status)
        handler.send_header("Content-Type", self.content_type)
        handler.send_header("Content-Length", str(len(self.body)))
        handler.end_headers()
        handler.wfile.write(self.body)


class JsonResponse(Response):
    """JSON 响应封装"""
    
    def __init__(
        self,
        data: Dict[str, Any],
        status: HTTPStatus = HTTPStatus.OK
    ):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        super().__init__(
            body=body,
            status=status,
            content_type="application/json; charset=utf-8"
        )


class HtmlResponse(Response):
    """HTML 响应封装"""
    
    def __init__(
        self,
        body: bytes,
        status: HTTPStatus = HTTPStatus.OK
    ):
        super().__init__(
            body=body,
            status=status,
            content_type="text/html; charset=utf-8"
        )


class DownloadResponse(Response):
    """下载文件响应"""
    
    def __init__(
        self,
        body: bytes,
        filename: str,
        status: HTTPStatus = HTTPStatus.OK
    ):
        super().__init__(
            body=body,
            status=status,
            content_type="application/octet-stream"
        )
        self.filename = filename
        
    def send(self, handler: 'BaseHTTPRequestHandler') -> None:
        """发送带附件头的响应"""
        handler.send_response(self.status)
        handler.send_header("Content-Type", self.content_type)
        handler.send_header("Content-Length", str(len(self.body)))
        # URL编码文件名以支持中文
        from urllib.parse import quote
        encoded_filename = quote(self.filename)
        handler.send_header("Content-Disposition", f"attachment; filename*=UTF-8''{encoded_filename}")
        handler.end_headers()
        handler.wfile.write(self.body)


# ============================================================
# 页面处理器
# ============================================================

class PageHandler:
    """页面请求处理器"""
    
    def __init__(self):
        self.config_service = get_config_service()
    
    def handle_index(self) -> Response:
        """处理首页请求 GET /"""
        stock_list = self.config_service.get_stock_list()
        env_filename = self.config_service.get_env_filename()
        body = render_config_page(stock_list, env_filename)
        return HtmlResponse(body)
    
    def handle_update(self, form_data: Dict[str, list]) -> Response:
        """
        处理配置更新 POST /update
        
        Args:
            form_data: 表单数据
        """
        stock_list = form_data.get("stock_list", [""])[0]
        normalized = self.config_service.set_stock_list(stock_list)
        env_filename = self.config_service.get_env_filename()
        body = render_config_page(normalized, env_filename, message="已保存")
        return HtmlResponse(body)


# ============================================================
# API 处理器
# ============================================================

class ApiHandler:
    """API 请求处理器"""
    
    def __init__(self):
        self.analysis_service = get_analysis_service()
    
    def handle_health(self) -> Response:
        """
        健康检查 GET /health
        
        返回:
            {
                "status": "ok",
                "timestamp": "2026-01-19T10:30:00",
                "service": "stock-analysis-webui"
            }
        """
        data = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "service": "stock-analysis-webui"
        }
        return JsonResponse(data)
    
    def handle_analysis(self, query: Dict[str, list]) -> Response:
        """
        触发股票分析 GET /analysis?code=xxx
        
        Args:
            query: URL 查询参数
            
        返回:
            {
                "success": true,
                "message": "分析任务已提交",
                "code": "600519",
                "task_id": "600519_20260119_103000"
            }
        """
        # 获取股票代码参数
        code_list = query.get("code", [])
        if not code_list or not code_list[0].strip():
            return JsonResponse(
                {"success": False, "error": "缺少必填参数: code (股票代码)"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        code = code_list[0].strip()
        
        # 验证股票代码格式：A股(6位数字) 或 港股(hk+5位数字)
        code = code.lower()
        is_valid = re.match(r'^\d{6}$', code) or re.match(r'^hk\d{5}$', code)
        if not is_valid:
            return JsonResponse(
                {"success": False, "error": f"无效的股票代码格式: {code} (A股6位数字 或 港股hk+5位数字)"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        # 获取报告类型参数（默认精简报告）
        report_type_str = query.get("report_type", ["simple"])[0]
        report_type = ReportType.from_str(report_type_str)
        
        # 提交异步分析任务
        try:
            result = self.analysis_service.submit_analysis(code, report_type=report_type)
            return JsonResponse(result)
        except Exception as e:
            logger.error(f"[ApiHandler] 提交分析任务失败: {e}")
            return JsonResponse(
                {"success": False, "error": f"提交任务失败: {str(e)}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    def handle_tasks(self, query: Dict[str, list]) -> Response:
        """
        查询任务列表 GET /tasks
        
        Args:
            query: URL 查询参数 (可选 limit)
            
        返回:
            {
                "success": true,
                "tasks": [...]
            }
        """
        limit_list = query.get("limit", ["20"])
        try:
            limit = int(limit_list[0])
        except ValueError:
            limit = 20
        
        tasks = self.analysis_service.list_tasks(limit=limit)
        return JsonResponse({"success": True, "tasks": tasks})
    
    def handle_task_status(self, query: Dict[str, list]) -> Response:
        """
        查询单个任务状态 GET /task?id=xxx
        
        Args:
            query: URL 查询参数
        """
        task_id_list = query.get("id", [])
        if not task_id_list or not task_id_list[0].strip():
            return JsonResponse(
                {"success": False, "error": "缺少必填参数: id (任务ID)"},
                status=HTTPStatus.BAD_REQUEST
            )
        
        task_id = task_id_list[0].strip()
        task = self.analysis_service.get_task_status(task_id)
        
        if task is None:
            return JsonResponse(
                {"success": False, "error": f"任务不存在: {task_id}"},
                status=HTTPStatus.NOT_FOUND
            )
        
        return JsonResponse({"success": True, "task": task})
    
    def handle_download_report(self, query: Dict[str, list]) -> Response:
        """
        下载报告 GET /report/download?code=xxx&type=detail|summary|plain_talk|zip&date=yyyymmdd
        """
        code_list = query.get("code", [])
        if not code_list or not code_list[0].strip():
            return JsonResponse(
                {"success": False, "error": "缺少必填参数: code"},
                status=HTTPStatus.BAD_REQUEST
            )
        code = code_list[0].strip()
        
        # 报告类型: detail, summary, plain_talk, zip
        type_list = query.get("type", ["detail"])
        report_type = type_list[0].strip()
        
        # 日期参数，默认今天
        date_list = query.get("date", [])
        if date_list and date_list[0].strip():
            date_str = date_list[0].strip()
        else:
            date_str = datetime.now().strftime('%Y%m%d')
        
        from pathlib import Path
        
        # 处理 ZIP 打包下载
        if report_type == "zip":
            return self._create_zip_package(code, date_str)
        
        # 处理大白话版本
        if report_type == "plain_talk":
            return self._create_plain_talk_report(code, date_str)
            
        # 构造文件名（summary 或 detail）
        if report_type == "summary":
            filename = f"summary_{code}_{date_str}.md"
        else:
            filename = f"detail_{code}_{date_str}.md"
            
        file_path = Path("reports") / filename
        
        if not file_path.exists():
            return JsonResponse(
                {"success": False, "error": f"未找到该股票的{'极简' if report_type == 'summary' else '深度'}报告，请先执行分析"},
                status=HTTPStatus.NOT_FOUND
            )
            
        try:
            content = file_path.read_bytes()
            # 设置正确的下载响应
            return DownloadResponse(content, filename)
        except Exception as e:
            logger.error(f"读取报告失败: {e}")
            return JsonResponse(
                {"success": False, "error": f"读取报告失败: {str(e)}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    def _create_plain_talk_report(self, code: str, date_str: str) -> Response:
        """生成大白话版报告"""
        from pathlib import Path
        import json
        
        # 读取 summary 文件获取大白话内容
        summary_path = Path("reports") / f"summary_{code}_{date_str}.md"
        
        if not summary_path.exists():
            return JsonResponse(
                {"success": False, "error": "未找到报告，请先执行分析"},
                status=HTTPStatus.NOT_FOUND
            )
        
        try:
            # 从数据库或缓存获取分析结果
            from main import StockAnalysisPipeline
            from config import get_config
            
            config = get_config()
            pipeline = StockAnalysisPipeline(config)
            
            # 尝试从最近的分析结果获取大白话
            # 这里简化处理：从 summary 文件中提取或重新分析
            summary_content = summary_path.read_text(encoding='utf-8')
            
            # 生成大白话报告内容
            plain_talk_content = f"""# {code} 大白话投资建议

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

## 📌 核心提示

本报告用最直白的语言告诉您：
- 短期该怎么操作
- 长期该怎么布局

---

{summary_content}

---

> ⚠️ 风险提示：股市有风险，投资需谨慎。本报告仅供参考，不构成投资建议。
"""
            
            filename = f"plain_talk_{code}_{date_str}.md"
            return DownloadResponse(plain_talk_content.encode('utf-8'), filename)
            
        except Exception as e:
            logger.error(f"生成大白话报告失败: {e}")
            return JsonResponse(
                {"success": False, "error": f"生成报告失败: {str(e)}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )
    
    def _create_zip_package(self, code: str, date_str: str) -> Response:
        """创建包含所有报告的 ZIP 文件"""
        from pathlib import Path
        import zipfile
        import io
        
        # 检查文件是否存在
        summary_path = Path("reports") / f"summary_{code}_{date_str}.md"
        detail_path = Path("reports") / f"detail_{code}_{date_str}.md"
        
        # 只要有一个文件存在就可以下载
        if not summary_path.exists() and not detail_path.exists():
            return JsonResponse(
                {"success": False, "error": "未找到任何报告，请先执行分析"},
                status=HTTPStatus.NOT_FOUND
            )
        
        try:
            # 创建内存中的 ZIP 文件
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 添加 summary (如果存在)
                if summary_path.exists():
                    zip_file.write(summary_path, f"summary_{code}_{date_str}.md")
                
                # 添加 detail (如果存在)
                if detail_path.exists():
                    zip_file.write(detail_path, f"detail_{code}_{date_str}.md")
                
                # 生成并添加 plain_talk (如果有 summary)
                if summary_path.exists():
                    try:
                        summary_content = summary_path.read_text(encoding='utf-8')
                        plain_talk_content = f"""# {code} 大白话投资建议

生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

{summary_content}

---

> ⚠️ 风险提示：股市有风险，投资需谨慎。本报告仅供参考，不构成投资建议。
"""
                        zip_file.writestr(f"plain_talk_{code}_{date_str}.md", plain_talk_content)
                    except Exception as e:
                        logger.warning(f"无法生成大白话报告: {e}")
            
            # 获取 ZIP 内容
            zip_content = zip_buffer.getvalue()
            filename = f"reports_{code}_{date_str}.zip"
            
            return DownloadResponse(zip_content, filename)
            
        except Exception as e:
            logger.error(f"创建 ZIP 文件失败: {e}")
            return JsonResponse(
                {"success": False, "error": f"创建压缩包失败: {str(e)}"},
                status=HTTPStatus.INTERNAL_SERVER_ERROR
            )


# ============================================================
# 处理器工厂
# ============================================================

_page_handler: PageHandler | None = None
_api_handler: ApiHandler | None = None


def get_page_handler() -> PageHandler:
    """获取页面处理器实例"""
    global _page_handler
    if _page_handler is None:
        _page_handler = PageHandler()
    return _page_handler


def get_api_handler() -> ApiHandler:
    """获取 API 处理器实例"""
    global _api_handler
    if _api_handler is None:
        _api_handler = ApiHandler()
    return _api_handler
