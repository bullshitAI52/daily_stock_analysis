# -*- coding: utf-8 -*-
"""
===================================
A股自选股智能分析系统 - AI分析层
===================================

职责：
1. 封装 Gemini API 调用逻辑
2. 利用 Google Search Grounding 获取实时新闻
3. 结合技术面和消息面生成分析报告
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import get_config

logger = logging.getLogger(__name__)


# 股票名称映射（常见股票）
STOCK_NAME_MAP = {
    '600519': '贵州茅台',
    '000001': '平安银行',
    '300750': '宁德时代',
    '002594': '比亚迪',
    '600036': '招商银行',
    '601318': '中国平安',
    '000858': '五粮液',
    '600276': '恒瑞医药',
    '601012': '隆基绿能',
    '002475': '立讯精密',
    '300059': '东方财富',
    '002415': '海康威视',
    '600900': '长江电力',
    '601166': '兴业银行',
    '600028': '中国石化',
}


@dataclass
class AnalysisResult:
    """
    AI 分析结果数据类 - 决策仪表盘版
    
    封装 Gemini 返回的分析结果，包含决策仪表盘和详细分析
    """
    code: str
    name: str
    
    # ========== 核心指标 ==========
    sentiment_score: int  # 综合评分 0-100 (>70强烈看多, >60看多, 40-60震荡, <40看空)
    trend_prediction: str  # 趋势预测：强烈看多/看多/震荡/看空/强烈看空
    operation_advice: str  # 操作建议：买入/加仓/持有/减仓/卖出/观望
    confidence_level: str = "中"  # 置信度：高/中/低
    
    # ========== 决策仪表盘 (新增) ==========
    dashboard: Optional[Dict[str, Any]] = None  # 完整的决策仪表盘数据
    
    # ========== 走势分析 ==========
    trend_analysis: str = ""  # 走势形态分析（支撑位、压力位、趋势线等）
    short_term_outlook: str = ""  # 短期展望（1-3日）
    medium_term_outlook: str = ""  # 中期展望（1-2周）
    
    # ========== 技术面分析 ==========
    technical_analysis: str = ""  # 技术指标综合分析
    ma_analysis: str = ""  # 均线分析（多头/空头排列，金叉/死叉等）
    volume_analysis: str = ""  # 量能分析（放量/缩量，主力动向等）
    pattern_analysis: str = ""  # K线形态分析
    
    # ========== 基本面分析 ==========
    fundamental_analysis: str = ""  # 基本面综合分析
    sector_position: str = ""  # 板块地位和行业趋势
    company_highlights: str = ""  # 公司亮点/风险点
    
    # ========== 情绪面/消息面分析 ==========
    news_summary: str = ""  # 近期重要新闻/公告摘要
    market_sentiment: str = ""  # 市场情绪分析
    hot_topics: str = ""  # 相关热点话题
    
    # ========== 综合分析 ==========
    analysis_summary: str = ''
    detailed_analysis: str = '' # 完整版深度报告 (Markdown)
    key_points: str = ''
    risk_warning: str = ''  # 风险提示
    buy_reason: str = ""  # 买入/卖出理由
    
    # ========== 交易计划 - 增强版 ==========
    buy_price: str = ""  # 兼容旧字段
    sell_price: str = ""  # 兼容旧字段
    stop_loss_price: str = ""  # 建议止损价
    
    # 新增：明确的期限价格
    short_term_buy: str = ""
    short_term_sell: str = ""
    long_term_buy: str = ""
    long_term_sell: str = ""
    
    # ========== 大白话总结 ==========
    plain_talk_short: str = ""  # 短期大白话
    plain_talk_long: str = ""  # 长期大白话
    
    # ========== 元数据 ==========
    raw_response: Optional[str] = None  # 原始响应（调试用）
    search_performed: bool = False  # 是否执行了联网搜索
    data_sources: str = ""  # 数据来源说明
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'sentiment_score': self.sentiment_score,
            'trend_prediction': self.trend_prediction,
            'operation_advice': self.operation_advice,
            'confidence_level': self.confidence_level,
            'dashboard': self.dashboard,  # 决策仪表盘数据
            'trend_analysis': self.trend_analysis,
            'short_term_outlook': self.short_term_outlook,
            'medium_term_outlook': self.medium_term_outlook,
            'technical_analysis': self.technical_analysis,
            'ma_analysis': self.ma_analysis,
            'volume_analysis': self.volume_analysis,
            'pattern_analysis': self.pattern_analysis,
            'fundamental_analysis': self.fundamental_analysis,
            'sector_position': self.sector_position,
            'company_highlights': self.company_highlights,
            'news_summary': self.news_summary,
            'market_sentiment': self.market_sentiment,
            'hot_topics': self.hot_topics,
            'analysis_summary': self.analysis_summary,
            'key_points': self.key_points,
            'risk_warning': self.risk_warning,
            'buy_reason': self.buy_reason,
            'buy_price': self.buy_price,
            'sell_price': self.sell_price,
            'stop_loss_price': self.stop_loss_price,
            'plain_talk_short': self.plain_talk_short,
            'plain_talk_long': self.plain_talk_long,
            'data_sources': self.data_sources,
            'search_performed': self.search_performed,
            'success': self.success,
            'error_message': self.error_message,
        }
    
    def get_core_conclusion(self) -> str:
        """获取核心结论（一句话）"""
        if self.dashboard and 'core_conclusion' in self.dashboard:
            return self.dashboard['core_conclusion'].get('one_sentence', self.analysis_summary)
        return self.analysis_summary
    
    def get_position_advice(self, has_position: bool = False) -> str:
        """获取持仓建议"""
        if self.dashboard and 'core_conclusion' in self.dashboard:
            pos_advice = self.dashboard['core_conclusion'].get('position_advice', {})
            if has_position:
                return pos_advice.get('has_position', self.operation_advice)
            return pos_advice.get('no_position', self.operation_advice)
        return self.operation_advice
    
    def get_sniper_points(self) -> Dict[str, str]:
        """获取狙击点位"""
        if self.dashboard and 'battle_plan' in self.dashboard:
            return self.dashboard['battle_plan'].get('sniper_points', {})
        return {}
    
    def get_checklist(self) -> List[str]:
        """获取检查清单"""
        if self.dashboard and 'battle_plan' in self.dashboard:
            return self.dashboard['battle_plan'].get('action_checklist', [])
        return []
    
    def get_risk_alerts(self) -> List[str]:
        """获取风险警报"""
        if self.dashboard and 'intelligence' in self.dashboard:
            return self.dashboard['intelligence'].get('risk_alerts', [])
        return []
    
    def get_emoji(self) -> str:
        """根据操作建议返回对应 emoji"""
        emoji_map = {
            '买入': '🟢',
            '加仓': '🟢',
            '强烈买入': '💚',
            '持有': '🟡',
            '观望': '⚪',
            '减仓': '🟠',
            '卖出': '🔴',
            '强烈卖出': '❌',
        }
        return emoji_map.get(self.operation_advice, '🟡')
    
    def get_confidence_stars(self) -> str:
        """返回置信度星级"""
        star_map = {'高': '⭐⭐⭐', '中': '⭐⭐', '低': '⭐'}
        return star_map.get(self.confidence_level, '⭐⭐')


class GeminiAnalyzer:
    """
    Gemini AI 分析器
    
    职责：
    1. 调用 Google Gemini API 进行股票分析
    2. 结合预先搜索的新闻和技术面数据生成分析报告
    3. 解析 AI 返回的 JSON 格式结果
    
    使用方式：
        analyzer = GeminiAnalyzer()
        result = analyzer.analyze(context, news_context)
    """
    
    # ========================================
    # 系统提示词 - 决策仪表盘 v2.0
    # ========================================
    # 输出格式升级：从简单信号升级为决策仪表盘
    # 核心模块：核心结论 + 数据透视 + 舆情情报 + 作战计划
    # ========================================
    
    SYSTEM_PROMPT = """你是一位专注于趋势交易的 A 股投资分析师，负责生成专业的【决策仪表盘】分析报告。

