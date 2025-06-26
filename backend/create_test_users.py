#!/usr/bin/env python3
"""
테스트용 사용자 데이터 생성 스크립트
30명의 다양한 사용자 계정을 생성합니다.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import List

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.connection_manager import DatabaseManager
from services.auth_service import AuthService, UserCreate, UserRole
from services.analytics_service import AnalyticsService

# 테스트 사용자 데이터
TEST_USERS = [
    {
        "email": "admin@test.com",
        "password": "admin123!",
        "full_name": "관리자",
        "company": "테스트 회사",
        "role": "admin"
    },
    {
        "email": "john.doe@techcorp.com",
        "password": "password123",
        "full_name": "John Doe",
        "company": "TechCorp",
        "role": "analyst"
    },
    {
        "email": "jane.smith@dataflow.com",
        "password": "password123",
        "full_name": "Jane Smith",
        "company": "DataFlow Inc",
        "role": "analyst"
    },
    {
        "email": "mike.johnson@analytics.com",
        "password": "password123",
        "full_name": "Mike Johnson",
        "company": "Analytics Pro",
        "role": "admin"
    },
    {
        "email": "sarah.wilson@startup.com",
        "password": "password123",
        "full_name": "Sarah Wilson",
        "company": "StartUp Solutions",
        "role": "analyst"
    },
    {
        "email": "david.brown@consulting.com",
        "password": "password123",
        "full_name": "David Brown",
        "company": "Brown Consulting",
        "role": "analyst"
    },
    {
        "email": "lisa.garcia@finance.com",
        "password": "password123",
        "full_name": "Lisa Garcia",
        "company": "Finance Corp",
        "role": "analyst"
    },
    {
        "email": "robert.martinez@logistics.com",
        "password": "password123",
        "full_name": "Robert Martinez",
        "company": "Logistics Plus",
        "role": "analyst"
    },
    {
        "email": "emily.davis@healthcare.com",
        "password": "password123",
        "full_name": "Emily Davis",
        "company": "Healthcare Systems",
        "role": "admin"
    },
    {
        "email": "james.miller@education.com",
        "password": "password123",
        "full_name": "James Miller",
        "company": "Education Tech",
        "role": "analyst"
    },
    {
        "email": "mary.anderson@retail.com",
        "password": "password123",
        "full_name": "Mary Anderson",
        "company": "Retail Solutions",
        "role": "analyst"
    },
    {
        "email": "thomas.taylor@manufacturing.com",
        "password": "password123",
        "full_name": "Thomas Taylor",
        "company": "Manufacturing Co",
        "role": "analyst"
    },
    {
        "email": "jennifer.white@media.com",
        "password": "password123",
        "full_name": "Jennifer White",
        "company": "Media Group",
        "role": "analyst"
    },
    {
        "email": "william.harris@insurance.com",
        "password": "password123",
        "full_name": "William Harris",
        "company": "Insurance Direct",
        "role": "analyst"
    },
    {
        "email": "elizabeth.clark@realestate.com",
        "password": "password123",
        "full_name": "Elizabeth Clark",
        "company": "Real Estate Pro",
        "role": "analyst"
    },
    {
        "email": "charles.lewis@automotive.com",
        "password": "password123",
        "full_name": "Charles Lewis",
        "company": "Automotive Systems",
        "role": "admin"
    },
    {
        "email": "patricia.walker@travel.com",
        "password": "password123",
        "full_name": "Patricia Walker",
        "company": "Travel Connect",
        "role": "analyst"
    },
    {
        "email": "daniel.hall@energy.com",
        "password": "password123",
        "full_name": "Daniel Hall",
        "company": "Energy Solutions",
        "role": "analyst"
    },
    {
        "email": "linda.allen@telecommunications.com",
        "password": "password123",
        "full_name": "Linda Allen",
        "company": "Telecom Networks",
        "role": "analyst"
    },
    {
        "email": "mark.young@construction.com",
        "password": "password123",
        "full_name": "Mark Young",
        "company": "Construction Plus",
        "role": "analyst"
    },
    {
        "email": "susan.king@agriculture.com",
        "password": "password123",
        "full_name": "Susan King",
        "company": "Agriculture Tech",
        "role": "analyst"
    },
    {
        "email": "paul.wright@aerospace.com",
        "password": "password123",
        "full_name": "Paul Wright",
        "company": "Aerospace Dynamics",
        "role": "analyst"
    },
    {
        "email": "nancy.lopez@biotechnology.com",
        "password": "password123",
        "full_name": "Nancy Lopez",
        "company": "BioTech Labs",
        "role": "admin"
    },
    {
        "email": "kevin.hill@chemicals.com",
        "password": "password123",
        "full_name": "Kevin Hill",
        "company": "Chemical Industries",
        "role": "analyst"
    },
    {
        "email": "karen.green@entertainment.com",
        "password": "password123",
        "full_name": "Karen Green",
        "company": "Entertainment Hub",
        "role": "analyst"
    },
    {
        "email": "steven.adams@sports.com",
        "password": "password123",
        "full_name": "Steven Adams",
        "company": "Sports Analytics",
        "role": "analyst"
    },
    {
        "email": "betty.baker@food.com",
        "password": "password123",
        "full_name": "Betty Baker",
        "company": "Food Services",
        "role": "analyst"
    },
    {
        "email": "ronald.gonzalez@government.com",
        "password": "password123",
        "full_name": "Ronald Gonzalez",
        "company": "Government Solutions",
        "role": "analyst"
    },
    {
        "email": "helen.nelson@nonprofit.com",
        "password": "password123",
        "full_name": "Helen Nelson",
        "company": "Non-Profit Org",
        "role": "analyst"
    },
    {
        "email": "gary.carter@security.com",
        "password": "password123",
        "full_name": "Gary Carter",
        "company": "Security Systems",
        "role": "admin"
    }
]

async def create_test_users():
    """테스트 사용자들을 생성합니다."""
    print("🚀 테스트 사용자 데이터 생성을 시작합니다...")
    
    try:
        # 데이터베이스 매니저 초기화
        db_manager = DatabaseManager()
        await db_manager.initialize()
        print("✅ 데이터베이스 연결 완료")
        
        # 서비스 초기화
        auth_service = AuthService(db_manager)
        analytics_service = AnalyticsService(db_manager)
        
        created_count = 0
        skipped_count = 0
        
        print(f"📝 {len(TEST_USERS)}명의 사용자 생성을 시작합니다...\n")
        
        for i, user_data in enumerate(TEST_USERS, 1):
            try:
                # 이미 존재하는 이메일인지 확인
                existing_user = await auth_service.get_user_by_email(user_data["email"])
                if existing_user:
                    print(f"⏭️  [{i:2d}/30] {user_data['email']} - 이미 존재하는 사용자")
                    skipped_count += 1
                    continue
                
                # UserCreate 객체 생성
                user_create = UserCreate(
                    email=user_data["email"],
                    password=user_data["password"],
                    full_name=user_data["full_name"],
                    company=user_data.get("company"),
                    role=UserRole(user_data["role"])
                )
                
                # 사용자 생성
                new_user = await auth_service.create_user(user_create, analytics_service)
                
                if new_user:
                    print(f"✅ [{i:2d}/30] {user_data['email']} - {user_data['full_name']} ({user_data['role']})")
                    created_count += 1
                else:
                    print(f"❌ [{i:2d}/30] {user_data['email']} - 생성 실패")
                    
            except Exception as e:
                print(f"❌ [{i:2d}/30] {user_data['email']} - 오류: {str(e)}")
        
        print(f"\n🎉 테스트 사용자 생성 완료!")
        print(f"   ✅ 성공: {created_count}명")
        print(f"   ⏭️  건너뜀: {skipped_count}명")
        print(f"   ❌ 실패: {len(TEST_USERS) - created_count - skipped_count}명")
        
        # 총 사용자 수 확인
        total_users = await auth_service.get_users_count()
        print(f"\n📊 현재 총 사용자 수: {total_users}명")
        
        # 역할별 통계
        admin_count = len([u for u in TEST_USERS if u["role"] == "admin"])
        analyst_count = len([u for u in TEST_USERS if u["role"] == "analyst"])
        print(f"   👑 관리자: {admin_count}명")
        print(f"   👤 일반 사용자: {analyst_count}명")
        
    except Exception as e:
        print(f"❌ 데이터베이스 초기화 실패: {str(e)}")
        sys.exit(1)

async def main():
    """메인 함수"""
    print("=" * 60)
    print("🔧 Text-to-SQL 테스트 사용자 생성 도구")
    print("=" * 60)
    
    await create_test_users()
    
    print("\n" + "=" * 60)
    print("✨ 완료! 이제 프론트엔드에서 사용자 관리 페이지를 테스트할 수 있습니다.")
    print("📱 http://localhost:3000 에서 관리자로 로그인 후 사용자 관리 메뉴를 확인하세요.")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
