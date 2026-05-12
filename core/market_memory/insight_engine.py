from typing import Dict, List, Optional
from datetime import datetime
import json
from .engine import MarketStateEngine
from .models import MarketSnapshot, MarketTrend, MarketInsight


class NarrativeEngine:
    """
    市场叙事引擎 - 将历史数据转换为市场故事
    
    核心功能：
    1. 将原始数据转换为AI可读的结构化摘要
    2. 生成市场故事（Market Story）
    3. 识别关键变化和转折点
    """
    
    def __init__(self, engine: MarketStateEngine):
        self.engine = engine
    
    def build_market_summary(self, snapshot: MarketSnapshot) -> Dict:
        """
        构建单日市场摘要
        
        将原始数据转换为AI可读的结构化摘要
        """
        return {
            "date": snapshot.date,
            "market_sentiment": snapshot.market_sentiment,
            "emotion_score": round(snapshot.emotion_score, 1),
            "volume_trend": snapshot.volume_trend,
            "limit_up_count": snapshot.limit_up_count,
            "limit_down_count": snapshot.limit_down_count,
            "highest_board": snapshot.highest_board,
            "top_sectors": snapshot.top_sectors[:3],
            "sector_rotation": {
                "outflow": snapshot.rotation_from,
                "inflow": snapshot.rotation_to
            } if snapshot.dragon_rotation else None,
            "leaders": [
                {
                    "name": leader,
                    "board": snapshot.highest_board,
                    "status": "空间龙" if "龙" in leader else "龙头"
                }
                for leader in snapshot.leaders[:3]
            ],
            "market_style": self._infer_market_style(snapshot),
            "risk_signal": self._infer_risk_signal(snapshot),
            "north_money": f"{snapshot.north_money:+.0f}亿" if snapshot.north_money else "未知"
        }
    
    def build_market_story(self, days: int = 5) -> str:
        """
        构建市场故事
        
        将最近N天的数据转换为一个连贯的市场叙事
        """
        snapshots = self.engine.get_recent_snapshots(days)
        
        if not snapshots:
            return "暂无历史数据，无法生成市场故事"
        
        # 生成情绪序列
        emotion_sequence = self._build_emotion_sequence(snapshots)
        
        # 生成市场阶段序列
        market_stage_sequence = self._build_market_stage_sequence(snapshots)
        
        # 生成热点演化
        hot_theme_evolution = self._build_hot_theme_evolution(snapshots)
        
        # 生成龙头切换
        leader_switch = self._build_leader_switch(snapshots)
        
        # 生成当前特征
        current_features = self._build_current_features(snapshots[0])
        
        # 组合成完整的故事
        story = f"""最近{days}日市场情绪持续变化：

{emotion_sequence}

市场阶段：
{market_stage_sequence}

热点演化：
{hot_theme_evolution}

龙头切换：
{leader_switch}

当前特征：
{current_features}

请基于以上市场故事，分析：
1. 当前市场处于什么周期
2. 主线是谁
3. 哪些股票具备龙头潜力
4. 风险点是什么
5. 明日预期如何
6. 哪些时机适合低吸/打板
"""
        
        return story
    
    def _build_emotion_sequence(self, snapshots: List[MarketSnapshot]) -> str:
        """构建情绪序列"""
        emotions = [s.emotion_score for s in snapshots]
        limit_ups = [s.limit_up_count for s in snapshots]
        
        sequence = " → ".join([f"{e:.0f}" for e in emotions])
        limit_up_sequence = " → ".join([f"{l}" for l in limit_ups])
        
        return f"""情绪得分：
{sequence}

涨停家数：
{limit_up_sequence}"""
    
    def _build_market_stage_sequence(self, snapshots: List[MarketSnapshot]) -> str:
        """构建市场阶段序列"""
        stages = [s.market_cycle for s in snapshots]
        return " → ".join(stages)
    
    def _build_hot_theme_evolution(self, snapshots: List[MarketSnapshot]) -> str:
        """构建热点演化"""
        themes = []
        for i, snapshot in enumerate(snapshots):
            day_label = f"T-{i}"
            theme = snapshot.hot_theme or "无"
            themes.append(f"{day_label}: {theme}")
        
        return "\n".join(themes)
    
    def _build_leader_switch(self, snapshots: List[MarketSnapshot]) -> str:
        """构建龙头切换"""
        if len(snapshots) < 2:
            return "数据不足"
        
        today_leaders = snapshots[0].leaders[:2]
        yesterday_leaders = snapshots[1].leaders[:2]
        
        if set(today_leaders) == set(yesterday_leaders):
            return f"龙头延续：{', '.join(today_leaders)}"
        else:
            return f"龙头切换：{', '.join(yesterday_leaders)} → {', '.join(today_leaders)}"
    
    def _build_current_features(self, snapshot: MarketSnapshot) -> str:
        """构建当前特征"""
        features = []
        
        if snapshot.rise_ratio > 0.6:
            features.append("- 普涨行情")
        elif snapshot.rise_ratio < 0.4:
            features.append("- 普跌行情")
        else:
            features.append("- 结构性行情")
        
        if snapshot.limit_up_count > 80:
            features.append("- 高位抱团明显")
        elif snapshot.limit_up_count < 30:
            features.append("- 低位补涨增加")
        
        if snapshot.top_sectors:
            features.append(f"- {snapshot.top_sectors[0]}板块持续加强")
        
        if snapshot.north_money and snapshot.north_money > 0:
            features.append("- 北向资金连续流入")
        
        if snapshot.bomb_rate > 0.3:
            features.append("- 炸板率较高，注意风险")
        
        return "\n".join(features)
    
    def _infer_market_style(self, snapshot: MarketSnapshot) -> str:
        """推断市场风格"""
        if snapshot.limit_up_count > 80 and snapshot.bomb_rate < 0.2:
            return "高位抱团"
        elif snapshot.limit_up_count < 30:
            return "低位补涨"
        elif snapshot.rise_ratio > 0.6:
            return "普涨行情"
        elif snapshot.rise_ratio < 0.4:
            return "普跌行情"
        else:
            return "结构性行情"
    
    def _infer_risk_signal(self, snapshot: MarketSnapshot) -> str:
        """推断风险信号"""
        signals = []
        
        if snapshot.bomb_rate > 0.3:
            signals.append("炸板率高")
        
        if snapshot.limit_down_count > 20:
            signals.append("跌停家数多")
        
        if snapshot.emotion_score > 90:
            signals.append("情绪过热")
        
        if snapshot.emotion_score < 30:
            signals.append("情绪冰点")
        
        if not signals:
            signals.append("风险可控")
        
        return "，".join(signals)


