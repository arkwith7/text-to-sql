"""
토큰 사용량 추정 모듈
실제 API 응답에서 토큰 정보를 얻지 못할 때 텍스트 기반으로 토큰을 추정
"""

import re
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

class TokenEstimator:
    """
    텍스트 기반 토큰 사용량 추정기
    OpenAI의 tiktoken 라이브러리를 사용하거나 간단한 추정 공식 사용
    """
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = model_name
        self.tiktoken_encoder = None
        self._init_tiktoken()
        
    def _init_tiktoken(self):
        """tiktoken 초기화 (선택적)"""
        try:
            import tiktoken
            # GPT-4o-mini는 cl100k_base 인코딩 사용
            self.tiktoken_encoder = tiktoken.get_encoding("cl100k_base")
            logger.info("✅ tiktoken 인코더 초기화 완료")
        except ImportError:
            logger.warning("tiktoken 라이브러리 없음 - 간단한 추정 방식 사용")
            self.tiktoken_encoder = None
    
    def estimate_tokens(self, text: str) -> int:
        """
        텍스트의 토큰 수 추정
        
        Args:
            text: 추정할 텍스트
            
        Returns:
            추정된 토큰 수
        """
        if not text:
            return 0
            
        if self.tiktoken_encoder:
            # tiktoken 사용 (정확)
            return len(self.tiktoken_encoder.encode(text))
        else:
            # 간단한 추정 (대략적)
            # 영어: ~4글자당 1토큰, 한국어: ~2글자당 1토큰
            korean_chars = len(re.findall(r'[가-힣]', text))
            other_chars = len(text) - korean_chars
            
            estimated_tokens = (korean_chars / 2) + (other_chars / 4)
            return max(1, int(estimated_tokens))
    
    def estimate_chat_tokens(self, messages: List[Dict], system_prompt: str = "") -> Dict[str, int]:
        """
        채팅 메시지들의 토큰 수 추정
        
        Args:
            messages: 채팅 메시지 리스트
            system_prompt: 시스템 프롬프트
            
        Returns:
            토큰 사용량 딕셔너리
        """
        prompt_tokens = 0
        
        # 시스템 프롬프트
        if system_prompt:
            prompt_tokens += self.estimate_tokens(system_prompt)
        
        # 메시지들
        for message in messages:
            if isinstance(message, dict) and 'content' in message:
                prompt_tokens += self.estimate_tokens(str(message['content']))
        
        return {
            'prompt_tokens': prompt_tokens,
            'completion_tokens': 0,  # 응답 전에는 알 수 없음
            'total_tokens': prompt_tokens
        }
    
    def estimate_completion_tokens(self, response_text: str) -> Dict[str, int]:
        """
        응답 텍스트의 토큰 수 추정
        
        Args:
            response_text: LLM 응답 텍스트
            
        Returns:
            완료된 토큰 사용량 딕셔너리
        """
        completion_tokens = self.estimate_tokens(response_text)
        
        return {
            'completion_tokens': completion_tokens
        }
    
    def estimate_agent_execution_tokens(self, 
                                     question: str, 
                                     response: str, 
                                     intermediate_steps: List = None,
                                     system_prompt: str = "") -> Dict[str, int]:
        """
        Agent 실행의 전체 토큰 사용량 추정
        
        Args:
            question: 사용자 질문
            response: 최종 응답
            intermediate_steps: 중간 단계들
            system_prompt: 시스템 프롬프트
            
        Returns:
            전체 토큰 사용량
        """
        # 기본 프롬프트 토큰
        prompt_tokens = self.estimate_tokens(system_prompt) + self.estimate_tokens(question)
        
        # 중간 단계들의 토큰 (도구 호출, 관찰 등)
        if intermediate_steps:
            for step in intermediate_steps:
                if isinstance(step, (list, tuple)) and len(step) >= 2:
                    action, observation = step[0], step[1]
                    
                    # 액션 토큰 (도구 호출)
                    if hasattr(action, 'log'):
                        prompt_tokens += self.estimate_tokens(action.log)
                    if hasattr(action, 'tool_input'):
                        prompt_tokens += self.estimate_tokens(str(action.tool_input))
                    
                    # 관찰 토큰 (도구 응답)
                    prompt_tokens += self.estimate_tokens(str(observation))
        
        # 응답 토큰
        completion_tokens = self.estimate_tokens(response)
        
        # 총 토큰 (OpenAI API 오버헤드 고려하여 10% 추가)
        total_prompt = int(prompt_tokens * 1.1)
        total_completion = int(completion_tokens * 1.1)
        total_tokens = total_prompt + total_completion
        
        # 비용 계산 (GPT-4o-mini 기준)
        input_cost = (total_prompt / 1000) * 0.00015
        output_cost = (total_completion / 1000) * 0.0006
        total_cost = input_cost + output_cost
        
        return {
            'prompt_tokens': total_prompt,
            'completion_tokens': total_completion,
            'total_tokens': total_tokens,
            'total_cost': total_cost,
            'successful_requests': 1,
            'estimation_method': 'text_based'
        }

# 전역 추정기 인스턴스
token_estimator = TokenEstimator()
