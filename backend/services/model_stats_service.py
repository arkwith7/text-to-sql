"""
모델별 상세 통계 서비스
사용자 프로필에서 모델별, 토큰별 비용 정보 제공
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, timezone
from database.connection_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ModelStatsService:
    """모델별 상세 통계 서비스"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def get_user_model_stats(self, user_id: str) -> Dict[str, Any]:
        """
        사용자의 모델별 상세 통계 반환
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            모델별 통계 정보
        """
        try:
            # 모델별 통계 쿼리
            model_stats_query = """
            SELECT 
                llm_model,
                COUNT(*) as query_count,
                SUM(prompt_tokens) as total_input_tokens,
                SUM(completion_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(llm_cost_estimate) as total_cost,
                AVG(llm_cost_estimate) as avg_cost_per_query,
                AVG(total_tokens) as avg_tokens_per_query,
                MIN(created_at) as first_used,
                MAX(created_at) as last_used
            FROM query_analytics 
            WHERE user_id = :user_id 
            AND llm_model IS NOT NULL 
            AND total_tokens > 0
            GROUP BY llm_model
            ORDER BY total_cost DESC
            """
            
            result = await self.db_manager.execute_query_safe(
                model_stats_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            if not result['success'] or not result['data']:
                return {"models": [], "summary": self._get_empty_summary()}
            
            models = []
            total_cost = 0
            total_tokens = 0
            total_queries = 0
            
            for row in result['data']:
                model_info = {
                    "model_name": row['llm_model'],
                    "query_count": row['query_count'],
                    "total_input_tokens": row['total_input_tokens'] or 0,
                    "total_output_tokens": row['total_output_tokens'] or 0,
                    "total_tokens": row['total_tokens'] or 0,
                    "total_cost": round(row['total_cost'] or 0, 6),
                    "avg_cost_per_query": round(row['avg_cost_per_query'] or 0, 6),
                    "avg_tokens_per_query": round(row['avg_tokens_per_query'] or 0, 1),
                    "cost_per_token": round((row['total_cost'] or 0) / (row['total_tokens'] or 1), 8),
                    "input_cost": round((row['total_input_tokens'] or 0) * 0.00015 / 1000, 6),
                    "output_cost": round((row['total_output_tokens'] or 0) * 0.0006 / 1000, 6),
                    "first_used": row['first_used'],
                    "last_used": row['last_used']
                }
                models.append(model_info)
                
                total_cost += model_info['total_cost']
                total_tokens += model_info['total_tokens']
                total_queries += model_info['query_count']
            
            # 전체 요약 정보
            summary = {
                "total_models_used": len(models),
                "total_cost": round(total_cost, 6),
                "total_tokens": total_tokens,
                "total_queries": total_queries,
                "avg_cost_per_query": round(total_cost / total_queries if total_queries > 0 else 0, 6),
                "avg_tokens_per_query": round(total_tokens / total_queries if total_queries > 0 else 0, 1),
                "most_used_model": models[0]['model_name'] if models else None,
                "most_expensive_model": max(models, key=lambda x: x['avg_cost_per_query'])['model_name'] if models else None
            }
            
            return {
                "models": models,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"모델별 통계 조회 실패: {e}")
            return {"models": [], "summary": self._get_empty_summary()}
    
    async def get_user_token_breakdown(self, user_id: str) -> Dict[str, Any]:
        """
        사용자의 토큰 사용 분석
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            토큰 사용 분석 정보
        """
        try:
            # 토큰 사용 분석 쿼리
            token_analysis_query = """
            SELECT 
                SUM(prompt_tokens) as total_input_tokens,
                SUM(completion_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(prompt_tokens * 0.00015 / 1000) as input_cost,
                SUM(completion_tokens * 0.0006 / 1000) as output_cost,
                COUNT(*) as total_queries,
                AVG(prompt_tokens) as avg_input_per_query,
                AVG(completion_tokens) as avg_output_per_query
            FROM query_analytics 
            WHERE user_id = :user_id 
            AND total_tokens > 0
            """
            
            result = await self.db_manager.execute_query_safe(
                token_analysis_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            if not result['success'] or not result['data']:
                return self._get_empty_token_breakdown()
            
            data = result['data'][0]
            
            total_input = data['total_input_tokens'] or 0
            total_output = data['total_output_tokens'] or 0
            total_tokens = data['total_tokens'] or 0
            
            return {
                "total_input_tokens": total_input,
                "total_output_tokens": total_output,
                "total_tokens": total_tokens,
                "input_percentage": round(total_input / total_tokens * 100 if total_tokens > 0 else 0, 1),
                "output_percentage": round(total_output / total_tokens * 100 if total_tokens > 0 else 0, 1),
                "input_cost": round(data['input_cost'] or 0, 6),
                "output_cost": round(data['output_cost'] or 0, 6),
                "total_cost": round((data['input_cost'] or 0) + (data['output_cost'] or 0), 6),
                "cost_per_input_token": round(0.00015 / 1000, 8),
                "cost_per_output_token": round(0.0006 / 1000, 8),
                "avg_input_per_query": round(data['avg_input_per_query'] or 0, 1),
                "avg_output_per_query": round(data['avg_output_per_query'] or 0, 1),
                "total_queries": data['total_queries'] or 0
            }
            
        except Exception as e:
            logger.error(f"토큰 분석 실패: {e}")
            return self._get_empty_token_breakdown()
    
    async def get_user_daily_model_stats(self, user_id: str, days: int = 30) -> Dict[str, Any]:
        """
        일별 모델 사용 통계
        
        Args:
            user_id: 사용자 ID
            days: 조회할 일수
            
        Returns:
            일별 모델 사용 통계
        """
        try:
            daily_stats_query = """
            SELECT 
                DATE(created_at) as date,
                llm_model,
                COUNT(*) as queries,
                SUM(total_tokens) as tokens,
                SUM(llm_cost_estimate) as cost
            FROM query_analytics 
            WHERE user_id = :user_id 
            AND created_at >= DATE('now', '-{} days')
            AND llm_model IS NOT NULL
            AND total_tokens > 0
            GROUP BY DATE(created_at), llm_model
            ORDER BY DATE(created_at) DESC, cost DESC
            """.format(days)
            
            result = await self.db_manager.execute_query_safe(
                daily_stats_query,
                params={"user_id": user_id},
                database_type="app"
            )
            
            if not result['success'] or not result['data']:
                return {"daily_stats": []}
            
            # 날짜별로 그룹화
            daily_data = {}
            for row in result['data']:
                date = row['date']
                if date not in daily_data:
                    daily_data[date] = {
                        "date": date,
                        "models": [],
                        "total_queries": 0,
                        "total_tokens": 0,
                        "total_cost": 0
                    }
                
                model_data = {
                    "model": row['llm_model'],
                    "queries": row['queries'],
                    "tokens": row['tokens'] or 0,
                    "cost": round(row['cost'] or 0, 6)
                }
                
                daily_data[date]["models"].append(model_data)
                daily_data[date]["total_queries"] += model_data["queries"]
                daily_data[date]["total_tokens"] += model_data["tokens"]
                daily_data[date]["total_cost"] += model_data["cost"]
            
            # 총 비용 반올림
            for date_data in daily_data.values():
                date_data["total_cost"] = round(date_data["total_cost"], 6)
            
            return {
                "daily_stats": list(daily_data.values())
            }
            
        except Exception as e:
            logger.error(f"일별 모델 통계 실패: {e}")
            return {"daily_stats": []}
    
    def _get_empty_summary(self) -> Dict[str, Any]:
        """빈 요약 정보 반환"""
        return {
            "total_models_used": 0,
            "total_cost": 0.0,
            "total_tokens": 0,
            "total_queries": 0,
            "avg_cost_per_query": 0.0,
            "avg_tokens_per_query": 0.0,
            "most_used_model": None,
            "most_expensive_model": None
        }
    
    def _get_empty_token_breakdown(self) -> Dict[str, Any]:
        """빈 토큰 분석 정보 반환"""
        return {
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "input_percentage": 0.0,
            "output_percentage": 0.0,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0,
            "cost_per_input_token": 0.00000015,
            "cost_per_output_token": 0.0000006,
            "avg_input_per_query": 0.0,
            "avg_output_per_query": 0.0,
            "total_queries": 0
        }
