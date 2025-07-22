from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel
import json

@dataclass
class CreateEvent:
    """原始的代币创建事件数据"""
    name: str
    symbol: str
    uri: str
    mint: str
    bonding_curve: str
    user: str
    creator: str
    timestamp: int
    virtual_token_reserves: int
    virtual_sol_reserves: int
    real_token_reserves: int
    token_total_supply: int

class TokenData(BaseModel):
    """处理后的代币数据"""
    name: str
    symbol: str
    uri: str
    mint: str
    bonding_curve: str
    user: str
    creator: str
    timestamp: int
    virtual_token_reserves: int
    virtual_sol_reserves: int
    real_token_reserves: int
    token_total_supply: int
    
    # 额外的计算字段
    market_cap: Optional[float] = None
    price_usd: Optional[float] = None
    created_at: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_json_dict(self) -> dict:
        """安全的JSON序列化方法"""
        return self.model_dump(mode='json')

class RiskLevel(BaseModel):
    """风险等级"""
    level: str  # "LOW", "MEDIUM", "HIGH", "CRITICAL"
    score: float  # 0-100
    description: str

class NarrativeAnalysis(BaseModel):
    """叙事分析"""
    category: str  # 例如: "MEME", "DEFI", "AI", "GAMING"
    description: str
    relevance_score: float  # 0-100
    trend_analysis: str

class MarketAnalysis(BaseModel):
    """市场分析"""
    liquidity_analysis: str
    volume_analysis: str
    holder_analysis: str
    price_prediction: str

class WebSearchResult(BaseModel):
    """网络搜索结果"""
    title: str
    url: str
    snippet: str
    relevance_score: float

class SimpleAnalysisResult(BaseModel):
    """简单分析结果"""
    narrative_analysis: str
    risk_assessment: str
    market_analysis: str
    ai_summary: str
    investment_recommendation: str

class AnalysisResult(BaseModel):
    """AI分析结果"""
    token_mint: str
    token_symbol: str
    token_name: str
    
    
    # 分析状态
    status: str  # "PENDING", "ANALYZING", "COMPLETED", "FAILED"
    progress: float  # 0-100
    
    # 分析结果
    narrative_analysis: Optional[NarrativeAnalysis|str] = ""
    risk_assessment: Optional[RiskLevel|str|int] = ""
    market_analysis: Optional[MarketAnalysis|str] = ""
    
    # 搜索结果
    web_search_results: List[WebSearchResult] = []
    tweet_result:List[Dict[str,Any]] = []
    
    # AI总结
    ai_summary: Optional[str] = None
    investment_recommendation: Optional[str] = None
    
    # 元数据
    analysis_started_at: datetime = datetime.now()
    analysis_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    # 标签
    narrative_tag:str = ""
    market_tag:str = ""
    investment_tag:str = ""
    ai_tag:str = ""

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def to_json_dict(self) -> dict:
        """安全的JSON序列化方法"""
        return self.model_dump(mode='json')

class StreamMessage(BaseModel):
    """流式消息格式"""
    type: str  # "new_token", "analysis_update", "analysis_complete", "error"
    data: Dict[str, Any]
    timestamp: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
