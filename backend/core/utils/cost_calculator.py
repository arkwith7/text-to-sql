"""
비용 계산 유틸리티
다양한 LLM 모델의 토큰 단가와 비용 계산 기능을 제공
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelPricing:
    """LLM 모델별 토큰 단가 정보"""
    
    # 토큰 단가 (USD per 1K tokens)
    PRICING_TABLE = {
        # OpenAI GPT-4 계열
        "gpt-4o": {
            "input_price_per_1k": 0.0025,
            "output_price_per_1k": 0.01,
            "currency": "USD"
        },
        "gpt-4o-mini": {
            "input_price_per_1k": 0.00015,
            "output_price_per_1k": 0.0006,
            "currency": "USD"
        },
        "gpt-4": {
            "input_price_per_1k": 0.03,
            "output_price_per_1k": 0.06,
            "currency": "USD"
        },
        "gpt-4-turbo": {
            "input_price_per_1k": 0.01,
            "output_price_per_1k": 0.03,
            "currency": "USD"
        },
        "gpt-3.5-turbo": {
            "input_price_per_1k": 0.0015,
            "output_price_per_1k": 0.002,
            "currency": "USD"
        },
        # Claude 계열 (참고용)
        "claude-3-sonnet": {
            "input_price_per_1k": 0.003,
            "output_price_per_1k": 0.015,
            "currency": "USD"
        },
        "claude-3-haiku": {
            "input_price_per_1k": 0.00025,
            "output_price_per_1k": 0.00125,
            "currency": "USD"
        },
        # 기본값 (알 수 없는 모델)
        "default": {
            "input_price_per_1k": 0.001,
            "output_price_per_1k": 0.002,
            "currency": "USD"
        }
    }
    
    @classmethod
    def get_model_pricing(cls, model_name: str) -> Dict[str, Any]:
        """모델명으로 단가 정보 조회"""
        try:
            # 정확한 모델명 매칭
            if model_name in cls.PRICING_TABLE:
                return cls.PRICING_TABLE[model_name]
            
            # 부분 매칭 시도
            model_lower = model_name.lower()
            for key in cls.PRICING_TABLE.keys():
                if key != "default" and key.lower() in model_lower:
                    logger.info(f"모델 '{model_name}'을 '{key}'로 매칭")
                    return cls.PRICING_TABLE[key]
            
            # 기본값 사용
            logger.warning(f"알 수 없는 모델 '{model_name}', 기본 단가 적용")
            return cls.PRICING_TABLE["default"]
            
        except Exception as e:
            logger.error(f"모델 단가 조회 실패: {e}")
            return cls.PRICING_TABLE["default"]


def calculate_token_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model_name: str = "gpt-4o-mini"
) -> Dict[str, Any]:
    """
    토큰 사용량 기반 비용 계산
    
    Args:
        prompt_tokens: 입력 토큰 수
        completion_tokens: 출력 토큰 수
        model_name: 모델명
        
    Returns:
        비용 계산 결과 딕셔너리
    """
    try:
        # 모델 단가 조회
        pricing = ModelPricing.get_model_pricing(model_name)
        
        # 비용 계산
        input_cost = (prompt_tokens / 1000) * pricing["input_price_per_1k"]
        output_cost = (completion_tokens / 1000) * pricing["output_price_per_1k"]
        total_cost = input_cost + output_cost
        
        result = {
            "model_name": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(total_cost, 6),
            "currency": pricing["currency"],
            "pricing_info": pricing,
            "calculated_at": datetime.utcnow().isoformat()
        }
        
        logger.debug(f"비용 계산 완료: {result}")
        return result
        
    except Exception as e:
        logger.error(f"비용 계산 실패: {e}")
        return {
            "model_name": model_name,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
            "input_cost": 0.0,
            "output_cost": 0.0,
            "total_cost": 0.0,
            "currency": "USD",
            "error": str(e),
            "calculated_at": datetime.utcnow().isoformat()
        }


def calculate_cost_from_usage(
    token_usage: Dict[str, int],
    model_name: str = "gpt-4o-mini"
) -> float:
    """
    토큰 사용량 딕셔너리에서 비용 계산
    
    Args:
        token_usage: 토큰 사용량 정보
        model_name: 모델명
        
    Returns:
        총 비용 (USD)
    """
    try:
        prompt_tokens = token_usage.get("prompt_tokens", 0)
        completion_tokens = token_usage.get("completion_tokens", 0)
        
        cost_info = calculate_token_cost(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model_name=model_name
        )
        
        return cost_info.get("total_cost", 0.0)
        
    except Exception as e:
        logger.error(f"사용량 기반 비용 계산 실패: {e}")
        return 0.0


def get_supported_models() -> list:
    """지원되는 모델 목록 반환"""
    models = list(ModelPricing.PRICING_TABLE.keys())
    models.remove("default")  # 기본값 제외
    return sorted(models)


def get_model_info(model_name: str) -> Dict[str, Any]:
    """모델 정보 조회"""
    pricing = ModelPricing.get_model_pricing(model_name)
    return {
        "model_name": model_name,
        "supported": model_name in ModelPricing.PRICING_TABLE,
        "pricing": pricing,
        "cost_per_1k_input": pricing["input_price_per_1k"],
        "cost_per_1k_output": pricing["output_price_per_1k"],
        "currency": pricing["currency"]
    }
