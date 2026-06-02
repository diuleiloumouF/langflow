# Yahoo Finance 数据查询组件，通过 yfinance 库获取股票和金融市场数据
import ast
import pprint
from enum import Enum

import yfinance as yf
from langchain_core.tools import ToolException
from pydantic import BaseModel, Field

from lfx.custom.custom_component.component import Component
from lfx.inputs.inputs import DropdownInput, IntInput, MessageTextInput
from lfx.io import Output
from lfx.log.logger import logger
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame


# Yahoo Finance 数据查询方法枚举，定义所有支持的查询类型
class YahooFinanceMethod(Enum):
    # 获取股票基本信息
    GET_INFO = "get_info"
    # 获取相关新闻
    GET_NEWS = "get_news"
    # 获取公司行动（分红、拆股等）
    GET_ACTIONS = "get_actions"
    # 获取分析师评级
    GET_ANALYSIS = "get_analysis"
    # 获取资产负债表
    GET_BALANCE_SHEET = "get_balance_sheet"
    # 获取财报日历
    GET_CALENDAR = "get_calendar"
    # 获取现金流数据
    GET_CASHFLOW = "get_cashflow"
    # 获取机构持仓信息
    GET_INSTITUTIONAL_HOLDERS = "get_institutional_holders"
    # 获取投资建议
    GET_RECOMMENDATIONS = "get_recommendations"
    # 获取可持续发展评级
    GET_SUSTAINABILITY = "get_sustainability"
    # 获取主要股东信息
    GET_MAJOR_HOLDERS = "get_major_holders"
    # 获取共同基金持仓
    GET_MUTUALFUND_HOLDERS = "get_mutualfund_holders"
    # 获取内部人购买记录
    GET_INSIDER_PURCHASES = "get_insider_purchases"
    # 获取内部人交易记录
    GET_INSIDER_TRANSACTIONS = "get_insider_transactions"
    # 获取内部人名册
    GET_INSIDER_ROSTER_HOLDERS = "get_insider_roster_holders"
    # 获取股息记录
    GET_DIVIDENDS = "get_dividends"
    # 获取资本利得
    GET_CAPITAL_GAINS = "get_capital_gains"
    # 获取拆股记录
    GET_SPLITS = "get_splits"
    # 获取流通股数
    GET_SHARES = "get_shares"
    # 获取快速概览信息
    GET_FAST_INFO = "get_fast_info"
    # 获取 SEC 文件
    GET_SEC_FILINGS = "get_sec_filings"
    # 获取投资建议摘要
    GET_RECOMMENDATIONS_SUMMARY = "get_recommendations_summary"
    # 获取评级升降记录
    GET_UPGRADES_DOWNGRADES = "get_upgrades_downgrades"
    # 获取盈利数据
    GET_EARNINGS = "get_earnings"
    # 获取利润表
    GET_INCOME_STMT = "get_income_stmt"


# Yahoo Finance 数据查询的输入参数模型
class YahooFinanceSchema(BaseModel):
    # 股票代码
    symbol: str = Field(..., description="The stock symbol to retrieve data for.")
    # 查询方法
    method: YahooFinanceMethod = Field(YahooFinanceMethod.GET_INFO, description="The type of data to retrieve.")
    # 新闻数量
    num_news: int | None = Field(5, description="The number of news articles to retrieve.")


# Yahoo Finance 数据查询组件，支持多种股票和金融市场数据查询
class YfinanceComponent(Component):
    # 组件显示名称
    display_name = "Yahoo! Finance"
    # 组件描述
    description = """Uses [yfinance](https://pypi.org/project/yfinance/) (unofficial package) \
to access financial data and market information from Yahoo! Finance."""
    # 组件图标
    icon = "trending-up"

    # 组件输入参数定义
    inputs = [
        # 股票代码（如 AAPL、GOOG）
        MessageTextInput(
            name="symbol",
            display_name="Stock Symbol",
            info="The stock symbol to retrieve data for (e.g., AAPL, GOOG).",
            tool_mode=True,
        ),
        # 数据查询方法下拉选择
        DropdownInput(
            name="method",
            display_name="Data Method",
            info="The type of data to retrieve.",
            options=list(YahooFinanceMethod),
            value="get_news",
        ),
        # 新闻数量（仅对 get_news 方法有效）
        IntInput(
            name="num_news",
            display_name="Number of News",
            info="The number of news articles to retrieve (only applicable for get_news).",
            value=5,
        ),
    ]

    # 组件输出定义
    outputs = [
        Output(display_name="Table", name="dataframe", method="fetch_content_dataframe"),
    ]

    # 运行模型并返回 DataFrame 格式结果
    def run_model(self) -> DataFrame:
        return self.fetch_content_dataframe()

    # 从 yfinance Ticker 对象获取指定方法的金融数据
    def _fetch_yfinance_data(self, ticker: yf.Ticker, method: YahooFinanceMethod, num_news: int | None) -> str:
        try:
            if method == YahooFinanceMethod.GET_INFO:
                result = ticker.info
            elif method == YahooFinanceMethod.GET_NEWS:
                result = ticker.news[:num_news]
            else:
                result = getattr(ticker, method.value)()
            return pprint.pformat(result)
        except Exception as e:
            error_message = f"Error retrieving data: {e}"
            logger.debug(error_message)
            self.status = error_message
            raise ToolException(error_message) from e

    # 获取 Yahoo Finance 内容
    def fetch_content(self) -> list[Data]:
        try:
            return self._yahoo_finance_tool(
                self.symbol,
                YahooFinanceMethod(self.method),
                self.num_news,
            )
        except ToolException:
            raise
        except Exception as e:
            error_message = f"Unexpected error: {e}"
            logger.debug(error_message)
            self.status = error_message
            raise ToolException(error_message) from e

    # Yahoo Finance 工具核心方法，查询指定股票的金融数据
    def _yahoo_finance_tool(
        self,
        symbol: str,
        method: YahooFinanceMethod,
        num_news: int | None = 5,
    ) -> list[Data]:
        ticker = yf.Ticker(symbol)
        result = self._fetch_yfinance_data(ticker, method, num_news)

        # 新闻类型需要特殊处理，转换为 Data 列表
        if method == YahooFinanceMethod.GET_NEWS:
            data_list = [
                Data(text=f"{article['title']}: {article['link']}", data=article)
                for article in ast.literal_eval(result)
            ]
        else:
            data_list = [Data(text=result, data={"result": result})]

        return data_list

    # 将内容转换为 DataFrame 格式
    def fetch_content_dataframe(self) -> DataFrame:
        data = self.fetch_content()
        return DataFrame(data)