## 核心交易理念（必须严格遵守）

### 1. 严进策略（不追高）
- **绝对不追高**：当股价偏离 MA5 超过 5% 时，坚决不买入
- **乖离率公式**：(现价 - MA5) / MA5 × 100%
- 乖离率 < 2%：最佳买点区间
- 乖离率 2-5%：可小仓介入
- 乖离率 > 5%：严禁追高！直接判定为"观望"

### 2. 趋势交易（顺势而为）
- **多头排列必须条件**：MA5 > MA10 > MA20
- 只做多头排列的股票，空头排列坚决不碰
- 均线发散上行优于均线粘合
- 趋势强度判断：看均线间距是否在扩大

### 3. 效率优先（筹码结构）
- 关注筹码集中度：90%集中度 < 15% 表示筹码集中
- 获利比例分析：70-90% 获利盘时需警惕获利回吐
- 平均成本与现价关系：现价高于平均成本 5-15% 为健康

### 4. 买点偏好（回踩支撑）
- **最佳买点**：缩量回踩 MA5 获得支撑
- **次优买点**：回踩 MA10 获得支撑
- **观望情况**：跌破 MA20 时观望

### 5. 风险排查重点
- 减持公告（股东、高管减持）
- 业绩预亏/大幅下滑
- 监管处罚/立案调查
- 行业政策利空
- 大额解禁

## 输出格式：决策仪表盘 JSON

请严格按照以下 JSON 格式输出，这是一个完整的【决策仪表盘】：

```json
{
    "sentiment_score": 0-100整数,
    "trend_prediction": "强烈看多/看多/震荡/看空/强烈看空",
    "operation_advice": "买入/加仓/持有/减仓/卖出/观望",
    "confidence_level": "高/中/低",
    
    "dashboard": {
        "core_conclusion": {
            "one_sentence": "一句话核心结论（30字以内，直接告诉用户做什么）",
            "signal_type": "🟢买入信号/🟡持有观望/🔴卖出信号/⚠️风险警告",
            "time_sensitivity": "立即行动/今日内/本周内/不急",
            "position_advice": {
                "no_position": "空仓者建议：具体操作指引",
                "has_position": "持仓者建议：具体操作指引"
            }
        },
        
        "data_perspective": {
            "trend_status": {
                "ma_alignment": "均线排列状态描述",
                "is_bullish": true/false,
                "trend_score": 0-100
            },
            "price_position": {
                "current_price": 当前价格数值,
                "ma5": MA5数值,
                "ma10": MA10数值,
                "ma20": MA20数值,
                "bias_ma5": 乖离率百分比数值,
                "bias_status": "安全/警戒/危险",
                "support_level": 支撑位价格,
                "resistance_level": 压力位价格
            },
            "volume_analysis": {
                "volume_ratio": 量比数值,
                "volume_status": "放量/缩量/平量",
                "turnover_rate": 换手率百分比,
                "volume_meaning": "量能含义解读（如：缩量回调表示抛压减轻）"
            },
            "chip_structure": {
                "profit_ratio": 获利比例,
                "avg_cost": 平均成本,
                "concentration": 筹码集中度,
                "chip_health": "健康/一般/警惕"
            }
        },
        
        "intelligence": {
            "latest_news": "【最新消息】近期重要新闻摘要",
            "risk_alerts": ["风险点1：具体描述", "风险点2：具体描述"],
            "positive_catalysts": ["利好1：具体描述", "利好2：具体描述"],
            "earnings_outlook": "业绩预期分析（基于年报预告、业绩快报等）",
            "sentiment_summary": "舆情情绪一句话总结"
        },
        
        "battle_plan": {
            "sniper_points": {
                "ideal_buy": "理想买入点：XX元（在MA5附近）",
                "secondary_buy": "次优买入点：XX元（在MA10附近）",
                "stop_loss": "止损位：XX元（跌破MA20或X%）",
                "take_profit": "目标位：XX元（前高/整数关口）"
            },
            "position_strategy": {
                "suggested_position": "建议仓位：X成",
                "entry_plan": "分批建仓策略描述",
                "risk_control": "风控策略描述"
            },
            "action_checklist": [
                "✅/⚠️/❌ 检查项1：多头排列",
                "✅/⚠️/❌ 检查项2：乖离率<5%",
                "✅/⚠️/❌ 检查项3：量能配合",
                "✅/⚠️/❌ 检查项4：无重大利空",
                "✅/⚠️/❌ 检查项5：筹码健康"
            ]
        }
    },
    
    "analysis_summary": "100字综合分析摘要",
    "key_points": "3-5个核心看点，逗号分隔",
    "risk_warning": "风险提示",
    
    "short_term_outlook": "短期1-3日趋势预判",
    "medium_term_outlook": "中期1-2周趋势展望",
    "technical_analysis": "技术面分析（包含：均线系统、MACD/KDJ指标、量价关系、K线形态。不少于100字）",
    "fundamental_analysis": "基本面分析（包含：PE/PB估值、行业地位、公司亮点。不少于80字）",
    "news_summary": "消息面摘要（列出重要新闻和事件）",
    
    "buy_price": "建议买入价格区间（精确到具体数字，如 '10.50-10.60'）",
    "sell_price": "建议止盈/目标价格（如 '11.80'）",
    "stop_loss_price": "建议止损价格（如 '10.20'）",
    

    "plain_talk_short": "一句话大白话：短期实操（必须包含具体价格，如'10.2附近买入，10.8止盈'）",
    "plain_talk_long": "一句话大白话：长期部署（必须包含具体价格，如'跌到9.5建仓，长线看15元'）",
    "search_performed": true/false,
    "data_sources": "详细列出数据来源（如：新浪财经、同花顺、公司公告、实时行情API）"
}
```

