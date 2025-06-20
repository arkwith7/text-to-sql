"""
Database Schema Service
스키마 정보 캐싱, LLM 문서화, 동적 스키마 조회 서비스
"""

import json
import hashlib
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from sqlalchemy.orm import selectinload

from models.models import DatabaseSchema, DatabaseConnection
from database.connection_manager import db_manager
from core.llm_providers.azure_openai_provider import AzureOpenAIProvider
from core.config import settings


class SchemaService:
    def __init__(self, session: AsyncSession):
        self.session = session
        # OpenAI Provider는 필요할 때만 초기화
        self.llm_provider = None

    def _get_llm_provider(self):
        """LLM Provider를 지연 초기화"""
        if self.llm_provider is None:
            try:
                config = {
                    "api_key": settings.azure_openai_api_key,
                    "endpoint": settings.azure_openai_endpoint,
                    "api_version": settings.azure_openai_api_version,
                    "deployment_name": settings.azure_openai_deployment_name
                }
                self.llm_provider = AzureOpenAIProvider(config)
            except Exception as e:
                print(f"⚠️ LLM Provider 초기화 실패: {str(e)}")
                self.llm_provider = None
        return self.llm_provider

    async def get_schema_info(self, user_id: str, connection_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        스키마 정보를 가져옵니다. 캐시된 정보가 있으면 사용하고, 없으면 DB에서 조회 후 캐싱합니다.
        """
        try:
            print(f"📋 SchemaService.get_schema_info 시작: user_id={user_id}, connection_id={connection_id}")
            # 1. 캐시된 스키마 정보 확인
            if not force_refresh:
                cached_schema = await self._get_cached_schema(connection_id)
                if cached_schema:
                    print(f"📋 캐시된 스키마 정보 사용: {connection_id}")
                    return self._format_schema_response(cached_schema)

            # 2. 실제 데이터베이스에서 스키마 조회
            print(f"🔍 데이터베이스에서 스키마 정보 조회: {connection_id}")
            raw_schema = await self._fetch_schema_from_db(user_id, connection_id)
            
            # 3. 스키마 해시 계산
            schema_hash = self._calculate_schema_hash(raw_schema)
            
            # 4. 기존 캐시와 해시 비교
            existing_schema = await self._get_cached_schema(connection_id)
            if existing_schema and existing_schema.schema_hash == schema_hash:
                print(f"✅ 스키마 변경 없음. 기존 캐시 사용: {connection_id}")
                return self._format_schema_response(existing_schema)

            # 5. LLM으로 문서화 생성
            print(f"🤖 LLM으로 스키마 문서화 생성 중...")
            documentation = await self._generate_documentation(raw_schema)
            
            # 6. 새 스키마 정보 저장/업데이트
            schema_record = await self._save_schema_info(
                connection_id=connection_id,
                raw_schema=raw_schema,
                schema_hash=schema_hash,
                documentation=documentation
            )
            
            print(f"💾 스키마 정보 저장 완료: {len(raw_schema)} 테이블")
            return self._format_schema_response(schema_record)
            
        except Exception as e:
            print(f"❌ 스키마 정보 조회 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def _get_cached_schema(self, connection_id: str) -> Optional[DatabaseSchema]:
        """캐시된 스키마 정보 조회"""
        stmt = select(DatabaseSchema).where(
            DatabaseSchema.connection_id == connection_id,
            DatabaseSchema.is_active == True
        ).order_by(DatabaseSchema.last_updated.desc())
        
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def _fetch_schema_from_db(self, user_id: str, connection_id: str) -> List[Dict[str, Any]]:
        """실제 데이터베이스에서 스키마 정보 조회"""
        print(f"🔍 _fetch_schema_from_db 시작: connection_id={connection_id}")
        
        try:
            # 동적 엔진 생성
            engine = await db_manager.get_analysis_db_engine(connection_id, user_id)
            print(f"✅ 엔진 생성 성공")
        
            schema_info = []
            async with engine.connect() as conn:
                # 테이블 목록 조회
                tables_query = """
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name;
                """
                
                tables_result = await conn.execute(text(tables_query))
                tables = [row[0] for row in tables_result.fetchall()]
                print(f"📋 테이블 발견: {len(tables)}개")
                
                # 각 테이블의 컬럼 정보 조회
                for table_name in tables:
                    columns_query = """
                        SELECT 
                            column_name,
                            data_type,
                            is_nullable,
                            column_default,
                            character_maximum_length,
                            numeric_precision,
                            numeric_scale
                        FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = :table_name
                        ORDER BY ordinal_position;
                    """
                    
                    columns_result = await conn.execute(text(columns_query), {"table_name": table_name})
                    columns = []
                    
                    for row in columns_result.fetchall():
                        column_info = {
                            "column_name": row[0],
                            "data_type": row[1],
                            "is_nullable": row[2] == "YES",
                            "column_default": row[3],
                            "max_length": row[4],
                            "numeric_precision": row[5],
                            "numeric_scale": row[6]
                        }
                        columns.append(column_info)
                    
                    table_info = {
                        "table_name": table_name,
                        "columns": columns,
                        "column_count": len(columns)
                    }
                    schema_info.append(table_info)
            
            await engine.dispose()
            print(f"✅ 스키마 조회 완료: {len(schema_info)}개 테이블")
            return schema_info
            
        except Exception as e:
            print(f"❌ _fetch_schema_from_db 실패: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    def _calculate_schema_hash(self, schema_data: List[Dict[str, Any]]) -> str:
        """스키마 데이터의 해시값 계산 (변경 감지용)"""
        schema_structure = []
        for table in schema_data:
            table_structure = {
                "table_name": table["table_name"],
                "columns": [
                    {
                        "column_name": col["column_name"],
                        "data_type": col["data_type"],
                        "is_nullable": col["is_nullable"]
                    }
                    for col in table["columns"]
                ]
            }
            schema_structure.append(table_structure)
        
        schema_json = json.dumps(schema_structure, sort_keys=True)
        return hashlib.sha256(schema_json.encode()).hexdigest()

    async def _generate_documentation(self, schema_data: List[Dict[str, Any]]) -> str:
        """LLM을 사용하여 스키마 문서화 생성"""
        try:
            schema_summary = self._create_schema_summary(schema_data)
            
            prompt = f"""다음은 데이터베이스 스키마 정보입니다. 사용자가 채팅 시 한국어로 질문할 때 정확한 SQL을 생성할 수 있도록 한국어 매핑 정보가 포함된 문서를 작성해주세요.

핵심 목적: 
- 사용자는 "고객별 주문 건수", "상품 판매량", "월별 매출" 등 한국어로 질문합니다
- 이 문서의 한국어 테이블명/컬럼명 매핑 정보를 기반으로 LLM이 정확한 SQL을 작성해야 합니다

요구 사항:
1. 모든 테이블 섹션은 아래 예시와 같은 **JSON-유사 마크다운 블록**으로 작성하세요.
2. `koreanName` 필드에 테이블의 정확한 한국어 명칭을 기록하세요.
3. `columns` 배열의 각 컬럼에 `koreanName`과 `description`을 모두 포함하세요.
4. `keywords` 배열에 사용자가 이 테이블/컬럼을 언급할 때 사용할 가능성이 높은 한국어 키워드들을 나열하세요.
5. `sqlMappings` 필드에 자주 사용될 한국어 질문 패턴과 해당 SQL 힌트를 제공하세요.

예시 형식:
```jsonc
{
  "name": "orders",
  "koreanName": "주문",
  "displayName": "🛒 주문 (Orders)",
  "description": "고객 주문 정보 및 배송 데이터를 관리하는 핵심 테이블",
  "relation": "customers.customerid → orders.customerid (고객-주문 관계)",
  "keywords": ["주문", "오더", "구매", "구입", "결제"],
  "columns": [
    { 
      "name": "orderid", 
      "type": "INTEGER", 
      "koreanName": "주문번호",
      "description": "각 주문을 고유하게 식별하는 기본키",
      "keywords": ["주문번호", "주문ID", "오더번호"]
    },
    { 
      "name": "customerid", 
      "type": "INTEGER", 
      "koreanName": "고객번호",
      "description": "주문한 고객을 식별하는 외래키",
      "keywords": ["고객번호", "고객ID", "구매자"]
    },
    { 
      "name": "orderdate", 
      "type": "DATE", 
      "koreanName": "주문일자",
      "description": "주문이 접수된 날짜",
      "keywords": ["주문일", "주문날짜", "구매일", "구입일"]
    }
  ],
  "sqlMappings": [
    {
      "koreanQuestion": "고객별 주문 건수",
      "sqlHint": "SELECT customerid, COUNT(*) FROM orders GROUP BY customerid"
    },
    {
      "koreanQuestion": "월별 주문량",
      "sqlHint": "SELECT EXTRACT(MONTH FROM orderdate), COUNT(*) FROM orders GROUP BY EXTRACT(MONTH FROM orderdate)"
    }
  ],
  "examples": [
    { "question": "이번 달 주문 수는?", "purpose": "최근 판매 실적 확인" },
    { "question": "가장 많이 주문한 고객은?", "purpose": "VIP 고객 분석" }
  ]
}
```
위와 같은 블록을 테이블별로 나열하되, 반드시 한국어 매핑 정보(`koreanName`, `keywords`, `sqlMappings`)를 정확하게 포함하세요.

스키마 요약:
{schema_summary}
"""

            llm_provider = self._get_llm_provider()
            if llm_provider:
                await llm_provider.initialize()
                
                messages = [
                    {"role": "user", "content": prompt}
                ]
                
                response = await llm_provider.generate_chat_completion(
                    messages=messages,
                    max_tokens=2000,
                    temperature=0.3
                )
                
                return response
            else:
                print("⚠️ LLM Provider를 사용할 수 없음 - 기본 문서화 생성")
                return self._create_fallback_documentation(schema_data)
            
        except Exception as e:
            print(f"⚠️ LLM 문서화 생성 실패: {str(e)}")
            return self._create_fallback_documentation(schema_data)

    def _create_schema_summary(self, schema_data: List[Dict[str, Any]]) -> str:
        """스키마 데이터를 LLM용 요약으로 변환"""
        summary_parts = []
        
        for table in schema_data:
            table_name = table["table_name"]
            columns = table["columns"]
            
            column_info = []
            for col in columns:
                col_desc = f"{col['column_name']} ({col['data_type']}"
                if not col['is_nullable']:
                    col_desc += ", NOT NULL"
                col_desc += ")"
                column_info.append(col_desc)
            
            table_summary = f"""테이블: {table_name}
컬럼 수: {len(columns)}
컬럼 목록: {', '.join(column_info)}"""
            summary_parts.append(table_summary)
        
        return "\n\n".join(summary_parts)

    def _create_fallback_documentation(self, schema_data: List[Dict[str, Any]]) -> str:
        """LLM 실패 시 기본 문서화 - 한국어 매핑 정보 포함"""
        blocks = []
        for table in schema_data:
            table_name = table["table_name"]
            
            # 기본적인 한국어 테이블명 추정
            korean_table_name = self._guess_korean_table_name(table_name)
            
            # 컬럼 정보 배열 구성
            cols_arr = []
            for col in table["columns"]:
                korean_col_name = self._guess_korean_column_name(col["column_name"])
                keywords = self._generate_basic_keywords(korean_col_name, col["column_name"])
                
                col_desc = {
                    "name": col["column_name"],
                    "type": col["data_type"],
                    "koreanName": korean_col_name,
                    "description": f"{korean_col_name} ({'NOT NULL' if not col['is_nullable'] else 'NULL 허용'})",
                    "keywords": keywords
                }
                cols_arr.append(col_desc)

            # 기본 SQL 매핑 생성
            sql_mappings = [
                {
                    "koreanQuestion": f"{korean_table_name} 전체 건수",
                    "sqlHint": f"SELECT COUNT(*) FROM {table_name}"
                },
                {
                    "koreanQuestion": f"{korean_table_name} 목록 조회",
                    "sqlHint": f"SELECT * FROM {table_name} LIMIT 10"
                }
            ]

            block = {
                "name": table_name,
                "koreanName": korean_table_name,
                "displayName": f"📊 {korean_table_name} ({table_name})",
                "description": f"{korean_table_name} 정보를 저장하는 테이블",
                "relation": "자동 분석 불가",
                "keywords": [korean_table_name, table_name],
                "columns": cols_arr,
                "sqlMappings": sql_mappings,
                "examples": [
                    {"question": f"{korean_table_name} 수는?", "purpose": "데이터 규모 확인"}
                ]
            }
            import json
            blocks.append("```jsonc\n" + json.dumps(block, ensure_ascii=False, indent=2) + "\n```")

        return "\n\n".join(blocks)
    
    def _guess_korean_table_name(self, table_name: str) -> str:
        """테이블명으로부터 기본적인 한국어명 추정"""
        name_mapping = {
            "users": "사용자", "user": "사용자",
            "customers": "고객", "customer": "고객",
            "orders": "주문", "order": "주문",
            "products": "상품", "product": "상품",
            "items": "품목", "item": "품목",
            "sales": "판매", "sale": "판매",
            "employees": "직원", "employee": "직원",
            "categories": "분류", "category": "분류",
            "invoices": "청구서", "invoice": "청구서",
            "payments": "결제", "payment": "결제",
            "shipments": "배송", "shipment": "배송",
            "suppliers": "공급업체", "supplier": "공급업체"
        }
        
        table_lower = table_name.lower()
        for eng, kor in name_mapping.items():
            if eng in table_lower:
                return kor
        
        return table_name  # 매핑되지 않으면 원본 반환
    
    def _guess_korean_column_name(self, column_name: str) -> str:
        """컬럼명으로부터 기본적인 한국어명 추정"""
        name_mapping = {
            "id": "번호", "_id": "번호",
            "name": "이름", "title": "제목",
            "date": "날짜", "time": "시간",
            "price": "가격", "cost": "비용", "amount": "금액",
            "quantity": "수량", "count": "건수",
            "address": "주소", "email": "이메일", "phone": "전화번호",
            "status": "상태", "type": "유형",
            "created": "생성일", "updated": "수정일",
            "description": "설명", "note": "메모"
        }
        
        col_lower = column_name.lower()
        for eng, kor in name_mapping.items():
            if eng in col_lower:
                return kor
        
        return column_name  # 매핑되지 않으면 원본 반환
    
    def _generate_basic_keywords(self, korean_name: str, english_name: str) -> List[str]:
        """기본적인 키워드 목록 생성"""
        keywords = [korean_name, english_name]
        
        # 일반적인 동의어 추가
        synonym_map = {
            "번호": ["ID", "아이디", "식별자"],
            "이름": ["명칭", "네임"],
            "날짜": ["일자", "일시"],
            "가격": ["단가", "비용", "금액"],
            "수량": ["개수", "양", "량"],
            "고객": ["구매자", "클라이언트"],
            "주문": ["오더", "구매", "구입"],
            "상품": ["제품", "아이템", "상오"]
        }
        
        if korean_name in synonym_map:
            keywords.extend(synonym_map[korean_name])
        
        return list(set(keywords))  # 중복 제거

    async def _save_schema_info(
        self,
        connection_id: str,
        raw_schema: List[Dict[str, Any]],
        schema_hash: str,
        documentation: str
    ) -> DatabaseSchema:
        """스키마 정보를 데이터베이스에 저장"""
        
        # 기존 활성 스키마 비활성화
        stmt = select(DatabaseSchema).where(
            DatabaseSchema.connection_id == connection_id,
            DatabaseSchema.is_active == True
        )
        result = await self.session.execute(stmt)
        existing_schemas = result.scalars().all()
        
        for schema in existing_schemas:
            schema.is_active = False
        
        # 새 스키마 레코드 생성
        total_columns = sum(len(table["columns"]) for table in raw_schema)
        
        new_schema = DatabaseSchema(
            connection_id=connection_id,
            schema_hash=schema_hash,
            raw_schema=raw_schema,
            generated_documentation=documentation,
            table_count=len(raw_schema),
            total_columns=total_columns,
            last_updated=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            is_active=True
        )
        
        self.session.add(new_schema)
        await self.session.commit()
        await self.session.refresh(new_schema)
        
        return new_schema

    def _format_schema_response(self, schema_record: DatabaseSchema) -> Dict[str, Any]:
        """스키마 레코드를 API 응답 형태로 변환"""
        return {
            "schema_id": schema_record.id,
            "connection_id": schema_record.connection_id,
            "table_count": schema_record.table_count,
            "total_columns": schema_record.total_columns,
            "last_updated": schema_record.last_updated.isoformat(),
            "tables": schema_record.raw_schema,
            "documentation": schema_record.generated_documentation,
            "schema_hash": schema_record.schema_hash
        }

    async def refresh_schema(self, user_id: str, connection_id: str) -> Dict[str, Any]:
        """강제로 스키마 정보를 새로고침합니다."""
        return await self.get_schema_info(user_id=user_id, connection_id=connection_id, force_refresh=True)
