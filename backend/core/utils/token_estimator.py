"""
토큰 사용량 추정 유틸리티
Azure OpenAI에서 실제 토큰 정보를 제공하지 않을 때 사용
"""

import logging
import tiktoken
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class TokenEstimator:
    """GPT 모델의 토큰 사용량을 추정하는 클래스"""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """
        토큰 추정기 초기화
        
        Args:
            model_name: OpenAI 모델 이름
        """
        self.model_name = model_name
        self.encoding = self._get_encoding(model_name)
        logger.info(f"TokenEstimator 초기화 완료 - 모델: {model_name}")
        
    def _get_encoding(self, model_name: str):
        """모델에 맞는 토큰 인코딩 가져오기"""
        try:
            # GPT-4 계열 모델들은 cl100k_base 인코딩 사용
            if "gpt-4" in model_name.lower() or "gpt-3.5" in model_name.lower():
                return tiktoken.get_encoding("cl100k_base")
            else:
                # 기본값으로 cl100k_base 사용
                return tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.warning(f"토큰 인코딩 로드 실패: {e}, 기본 인코딩 사용")
            return tiktoken.get_encoding("cl100k_base")
    
    def count_tokens(self, text: str) -> int:
        """텍스트의 토큰 수 계산"""
        try:
            if not text:
                return 0
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"토큰 계산 실패: {e}")
            # 대략적인 추정: 영어는 4자/토큰, 한국어는 2자/토큰
            return max(1, len(text) // 3)
    
    def estimate_tokens_from_messages(self, messages: List[Dict[str, Any]]) -> int:
        """메시지 리스트에서 토큰 수 추정"""
        try:
            total_tokens = 0
            
            for message in messages:
                # 메시지 오버헤드 (역할, 구조 등)
                total_tokens += 4  # 메시지당 기본 오버헤드
                
                # 역할 토큰
                if "role" in message:
                    total_tokens += self.count_tokens(message["role"])
                
                # 내용 토큰
                if "content" in message:
                    if isinstance(message["content"], str):
                        total_tokens += self.count_tokens(message["content"])
                    elif isinstance(message["content"], list):
                        for content_item in message["content"]:
                            if isinstance(content_item, dict) and "text" in content_item:
                                total_tokens += self.count_tokens(content_item["text"])
            
            # 전체 대화 오버헤드
            total_tokens += 2
            
            return total_tokens
            
        except Exception as e:
            logger.warning(f"메시지 토큰 추정 실패: {e}")
            return 0
    
    def estimate_from_question_and_answer(
        self, 
        question: str, 
        answer: str,
        system_prompt: str = "",
        tool_calls: Optional[List[Dict]] = None
    ) -> Dict[str, int]:
        """질문과 답변에서 토큰 사용량 추정"""
        try:
            prompt_tokens = 0
            completion_tokens = 0
            
            # 시스템 프롬프트 토큰
            if system_prompt:
                prompt_tokens += self.count_tokens(system_prompt)
                prompt_tokens += 4  # 메시지 오버헤드
            
            # 질문 토큰
            prompt_tokens += self.count_tokens(question)
            prompt_tokens += 4  # 메시지 오버헤드
            
            # 도구 호출이 있는 경우 (function calls)
            if tool_calls:
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict):
                        tool_str = str(tool_call)
                        prompt_tokens += self.count_tokens(tool_str)
                        prompt_tokens += 10  # function call 오버헤드
            
            # 답변 토큰 (Text-to-SQL Agent의 실제 출력량을 반영하여 2.5배 가중치 적용)
            base_completion_tokens = self.count_tokens(answer)
            completion_tokens = int(base_completion_tokens * 2.5)  # Agent의 중간 생성물들을 고려한 가중치
            
            # 전체 대화 오버헤드
            prompt_tokens += 10
            
            total_tokens = prompt_tokens + completion_tokens
            
            # 비용 계산 (GPT-4o-mini 기준)
            input_cost = (prompt_tokens / 1000) * 0.00015  # $0.00015 per 1K input tokens
            output_cost = (completion_tokens / 1000) * 0.0006  # $0.0006 per 1K output tokens
            total_cost = input_cost + output_cost
            
            result = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "estimated_cost": round(total_cost, 6),
                "successful_requests": 1
            }
            
            logger.debug(f"토큰 추정 결과: {result}")
            return result
            
        except Exception as e:
            logger.error(f"토큰 추정 실패: {e}")
            return {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "estimated_cost": 0.0,
                "successful_requests": 0
            }
    
    def estimate_from_intermediate_steps(
        self,
        question: str,
        answer: str,
        intermediate_steps: List[tuple],
        system_prompt: str = ""
    ) -> Dict[str, int]:
        """중간 단계들을 포함한 토큰 사용량 추정"""
        try:
            # 기본 질문/답변 토큰
            base_tokens = self.estimate_from_question_and_answer(
                question=question,
                answer=answer,
                system_prompt=system_prompt
            )
            
            # 중간 단계들의 토큰 추가
            additional_prompt_tokens = 0
            additional_completion_tokens = 0
            
            for step in intermediate_steps:
                if isinstance(step, tuple) and len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    # Action (도구 호출) 토큰 - 가중치 적용
                    if hasattr(action, 'tool') and hasattr(action, 'tool_input'):
                        tool_text = f"{action.tool}: {str(action.tool_input)}"
                        base_tokens = self.count_tokens(tool_text)
                        additional_completion_tokens += int(base_tokens * 2.5)  # 가중치 적용
                    
                    # Observation (도구 결과) 토큰
                    observation_text = str(observation)
                    if len(observation_text) > 1000:  # 긴 결과는 자르기
                        observation_text = observation_text[:1000] + "..."
                    additional_prompt_tokens += self.count_tokens(observation_text)
            
            # 결과 업데이트
            result = base_tokens.copy()
            result["prompt_tokens"] += additional_prompt_tokens
            result["completion_tokens"] += additional_completion_tokens
            result["total_tokens"] = result["prompt_tokens"] + result["completion_tokens"]
            
            # 비용 재계산
            input_cost = (result["prompt_tokens"] / 1000) * 0.00015
            output_cost = (result["completion_tokens"] / 1000) * 0.0006
            result["estimated_cost"] = round(input_cost + output_cost, 6)
            
            logger.info(f"중간 단계 포함 토큰 추정: {result}")
            return result
            
        except Exception as e:
            logger.error(f"중간 단계 토큰 추정 실패: {e}")
            return self.estimate_from_question_and_answer(question, answer, system_prompt)


# 전역 토큰 추정기 인스턴스
_token_estimator = None


def get_token_estimator(model_name: str = "gpt-4o-mini") -> TokenEstimator:
    """전역 토큰 추정기 인스턴스 반환"""
    global _token_estimator
    if _token_estimator is None or _token_estimator.model_name != model_name:
        _token_estimator = TokenEstimator(model_name)
    return _token_estimator
