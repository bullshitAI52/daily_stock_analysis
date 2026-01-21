# -*- coding: utf-8 -*-
"""
===================================
Web 模板层 - HTML 页面生成
===================================

职责：
1. 生成 HTML 页面
2. 管理 CSS 样式
3. 提供可复用的页面组件
"""

from __future__ import annotations

import html
from typing import Optional


# ============================================================
# CSS 样式定义
# ============================================================

BASE_CSS = """
:root {
    --primary: #2563eb;
    --primary-hover: #1d4ed8;
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #1e293b;
    --text-light: #64748b;
    --border: #e2e8f0;
    --success: #10b981;
    --error: #ef4444;
    --warning: #f59e0b;
}

/* Mobile Responsive Fixes */
@media (max-width: 600px) {
    body { padding: 10px; }
    .container { padding: 1.25rem; }
    
    .input-group { 
        flex-direction: column; 
    }
    
    .report-select {
        width: 100%;
    }
    
    .task-card {
        flex-wrap: wrap;
        padding-bottom: 0.75rem;
    }
    
    .task-main {
        min-width: 60%; /* Ensure title takes space */
    }
    
    .task-result {
        margin-left: auto; /* Push to right */
    }
    
    .task-actions {
        /* Position absolute to top right if needed, or just flow */
        margin-left: 0.5rem;
    }
    
    .task-detail {
        padding-left: 1rem; /* Reduce padding on mobile */
    }
}

* {
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background-color: var(--bg);
    color: var(--text);
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    margin: 0;
    padding: 20px;
}

.container {
    background: var(--card);
    padding: 2rem;
    border-radius: 1rem;
    box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    width: 100%;
    max-width: 500px;
}

h2 {
    margin-top: 0;
    color: var(--text);
    font-size: 1.5rem;
    font-weight: 700;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.subtitle {
    color: var(--text-light);
    font-size: 0.875rem;
    margin-bottom: 2rem;
    line-height: 1.5;
}

.code-badge {
    background: #f1f5f9;
    padding: 0.2rem 0.4rem;
    border-radius: 0.25rem;
    font-family: monospace;
    color: var(--primary);
}

.form-group {
    margin-bottom: 1.5rem;
}

label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text);
}

textarea, input[type="text"] {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    font-family: monospace;
    font-size: 0.875rem;
    line-height: 1.5;
    resize: vertical;
    transition: border-color 0.2s, box-shadow 0.2s;
}

textarea:focus, input[type="text"]:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

button {
    background-color: var(--primary);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 0.5rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    width: 100%;
    font-size: 1rem;
}

button:hover {
    background-color: var(--primary-hover);
    transform: translateY(-1px);
}

button:active {
    transform: translateY(0);
}

.btn-secondary {
    background-color: var(--text-light);
}

.btn-secondary:hover {
    background-color: var(--text);
}

.footer {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border);
    color: var(--text-light);
    font-size: 0.75rem;
    text-align: center;
}

/* Toast Notification */
.toast {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%) translateY(100px);
    background: white;
    border-left: 4px solid var(--success);
    padding: 1rem 1.5rem;
    border-radius: 0.5rem;
    box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    opacity: 0;
    z-index: 1000;
}

.toast.show {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
}

.toast.error {
    border-left-color: var(--error);
}

.toast.warning {
    border-left-color: var(--warning);
}

/* Helper classes */
.text-muted {
    font-size: 0.75rem;
    color: var(--text-light);
    margin-top: 0.5rem;
}

.mt-2 { margin-top: 0.5rem; }
.mt-4 { margin-top: 1rem; }
.mb-2 { margin-bottom: 0.5rem; }
.mb-4 { margin-bottom: 1rem; }

/* Section divider */
.section-divider {
    margin: 2rem 0;
    border: none;
    border-top: 1px solid var(--border);
}

/* Analysis section */
.analysis-section {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--border);
}

.analysis-section h3 {
    font-size: 1.1rem;
    font-weight: 600;
    margin-bottom: 1rem;
    color: var(--text);
}

.input-group {
    display: flex;
    gap: 0.5rem;
}

.input-group input {
    flex: 1;
    resize: none;
}

.input-group button {
    width: auto;
    padding: 0.75rem 1.25rem;
    white-space: nowrap;
}

.report-select {
    padding: 0.75rem 0.5rem;
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    font-size: 0.8rem;
    background: white;
    color: var(--text);
    cursor: pointer;
    min-width: 110px;
    transition: border-color 0.2s, box-shadow 0.2s;
}

.report-select:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.btn-analysis {
    background-color: var(--success);
}

.btn-analysis:hover {
    background-color: #059669;
}

.btn-analysis:disabled {
    background-color: var(--text-light);
    cursor: not-allowed;
    transform: none;
}

/* Result box */
.result-box {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 0.5rem;
    font-size: 0.875rem;
    display: none;
}

.result-box.show {
    display: block;
}

.result-box.success {
    background-color: #ecfdf5;
    border: 1px solid #a7f3d0;
    color: #065f46;
}

.result-box.error {
    background-color: #fef2f2;
    border: 1px solid #fecaca;
    color: #991b1b;
}

.result-box.loading {
    background-color: #eff6ff;
    border: 1px solid #bfdbfe;
    color: #1e40af;
}

.spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid currentColor;
    border-right-color: transparent;
    border-radius: 50%;
    animation: spin 0.75s linear infinite;
    margin-right: 0.5rem;
    vertical-align: middle;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Task List Container */
.task-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-height: 400px;
    overflow-y: auto;
}

.task-list:empty::after {
    content: '暂无任务';
    display: block;
    text-align: center;
    color: var(--text-light);
    font-size: 0.8rem;
    padding: 1rem;
}

/* Task Card - Compact */
.task-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.75rem;
    background: var(--bg);
    border-radius: 0.5rem;
    border: 1px solid var(--border);
    font-size: 0.8rem;
    transition: all 0.2s;
}

.task-card:hover {
    border-color: var(--primary);
    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

.task-card.running {
    border-color: var(--primary);
    background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
}

.task-card.completed {
    border-color: var(--success);
    background: linear-gradient(135deg, #ecfdf5 0%, #f8fafc 100%);
}

.task-card.failed {
    border-color: var(--error);
    background: linear-gradient(135deg, #fef2f2 0%, #f8fafc 100%);
}

/* Task Status Icon */
.task-status {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    flex-shrink: 0;
    font-size: 0.9rem;
}

.task-card.running .task-status {
    background: var(--primary);
    color: white;
}

.task-card.completed .task-status {
    background: var(--success);
    color: white;
}

.task-card.failed .task-status {
    background: var(--error);
    color: white;
}

.task-card.pending .task-status {
    background: var(--border);
    color: var(--text-light);
}

/* Task Main Info */
.task-main {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
}

.task-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: var(--text);
}

.task-title .code {
    font-family: monospace;
    background: rgba(0,0,0,0.05);
    padding: 0.1rem 0.3rem;
    border-radius: 0.25rem;
}

.task-title .name {
    color: var(--text-light);
    font-weight: 400;
    font-size: 0.75rem;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.task-meta {
    display: flex;
    gap: 0.75rem;
    font-size: 0.7rem;
    color: var(--text-light);
}

.task-meta span {
    display: flex;
    align-items: center;
    gap: 0.2rem;
}

/* Task Result Badge */
.task-result {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.15rem;
    flex-shrink: 0;
}

.task-advice {
    font-weight: 600;
    font-size: 0.75rem;
    padding: 0.15rem 0.4rem;
    border-radius: 0.25rem;
    background: var(--primary);
    color: white;
}

.task-advice.buy { background: #059669; }
.task-advice.sell { background: #dc2626; }
.task-advice.hold { background: #d97706; }
.task-advice.wait { background: #6b7280; }

.task-score {
    font-size: 0.7rem;
    color: var(--text-light);
}

/* Task Actions */
.task-actions {
    display: flex;
    gap: 0.25rem;
    flex-shrink: 0;
}

.task-btn {
    width: 24px;
    height: 24px;
    padding: 0;
    border-radius: 0.25rem;
    background: transparent;
    color: var(--text-light);
    font-size: 0.75rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

.task-btn:hover {
    background: rgba(0,0,0,0.05);
    color: var(--text);
    transform: none;
}

/* Spinner in task */
.task-card .spinner {
    width: 12px;
    height: 12px;
    border-width: 1.5px;
    margin: 0;
}

/* Empty state hint */
.task-hint {
    text-align: center;
    padding: 0.75rem;
    color: var(--text-light);
    font-size: 0.75rem;
    background: var(--bg);
    border-radius: 0.375rem;
}

/* Task detail expand */
.task-detail {
    display: none;
    padding: 0.5rem 0.75rem;
    padding-left: 3rem;
    background: rgba(0,0,0,0.02);
    border-radius: 0 0 0.5rem 0.5rem;
    margin-top: -0.5rem;
    font-size: 0.75rem;
    border: 1px solid var(--border);
    border-top: none;
}

.task-detail.show {
    display: block;
}

.task-detail-row {
    display: flex;
    justify-content: space-between;
    padding: 0.25rem 0;
}

.task-detail-row .label {
    color: var(--text-light);
}

.task-detail-summary {
    font-size: 0.95rem;
    line-height: 1.6;
    color: var(--text);
    background: #f8fafc;
    padding: 0.75rem;
    border-radius: 0.5rem;
    border-left: 3px solid var(--primary);
}

.task-detail-block {
    margin-top: 1rem;
}

.task-detail-block h4 {
    margin: 0 0 0.5rem 0;
    font-size: 0.9rem;
    color: var(--text-light);
    font-weight: 600;
    border-bottom: 1px dashed #e2e8f0;
    padding-bottom: 0.25rem;
}

.task-detail-text {
    font-size: 0.9rem;
    line-height: 1.5;
    color: #334155;
    white-space: pre-wrap;
    word-break: break-all;
}

.task-detail-block.warning .task-detail-text {
    color: #b91c1c;
    background: #fef2f2;
    padding: 0.5rem;
    border-radius: 0.25rem;
}

.task-detail-footer {
    margin-top: 1rem;
    font-size: 0.75rem;
    color: #94a3b8;
    border-top: 1px dashed #e2e8f0;
    padding-top: 0.5rem;
}
"""