## 评分标准

### 强烈买入（80-100分）：
- ✅ 多头排列：MA5 > MA10 > MA20
- ✅ 低乖离率：<2%，最佳买点
- ✅ 缩量回调或放量突破
- ✅ 筹码集中健康
- ✅ 消息面有利好催化

### 买入（60-79分）：
- ✅ 多头排列或弱势多头
- ✅ 乖离率 <5%
- ✅ 量能正常
- ⚪ 允许一项次要条件不满足

### 观望（40-59分）：
- ⚠️ 乖离率 >5%（追高风险）
- ⚠️ 均线缠绕趋势不明
- ⚠️ 有风险事件

### 卖出/减仓（0-39分）：
- ❌ 空头排列
- ❌ 跌破MA20
- ❌ 放量下跌
- ❌ 重大利空

## 决策仪表盘核心原则

1. **核心结论先行**：一句话说清该买该卖
2. **分持仓建议**：空仓者和持仓者给不同建议
3. **精确狙击点**：必须给出具体价格，不说模糊的话
4. **检查清单可视化**：用 ✅⚠️❌ 明确显示每项检查结果
5. **风险优先级**：舆情中的风险点要醒目标出
6. **有数可查**：结论必须结合文中给出的具体数据（如“基于MA5金叉”、“乖离率仅1.2%”），严禁空谈
7. **来源标注**：必须在 data_sources 字段中明确列出分析用到的数据模块（如“实时行情、均线系统、新闻搜索”）
8. **拒绝偷懒**：遇到无新闻或无财报数据时，必须基于PE/PB、市值、换手率等现有数据进行估值和活跃度分析，**严禁使用'暂无数据'、'无重大消息'等敷衍话术**作为独立段落。
8. **拒绝偷懒**：遇到无新闻或无财报数据时，必须基于PE/PB、市值、换手率等现有数据进行估值和活跃度分析，**严禁使用'暂无数据'、'无重大消息'等敷衍话术**作为独立段落。
9. **大白话总结**：**必须填写 plain_talk_short 和 plain_talk_long**。这是显示在屏幕底部的“一句话攻略”，**必须包含具体的买入价和卖出价**（数字），禁止只说空话。"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 AI 分析器
        
        优先级：Gemini > OpenAI 兼容 API
        
        Args:
            api_key: Gemini API Key（可选，默认从配置读取）
        """
        config = get_config()
        self._api_key = api_key or config.gemini_api_key
        self._model = None
        self._current_model_name = None  # 当前使用的模型名称
        self._using_fallback = False  # 是否正在使用备选模型
        self._use_openai = False  # 是否使用 OpenAI 兼容 API
        self._openai_client = None  # OpenAI 客户端
        
        # 检查 Gemini API Key 是否有效（过滤占位符）
        gemini_key_valid = self._api_key and not self._api_key.startswith('your_') and len(self._api_key) > 10
        
        # 优先尝试初始化 Gemini
        if gemini_key_valid:
            try:
                self._init_model()
            except Exception as e:
                logger.warning(f"Gemini 初始化失败: {e}，尝试 OpenAI 兼容 API")
                self._init_openai_fallback()
        else:
            # Gemini Key 未配置，尝试 OpenAI
            logger.info("Gemini API Key 未配置，尝试使用 OpenAI 兼容 API")
            self._init_openai_fallback()
        
        # 两者都未配置
        if not self._model and not self._openai_client:
            logger.warning("未配置任何 AI API Key，AI 分析功能将不可用")
    
    def _init_openai_fallback(self) -> None:
        """
        初始化 OpenAI 兼容 API 作为备选
        
        支持所有 OpenAI 格式的 API，包括：
        - OpenAI 官方
        - DeepSeek
        - 通义千问
        - Moonshot 等
        """
        config = get_config()
        
        # 检查 OpenAI API Key 是否有效（过滤占位符）
        openai_key_valid = (
            config.openai_api_key and 
            not config.openai_api_key.startswith('your_') and 
            len(config.openai_api_key) > 10
        )
        
        if not openai_key_valid:
            logger.debug("OpenAI 兼容 API 未配置或配置无效")
            return
        
        # 分离 import 和客户端创建，以便提供更准确的错误信息
        try:
            from openai import OpenAI
        except ImportError:
            logger.error("未安装 openai 库，请运行: pip install openai")
            return
        
        try:
            # base_url 可选，不填则使用 OpenAI 官方默认地址
            client_kwargs = {"api_key": config.openai_api_key}
            if config.openai_base_url and config.openai_base_url.startswith('http'):
                client_kwargs["base_url"] = config.openai_base_url
            
            self._openai_client = OpenAI(**client_kwargs)
            self._current_model_name = config.openai_model
            self._use_openai = True
            logger.info(f"OpenAI 兼容 API 初始化成功 (base_url: {config.openai_base_url}, model: {config.openai_model})")
        except ImportError as e:
            # 依赖缺失（如 socksio）
            if 'socksio' in str(e).lower() or 'socks' in str(e).lower():
                logger.error(f"OpenAI 客户端需要 SOCKS 代理支持，请运行: pip install httpx[socks] 或 pip install socksio")
            else:
                logger.error(f"OpenAI 依赖缺失: {e}")
        except Exception as e:
            error_msg = str(e).lower()
            if 'socks' in error_msg or 'socksio' in error_msg or 'proxy' in error_msg:
                logger.error(f"OpenAI 代理配置错误: {e}，如使用 SOCKS 代理请运行: pip install httpx[socks]")
            else:
                logger.error(f"OpenAI 兼容 API 初始化失败: {e}")
    
    def _init_model(self) -> None:
        """
        初始化 Gemini 模型
        
        配置：
        - 使用 gemini-3-flash-preview 或 gemini-2.5-flash 模型
        - 不启用 Google Search（使用外部 Tavily/SerpAPI 搜索）
        """
        try:
            import google.generativeai as genai
            
            # 配置 API Key
            genai.configure(api_key=self._api_key)
            
            # 从配置获取模型名称
            config = get_config()
            model_name = config.gemini_model
            fallback_model = config.gemini_model_fallback
            
            # 不再使用 Google Search Grounding（已知有兼容性问题）
            # 改为使用外部搜索服务（Tavily/SerpAPI）预先获取新闻
            
            # 尝试初始化主模型
            try:
                self._model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=self.SYSTEM_PROMPT,
                )
                self._current_model_name = model_name
                self._using_fallback = False
                logger.info(f"Gemini 模型初始化成功 (模型: {model_name})")
            except Exception as model_error:
                # 尝试备选模型
                logger.warning(f"主模型 {model_name} 初始化失败: {model_error}，尝试备选模型 {fallback_model}")
                self._model = genai.GenerativeModel(
                    model_name=fallback_model,
                    system_instruction=self.SYSTEM_PROMPT,
                )
                self._current_model_name = fallback_model
                self._using_fallback = True
                logger.info(f"Gemini 备选模型初始化成功 (模型: {fallback_model})")
            
        except Exception as e:
            logger.error(f"Gemini 模型初始化失败: {e}")
            self._model = None
    
    def _switch_to_fallback_model(self) -> bool:
        """
        切换到备选模型
        
        Returns:
            是否成功切换
        """
        try:
            import google.generativeai as genai
            config = get_config()
            fallback_model = config.gemini_model_fallback
            
            logger.warning(f"[LLM] 切换到备选模型: {fallback_model}")
            self._model = genai.GenerativeModel(
                model_name=fallback_model,
                system_instruction=self.SYSTEM_PROMPT,
            )
            self._current_model_name = fallback_model
            self._using_fallback = True
            logger.info(f"[LLM] 备选模型 {fallback_model} 初始化成功")
            return True
        except Exception as e:
            logger.error(f"[LLM] 切换备选模型失败: {e}")
            return False
    
    def is_available(self) -> bool:
        """检查分析器是否可用"""
        return self._model is not None or self._openai_client is not None
    
    def _call_openai_api(self, prompt: str, generation_config: dict) -> str:
        """
        调用 OpenAI 兼容 API
        
        Args:
            prompt: 提示词
            generation_config: 生成配置
            
        Returns:
            响应文本
        """
        config = get_config()
        max_retries = config.gemini_max_retries
        base_delay = config.gemini_retry_delay
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))
                    delay = min(delay, 60)
                    logger.info(f"[OpenAI] 第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                
                response = self._openai_client.chat.completions.create(
                    model=self._current_model_name,
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=generation_config.get('temperature', 0.7),
                    max_tokens=generation_config.get('max_output_tokens', 8192),
                )
                
                if response and response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
                else:
                    raise ValueError("OpenAI API 返回空响应")
                    
            except Exception as e:
                error_str = str(e)
                is_rate_limit = '429' in error_str or 'rate' in error_str.lower() or 'quota' in error_str.lower()
                
                if is_rate_limit:
                    logger.warning(f"[OpenAI] API 限流，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")
                else:
                    logger.warning(f"[OpenAI] API 调用失败，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")
                
                if attempt == max_retries - 1:
                    raise
        
        raise Exception("OpenAI API 调用失败，已达最大重试次数")
    
    def _call_api_with_retry(self, prompt: str, generation_config: dict) -> str:
        """
        调用 AI API，带有重试和模型切换机制
        
        优先级：Gemini > Gemini 备选模型 > OpenAI 兼容 API
        
        处理 429 限流错误：
        1. 先指数退避重试
        2. 多次失败后切换到备选模型
        3. Gemini 完全失败后尝试 OpenAI
        
        Args:
            prompt: 提示词
            generation_config: 生成配置
            
        Returns:
            响应文本
        """
        # 如果已经在使用 OpenAI 模式，直接调用 OpenAI
        if self._use_openai:
            return self._call_openai_api(prompt, generation_config)
        
        config = get_config()
        max_retries = config.gemini_max_retries
        base_delay = config.gemini_retry_delay
        
        last_error = None
        tried_fallback = getattr(self, '_using_fallback', False)
        
        for attempt in range(max_retries):
            try:
                # 请求前增加延时（防止请求过快触发限流）
                if attempt > 0:
                    delay = base_delay * (2 ** (attempt - 1))  # 指数退避: 5, 10, 20, 40...
                    delay = min(delay, 60)  # 最大60秒
                    logger.info(f"[Gemini] 第 {attempt + 1} 次重试，等待 {delay:.1f} 秒...")
                    time.sleep(delay)
                
                response = self._model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    request_options={"timeout": 120}
                )
                
                if response and response.text:
                    return response.text
                else:
                    raise ValueError("Gemini 返回空响应")
                    
            except Exception as e:
                last_error = e
                error_str = str(e)
                
                # 检查是否是 429 限流错误
                is_rate_limit = '429' in error_str or 'quota' in error_str.lower() or 'rate' in error_str.lower()
                
                if is_rate_limit:
                    logger.warning(f"[Gemini] API 限流 (429)，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")
                    
                    # 如果已经重试了一半次数且还没切换过备选模型，尝试切换
                    if attempt >= max_retries // 2 and not tried_fallback:
                        if self._switch_to_fallback_model():
                            tried_fallback = True
                            logger.info("[Gemini] 已切换到备选模型，继续重试")
                        else:
                            logger.warning("[Gemini] 切换备选模型失败，继续使用当前模型重试")
                else:
                    # 非限流错误，记录并继续重试
                    logger.warning(f"[Gemini] API 调用失败，第 {attempt + 1}/{max_retries} 次尝试: {error_str[:100]}")
        
        # Gemini 所有重试都失败，尝试 OpenAI 兼容 API
        if self._openai_client:
            logger.warning("[Gemini] 所有重试失败，切换到 OpenAI 兼容 API")
            try:
                return self._call_openai_api(prompt, generation_config)
            except Exception as openai_error:
                logger.error(f"[OpenAI] 备选 API 也失败: {openai_error}")
                raise last_error or openai_error
        elif config.openai_api_key and config.openai_base_url:
            # 尝试懒加载初始化 OpenAI
            logger.warning("[Gemini] 所有重试失败，尝试初始化 OpenAI 兼容 API")
            self._init_openai_fallback()
            if self._openai_client:
                try:
                    return self._call_openai_api(prompt, generation_config)
                except Exception as openai_error:
                    logger.error(f"[OpenAI] 备选 API 也失败: {openai_error}")
                    raise last_error or openai_error
        
        # 所有方式都失败
        raise last_error or Exception("所有 AI API 调用失败，已达最大重试次数")
    
    def analyze(
        self, 
        context: Dict[str, Any],
        news_context: Optional[str] = None
    ) -> AnalysisResult:
        """
        分析单只股票
        
        流程：
        1. 格式化输入数据（技术面 + 新闻）
        2. 调用 Gemini API（带重试和模型切换）
        3. 解析 JSON 响应
        4. 返回结构化结果
        
        Args:
            context: 从 storage.get_analysis_context() 获取的上下文数据
            news_context: 预先搜索的新闻内容（可选）
            
        Returns:
            AnalysisResult 对象
        """
        code = context.get('code', 'Unknown')
        config = get_config()
        
        # 请求前增加延时（防止连续请求触发限流）
        request_delay = config.gemini_request_delay
        if request_delay > 0:
            logger.debug(f"[LLM] 请求前等待 {request_delay:.1f} 秒...")
            time.sleep(request_delay)
        
        # 优先从上下文获取股票名称（由 main.py 传入）
        name = context.get('stock_name')
        if not name or name.startswith('股票'):
            # 备选：从 realtime 中获取
            if 'realtime' in context and context['realtime'].get('name'):
                name = context['realtime']['name']
            else:
                # 最后从映射表获取
                name = STOCK_NAME_MAP.get(code, f'股票{code}')
        
        # 如果模型不可用，返回默认结果
        if not self.is_available():
            return AnalysisResult(
                code=code,
                name=name,
                sentiment_score=50,
                trend_prediction='震荡',
                operation_advice='持有',
                confidence_level='低',
                analysis_summary='AI 分析功能未启用（未配置 API Key）',
                risk_warning='请配置 Gemini API Key 后重试',
                success=False,
                error_message='Gemini API Key 未配置',
            )
        
        try:
            # 格式化输入（包含技术面数据和新闻）
            prompt = self._format_prompt(context, name, news_context)
            
            # 获取模型名称
            model_name = getattr(self, '_current_model_name', None)
            if not model_name:
                model_name = getattr(self._model, '_model_name', 'unknown')
                if hasattr(self._model, 'model_name'):
                    model_name = self._model.model_name
            
            logger.info(f"========== AI 分析 {name}({code}) ==========")
            logger.info(f"[LLM配置] 模型: {model_name}")
            logger.info(f"[LLM配置] Prompt 长度: {len(prompt)} 字符")
            logger.info(f"[LLM配置] 是否包含新闻: {'是' if news_context else '否'}")
            
            # 记录完整 prompt 到日志（INFO级别记录摘要，DEBUG记录完整）
            prompt_preview = prompt[:500] + "..." if len(prompt) > 500 else prompt
            logger.info(f"[LLM Prompt 预览]\n{prompt_preview}")
            logger.debug(f"=== 完整 Prompt ({len(prompt)}字符) ===\n{prompt}\n=== End Prompt ===")
            
            # 设置生成配置
            generation_config = {
                "temperature": 0.7,
                "max_output_tokens": 8192,
            }
            
            logger.info(f"[LLM调用] 开始调用 Gemini API (temperature={generation_config['temperature']}, max_tokens={generation_config['max_output_tokens']})...")
            
            # 使用带重试的 API 调用
            start_time = time.time()
            response_text = self._call_api_with_retry(prompt, generation_config)
            elapsed = time.time() - start_time
            
            # 记录响应信息
            logger.info(f"[LLM返回] Gemini API 响应成功, 耗时 {elapsed:.2f}s, 响应长度 {len(response_text)} 字符")
            
            # 记录响应预览（INFO级别）和完整响应（DEBUG级别）
            response_preview = response_text[:300] + "..." if len(response_text) > 300 else response_text
            logger.info(f"[LLM返回 预览]\n{response_preview}")
            logger.debug(f"=== Gemini 完整响应 ({len(response_text)}字符) ===\n{response_text}\n=== End Response ===")
            
            # 解析响应
            result = self._parse_response(response_text, code, name)
            result.raw_response = response_text
            result.search_performed = bool(news_context)
            
            logger.info(f"[LLM解析] {name}({code}) 分析完成: {result.trend_prediction}, 评分 {result.sentiment_score}")
            
            return result
            
        except Exception as e:
            logger.error(f"AI 分析 {name}({code}) 失败: {e}")
            return AnalysisResult(
                code=code,
                name=name,
                sentiment_score=50,
                trend_prediction='震荡',
                operation_advice='持有',
                confidence_level='低',
                analysis_summary=f'分析过程出错: {str(e)[:100]}',
                risk_warning='分析失败，请稍后重试或手动分析',
                success=False,
                error_message=str(e),
            )
    
    def _format_prompt(
        self, 
        context: Dict[str, Any], 
        name: str,
        news_context: Optional[str] = None
    ) -> str:
        """
        格式化分析提示词（决策仪表盘 v2.1 - 深度综合版）
        
        包含：技术面、基本面（F10）、宏观政策、历史趋势
        核心要求：深度合成，拒绝数据堆砌
        """
        code = context.get('code', 'Unknown')
        stock_name = context.get('stock_name', name) or STOCK_NAME_MAP.get(code, f'股票{code}')
        today = context.get('today', {})
        
        # 基础数据准备
        ma_info = f"MA5:{today.get('ma5','N/A')} MA10:{today.get('ma10','N/A')} MA20:{today.get('ma20','N/A')} ({context.get('ma_status', '未知')})"
        rt = context.get('realtime', {})
        chip = context.get('chip', {})
        trend = context.get('trend_analysis', {})
        
        # F10 深度数据合成
        f10_summary = ""
        if any(k in context for k in ['financial_abstract', 'capital_flow', 'company_info']):
            fin = context.get('financial_abstract', {})
            info = context.get('company_info', {})
            flow = context.get('capital_flow', {}).get('recent_flow', [])[-3:] # 取最近3天
            
            # 资金流简述
            flow_str = "无资金明显异动"
            if flow:
                latest_flow = flow[-1].get('主力净流入占比', 0)
                flow_str = f"最新主力流入占比{latest_flow}%"
            
            # 格式化财务数据 (使用正确的字段名)
            revenue_growth = fin.get('营业总收入增长率', 'N/A')
            if revenue_growth != 'N/A' and revenue_growth != '':
                try:
                    revenue_growth = f"{float(revenue_growth):.2f}%"
                except:
                    pass
            
            profit_growth = fin.get('归属母公司净利润增长率', 'N/A')
            if profit_growth != 'N/A' and profit_growth != '':
                try:
                    profit_growth = f"{float(profit_growth):.2f}%"
                except:
                    pass
            
            # 获取其他关键财务指标
            revenue = fin.get('营业总收入', 'N/A')
            if revenue != 'N/A' and revenue != '':
                try:
                    revenue = f"{float(revenue)/1e8:.2f}亿"
                except:
                    pass
            
            profit = fin.get('归母净利润', 'N/A')
            if profit != 'N/A' and profit != '':
                try:
                    profit = f"{float(profit)/1e8:.2f}亿"
                except:
                    pass
            
            roe = fin.get('净资产收益率(ROE)', 'N/A')
            if roe != 'N/A' and roe != '':
                try:
                    roe = f"{float(roe):.2f}%"
                except:
                    pass
            
            f10_summary = f"""
