"""
A股财报量化打分器

基于五大维度对 A 股上市公司进行量化评分：
- 成长性（25分）：营业收入同比增长率
- 盈利能力（25分）：ROE + 归母净利润变化
- 财务安全（20分）：资产负债率 + 货币资金充裕度
- 现金流（15分）：经营活动现金流净额
- 行业前景（15分）：行业定性评估

数据来源：AkShare（底层数据来自东方财富、同花顺等官方披露渠道）
"""

import akshare as ak
import pandas as pd
import traceback
import os

# 禁用代理环境变量
os.environ['HTTP_PROXY'] = ''
os.environ['HTTPS_PROXY'] = ''
os.environ['http_proxy'] = ''
os.environ['https_proxy'] = ''


class FinancialScorer:
    """A股财报量化打分器"""

    # 行业分类评分映射：基于行业前景的定性评估
    INDUSTRY_SCORE_MAP = {
        # 高前景行业（12-15分）
        '网络安全': 14, '信息安全': 14, '数据安全': 14, 'AI安全': 14,
        '人工智能': 13, 'AI': 13, '大模型': 13, '机器学习': 13,
        '半导体': 14, '芯片': 14, '集成电路': 14, '光刻': 13,
        '新能源': 13, '光伏': 13, '风电': 13, '储能': 13, '锂电池': 12,
        '创新药': 13, '生物医药': 12, '基因': 13,
        '量子': 14, '航天': 13, '军工': 12,
        '机器人': 13, '自动驾驶': 13, '智能驾驶': 13,
        '云计算': 13, '大数据': 13, '区块链': 11,
        '5G': 12, '6G': 12, '通信': 11,

        # 中等前景行业（8-12分）
        '消费': 11, '食品': 10, '饮料': 11, '白酒': 12, '乳业': 10,
        '医药': 10, '医疗': 10, '医疗器械': 11,
        '汽车': 10, '零部件': 8, '整车': 10,
        '银行': 8, '证券': 9, '保险': 9, '金融': 8,
        '房地产': 6, '地产': 6, '物业': 7,
        '家电': 9, '家居': 8,
        '电力': 9, '电网': 9, '发电': 8,
        '环保': 8, '水务': 7, '燃气': 7,
        '建筑': 7, '建材': 7, '装修': 6,
        '传媒': 9, '游戏': 10, '广告': 7,
        '物流': 8, '快递': 9, '港口': 7,
        '旅游': 9, '酒店': 8, '餐饮': 7,
        '教育': 7, '培训': 6,
        '软件': 11, '计算机': 10, '互联网': 11,

        # 传统行业（5-8分）
        '钢铁': 6, '煤炭': 5, '有色': 7, '石油': 5, '化工': 7,
        '纺织': 5, '服装': 6, '造纸': 5, '包装': 5,
        '农业': 6, '养殖': 5, '渔业': 5,
        '商业': 6, '零售': 6, '贸易': 5,
    }

    def __init__(self):
        self.scoring_weights = {
            'growth': 25,
            'profitability': 25,
            'safety': 20,
            'cashflow': 15,
            'industry': 15,
        }

    # ------------------------------------------------------------------
    # 数据获取
    # ------------------------------------------------------------------

    def fetch_financial_data(self, stock_code: str) -> dict:
        """从 AkShare 获取财报原始数据，返回结构化字典"""
        raw_code = self._normalize_code(stock_code)
        # 确定交易所前缀
        if raw_code.startswith('6'):
            em_symbol = f"SH{raw_code}"
        else:
            em_symbol = f"SZ{raw_code}"

        result = {
            'stock_code': stock_code,
            'symbol': raw_code,
            'em_symbol': em_symbol,
            'success': False,
            'errors': [],
            # 结构化数据
            'revenue_current': None,
            'revenue_last': None,
            'revenue_growth_rate': None,
            'net_profit_current': None,
            'net_profit_last': None,
            'roe': None,
            'total_assets': None,
            'total_liabilities': None,
            'cash_equivalents': None,
            'asset_liability_ratio': None,
            'operating_cf_current': None,
            'operating_cf_last': None,
            'industry': None,
        }

        # 1. 财务摘要（按年度）- 核心数据源
        #    返回 DataFrame，每行为一个年度，列为各项指标
        try:
            abstract = ak.stock_financial_abstract_ths(symbol=raw_code, indicator="按年度")
            if abstract is not None and not abstract.empty:
                self._parse_abstract_annual(abstract, result)
        except Exception as e:
            result['errors'].append(f"财务摘要获取失败: {str(e)}")

        # 2. 资产负债表 - 补充总资产、总负债、货币资金
        try:
            balance = ak.stock_balance_sheet_by_report_em(symbol=em_symbol)
            if balance is not None and not balance.empty:
                self._parse_balance_em(balance, result)
        except Exception as e:
            result['errors'].append(f"资产负债表获取失败: {str(e)}")

        # 3. 现金流量表 - 补充经营现金流净额
        try:
            cashflow = ak.stock_cash_flow_sheet_by_report_em(symbol=em_symbol)
            if cashflow is not None and not cashflow.empty:
                self._parse_cashflow_em(cashflow, result)
        except Exception as e:
            result['errors'].append(f"现金流量表获取失败: {str(e)}")

        # 判断核心数据是否可用
        has_core = result['revenue_current'] is not None
        if has_core:
            result['success'] = True

        return result

    def _normalize_code(self, stock_code: str) -> str:
        """规范化股票代码，去掉可能的前后缀"""
        code = str(stock_code).strip()
        if '.' in code:
            code = code.split('.')[0]
        return code

    def _parse_abstract_annual(self, df: pd.DataFrame, result: dict):
        """
        解析按年度财务摘要 DataFrame

        stock_financial_abstract_ths(symbol, indicator="按年度") 返回格式：
        - 每行为一个年度（如 2008, 2009, ...）
        - 列为各项财务指标：
          报告期, 净利润, 净利润同比增长率, 营业总收入, 营业总收入同比增长率,
          净资产收益率, 资产负债率, 每股经营现金流, ...
        """
        if df.empty or len(df) < 2:
            return

        # 数据按年度升序排列，最后两行为最近两年
        current = df.iloc[-1]
        last = df.iloc[-2]

        # 营业收入
        try:
            result['revenue_current'] = self._parse_value(current.get('营业总收入'))
            result['revenue_last'] = self._parse_value(last.get('营业总收入'))
        except Exception:
            pass

        # 营收同比增长率（直接使用财报数据）
        try:
            growth_str = str(current.get('营业总收入同比增长率', '')).replace('%', '')
            result['revenue_growth_rate'] = self._to_float(growth_str)
        except Exception:
            pass

        # 归母净利润
        try:
            result['net_profit_current'] = self._parse_value(current.get('净利润'))
            result['net_profit_last'] = self._parse_value(last.get('净利润'))
        except Exception:
            pass

        # ROE（净资产收益率）
        try:
            roe_str = str(current.get('净资产收益率', '')).replace('%', '')
            result['roe'] = self._to_float(roe_str)
        except Exception:
            pass

        # 资产负债率
        try:
            alr_str = str(current.get('资产负债率', '')).replace('%', '')
            result['asset_liability_ratio'] = self._to_float(alr_str)
        except Exception:
            pass

    def _parse_balance_em(self, df: pd.DataFrame, result: dict):
        """
        解析东方财富资产负债表

        格式：每行为一个报告期，列为英文指标名
        - REPORT_TYPE: 报告类型（年报、一季报等）
        - TOTAL_ASSETS: 总资产
        - TOTAL_LIABILITIES: 总负债
        - MONETARYFUNDS: 货币资金
        """
        if df.empty:
            return

        # 筛选年报数据
        annual = df[df['REPORT_TYPE'] == '年报']
        if annual.empty:
            return

        # 按 REPORT_DATE 排序，取最新一期
        annual = annual.sort_values('REPORT_DATE')
        latest = annual.iloc[-1]

        try:
            val = latest.get('TOTAL_ASSETS')
            if pd.notna(val):
                result['total_assets'] = float(val)
        except Exception:
            pass

        try:
            val = latest.get('TOTAL_LIABILITIES')
            if pd.notna(val):
                result['total_liabilities'] = float(val)
        except Exception:
            pass

        try:
            val = latest.get('MONETARYFUNDS')
            if pd.notna(val):
                result['cash_equivalents'] = float(val)
        except Exception:
            pass

    def _parse_cashflow_em(self, df: pd.DataFrame, result: dict):
        """
        解析东方财富现金流量表

        格式：每行为一个报告期，列为英文指标名
        - NETCASH_OPERATE: 经营活动现金流量净额
        """
        if df.empty:
            return

        annual = df[df['REPORT_TYPE'] == '年报']
        if annual.empty:
            return

        annual = annual.sort_values('REPORT_DATE')

        if len(annual) >= 1:
            latest = annual.iloc[-1]
            try:
                val = latest.get('NETCASH_OPERATE')
                if pd.notna(val):
                    result['operating_cf_current'] = float(val)
            except Exception:
                pass

        if len(annual) >= 2:
            prev = annual.iloc[-2]
            try:
                val = prev.get('NETCASH_OPERATE')
                if pd.notna(val):
                    result['operating_cf_last'] = float(val)
            except Exception:
                pass

    def _parse_value(self, val):
        """解析带单位的值（如 '79.48亿', '2.63亿', '5897.76万'）"""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().replace(',', '').replace(' ', '')
        if s in ('', '-', '--', 'nan', 'None', 'NaN', 'False'):
            return None
        try:
            if '亿' in s:
                return float(s.replace('亿', '')) * 1e8
            elif '万' in s:
                return float(s.replace('万', '')) * 1e4
            else:
                return float(s)
        except ValueError:
            return None

    def _to_float(self, val):
        """安全转换为浮点数"""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val).strip().replace(',', '').replace(' ', '')
        if s in ('', '-', '--', 'nan', 'None', 'NaN', 'False'):
            return None
        try:
            return float(s)
        except ValueError:
            return None

    # ------------------------------------------------------------------
    # 评分算法
    # ------------------------------------------------------------------

    def score_growth(self, data: dict) -> dict:
        """
        成长性评分（满分 25）
        基于营业收入同比增长率
        """
        # 优先使用财报直接提供的增长率
        growth_rate = data.get('revenue_growth_rate')

        # 如果直接增长率不可用，从营收数据计算
        if growth_rate is None:
            rev_cur = data.get('revenue_current')
            rev_last = data.get('revenue_last')
            if rev_cur is not None and rev_last is not None and rev_last != 0:
                growth_rate = (rev_cur - rev_last) / abs(rev_last) * 100

        if growth_rate is None:
            return {
                'score': 0, 'max': 25, 'label': '成长性',
                'reason': '数据不足，无法评估营收增长', 'growth_rate': None
            }

        if growth_rate >= 50:
            score = 25
            desc = '超高速增长'
        elif growth_rate >= 30:
            score = 23
            desc = '高速增长'
        elif growth_rate >= 20:
            score = 20
            desc = '快速增长'
        elif growth_rate >= 10:
            score = 17
            desc = '稳健增长'
        elif growth_rate >= 5:
            score = 15
            desc = '温和增长'
        elif growth_rate >= 0:
            score = 10
            desc = '微增'
        elif growth_rate >= -10:
            score = 5
            desc = '小幅下滑'
        else:
            score = 2
            desc = '明显下滑'

        return {
            'score': score,
            'max': 25,
            'label': '成长性',
            'reason': f'营收同比增长 {growth_rate:+.1f}%，{desc}',
            'growth_rate': round(growth_rate, 2),
        }

    def score_profitability(self, data: dict) -> dict:
        """
        盈利能力评分（满分 25）
        基于 ROE + 归母净利润扭亏加分
        """
        roe = data.get('roe')
        np_cur = data.get('net_profit_current')
        np_last = data.get('net_profit_last')

        reason_parts = []
        score = 0

        # ROE 基础分
        if roe is not None:
            if roe >= 20:
                base = 25
                desc = '优秀'
            elif roe >= 15:
                base = 22
                desc = '很好'
            elif roe >= 10:
                base = 18
                desc = '合格'
            elif roe >= 5:
                base = 14
                desc = '一般'
            elif roe >= 2:
                base = 10
                desc = '偏低'
            elif roe >= 0:
                base = 7
                desc = '极低'
            else:
                base = 3
                desc = '亏损'
            score = base
            reason_parts.append(f'ROE {roe:.2f}%（{desc}）')
        else:
            reason_parts.append('ROE 数据缺失')

        # 扭亏加分：去年亏损、今年盈利
        if np_cur is not None and np_last is not None:
            if np_last < 0 and np_cur > 0:
                turnaround_bonus = 3
                score = min(score + turnaround_bonus, 25)
                reason_parts.append(
                    f'扭亏加分 +{turnaround_bonus}'
                    f'（从 {np_last/1e8:.1f}亿 到 {np_cur/1e8:.1f}亿）'
                )

        if not reason_parts:
            reason_parts.append('数据不足')

        return {
            'score': min(score, 25),
            'max': 25,
            'label': '盈利能力',
            'reason': '；'.join(reason_parts),
            'roe': round(roe, 2) if roe is not None else None,
        }

    def score_safety(self, data: dict) -> dict:
        """
        财务安全评分（满分 20）
        基于资产负债率 + 货币资金充裕度
        """
        # 优先使用财报抽象中的资产负债率
        al_ratio = data.get('asset_liability_ratio')

        # 如果直接比率不可用，尝试从总资产/总负债计算
        if al_ratio is None:
            assets = data.get('total_assets')
            liabilities = data.get('total_liabilities')
            if assets and liabilities and assets > 0:
                al_ratio = (liabilities / assets) * 100

        cash = data.get('cash_equivalents')
        assets = data.get('total_assets')

        if al_ratio is None:
            return {
                'score': 0, 'max': 20, 'label': '财务安全',
                'reason': '数据不足，无法评估'
            }

        reason_parts = []
        score = 0

        # 资产负债率基础分
        if al_ratio < 20:
            base = 16
            desc = '非常健康'
        elif al_ratio < 30:
            base = 14
            desc = '健康'
        elif al_ratio < 40:
            base = 12
            desc = '适中'
        elif al_ratio < 50:
            base = 8
            desc = '偏高'
        elif al_ratio < 60:
            base = 5
            desc = '较高'
        else:
            base = 2
            desc = '过高'
        score = base
        reason_parts.append(f'资产负债率 {al_ratio:.1f}%（{desc}）')

        # 货币资金充裕度加分
        if cash is not None and assets is not None and assets > 0:
            cash_ratio = (cash / assets) * 100
            if cash_ratio > 50:
                bonus = 4
                cash_desc = '极其充裕'
            elif cash_ratio > 30:
                bonus = 3
                cash_desc = '非常充裕'
            elif cash_ratio > 15:
                bonus = 2
                cash_desc = '充裕'
            elif cash_ratio > 5:
                bonus = 1
                cash_desc = '正常'
            else:
                bonus = 0
                cash_desc = '偏少'
            score = min(score + bonus, 20)
            reason_parts.append(f'现金占比 {cash_ratio:.1f}%（{cash_desc}）+{bonus}')

        return {
            'score': score,
            'max': 20,
            'label': '财务安全',
            'reason': '；'.join(reason_parts),
        }

    def score_cashflow(self, data: dict) -> dict:
        """
        现金流评分（满分 15）
        基于经营活动现金流净额及同比变化趋势
        """
        cf_cur = data.get('operating_cf_current')
        cf_last = data.get('operating_cf_last')

        if cf_cur is None:
            return {
                'score': 0, 'max': 15, 'label': '现金流',
                'reason': '经营现金流数据不足'
            }

        cf_cur_yi = cf_cur / 1e8  # 转为亿
        reason_parts = [f'经营现金流 {cf_cur_yi:+.2f}亿']

        if cf_cur > 0:
            if cf_last is not None and cf_last > 0:
                if cf_cur > cf_last:
                    score = 15
                    desc = '持续向好'
                else:
                    score = 12
                    desc = '正流但下滑'
            else:
                score = 13
                desc = '本期转正'
            reason_parts.append(desc)
        else:
            if cf_last is not None and cf_last < 0:
                improvement = abs(cf_last) - abs(cf_cur)
                if improvement > 0:
                    pct = (improvement / abs(cf_last)) * 100
                    if pct > 50:
                        score = 10
                        desc = f'亏损收窄 {pct:.0f}%，恢复明显'
                    elif pct > 20:
                        score = 8
                        desc = f'亏损收窄 {pct:.0f}%，逐步恢复'
                    else:
                        score = 6
                        desc = f'亏损略微收窄 {pct:.0f}%'
                else:
                    score = 3
                    desc = '亏损扩大'
            else:
                score = 5
                desc = '由正转负'
            reason_parts.append(desc)

        return {
            'score': min(score, 15),
            'max': 15,
            'label': '现金流',
            'reason': '；'.join(reason_parts),
        }

    def score_industry(self, data: dict) -> dict:
        """
        行业前景评分（满分 15）
        基于行业关键词匹配的定性评估
        """
        industry = data.get('industry', '')

        if not industry:
            return {
                'score': 7, 'max': 15, 'label': '行业前景',
                'reason': '行业信息缺失，按中性评估'
            }

        # 按关键词匹配评分
        best_score = 7  # 默认中性
        matched = None
        for keyword, score in self.INDUSTRY_SCORE_MAP.items():
            if keyword in industry:
                if score > best_score:
                    best_score = score
                    matched = keyword

        if matched:
            reason = f'行业含"{matched}"，前景评分 {best_score}/15'
        else:
            # 根据行业特征推断
            if any(kw in industry for kw in
                   ['科技', '信息', '电子', '软件', '通信', '互联网']):
                best_score = 10
                reason = f'行业"{industry}"属科技板块，前景良好'
            elif any(kw in industry for kw in
                     ['消费', '食品', '医药', '医疗', '汽车']):
                best_score = 9
                reason = f'行业"{industry}"属消费/民生板块，前景稳健'
            elif any(kw in industry for kw in
                     ['金融', '银行', '证券', '保险']):
                best_score = 8
                reason = f'行业"{industry}"属金融板块，前景稳定'
            elif any(kw in industry for kw in
                     ['制造', '化工', '建材', '钢铁', '煤炭']):
                best_score = 6
                reason = f'行业"{industry}"属传统制造板块'
            else:
                reason = f'行业"{industry}"按中性评估'

        return {
            'score': best_score,
            'max': 15,
            'label': '行业前景',
            'reason': reason,
        }

    # ------------------------------------------------------------------
    # 综合评分
    # ------------------------------------------------------------------

    def score_all(self, stock_code: str, industry: str = None) -> dict:
        """综合评分入口：拉取数据 → 五维度评分 → 汇总"""
        raw_data = self.fetch_financial_data(stock_code)

        if industry:
            raw_data['industry'] = industry

        scores = {
            'growth': self.score_growth(raw_data),
            'profitability': self.score_profitability(raw_data),
            'safety': self.score_safety(raw_data),
            'cashflow': self.score_cashflow(raw_data),
            'industry': self.score_industry(raw_data),
        }

        total_score = sum(s['score'] for s in scores.values())
        max_total = sum(s['max'] for s in scores.values())

        if total_score >= 90:
            rating = '顶级公司'
            rating_desc = '各项指标优异，具有强大竞争壁垒和持续盈利能力'
        elif total_score >= 80:
            rating = '优秀企业'
            rating_desc = '整体表现优秀，值得重点关注'
        elif total_score >= 70:
            rating = '值得持续跟踪'
            rating_desc = '具备一定竞争优势，需持续观察发展趋势'
        elif total_score >= 60:
            rating = '能看'
            rating_desc = '基本面尚可，有一定安全边际，但赚钱能力待提升'
        elif total_score >= 50:
            rating = '一般'
            rating_desc = '多项指标偏弱，需关注改善信号'
        else:
            rating = '需谨慎'
            rating_desc = '基本面较弱，投资需格外谨慎'

        return {
            'stock_code': stock_code,
            'success': raw_data['success'],
            'errors': raw_data['errors'],
            'total_score': total_score,
            'max_total': max_total,
            'rating': rating,
            'rating_desc': rating_desc,
            'scores': scores,
            'raw_data': {
                'revenue_current': raw_data.get('revenue_current'),
                'revenue_last': raw_data.get('revenue_last'),
                'net_profit_current': raw_data.get('net_profit_current'),
                'net_profit_last': raw_data.get('net_profit_last'),
                'roe': raw_data.get('roe'),
                'total_assets': raw_data.get('total_assets'),
                'total_liabilities': raw_data.get('total_liabilities'),
                'cash_equivalents': raw_data.get('cash_equivalents'),
                'operating_cf_current': raw_data.get('operating_cf_current'),
                'operating_cf_last': raw_data.get('operating_cf_last'),
            }
        }