# ============================================================
# 页面模板
# ============================================================

def render_base(
    title: str,
    content: str,
    extra_css: str = "",
    extra_js: str = ""
) -> str:
    """
    渲染基础 HTML 模板
    
    Args:
        title: 页面标题
        content: 页面内容 HTML
        extra_css: 额外的 CSS 样式
        extra_js: 额外的 JavaScript
    """
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{html.escape(title)}</title>
  <style>{BASE_CSS}{extra_css}</style>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
</head>
<body>
  {content}
  {extra_js}
</body>
</html>"""


def render_toast(message: str, toast_type: str = "success") -> str:
    """
    渲染 Toast 通知
    
    Args:
        message: 通知消息
        toast_type: 类型 (success, error, warning)
    """
    icon_map = {
        "success": "✅",
        "error": "❌",
        "warning": "⚠️"
    }
    icon = icon_map.get(toast_type, "ℹ️")
    type_class = f" {toast_type}" if toast_type != "success" else ""
    
    return f"""
    <div id="toast" class="toast show{type_class}">
        <span class="icon">{icon}</span> {html.escape(message)}
    </div>
    <script>
        setTimeout(() => {{
            document.getElementById('toast').classList.remove('show');
        }}, 3000);
    </script>
    """


def render_config_page(
    stock_list: str,
    env_filename: str,
    message: Optional[str] = None
) -> bytes:
    """
    渲染配置页面
    
    Args:
        stock_list: 当前自选股列表
        env_filename: 环境文件名
        message: 可选的提示消息
    """
    safe_value = html.escape(stock_list)
    toast_html = render_toast(message) if message else ""
    
    # 分析组件的 JavaScript - 支持多任务
    analysis_js = """