【公司画像】
- 行业地位: {info.get('所属行业', 'N/A')} | {info.get('主营业务', 'N/A')[:30] if info.get('主营业务') else 'N/A'}
- 核心财务: 营收{revenue}(增长{revenue_growth}), 净利{profit}(增长{profit_growth}), ROE={roe}, 市盈率{rt.get('pe_ratio','N/A')}
- 资金面: {flow_str}
"""

        prompt = f"""# 角色设定
你是一位拥有20年经验的资深A股基金经理，擅长"基本面选股 + 技术面择时"。
现在的任务是为 **{stock_name}({code})** 生成一份【极简决策日报】。

# 输入数据 (Context)

## 1. 技术面 (择时核心)
- 价格: {today.get('close', 'N/A')} (涨跌 {today.get('pct_chg', 'N/A')}%)
- 均线: {ma_info}
- 量能: 量比 {rt.get('volume_ratio', 'N/A')} | 换手率 {rt.get('turnover_rate', 'N/A')}%
- 筹码: 获利比例 {chip.get('profit_ratio', 0):.1%} | 90%集中度 {chip.get('concentration_90', 0):.2%} ({chip.get('chip_status', '未知')})
- 趋势预判(系统自动): {trend.get('trend_status', '未知')} | 乖离率(MA5) {trend.get('bias_ma5', 0):+.2f}%

