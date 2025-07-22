import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime
import redis.asyncio as redis

from backend.models.token import TokenData, AnalysisResult
from backend.utils.logger import setup_logger
from backend.utils.env_loader import get_env_var
import uuid

logger = setup_logger(__name__)

class MessageQueue:
    """消息队列服务，用于处理代币分析任务的积压和异步消费"""
    
    def __init__(self, redis_url: str = None):
        # 从环境变量读取Redis URL，如果没有则使用默认值
        self.redis_url = redis_url or get_env_var("REDIS_URL", "redis://localhost:6379/1")
        self.redis_client: Optional[redis.Redis] = None
        self.analysis_queue_key = "token_analysis_queue"
        self.result_channel = "analysis_results"
        self.pending_analyses: Dict[str, AnalysisResult] = {}
        
    async def initialize(self):
        """初始化Redis连接"""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            logger.info("Redis连接成功建立")
        except Exception as e:
            logger.warning(f"Redis连接失败，使用内存队列: {e}")
            self.redis_client = None

        # 无论是否使用Redis，都创建内存队列作为备选
        # 分离任务队列和结果队列
        self._memory_task_queue = asyncio.Queue()  # 任务队列
        self._memory_result_queue = asyncio.Queue()  # 结果队列
            
    async def close(self):
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            
    async def add_analysis_task(self, token_data: TokenData):
        """添加代币分析任务到队列"""
        # 使用安全的JSON序列化方法
        task_data = {
            "token_data": token_data.to_json_dict(),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "task_id": f"{token_data.mint}_{str(uuid.uuid4())}"
        }
        logger.info(f"task_data = {task_data}")
        
        # 创建初始分析结果
        analysis_result = AnalysisResult(
            token_mint=token_data.mint,
            token_symbol=token_data.symbol,
            token_name=token_data.name,
            status="PENDING",
            progress=0.0
        )
        
        self.pending_analyses[token_data.mint] = analysis_result
        
        if self.redis_client:
            try:
                await self.redis_client.lpush(
                    self.analysis_queue_key, 
                    json.dumps(task_data)
                )
                logger.info(f"任务已添加到Redis队列: {token_data.symbol}")
            except Exception as e:
                logger.error(f"添加任务到Redis失败: {e}")
                # 回退到内存队列
                await self._memory_queue.put(task_data)
        else:
            # 使用内存任务队列
            await self._memory_task_queue.put(task_data)
            
        logger.info(f"代币分析任务已入队: {token_data.symbol} ({token_data.mint})")
        
    async def get_analysis_task(self) -> Optional[Dict[str, Any]]:
        """从队列获取分析任务"""
        if self.redis_client:
            try:
                result = await self.redis_client.brpop(self.analysis_queue_key, timeout=1)
                if result:
                    _, task_json = result
                    return json.loads(task_json)
            except Exception as e:
                logger.error(f"从Redis获取任务失败: {e}")
                return None
        else:
            # 使用内存任务队列
            try:
                return await asyncio.wait_for(self._memory_task_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                return None
                
        return None
        
    async def update_analysis_progress(self, token_mint: str, progress: float, status: str = None):
        """更新分析进度"""
        if token_mint in self.pending_analyses:
            analysis = self.pending_analyses[token_mint]
            analysis.progress = progress
            if status:
                analysis.status = status
                
            # 发布进度更新
            await self.publish_analysis_update(analysis)
            
    async def complete_analysis(self, analysis_result: AnalysisResult,type:str="simple"):
        """完成分析任务"""
        analysis_result.status = "COMPLETED"
        analysis_result.progress = 100.0
        analysis_result.analysis_completed_at = datetime.now()
        
        self.pending_analyses[analysis_result.token_mint] = analysis_result
        
        # 发布完成结果
        await self.publish_analysis_result(analysis_result,type)
        
    async def fail_analysis(self, token_mint: str, error_message: str):
        """标记分析失败"""
        if token_mint in self.pending_analyses:
            analysis = self.pending_analyses[token_mint]
            analysis.status = "FAILED"
            analysis.error_message = error_message
            analysis.analysis_completed_at = datetime.now()
            
            await self.publish_analysis_update(analysis)
            
    async def publish_analysis_update(self, analysis_result: AnalysisResult):
        """发布分析更新"""
        message = {
            "type": "analysis_update",
            "data": analysis_result.to_json_dict(),
            "timestamp": datetime.now().isoformat()
        }
        
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    self.result_channel, 
                    json.dumps(message)
                )
            except Exception as e:
                logger.error(f"发布分析更新失败: {e}")
        
        logger.info(f"分析进度更新: {analysis_result.token_symbol} - {analysis_result.progress}%")
        
    async def publish_analysis_result(self, analysis_result: AnalysisResult,type:str="simple"):
        """发布分析结果"""
        
        message = {
            "type": "analysis_complete",
            "data": analysis_result.to_json_dict(),
            "timestamp": datetime.now().isoformat()
        }
        if type=="full":
            message["type"] = "analysis_complete_full"
        # logger.info(f"分析完成 :{analysis_result.token_mint}")
        if self.redis_client:
            try:
                await self.redis_client.publish(
                    self.result_channel, 
                    json.dumps(message)
                )
            except Exception as e:
                logger.error(f"发布分析结果失败: {e}")
                # 回退到内存结果队列，存储JSON字符串
                await self._memory_result_queue.put(json.dumps(message))
        else:
            # 使用内存结果队列，存储JSON字符串
            await self._memory_result_queue.put(json.dumps(message))
            logger.info(f"current memory_result_queue = {self._memory_result_queue}")
        
        logger.info(f"分析完成: {analysis_result.token_symbol}")
        
    async def get_queue_size(self) -> int:
        """获取队列大小"""
        if self.redis_client:
            try:
                return await self.redis_client.llen(self.analysis_queue_key)
            except Exception as e:
                logger.error(f"获取队列大小失败: {e}")
                return 0
        else:
            return self._memory_task_queue.qsize()
            
    async def get_pending_analyses(self) -> Dict[str, AnalysisResult]:
        """获取待处理的分析"""
        return self.pending_analyses.copy()

    async def get_result_message(self) -> Optional[str]:
        """从结果队列获取消息（用于内存模式）"""
        if not self.redis_client:
            try:
                return await asyncio.wait_for(self._memory_result_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                return None
        return None
        
    async def clear_completed_analyses(self, max_age_hours: int = 24):
        """清理已完成的分析（避免内存泄漏）"""
        current_time = datetime.now()
        to_remove = []
        
        for mint, analysis in self.pending_analyses.items():
            if analysis.analysis_completed_at:
                age = current_time - analysis.analysis_completed_at
                if age.total_seconds() > max_age_hours * 3600:
                    to_remove.append(mint)
                    
        for mint in to_remove:
            del self.pending_analyses[mint]
            
        if to_remove:
            logger.info(f"清理了 {len(to_remove)} 个已完成的分析记录")