class MarketContextBuilder:
    """
    市场上下文构建器
    
    构建AI可理解的市场状态
    """
    
    def __init__(self, engine: MarketStateEngine):
        self.engine = engine
        self.narrative_engine = NarrativeEngine(engine)
    
    def build_market_context(self, days: int = 5) -> Dict:
        """
        构建市场上下文
        
        Args:
            days: 分析天数
        
        Returns:
            Dict: 市场上下文
        """
        snapshots = self.engine.get_recent_snapshots(days)
        
        if not snapshots:
            return {
                "has_context": False,
                "message": "暂无历史数据"
            }
        
        # 获取最新快照
        latest = snapshots[0]
        
        # 构建今日摘要
        today_summary = self.narrative_engine.build_market_summary(latest)
        
        # 构建历史趋势
        market_cycle = self.engine.analyze_market_cycle(snapshots)
        emotion_trend = self.engine.analyze_emotion_trend(snapshots, days)
        sector_rotation = self.engine.analyze_sector_rotation(snapshots, days)
        leader_rotation = self.engine.analyze_leader_rotation(snapshots, days)
        risk_change = self.engine.analyze_risk_change(snapshots, days)
        
        return {
            "has_context": True,
            "days": days,
            "latest_date": latest.date,
            "today_summary": today_summary,
            "market_cycle": market_cycle,
            "emotion_trend": emotion_trend,
            "sector_rotation": sector_rotation,
            "leader_rotation": leader_rotation,
            "risk_change": risk_change,
            "snapshots": [s.to_dict() for s in snapshots]
        }
    
    def build_llm_context(self, days: int = 5) -> str:
        """
        构建适合LLM的上下文字符串
        
        Args:
            days: 分析天数
        
        Returns:
            str: LLM上下文
        """
        context = self.build_market_context(days)
        
        if not context.get("has_context"):
            return "暂无历史市场数据"
        
        lines = [
            f"【市场上下文（最近{days}天）】",
            f"━━━━━━━━━━━━━━━━━━━━",
            f"",
            f"📊 市场周期：{context['market_cycle']['cycle']}（{context['market_cycle']['stage']}）",
            f"   {context['market_cycle']['description']}",
            f"",
            f"😊 情绪趋势：{context['emotion_trend']['direction']}",
            f"   {context['emotion_trend']['description']}",
            f"",
            f"🔄 板块轮动：{context['sector_rotation']['description']}",
            f"",
            f"🐉 龙头切换：{context['leader_rotation']['description']}",
            f"",
            f"⚠️  风险变化：{context['risk_change']['description']}",
            f"",
            f"━━━━━━━━━━━━━━━━━━━━",
        ]
        
        return "\n".join(lines)


