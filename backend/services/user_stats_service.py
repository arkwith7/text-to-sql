"""
사용자 통계 서비스 - 모델별, 토큰별 상세 정보 제공
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class UserStatsService:
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def get_model_breakdown(self, user_id: str) -> Dict[str, Any]:
        """모델별 사용량 및 비용 분석"""
        try:
            query = """
            SELECT 
                llm_model,
                COUNT(*) as query_count,
                SUM(prompt_tokens) as total_prompt_tokens,
                SUM(completion_tokens) as total_completion_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(llm_cost_estimate) as total_cost,
                AVG(llm_cost_estimate) as avg_cost_per_query,
                AVG(total_tokens) as avg_tokens_per_query
            FROM query_analytics 
            WHERE user_id = :user_id AND llm_model IS NOT NULL
            GROUP BY llm_model
            ORDER BY total_cost DESC
            """
            
            result = await self.db_manager.execute_query_safe(
                query, params={"user_id": user_id}, database_type="app"
            )
            
            if result['success'] and result['data']:
                return {
                    "model_breakdown": [
                        {
                            "model": row['llm_model'],
                            "query_count": row['query_count'],
                            "total_tokens": row['total_tokens'],
                            "prompt_tokens": row['total_prompt_tokens'],
                            "completion_tokens": row['total_completion_tokens'],
                            "total_cost": round(row['total_cost'], 6),
                            "avg_cost_per_query": round(row['avg_cost_per_query'], 6),
                            "avg_tokens_per_query": round(row['avg_tokens_per_query'], 2)
                        }
                        for row in result['data']
                    ]
                }
            return {"model_breakdown": []}
            
        except Exception as e:
            logger.error(f"모델별 통계 조회 실패: {e}")
            return {"model_breakdown": []}