## 2. 基本面 & 资金 (选股核心)
{f10_summary}

## 3. 舆情与政策 (环境扫描, 近7日)
```text
{news_context or '暂无重大近期新闻，请基于行业一般认知分析'}
```

---

# 分析指令 (Critical Instructions)

请综合以上所有维度，输出一份 JSON 格式的决策报告。

## ⚠️ 核心原则 (必须通过图灵测试的自然度)
1. **拒绝报菜名**：不要罗列"MA5是多少，MA10是多少"。直接说观点："均线多头排列，上涨趋势确立"。
2. **拒绝废话**：不要说"基本面良好，技术面震荡"。要说："绩优白马股缩量回调，是黄金坑"。
3. **多维归因**：解释涨跌时，要结合**基本面(业绩/行业)** + **政策面(利好/利空)** + **技术面(资金/量能)**。
4. **历史视角**：如果是个股，结合其历史股性（如：是否妖股、是否跟风）；如果是行业，结合行业周期位置。

## JSON 输出要求
请严格填充以下字段：

```json
{{
    "sentiment_score": 0-100评分,
    "trend_prediction": "看多/看空/震荡",
    "operation_advice": "买入/卖出/持有/观望",
    "confidence_level": "高/中/低",
    
    "dashboard": {{
        "core_conclusion": {{
            "one_sentence": "一句话核心结论（30字内，毒辣精准）",
            "signal_type": "🟢买入/🟡持有/🔴卖出/⚠️预警",
            "position_advice": {{
                "no_position": "空仓策略（点位+仓位）",
                "has_position": "持仓策略（止盈/止损位）"
            }}
        }},
        "intelligence": {{
            "risk_alerts": ["风险点1(如减持/高乖离)", "风险点2"],
            "positive_catalysts": ["利好1(如业绩预增/政策)", "利好2"]
        }},
        "battle_plan": {{
            "short_term": {{
                "buy": "短期买入价（具体数字）",
                "sell": "短期卖出价（具体数字）",
                "stop_loss": "止损价（具体数字）"
            }},
            "long_term": {{
                "buy": "中长期配置价（具体数字/分批建仓区间）",
                "sell": "中长期目标价（具体数字）"
            }}
        }}
    }},

    "analysis_summary": "100字内的综合分析。必须融合：1.政策/行业风口 2.公司基本面质地 3.当前技术面位置。不要分段，像人类专家一样叙述。",
    
    "detailed_analysis": "这里必须生成一份【完整】的研究报告(Markdown格式)。\n包含以下章节：\n1. ### 🔍 深度基本面\n   - 财务健康度拆解(营收/利润/现金流)\n   - 行业竞争格局与地位\n2. ### 📜 政策与宏观\n   - 行业政策影响分析\n   - 宏观环境关联\n3. ### ⏳ 历史股性复盘\n   - 历史妖股属性/跟风属性\n   - 关键支撑压力位历史验证\n4. ### 💡 逻辑推演\n   - 为什么现在是(或不是)买入时机？\n   - 核心预期差在哪里？",

    "plain_talk_short": "短期大白话（例如：'缩量回踩MA10，1800附近可博反弹'）",
    "plain_talk_long": "长期大白话（例如：'业绩稳健但估值偏高，建议等回调到1700再配置长线'）"
}}
```