class LLMPromptBuilder:
    """
    LLM提示词构建器
    
    生成适合LLM的提示词
    """
    
    def __init__(self, context_builder: MarketContextBuilder):
        self.context_builder = context_builder
    
    def build_market_insight_prompt(self, days: int = 5) -> str:
        """
        构建市场洞察提示词
        
        Args:
            days: 分析天数
        
        Returns:
            str: LLM提示词
        """
        # 获取市场故事
        narrative_engine = NarrativeEngine(self.context_builder.engine)
        market_story = narrative_engine.build_market_story(days)
        
        # 获取市场上下文
        llm_context = self.context_builder.build_llm_context(days)
        
        prompt = f"""你是一位专业的A股市场分析师，擅长基于历史数据和情绪周期进行市场推理。

{llm_context}

{market_story}

请基于以上信息，生成一份专业的市场洞察报告，包括：

1. **市场阶段判断**：当前市场处于什么周期（冰点期/修复期/主升期/分歧期/高潮期/退潮期），并说明理由

2. **主线方向**：当前市场的主线板块是什么，为什么

3. **龙头潜力股**：基于当前市场状态，哪些类型的股票具备龙头潜力，具体特征是什么

4. **风险提示**：当前市场的主要风险点是什么

5. **明日预期**：对明天的市场走势有什么预期

6. **操作建议**：
   - 适合低吸的时机和标的特征
   - 适合打板的时机和标的特征
   - 仓位建议

7. **关键观察点**：明天需要重点观察哪些指标和信号

请以JSON格式输出，结构如下：
{{
    "market_stage": "市场阶段",
    "stage_reason": "判断理由",
    "main_sector": "主线板块",
    "sector_reason": "主线理由",
    "leader_potential": ["龙头潜力股特征1", "特征2", "特征3"],
    "risk_alerts": ["风险点1", "风险点2"],
    "tomorrow_expectation": "明日预期",
    "action_suggestions": {{
        "low_buy": "低吸建议",
        "limit_up": "打板建议",
        "position": "仓位建议"
    }},
    "key_observations": ["观察点1", "观察点2", "观察点3"],
    "confidence": 0.85
}}
"""
        
        return prompt


