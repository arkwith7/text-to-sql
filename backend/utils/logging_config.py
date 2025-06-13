"""
로깅 설정 모듈 - 파일 기반 로깅과 구조화된 로그 관리
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from core.config import get_settings

class JsonFormatter(logging.Formatter):
    """JSON 형태로 로그를 포맷하는 커스텀 포맷터"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # 추가 컨텍스트 정보가 있으면 포함
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry['session_id'] = record.session_id
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        if hasattr(record, 'sql_query'):
            log_entry['sql_query'] = record.sql_query
        if hasattr(record, 'execution_time'):
            log_entry['execution_time'] = record.execution_time
        if hasattr(record, 'error_details'):
            log_entry['error_details'] = record.error_details
        
        # 예외 정보 포함
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)

def setup_logging():
    """로깅 설정 초기화"""
    settings = get_settings()
    
    # 로그 디렉토리 생성
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # 기존 핸들러 제거
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 1. 콘솔 핸들러 (개발 환경용)
    if settings.environment == "development":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # 2. 전체 로그 파일 핸들러 (JSON 형태)
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(file_handler)
    
    # 3. 에러 로그 파일 핸들러
    error_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JsonFormatter())
    root_logger.addHandler(error_handler)
    
    # 4. API 요청 로그 파일 핸들러
    api_logger = logging.getLogger("api_requests")
    api_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "api_requests.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    api_handler.setLevel(logging.INFO)
    api_handler.setFormatter(JsonFormatter())
    api_logger.addHandler(api_handler)
    api_logger.setLevel(logging.INFO)
    api_logger.propagate = False  # 중복 로깅 방지
    
    # 5. SQL 쿼리 로그 파일 핸들러
    sql_logger = logging.getLogger("sql_queries")
    sql_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "sql_queries.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    sql_handler.setLevel(logging.INFO)
    sql_handler.setFormatter(JsonFormatter())
    sql_logger.addHandler(sql_handler)
    sql_logger.setLevel(logging.INFO)
    sql_logger.propagate = False
    
    # 6. 채팅 로그 파일 핸들러
    chat_logger = logging.getLogger("chat_sessions")
    chat_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "chat_sessions.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    chat_handler.setLevel(logging.INFO)
    chat_handler.setFormatter(JsonFormatter())
    chat_logger.addHandler(chat_handler)
    chat_logger.setLevel(logging.INFO)
    chat_logger.propagate = False
    
    # 7. 인증 로그 파일 핸들러
    auth_logger = logging.getLogger("authentication")
    auth_handler = logging.handlers.RotatingFileHandler(
        filename=log_dir / "authentication.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    auth_handler.setLevel(logging.INFO)
    auth_handler.setFormatter(JsonFormatter())
    auth_logger.addHandler(auth_handler)
    auth_logger.setLevel(logging.INFO)
    auth_logger.propagate = False
    
    logging.info("로깅 시스템이 초기화되었습니다.")

def get_logger_with_context(name: str, **context) -> logging.LoggerAdapter:
    """컨텍스트 정보를 포함한 로거 어댑터 반환"""
    logger = logging.getLogger(name)
    return logging.LoggerAdapter(logger, context)

class RequestLogger:
    """API 요청/응답 로깅을 위한 헬퍼 클래스"""
    
    @staticmethod
    def log_request(
        request_id: str,
        method: str,
        path: str,
        user_id: str = None,
        body: Dict[str, Any] = None,
        query_params: Dict[str, Any] = None
    ):
        """API 요청 로깅"""
        api_logger = logging.getLogger("api_requests")
        
        # 민감한 정보 마스킹
        masked_body = RequestLogger._mask_sensitive_data(body) if body else None
        
        extra = {
            'request_id': request_id,
            'user_id': user_id,
            'request_method': method,
            'request_path': path,
            'request_body': masked_body,
            'query_params': query_params,
            'event_type': 'api_request'
        }
        
        api_logger.info(
            f"API 요청: {method} {path}",
            extra=extra
        )
    
    @staticmethod
    def log_response(
        request_id: str,
        status_code: int,
        response_time: float,
        user_id: str = None,
        response_size: int = None,
        error_message: str = None
    ):
        """API 응답 로깅"""
        api_logger = logging.getLogger("api_requests")
        
        extra = {
            'request_id': request_id,
            'user_id': user_id,
            'status_code': status_code,
            'response_time_ms': round(response_time * 1000, 2),
            'response_size_bytes': response_size,
            'error_message': error_message,
            'event_type': 'api_response'
        }
        
        level = logging.ERROR if status_code >= 400 else logging.INFO
        api_logger.log(
            level,
            f"API 응답: {status_code} ({extra['response_time_ms']}ms)",
            extra=extra
        )
    
    @staticmethod
    def _mask_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """민감한 데이터 마스킹"""
        if not isinstance(data, dict):
            return data
        
        sensitive_keys = {'password', 'token', 'secret', 'key', 'auth'}
        masked_data = {}
        
        for key, value in data.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                masked_data[key] = "***MASKED***"
            elif isinstance(value, dict):
                masked_data[key] = RequestLogger._mask_sensitive_data(value)
            else:
                masked_data[key] = value
        
        return masked_data

class SQLLogger:
    """SQL 쿼리 로깅을 위한 헬퍼 클래스"""
    
    @staticmethod
    def log_query_execution(
        query: str,
        params: Dict[str, Any] = None,
        execution_time: float = None,
        result_count: int = None,
        user_id: str = None,
        session_id: str = None,
        success: bool = True,
        error_message: str = None
    ):
        """SQL 쿼리 실행 로깅"""
        sql_logger = logging.getLogger("sql_queries")
        
        extra = {
            'user_id': user_id,
            'session_id': session_id,
            'sql_query': query,
            'query_params': params,
            'execution_time': execution_time,
            'result_count': result_count,
            'success': success,
            'error_message': error_message,
            'event_type': 'sql_execution'
        }
        
        level = logging.ERROR if not success else logging.INFO
        message = f"SQL 쿼리 {'실행 완료' if success else '실행 실패'}"
        if execution_time:
            message += f" ({execution_time:.3f}s)"
        
        sql_logger.log(level, message, extra=extra)

class ChatLogger:
    """채팅 세션 로깅을 위한 헬퍼 클래스"""
    
    @staticmethod
    def log_chat_message(
        session_id: str,
        user_id: str,
        message_type: str,
        content: str,
        query_result: Dict[str, Any] = None,
        execution_time: float = None
    ):
        """채팅 메시지 로깅"""
        chat_logger = logging.getLogger("chat_sessions")
        
        # 긴 컨텐츠는 요약
        content_preview = content[:200] + "..." if len(content) > 200 else content
        
        extra = {
            'session_id': session_id,
            'user_id': user_id,
            'message_type': message_type,
            'content_preview': content_preview,
            'content_length': len(content),
            'has_query_result': query_result is not None,
            'execution_time': execution_time,
            'event_type': 'chat_message'
        }
        
        chat_logger.info(
            f"채팅 메시지: {message_type} (길이: {len(content)})",
            extra=extra
        )
    
    @staticmethod
    def log_session_event(
        session_id: str,
        user_id: str,
        event_type: str,
        details: Dict[str, Any] = None
    ):
        """채팅 세션 이벤트 로깅"""
        chat_logger = logging.getLogger("chat_sessions")
        
        extra = {
            'session_id': session_id,
            'user_id': user_id,
            'event_type': f'session_{event_type}',
            'event_details': details
        }
        
        chat_logger.info(f"세션 이벤트: {event_type}", extra=extra)

class AuthLogger:
    """인증 관련 로깅을 위한 헬퍼 클래스"""
    
    @staticmethod
    def log_auth_event(
        event_type: str,
        user_id: str = None,
        email: str = None,
        success: bool = True,
        ip_address: str = None,
        user_agent: str = None,
        error_message: str = None
    ):
        """인증 이벤트 로깅"""
        auth_logger = logging.getLogger("authentication")
        
        extra = {
            'user_id': user_id,
            'email': email,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'error_message': error_message,
            'event_type': f'auth_{event_type}'
        }
        
        level = logging.ERROR if not success else logging.INFO
        message = f"인증 이벤트: {event_type} {'성공' if success else '실패'}"
        
        auth_logger.log(level, message, extra=extra)