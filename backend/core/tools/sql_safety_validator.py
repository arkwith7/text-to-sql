"""
SQL 안전성 검증기 - PostgreSQL 데이터베이스 보호
Text-to-SQL 시스템에서 위험한 쿼리를 사전에 차단합니다.
"""

import re
import logging
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QueryValidationResult:
    """쿼리 검증 결과"""
    is_safe: bool
    reason: str
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    suggested_action: str

class PostgreSQLSafetyValidator:
    """PostgreSQL용 SQL 안전성 검증기"""
    
    # 위험한 키워드들 (대소문자 무관)
    CRITICAL_KEYWORDS = [
        r'\bDROP\s+TABLE\b',
        r'\bDROP\s+DATABASE\b', 
        r'\bDROP\s+SCHEMA\b',
        r'\bTRUNCATE\b',
        r'\bALTER\s+TABLE\b',
        r'\bCREATE\s+TABLE\b',
        r'\bDELETE\s+FROM\b.*\bWHERE\s+1\s*=\s*1\b',  # 전체 삭제
        r'\bUPDATE\b.*\bSET\b.*\bWHERE\s+1\s*=\s*1\b',  # 전체 업데이트
    ]
    
    # 중간 위험 키워드들
    MEDIUM_RISK_KEYWORDS = [
        r'\bDELETE\s+FROM\b',
        r'\bUPDATE\b.*\bSET\b',
        r'\bINSERT\s+INTO\b',
        r'\bCREATE\s+INDEX\b',
        r'\bDROP\s+INDEX\b',
    ]
    
    # 낮은 위험 키워드들 (제한적 허용)
    LOW_RISK_KEYWORDS = [
        r'\bCREATE\s+TEMP\s+TABLE\b',
        r'\bCREATE\s+TEMPORARY\s+TABLE\b',
    ]
    
    # 안전한 읽기 전용 키워드들
    SAFE_KEYWORDS = [
        r'\bSELECT\b',
        r'\bWITH\b',
        r'\bUNION\b',
        r'\bEXPLAIN\b',
        r'\bSHOW\b',
        r'\bDESCRIBE\b',
    ]
    
    def __init__(self, read_only_mode: bool = True):
        """
        초기화
        
        Args:
            read_only_mode: True면 SELECT류 쿼리만 허용
        """
        self.read_only_mode = read_only_mode
        logger.info(f"PostgreSQL 안전성 검증기 초기화 - 읽기전용 모드: {read_only_mode}")
    
    def validate_query(self, query: str) -> QueryValidationResult:
        """
        SQL 쿼리의 안전성을 검증합니다.
        
        Args:
            query: 검증할 SQL 쿼리
            
        Returns:
            QueryValidationResult: 검증 결과
        """
        if not query or not query.strip():
            return QueryValidationResult(
                is_safe=False,
                reason="빈 쿼리입니다",
                risk_level="LOW",
                suggested_action="유효한 쿼리를 입력하세요"
            )
        
        # 쿼리 정규화 (공백, 주석 제거)
        normalized_query = self._normalize_query(query)
        
        # 1. CRITICAL 위험 검사
        critical_result = self._check_critical_risks(normalized_query)
        if not critical_result.is_safe:
            return critical_result
        
        # 2. 읽기전용 모드에서 쓰기 작업 검사
        if self.read_only_mode:
            readonly_result = self._check_readonly_violation(normalized_query)
            if not readonly_result.is_safe:
                return readonly_result
        
        # 3. MEDIUM 위험 검사
        medium_result = self._check_medium_risks(normalized_query)
        if not medium_result.is_safe:
            return medium_result
        
        # 4. 쿼리 복잡도 검사
        complexity_result = self._check_query_complexity(normalized_query)
        if not complexity_result.is_safe:
            return complexity_result
        
        # 5. 무한 루프 가능성 검사
        loop_result = self._check_infinite_loop_risk(normalized_query)
        if not loop_result.is_safe:
            return loop_result
        
        return QueryValidationResult(
            is_safe=True,
            reason="안전한 쿼리입니다",
            risk_level="LOW",
            suggested_action="실행 가능합니다"
        )
    
    def _normalize_query(self, query: str) -> str:
        """쿼리 정규화"""
        # 주석 제거
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # 불필요한 공백 제거
        query = ' '.join(query.split())
        
        return query.upper()
    
    def _check_critical_risks(self, query: str) -> QueryValidationResult:
        """치명적 위험 검사"""
        for pattern in self.CRITICAL_KEYWORDS:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryValidationResult(
                    is_safe=False,
                    reason=f"치명적 위험 쿼리 감지: {pattern}",
                    risk_level="CRITICAL",
                    suggested_action="이 쿼리는 실행할 수 없습니다. 데이터베이스 구조를 변경하거나 데이터를 삭제할 수 있습니다."
                )
        
        return QueryValidationResult(True, "", "LOW", "")
    
    def _check_readonly_violation(self, query: str) -> QueryValidationResult:
        """읽기전용 모드 위반 검사"""
        write_operations = [
            r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b',
            r'\bCREATE\b', r'\bALTER\b', r'\bDROP\b',
            r'\bTRUNCATE\b', r'\bREPLACE\b'
        ]
        
        for pattern in write_operations:
            if re.search(pattern, query, re.IGNORECASE):
                return QueryValidationResult(
                    is_safe=False,
                    reason="읽기전용 모드에서 쓰기 작업은 허용되지 않습니다",
                    risk_level="HIGH",
                    suggested_action="SELECT 쿼리만 사용하세요"
                )
        
        return QueryValidationResult(True, "", "LOW", "")
    
    def _check_medium_risks(self, query: str) -> QueryValidationResult:
        """중간 위험 검사"""
        if not self.read_only_mode:  # 읽기전용이 아닐 때만 검사
            for pattern in self.MEDIUM_RISK_KEYWORDS:
                if re.search(pattern, query, re.IGNORECASE):
                    return QueryValidationResult(
                        is_safe=False,
                        reason=f"위험한 쓰기 작업 감지: {pattern}",
                        risk_level="MEDIUM",
                        suggested_action="쿼리를 신중히 검토하고 WHERE 조건을 확인하세요"
                    )
        
        return QueryValidationResult(True, "", "LOW", "")
    
    def _check_query_complexity(self, query: str) -> QueryValidationResult:
        """쿼리 복잡도 검사"""
        # 중첩 서브쿼리 개수 확인
        subquery_count = len(re.findall(r'\bSELECT\b', query, re.IGNORECASE))
        if subquery_count > 5:
            return QueryValidationResult(
                is_safe=False,
                reason=f"과도하게 복잡한 쿼리 (서브쿼리 {subquery_count}개)",
                risk_level="MEDIUM",
                suggested_action="쿼리를 단순화하거나 여러 개로 분할하세요"
            )
        
        # JOIN 개수 확인
        join_count = len(re.findall(r'\bJOIN\b', query, re.IGNORECASE))
        if join_count > 8:
            return QueryValidationResult(
                is_safe=False,
                reason=f"과도한 JOIN 사용 ({join_count}개)",
                risk_level="MEDIUM", 
                suggested_action="JOIN 수를 줄이거나 쿼리를 최적화하세요"
            )
        
        return QueryValidationResult(True, "", "LOW", "")
    
    def _check_infinite_loop_risk(self, query: str) -> QueryValidationResult:
        """무한 루프 가능성 검사"""
        # WITH RECURSIVE 확인
        if re.search(r'\bWITH\s+RECURSIVE\b', query, re.IGNORECASE):
            # 종료 조건이 있는지 확인
            if not re.search(r'\bWHERE\b.*\bNOT\b', query, re.IGNORECASE):
                return QueryValidationResult(
                    is_safe=False,
                    reason="재귀 쿼리에 명확한 종료 조건이 없습니다",
                    risk_level="HIGH",
                    suggested_action="재귀 쿼리에 적절한 종료 조건을 추가하세요"
                )
        
        # 카티지안 곱 위험 확인
        from_count = len(re.findall(r'\bFROM\b', query, re.IGNORECASE))
        where_count = len(re.findall(r'\bWHERE\b', query, re.IGNORECASE))
        
        if from_count > 1 and where_count == 0:
            return QueryValidationResult(
                is_safe=False,
                reason="카티지안 곱 가능성 - WHERE 조건이 없는 다중 테이블 조인",
                risk_level="MEDIUM",
                suggested_action="적절한 JOIN 조건이나 WHERE 절을 추가하세요"
            )
        
        return QueryValidationResult(True, "", "LOW", "")
    
    def get_safe_query_suggestions(self, original_query: str) -> List[str]:
        """안전한 대체 쿼리 제안"""
        suggestions = []
        
        # 기본적인 SELECT 형태로 변환 제안
        if re.search(r'\bDELETE\b|\bUPDATE\b|\bDROP\b', original_query, re.IGNORECASE):
            suggestions.append("데이터 조회만 하는 SELECT 쿼리로 변경해보세요")
            suggestions.append("예: SELECT * FROM table_name WHERE condition LIMIT 10")
        
        # LIMIT 추가 제안
        if not re.search(r'\bLIMIT\b', original_query, re.IGNORECASE):
            suggestions.append("대량 데이터 조회 시 LIMIT을 추가하세요")
            suggestions.append("예: SELECT * FROM customers LIMIT 100")
        
        return suggestions

# 사용 예시 및 테스트
if __name__ == "__main__":
    validator = PostgreSQLSafetyValidator(read_only_mode=True)
    
    test_queries = [
        "SELECT * FROM customers",
        "DROP TABLE customers",
        "DELETE FROM customers WHERE 1=1",
        "SELECT c.customerid, COUNT(o.orderid) FROM customers c LEFT JOIN orders o ON c.customerid = o.customerid GROUP BY c.customerid",
        "WITH RECURSIVE employee_hierarchy AS (SELECT * FROM employees) SELECT * FROM employee_hierarchy"
    ]
    
    for query in test_queries:
        result = validator.validate_query(query)
        print(f"Query: {query[:50]}...")
        print(f"Safe: {result.is_safe}, Risk: {result.risk_level}")
        print(f"Reason: {result.reason}")
        print("-" * 50)