class MarketInsightEngine:
    """
    市场洞察引擎 - 核心大脑
    
    功能：
    1. 加载历史上下文
    2. 构建市场故事
    3. 构建LLM提示词
    4. 生成市场洞察
    """
    
    def __init__(self, db_path: str = None, llm_client=None):
        self.engine = MarketStateEngine(db_path)
        self.narrative_engine = NarrativeEngine(self.engine)
        self.context_builder = MarketContextBuilder(self.engine)
        self.prompt_builder = LLMPromptBuilder(self.context_builder)
        self.llm_client = llm_client
    
    def load_history_context(self, days: int = 5) -> Dict:
        """
        加载历史上下文
        
        Args:
            days: 加载天数
        
        Returns:
            Dict: 历史上下文
        """
        return self.context_builder.build_market_context(days)
    
    def build_market_story(self, days: int = 5) -> str:
        """
        构建市场故事
        
        Args:
            days: 分析天数
        
        Returns:
            str: 市场故事
        """
        return self.narrative_engine.build_market_story(days)
    
    def build_llm_prompt(self, days: int = 5) -> str:
        """
        构建LLM提示词
        
        Args:
            days: 分析天数
        
        Returns:
            str: LLM提示词
        """
        return self.prompt_builder.build_market_insight_prompt(days)
    
    def generate_market_insight(self, days: int = 5) -> MarketInsight:
        """
        生成市场洞察
        
        Args:
            days: 分析天数
        
        Returns:
            MarketInsight: 市场洞察对象
        """
        # 加载历史上下文
        context = self.load_history_context(days)
        
        # 构建市场故事
        market_story = self.build_market_story(days)
        
        # 构建LLM提示词
        prompt = self.build_llm_prompt(days)
        
        # 如果有LLM客户端，调用LLM生成洞察
        if self.llm_client:
            try:
                llm_response = self.llm_client.generate(prompt)
                insight_data = json.loads(llm_response)
                
                return MarketInsight(
                    date=datetime.now().strftime("%Y-%m-%d"),
                    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    current_state=insight_data.get("market_stage", "未知"),
                    state_description=insight_data.get("stage_reason", ""),
                    trend_analysis=market_story,
                    risk_alert="；".join(insight_data.get("risk_alerts", [])),
                    opportunity=f"主线：{insight_data.get('main_sector', '未知')}，龙头特征：{', '.join(insight_data.get('leader_potential', []))}",
                    action_suggestion=f"低吸：{insight_data.get('action_suggestions', {}).get('low_buy', '')}；打板：{insight_data.get('action_suggestions', {}).get('limit_up', '')}；仓位：{insight_data.get('action_suggestions', {}).get('position', '')}",
                    key_changes=insight_data.get("key_observations", []),
                    confidence=insight_data.get("confidence", 0.7)
                )
            except Exception as e:
                print(f"LLM生成洞察失败: {e}")
        
        # 如果没有LLM或LLM失败，返回基于规则的洞察
        return self._generate_rule_based_insight(context, market_story)
    
    def _generate_rule_based_insight(self, context: Dict, market_story: str) -> MarketInsight:
        """
        基于规则生成市场洞察（当LLM不可用时）
        """
        market_cycle = context.get("market_cycle", {})
        emotion_trend = context.get("emotion_trend", {})
        sector_rotation = context.get("sector_rotation", {})
        risk_change = context.get("risk_change", {})
        
        current_state = market_cycle.get("cycle", "未知")
        state_description = market_cycle.get("description", "")
        
        # 风险提示
        risk_alerts = []
        if risk_change.get("trend") == "上升":
            risk_alerts.append("风险上升，注意控制仓位")
        if emotion_trend.get("direction") == "下降":
            risk_alerts.append("情绪降温，谨慎操作")
        if sector_rotation.get("has_rotation"):
            risk_alerts.append("主线切换，注意追高风险")
        
        # 机会提示
        opportunities = []
        if emotion_trend.get("direction") == "上升":
            opportunities.append("情绪回暖，可以积极参与主线")
        if sector_rotation.get("has_rotation"):
            opportunities.append(f"新主线：{sector_rotation.get('rotation_to', '未知')}，关注龙头")
        
        # 操作建议
        action_suggestions = []
        if current_state == "冰点期":
            action_suggestions.append("建议观望，等待情绪修复")
        elif current_state == "修复期":
            action_suggestions.append("可以小仓位试错，关注龙头")
        elif current_state == "主升期":
            action_suggestions.append("积极参与主线，敢于持股")
        elif current_state == "高潮期":
            action_suggestions.append("注意风险，逐步减仓")
        elif current_state == "退潮期":
            action_suggestions.append("降低仓位，等待新周期")
        
        return MarketInsight(
            date=datetime.now().strftime("%Y-%m-%d"),
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            current_state=current_state,
            state_description=state_description,
            trend_analysis=market_story,
            risk_alert="；".join(risk_alerts) if risk_alerts else "风险可控",
            opportunity="；".join(opportunities) if opportunities else "等待机会",
            action_suggestion="；".join(action_suggestions) if action_suggestions else "观望",
            key_changes=[
                f"市场周期：{current_state}",
                f"情绪趋势：{emotion_trend.get('direction', '未知')}",
                f"板块轮动：{sector_rotation.get('description', '未知')}"
            ],
            confidence=0.7
        )
    
    def save_insight(self, insight: MarketInsight) -> bool:
        """
        保存市场洞察到数据库
        
        Args:
            insight: 市场洞察对象
        
        Returns:
            bool: 是否成功
        """
        try:
            import sqlite3
            conn = sqlite3.connect(self.engine.db_path)
            cursor = conn.cursor()
            
            import json
            cursor.execute("""
            INSERT OR REPLACE INTO market_insights (
                date, timestamp, current_state, state_description,
                trend_analysis, risk_alert, opportunity, action_suggestion,
                key_changes, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                insight.date,
                insight.timestamp,
                insight.current_state,
                insight.state_description,
                insight.trend_analysis,
                insight.risk_alert,
                insight.opportunity,
                insight.action_suggestion,
                json.dumps(insight.key_changes, ensure_ascii=False),
                insight.confidence,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存市场洞察失败: {e}")
            return False
    
    def get_latest_insight(self) -> Optional[MarketInsight]:
        """
        获取最新的市场洞察
        
        Returns:
            MarketInsight: 最新的市场洞察
        """
        import sqlite3
        conn = sqlite3.connect(self.engine.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT date, timestamp, current_state, state_description,
               trend_analysis, risk_alert, opportunity, action_suggestion,
               key_changes, confidence
        FROM market_insights
        ORDER BY date DESC
        LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            import json
            return MarketInsight(
                date=row[0],
                timestamp=row[1],
                current_state=row[2],
                state_description=row[3],
                trend_analysis=row[4],
                risk_alert=row[5],
                opportunity=row[6],
                action_suggestion=row[7],
                key_changes=json.loads(row[8]) if row[8] else [],
                confidence=row[9]
            )
        
        return None
    
    def get_recent_insights(self, days: int = 30) -> List[MarketInsight]:
        """
        获取最近N天的市场洞察
        
        Args:
            days: 天数
        
        Returns:
            List[MarketInsight]: 市场洞察列表
        """
        import sqlite3
        conn = sqlite3.connect(self.engine.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
        SELECT date, timestamp, current_state, state_description,
               trend_analysis, risk_alert, opportunity, action_suggestion,
               key_changes, confidence
        FROM market_insights
        ORDER BY date DESC
        LIMIT ?
        """, (days,))
        
        rows = cursor.fetchall()
        conn.close()
        
        insights = []
        import json
        for row in rows:
            insights.append(MarketInsight(
                date=row[0],
                timestamp=row[1],
                current_state=row[2],
                state_description=row[3],
                trend_analysis=row[4],
                risk_alert=row[5],
                opportunity=row[6],
                action_suggestion=row[7],
                key_changes=json.loads(row[8]) if row[8] else [],
                confidence=row[9]
            ))
        
        return insights