<script>
    // 全局变量
    const tasks = new Map();
    const openDetails = new Set();
    let pollInterval = null;
    const MAX_POLL_COUNT = 120;
    const POLL_INTERVAL_MS = 3000;
    const MAX_TASKS_DISPLAY = 10;
    
    // 获取 DOM 元素 (每次调用时获取，防止初始化失败)
    function getEl(id) { return document.getElementById(id); }
    
    // 初始化事件监听
    window.addEventListener('load', function() {
        // A股输入框
        const inputA = getEl('code_a');
        if (inputA) {
            inputA.addEventListener('input', function(e) {
                this.value = this.value.replace(/\D/g, '').slice(0, 6);
            });
            inputA.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') submitAnalysis('a');
            });
        }
        
        // 港股输入框
        const inputHK = getEl('code_hk');
        if (inputHK) {
            inputHK.addEventListener('input', function(e) {
                this.value = this.value.replace(/\D/g, '').slice(0, 5);
            });
            inputHK.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') submitAnalysis('hk');
            });
        }
        
        renderAllTasks();
    });

    // 格式化时间
    function formatTime(isoString) {
        if (!isoString) return '-';
        const date = new Date(isoString);
        return date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit', second: '2-digit'});
    }
    
    // 计算耗时
    function calcDuration(start, end) {
        if (!start) return '-';
        const startTime = new Date(start).getTime();
        const endTime = end ? new Date(end).getTime() : Date.now();
        const seconds = Math.floor((endTime - startTime) / 1000);
        if (seconds < 60) return seconds + 's';
        const minutes = Math.floor(seconds / 60);
        return minutes + 'm' + (seconds % 60) + 's';
    }
    
    // 获取建议样式
    function getAdviceClass(advice) {
        if (!advice) return '';
        if (advice.includes('买') || advice.includes('加仓')) return 'buy';
        if (advice.includes('卖') || advice.includes('减仓')) return 'sell';
        if (advice.includes('持有')) return 'hold';
        return 'wait';
    }
    
    // 渲染所有任务
    function renderAllTasks() {
        const taskList = getEl('task_list');
        if (!taskList) return;
        
        if (tasks.size === 0) {
            taskList.innerHTML = '<div class="task-hint">💡 输入股票代码开始分析</div>';
            return;
        }
        
        let html = '';
        const sortedTasks = Array.from(tasks.entries())
            .sort((a, b) => (b[1].task?.start_time || '').localeCompare(a[1].task?.start_time || ''));
        
        sortedTasks.slice(0, MAX_TASKS_DISPLAY).forEach(([taskId, taskData]) => {
            html += renderTaskCard(taskId, taskData);
        });
        
        taskList.innerHTML = html;
    }
    
    // 渲染单个任务卡片
    function renderTaskCard(taskId, taskData) {
        const task = taskData.task || {};
        const status = task.status || 'pending';
        const code = task.code || taskId.split('_')[0];
        const result = task.result || {};
        
        let statusIcon = '⏳';
        if (status === 'running') statusIcon = '<span class="spinner"></span>';
        else if (status === 'completed') statusIcon = '✓';
        else if (status === 'failed') statusIcon = '✗';
        
        let resultHtml = '';
        if (status === 'completed' && result.operation_advice) {
            const adviceClass = getAdviceClass(result.operation_advice);
            resultHtml = `<div class="task-result">
                <span class="task-advice ${adviceClass}">${result.operation_advice}</span>
                <span class="task-score">${result.sentiment_score || '-'}分</span>
            </div>`;
        } else if (status === 'failed') {
            resultHtml = '<div class="task-result"><span class="task-advice sell">失败</span></div>';
        }
        
        let detailHtml = '';
        if (status === 'completed' && result.name) {
            const isOpen = openDetails.has(taskId);
            const detailClass = isOpen ? 'task-detail show' : 'task-detail';
            const cleanSummary = (result.analysis_summary || '').replace(/\\n/g, '<br>');
            
            detailHtml = `<div class="${detailClass}" id="detail_${taskId}">
                <div class="task-detail-row"><span class="label">趋势</span><span>${result.trend_prediction || '-'}</span></div>
                
                <div class="task-detail-block">
                    <h4>💡 核心结论</h4>
                    <div class="task-detail-summary">${cleanSummary}</div>
                </div>

                ${(result.buy_price && result.sell_price) ? `
                <div class="task-detail-block" style="background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2);">
                    <h4 style="color: #10b981;">🎯 交易计划</h4>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px;">
                        <div style="text-align: center; padding: 5px; background: rgba(16, 185, 129, 0.1); border-radius: 4px;">
                            <div style="font-size: 0.8rem; color: #059669;">买入区间</div>
                            <div style="font-weight: bold; color: #059669;">${result.buy_price}</div>
                        </div>
                         <div style="text-align: center; padding: 5px; background: rgba(239, 68, 68, 0.1); border-radius: 4px;">
                            <div style="font-size: 0.8rem; color: #dc2626;">止损价格</div>
                            <div style="font-weight: bold; color: #dc2626;">${result.stop_loss_price || '-'}</div>
                        </div>
                        <div style="text-align: center; padding: 5px; background: rgba(245, 158, 11, 0.1); border-radius: 4px;">
                            <div style="font-size: 0.8rem; color: #d97706;">目标止盈</div>
                            <div style="font-weight: bold; color: #d97706;">${result.sell_price}</div>
                        </div>
                    </div>
                </div>` : ''}

                ${(result.short_term_outlook || result.medium_term_outlook) ? `
                <div class="task-detail-block">
                    <h4>🔮 走势预判</h4>
                    <div style="margin-bottom: 8px;">
                        <div style="font-size: 0.9rem; font-weight: bold; color: var(--text-color);">⚡️ 短期 (1-3日)</div>
                        <div class="task-detail-text">${result.short_term_outlook || '-'}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9rem; font-weight: bold; color: var(--text-color);">📅 中期 (1-2周)</div>
                        <div class="task-detail-text">${result.medium_term_outlook || '-'}</div>
                    </div>
                </div>` : ''}

                ${result.technical_analysis ? `
                <div class="task-detail-block">
                    <h4>📊 技术面分析</h4>
                    <div class="task-detail-text">${(result.technical_analysis || '').replace(/\\n/g, '<br>')}</div>
                </div>` : ''}

                ${result.fundamental_analysis ? `
                <div class="task-detail-block">
                    <h4>🏢 基本面分析</h4>
                    <div class="task-detail-text">${(result.fundamental_analysis || '').replace(/\\n/g, '<br>')}</div>
                </div>` : ''}

                ${result.news_summary ? `
                <div class="task-detail-block">
                    <h4>📰 消息面摘要</h4>
                    <div class="task-detail-text">${(result.news_summary || '').replace(/\\n/g, '<br>')}</div>
                </div>` : ''}

                ${result.risk_warning ? `
                <div class="task-detail-block warning">
                    <h4>⚠️ 风险提示</h4>
                    <div class="task-detail-text">${(result.risk_warning || '').replace(/\\n/g, '<br>')}</div>
                </div>` : ''}

                </div>` : ''}

                ${(result.plain_talk_short || result.plain_talk_long) ? `
                <div style="margin: 20px 0; border-top: 2px dashed #eee; padding-top: 20px;">
                    <div class="task-detail-block" style="background: linear-gradient(to right, #eff6ff, #ffffff); border-left: 5px solid #2563eb; border-radius: 4px; padding: 15px;">
                        <h4 style="color: #1e40af; border-bottom: none; margin-bottom: 15px; font-size: 1.1rem; display: flex; align-items: center;">
                            <span style="font-size: 1.4rem; margin-right: 8px;">🗣️</span> 
                            深度研报 · 大白话总结
                        </h4>
                        
                        ${result.plain_talk_short ? `
                        <div style="margin-bottom: 12px; padding: 10px; background: rgba(37, 99, 235, 0.05); border-radius: 6px;">
                            <div style="font-weight: bold; color: #1d4ed8; margin-bottom: 4px;">⚡️ 短期怎么做？</div>
                            <div style="color: #333; line-height: 1.6;">${result.plain_talk_short}</div>
                        </div>` : ''}
                        
                        ${result.plain_talk_long ? `
                        <div style="padding: 10px; background: rgba(37, 99, 235, 0.05); border-radius: 6px;">
                            <div style="font-weight: bold; color: #1d4ed8; margin-bottom: 4px;">⏳ 长期怎么拿？</div>
                            <div style="color: #333; line-height: 1.6;">${result.plain_talk_long}</div>
                        </div>` : ''}
                    </div>
                </div>` : ''}
                
                ${result.data_sources ? `
                <div class="task-detail-footer">
                    <span>📚 数据来源: ${result.data_sources}</span>
                </div>` : ''}
            </div>`;
        }
        
        return `<div class="task-card ${status}" id="task_${taskId}" onclick="toggleDetail('${taskId}')">
            <div class="task-status">${statusIcon}</div>
            <div class="task-main">
                <div class="task-title">
                    <span class="code">${code}</span>
                    ${result.name ? '<span class="name">' + result.name + '</span>' : ''}
                </div>
                <div class="task-meta">
                    <span>⏱ ${formatTime(task.start_time)}</span>
                    <span>⏳ ${calcDuration(task.start_time, task.end_time)}</span>
                    <span>${task.report_type === 'full' ? '📊完整' : '📝精简'}</span>
                </div>
            </div>
            ${resultHtml}
            <div class="task-actions">
                ${status === 'completed' ? `<button class="task-btn" onclick="event.stopPropagation();exportToPDF('${taskId}', '${code}', '${result.name || ''}')" title="导出PDF">💾</button>` : ''}
                <button class="task-btn" onclick="event.stopPropagation();removeTask('${taskId}')">×</button>
            </div>
        </div>${detailHtml}`;
    }
    
    // 全局函数：导出PDF
    window.exportToPDF = function(taskId, code, name) {
        const detailEl = getEl('detail_' + taskId);
        if (!detailEl) return;
        
        // 创建临时容器用于生成PDF
        const container = document.createElement('div');
        container.style.padding = '20px';
        container.style.background = 'white';
        container.style.color = '#000';
        
        // 标题头
        const title = `<h3>${code} ${name} - 投资分析报告</h3>`;
        const time = `<div style="color:#666; font-size:0.8rem; margin-bottom:15px;">生成时间: ${new Date().toLocaleString()}</div>`;
        
        // 内容 (克隆详情节点，去除隐藏类)
        const content = detailEl.cloneNode(true);
        content.style.display = 'block';
        content.style.maxHeight = 'none';
        content.style.borderTop = 'none';
        content.style.paddingTop = '0';
        
        container.innerHTML = title + time;
        container.appendChild(content);
        
        // 配置并导出
        const opt = {
            margin: 10,
            filename: `${code}_${name}_分析报告.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };
        
        html2pdf().set(opt).from(container).save().then(() => {
            // 导出完成后无需清理，container未挂载到DOM
        });
    };
    
    // 全局函数：切换详情
    window.toggleDetail = function(taskId) {
        const detail = getEl('detail_' + taskId);
        if (detail) {
            const isShowing = detail.classList.toggle('show');
            if (isShowing) openDetails.add(taskId);
            else openDetails.delete(taskId);
        }
    };
    
    // 全局函数：移除任务
    window.removeTask = function(taskId) {
        tasks.delete(taskId);
        renderAllTasks();
        checkStopPolling();
    };
    
    // 轮询逻辑
    function pollAllTasks() {
        let hasRunning = false;
        tasks.forEach((taskData, taskId) => {
            const status = taskData.task?.status;
            if (status === 'running' || status === 'pending' || !status) {
                hasRunning = true;
                taskData.pollCount = (taskData.pollCount || 0) + 1;
                
                if (taskData.pollCount > MAX_POLL_COUNT) {
                    taskData.task = taskData.task || {};
                    taskData.task.status = 'failed';
                    taskData.task.error = '超时';
                    return;
                }
                
                fetch('/task?id=' + encodeURIComponent(taskId))
                    .then(r => r.json())
                    .then(data => {
                        if (data.success && data.task) {
                            taskData.task = data.task;
                            renderAllTasks();
                        }
                    }).catch(e => console.error(e));
            }
        });
        
        if (!hasRunning) checkStopPolling();
    }
    
    function checkStopPolling() {
        let hasRunning = false;
        tasks.forEach((t) => {
            if (t.task?.status === 'running' || t.task?.status === 'pending') hasRunning = true;
        });
        if (!hasRunning && pollInterval) {
            clearInterval(pollInterval);
            pollInterval = null;
        }
    }
    
    function startPolling() {
        if (!pollInterval) pollInterval = setInterval(pollAllTasks, POLL_INTERVAL_MS);
    }
    
    // 全局提交函数
    window.submitAnalysis = function(type) {
        let codeInput, submitBtn;
        let code = '';
        
        // 根据类型获取元素
        if (type === 'a') {
            codeInput = getEl('code_a');
            submitBtn = getEl('btn_a');
        } else if (type === 'hk') {
            codeInput = getEl('code_hk');
            submitBtn = getEl('btn_hk');
        } else {
            console.error('未知类型');
            return;
        }

        const reportSelect = getEl('report_type');
        
        if (!codeInput || !submitBtn) {
            alert('页面控件加载失败，请刷新');
            return;
        }
        
        const rawValue = codeInput.value.trim();
        
        // 校验逻辑
        if (type === 'a') {
            if (!/^\d{6}$/.test(rawValue)) {
                alert('A股代码必须是 6 位数字，如 600519');
                return;
            }
            code = rawValue;
        } else if (type === 'hk') {
            if (!/^\d{5}$/.test(rawValue)) {
                alert('港股代码必须是 5 位数字，如 00700');
                return;
            }
            code = 'hk' + rawValue;
        }
        
        // 视觉反馈
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = '⏳';
        
        const reportType = reportSelect ? reportSelect.value : 'simple';
        
        fetch('/analysis?code=' + encodeURIComponent(code) + '&report_type=' + encodeURIComponent(reportType))
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    // 创建新任务
                     tasks.set(data.task_id, {
                        task: {
                            code: code,
                            status: 'running',
                            start_time: new Date().toISOString(),
                            report_type: reportType
                        },
                        pollCount: 0
                    });
                    
                    openDetails.add(data.task_id); // 自动展开
                    renderAllTasks();
                    startPolling();
                    codeInput.value = ''; // 清空输入
                    
                    // 立即轮询一次
                    setTimeout(() => {
                        pollAllTasks(); 
                    }, 500);
                } else {
                    alert('提交失败: ' + (data.error || '未知错误'));
                }
            })
            .catch(e => {
                alert('网络请求失败: ' + e.message);
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            });
    };