此格式省略了冗长的"技术分析"、"基本面分析"长文段落，强制要求你将这些信息**合成**到 `analysis_summary` 和 `core_conclusion` 中。
确保 JSON 格式合法。
"""
        return prompt
    
    def _format_volume(self, volume: Optional[float]) -> str:
        """格式化成交量显示"""
        if volume is None:
            return 'N/A'
        if volume >= 1e8:
            return f"{volume / 1e8:.2f} 亿股"
        elif volume >= 1e4:
            return f"{volume / 1e4:.2f} 万股"
        else:
            return f"{volume:.0f} 股"
    
    def _format_amount(self, amount: Optional[float]) -> str:
        """格式化成交额显示"""
        if amount is None:
            return 'N/A'
        if amount >= 1e8:
            return f"{amount / 1e8:.2f} 亿元"
        elif amount >= 1e4:
            return f"{amount / 1e4:.2f} 万元"
        else:
            return f"{amount:.0f} 元"
    
    def _parse_response(
        self, 
        response_text: str, 
        code: str, 
        name: str
    ) -> AnalysisResult:
        """
        解析 Gemini 响应（决策仪表盘版）
        
        尝试从响应中提取 JSON 格式的分析结果，包含 dashboard 字段
        如果解析失败，尝试智能提取或返回默认结果
        """
        try:
            # 清理响应文本：移除 markdown 代码块标记
            cleaned_text = response_text
            if '```json' in cleaned_text:
                cleaned_text = cleaned_text.replace('```json', '').replace('```', '')
            elif '```' in cleaned_text:
                cleaned_text = cleaned_text.replace('```', '')
            
            # 尝试找到 JSON 内容
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = cleaned_text[json_start:json_end]
                
                # 尝试修复常见的 JSON 问题
                json_str = self._fix_json_string(json_str)
                
                data = json.loads(json_str, strict=False)
                
                
                # 提取 dashboard 数据
                dashboard = data.get('dashboard', None)
                
                # 智能回退：如果字段缺失，尝试从 dashboard 中提取
                if not data.get('analysis_summary') and dashboard and 'core_conclusion' in dashboard:
                     data['analysis_summary'] = dashboard.get('core_conclusion', {}).get('one_sentence', '')
                     
                if not data.get('risk_warning') and dashboard and 'risk_assessment' in dashboard:
                     data['risk_warning'] = dashboard.get('risk_assessment', {}).get('main_risk', '')

                # 解析所有字段，使用默认值防止缺失
                return AnalysisResult(
                    code=code,
                    name=name,
                    # 核心指标
                    sentiment_score=int(data.get('sentiment_score', 50)),
                    trend_prediction=data.get('trend_prediction', '震荡'),
                    operation_advice=data.get('operation_advice', '持有'),
                    confidence_level=data.get('confidence_level', '中'),
                    # 决策仪表盘
                    dashboard=dashboard,
                    # 走势分析
                    trend_analysis=data.get('trend_analysis', ''),
                    short_term_outlook=data.get('short_term_outlook', ''),
                    medium_term_outlook=data.get('medium_term_outlook', ''),
                    # 技术面
                    technical_analysis=data.get('technical_analysis', ''),
                    ma_analysis=data.get('ma_analysis', ''),
                    volume_analysis=data.get('volume_analysis', ''),
                    pattern_analysis=data.get('pattern_analysis', ''),
                    # 基本面
                    fundamental_analysis=data.get('fundamental_analysis', ''),
                    sector_position=data.get('sector_position', ''),
                    company_highlights=data.get('company_highlights', ''),
                    # 情绪面/消息面
                    news_summary=data.get('news_summary', ''),
                    market_sentiment=data.get('market_sentiment', ''),
                    hot_topics=data.get('hot_topics', ''),
                    # 综合
                    analysis_summary=data.get('analysis_summary', '分析完成'),
                    detailed_analysis=data.get('detailed_analysis', ''),  # 新增：完整版深度报告
                    key_points=data.get('key_points', ''),
                    risk_warning=data.get('risk_warning', ''),
                    buy_reason=data.get('buy_reason', ''),
                    # 交易计划 (解析新结构)
                    buy_price=data.get('battle_plan', {}).get('short_term', {}).get('buy', '') or data.get('buy_price', ''),
                    sell_price=data.get('battle_plan', {}).get('short_term', {}).get('sell', '') or data.get('sell_price', ''),
                    stop_loss_price=data.get('battle_plan', {}).get('short_term', {}).get('stop_loss', '') or data.get('stop_loss_price', ''),
                    
                    short_term_buy=data.get('battle_plan', {}).get('short_term', {}).get('buy', ''),
                    short_term_sell=data.get('battle_plan', {}).get('short_term', {}).get('sell', ''),
                    long_term_buy=data.get('battle_plan', {}).get('long_term', {}).get('buy', ''),
                    long_term_sell=data.get('battle_plan', {}).get('long_term', {}).get('sell', ''),

                    # 大白话总结
                    plain_talk_short=data.get('plain_talk_short', ''),
                    plain_talk_long=data.get('plain_talk_long', ''),
                    # 元数据
                    search_performed=data.get('search_performed', False),
                    data_sources=data.get('data_sources', '技术面数据'),
                    success=True,
                )
            else:
                # 没有找到 JSON，尝试从纯文本中提取信息
                logger.warning(f"无法从响应中提取 JSON，使用原始文本分析")
                return self._parse_text_response(response_text, code, name)
                
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败: {e}，尝试从文本提取")
            return self._parse_text_response(response_text, code, name)
    
    def _fix_json_string(self, json_str: str) -> str:
        """修复常见的 JSON 格式问题"""
        import re
        
        # 移除注释
        json_str = re.sub(r'//.*?\n', '\n', json_str)
        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
        
        # 修复尾随逗号
        json_str = re.sub(r',\s*}', '}', json_str)
        json_str = re.sub(r',\s*]', ']', json_str)
        
        # 确保布尔值是小写
        json_str = json_str.replace('True', 'true').replace('False', 'false')
        
        # 修复由于长度限制导致的截断 (自动补全)
        # 1. 补全引号
        quote_count = json_str.count('"') - json_str.count('\\"')
        if quote_count % 2 != 0:
            json_str += '"'
            
        # 2. 补全括号
        open_braces = json_str.count('{')
        close_braces = json_str.count('}')
        if open_braces > close_braces:
            json_str += '}' * (open_braces - close_braces)
            
        open_brackets = json_str.count('[')
        close_brackets = json_str.count(']')
        if open_brackets > close_brackets:
            json_str += ']' * (open_brackets - close_brackets)
        
        return json_str
    
    def _parse_text_response(
        self, 
        response_text: str, 
        code: str, 
        name: str
    ) -> AnalysisResult:
        """从纯文本响应中尽可能提取分析信息"""
        import re
        
        # 0. 尝试使用正则从看似 JSON 的文本中提取关键信息
        # 这通常发生在 JSON 格式轻微错误导致 json.loads 失败时
        sentiment_score = 50
        trend = '震荡'
        advice = '持有'
        summary = ''
        
        # 提取评分
        score_match = re.search(r'"sentiment_score":\s*(\d+)', response_text)
        if score_match:
            sentiment_score = int(score_match.group(1))
            
        # 提取趋势
        trend_match = re.search(r'"trend_prediction":\s*"([^"]+)"', response_text)
        if trend_match:
            trend = trend_match.group(1)
            
        # 提取建议
        advice_match = re.search(r'"operation_advice":\s*"([^"]+)"', response_text)
        if advice_match:
            advice = advice_match.group(1)
            
        # 提取核心结论 (尝试多种可能的键名)
        summary_match = re.search(r'"one_sentence":\s*"([^"]+)"', response_text)
        if not summary_match:
            summary_match = re.search(r'"analysis_summary":\s*"([^"]+)"', response_text)
            
        if summary_match:
            summary = summary_match.group(1)
        else:
            # 如果没提取到 JSON 字段，使用文本分析回退
            
            # 截取前500字符作为摘要，但过滤掉 JSON 结构符号
            clean_text = re.sub(r'["{}\[\],]', '', response_text[:500])
            # 移除键名
            clean_text = re.sub(r'\w+:', '', clean_text)
            # 压缩空白
            summary = re.sub(r'\s+', ' ', clean_text).strip()
            if len(summary) < 10: # 如果清理后太短，还是用原来的但截断
                 summary = response_text[:200]
        
        # 如果还没提取到评分，使用关键词分析
        if sentiment_score == 50 and not score_match:
            text_lower = response_text.lower()
            positive_keywords = ['看多', '买入', '上涨', '突破', '强势', '利好', '加仓', 'bullish', 'buy']
            negative_keywords = ['看空', '卖出', '下跌', '跌破', '弱势', '利空', '减仓', 'bearish', 'sell']
            
            positive_count = sum(1 for kw in positive_keywords if kw in text_lower)
            negative_count = sum(1 for kw in negative_keywords if kw in text_lower)
            
            if positive_count > negative_count + 1:
                sentiment_score = 65
                trend = '看多'
                advice = '买入'
            elif negative_count > positive_count + 1:
                sentiment_score = 35
                trend = '看空'
                advice = '卖出'
        
        # 构建一个替代的详细报告
        fallback_report = f"""# {name}({code}) 投资分析报告

