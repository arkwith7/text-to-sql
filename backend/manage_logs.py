#!/usr/bin/env python3
"""
로그 관리 스크립트
Text-to-SQL AI Agent의 로그를 관리하고 분석하는 편의 도구
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.log_analyzer import LogAnalyzer
import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

def show_log_status():
    """로그 파일 상태 표시"""
    print("📊 로그 파일 상태:")
    print("-" * 50)
    
    log_dir = Path("logs")
    if not log_dir.exists():
        print("⚠️ 로그 디렉토리가 존재하지 않습니다.")
        return
    
    log_files = {
        'app.log': '전체 애플리케이션 로그',
        'error.log': '에러 로그',
        'api_requests.log': 'API 요청 로그',
        'sql_queries.log': 'SQL 쿼리 로그',
        'chat_sessions.log': '채팅 세션 로그',
        'authentication.log': '인증 로그'
    }
    
    for filename, description in log_files.items():
        filepath = log_dir / filename
        if filepath.exists():
            stat = filepath.stat()
            size_mb = stat.st_size / (1024 * 1024)
            modified = datetime.fromtimestamp(stat.st_mtime)
            print(f"✅ {filename:<20} | {size_mb:>8.2f}MB | 수정: {modified.strftime('%Y-%m-%d %H:%M:%S')} | {description}")
        else:
            print(f"❌ {filename:<20} | 파일 없음      |                    | {description}")

def analyze_logs(hours=24, detailed=False):
    """로그 분석 실행"""
    print(f"🔍 최근 {hours}시간 로그 분석 중...")
    print("-" * 50)
    
    analyzer = LogAnalyzer()
    
    # 에러 분석
    print("📈 에러 분석:")
    error_analysis = analyzer.analyze_errors(hours)
    print(f"  - 총 에러: {error_analysis['total_errors']}개")
    if error_analysis['error_by_module']:
        print("  - 모듈별 에러:")
        for module, count in error_analysis['error_by_module'].items():
            print(f"    * {module}: {count}개")
    print()
    
    # API 성능 분석
    print("🚀 API 성능 분석:")
    api_analysis = analyzer.analyze_api_performance(hours)
    print(f"  - 총 요청: {api_analysis['total_requests']}개")
    print(f"  - 평균 응답시간: {api_analysis['avg_response_time_ms']:.1f}ms")
    print(f"  - 최대 응답시간: {api_analysis['max_response_time_ms']:.1f}ms")
    if api_analysis['slow_requests']:
        print(f"  - 느린 요청: {len(api_analysis['slow_requests'])}개")
    print()
    
    # SQL 쿼리 분석
    print("🗄️ SQL 쿼리 분석:")
    sql_analysis = analyzer.analyze_sql_queries(hours)
    print(f"  - 총 쿼리: {sql_analysis['total_queries']}개")
    print(f"  - 평균 실행시간: {sql_analysis['avg_execution_time']:.3f}초")
    if sql_analysis['slow_queries']:
        print(f"  - 느린 쿼리: {len(sql_analysis['slow_queries'])}개")
    if sql_analysis['failed_queries']:
        print(f"  - 실패한 쿼리: {len(sql_analysis['failed_queries'])}개")
    print()
    
    # 사용자 활동 분석
    print("👥 사용자 활동 분석:")
    user_analysis = analyzer.analyze_user_activity(hours)
    print(f"  - 활성 사용자: {user_analysis['total_active_users']}명")
    print(f"  - 총 로그인: {user_analysis['total_logins']}회")
    print(f"  - 총 채팅 메시지: {user_analysis['total_chat_messages']}개")
    print()
    
    if detailed:
        # 상세 정보 출력
        print("📋 상세 분석:")
        print("-" * 30)
        
        if api_analysis['slow_requests']:
            print("⏱️ 느린 API 요청:")
            for req in api_analysis['slow_requests'][:3]:
                print(f"  - {req['path']}: {req['response_time']:.0f}ms")
        
        if sql_analysis['slow_queries']:
            print("🐌 느린 SQL 쿼리:")
            for query in sql_analysis['slow_queries'][:3]:
                print(f"  - {query['execution_time']:.3f}s: {query['query'][:50]}...")
        
        if error_analysis['error_details']:
            print("❌ 최근 에러:")
            for module, errors in error_analysis['error_details'].items():
                if errors:
                    latest_error = errors[0]
                    print(f"  - {module}: {latest_error['message'][:60]}...")

def tail_logs(log_type='app', lines=50):
    """실시간 로그 모니터링"""
    analyzer = LogAnalyzer()
    analyzer.tail_log(log_type, lines)

def generate_report(hours=24, output_file=None):
    """종합 리포트 생성"""
    analyzer = LogAnalyzer()
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"logs/report_{timestamp}.json"
    
    print(f"📋 리포트 생성 중: {output_file}")
    report = analyzer.generate_report(hours, output_file)
    
    print(f"✅ 리포트가 생성되었습니다: {output_file}")
    return report

def cleanup_logs(days=30, dry_run=False):
    """오래된 로그 정리"""
    analyzer = LogAnalyzer()
    
    if dry_run:
        print(f"🔍 {days}일 이전 로그 파일 확인 중... (실제 삭제하지 않음)")
        # TODO: dry-run 모드 구현
    else:
        print(f"🧹 {days}일 이전 로그 파일 정리 중...")
        cleaned_files = analyzer.cleanup_old_logs(days)
        print(f"✅ {len(cleaned_files)}개 파일이 정리되었습니다.")

def main():
    parser = argparse.ArgumentParser(description='Text-to-SQL AI Agent 로그 관리 도구')
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령어')
    
    # status 명령어
    status_parser = subparsers.add_parser('status', help='로그 파일 상태 확인')
    
    # analyze 명령어
    analyze_parser = subparsers.add_parser('analyze', help='로그 분석')
    analyze_parser.add_argument('--hours', type=int, default=24, help='분석 기간 (시간, 기본값: 24)')
    analyze_parser.add_argument('--detailed', action='store_true', help='상세 분석 정보 표시')
    
    # tail 명령어
    tail_parser = subparsers.add_parser('tail', help='실시간 로그 모니터링')
    tail_parser.add_argument('--type', choices=['app', 'error', 'api', 'sql', 'chat', 'auth'],
                           default='app', help='모니터링할 로그 타입')
    tail_parser.add_argument('--lines', type=int, default=50, help='표시할 라인 수')
    
    # report 명령어
    report_parser = subparsers.add_parser('report', help='종합 리포트 생성')
    report_parser.add_argument('--hours', type=int, default=24, help='분석 기간 (시간)')
    report_parser.add_argument('--output', help='출력 파일 경로')
    
    # cleanup 명령어
    cleanup_parser = subparsers.add_parser('cleanup', help='오래된 로그 정리')
    cleanup_parser.add_argument('--days', type=int, default=30, help='보관 기간 (일, 기본값: 30)')
    cleanup_parser.add_argument('--dry-run', action='store_true', help='실제 삭제하지 않고 확인만')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    print("🤖 Text-to-SQL AI Agent 로그 관리 도구")
    print("=" * 50)
    
    try:
        if args.command == 'status':
            show_log_status()
        
        elif args.command == 'analyze':
            analyze_logs(args.hours, args.detailed)
        
        elif args.command == 'tail':
            tail_logs(args.type, args.lines)
        
        elif args.command == 'report':
            generate_report(args.hours, args.output)
        
        elif args.command == 'cleanup':
            cleanup_logs(args.days, args.dry_run)
        
    except KeyboardInterrupt:
        print("\n\n👋 작업이 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 