</script>
"""
    
    content = f"""
  <div class="container">
    <h2>📈 A/H股分析</h2>
    
    <!-- 快速分析区域 -->
    <!-- 快速分析区域 -->
    <div class="analysis-section" style="margin-top: 0; padding-top: 0; border-top: none;">
      
      <!-- A股 -->
      <div class="form-group" style="margin-bottom: 1rem;">
        <label style="font-size: 0.9rem; color: var(--text-light);">🇨🇳 A股</label>
        <div class="input-group">
          <input 
              type="text" 
              id="code_a" 
              placeholder="输入6位代码 (如 600519)"
              maxlength="6"
              autocomplete="off"
              style="font-size: 1rem;"
          />
          <button type="button" id="btn_a" class="btn-analysis" onclick="submitAnalysis('a')">
            🚀 分析
          </button>
        </div>
      </div>

      <!-- 港股 -->
      <div class="form-group" style="margin-bottom: 1rem;">
        <label style="font-size: 0.9rem; color: var(--text-light);">🇭🇰 港股</label>
        <div class="input-group">
          <input 
              type="text" 
              id="code_hk" 
              placeholder="输入5位代码 (如 00700)"
              maxlength="5"
              autocomplete="off"
              style="font-size: 1rem;"
          />
          <button type="button" id="btn_hk" class="btn-analysis" style="background-color: #8b5cf6;" onclick="submitAnalysis('hk')">
            🛸 分析
          </button>
        </div>
      </div>
      
      <!-- 选项 -->
      <div class="form-group" style="margin-bottom: 0.75rem;">
        <select id="report_type" class="report-select" style="width: 100%; text-align: center;" title="选择报告类型">
            <option value="full" selected>📊 完整报告 (默认)</option>
            <option value="simple">📝 精简报告 (极速)</option>
        </select>
      </div>
      
      <!-- 任务列表 -->
      <div id="task_list" class="task-list"></div>
    </div>
    
    <hr class="section-divider">
    
    <!-- 自选股配置区域 -->
    <!-- 市场概览 & 快捷自选 -->
    <!-- 市场概览 & 快捷自选 (Dashboard Grid) -->


    <script>
    // 渲染自选股列表 (removed)
    </script>
    
    <div class="footer">
      <p style="margin: 0; margin-bottom: 0.5rem;">⚠️ 炒股有风险，仅供参考</p>
      <p style="margin: 0; font-size: 0.8rem; opacity: 0.8;">⏳ 分析需要5分钟左右，可以多次执行分析不同股票代码</p>
    </div>
  </div>
  
  {toast_html}
  {analysis_js}
"""
    
    page = render_base(
        title="A/H股自选配置 | WebUI",
        content=content
    )
    return page.encode("utf-8")


def render_error_page(
    status_code: int,
    message: str,
    details: Optional[str] = None
) -> bytes:
    """
    渲染错误页面
    
    Args:
        status_code: HTTP 状态码
        message: 错误消息
        details: 详细信息
    """
    details_html = f"<p class='text-muted'>{html.escape(details)}</p>" if details else ""
    
    content = f"""
  <div class="container" style="text-align: center;">
    <h2>😵 {status_code}</h2>
    <p>{html.escape(message)}</p>
    {details_html}
    <a href="/" style="color: var(--primary); text-decoration: none;">← 返回首页</a>
  </div>
"""
    
    page = render_base(
        title=f"错误 {status_code}",
        content=content
    )
    return page.encode("utf-8")