> ⚠️ 注意：本次分析结果由系统从原始响应中提取，可能不包含完整细节。

## 1. 核心结论
- **综合评分**: {sentiment_score}分
- **趋势预判**: {trend}
- **操作建议**: {advice}

## 2. 分析摘要
{summary}

## 3. 详细内容
(由于格式解析限制，无法展示结构化详情，请参考上述摘要或重新运行分析)
"""

        return AnalysisResult(
            code=code,
            name=name,
            sentiment_score=sentiment_score,
            trend_prediction=trend,
            operation_advice=advice,
            confidence_level='低',
            analysis_summary=summary,
            detailed_analysis=fallback_report,
            success=True
        )
    
    def batch_analyze(
        self, 
        contexts: List[Dict[str, Any]],
        delay_between: float = 2.0
    ) -> List[AnalysisResult]:
        """
        批量分析多只股票
        
        注意：为避免 API 速率限制，每次分析之间会有延迟
        
        Args:
            contexts: 上下文数据列表
            delay_between: 每次分析之间的延迟（秒）
            
        Returns:
            AnalysisResult 列表
        """
        results = []
        
        for i, context in enumerate(contexts):
            if i > 0:
                logger.debug(f"等待 {delay_between} 秒后继续...")
                time.sleep(delay_between)
            
            result = self.analyze(context)
            results.append(result)
        
        return results


# 便捷函数
def get_analyzer() -> GeminiAnalyzer:
    """获取 Gemini 分析器实例"""
    return GeminiAnalyzer()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.DEBUG)
    
    # 模拟上下文数据
    test_context = {
        'code': '600519',
        'date': '2026-01-09',
        'today': {
            'open': 1800.0,
            'high': 1850.0,
            'low': 1780.0,
            'close': 1820.0,
            'volume': 10000000,
            'amount': 18200000000,
            'pct_chg': 1.5,
            'ma5': 1810.0,
            'ma10': 1800.0,
            'ma20': 1790.0,
            'volume_ratio': 1.2,
        },
        'ma_status': '多头排列 📈',
        'volume_change_ratio': 1.3,
        'price_change_ratio': 1.5,
    }
    
    analyzer = GeminiAnalyzer()
    
    if analyzer.is_available():
        print("=== AI 分析测试 ===")
        result = analyzer.analyze(test_context)
        print(f"分析结果: {result.to_dict()}")
    else:
        print("Gemini API 未配置，跳过测试")
