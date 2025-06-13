"""
로그 분석 및 관리 유틸리티
utils/log_analyzer.py
"""

import json
import os
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import argparse
import pandas as pd

class LogAnalyzer:
    """로그 파일 분석 및 관리 도구"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_files = {
            'app': self.log_dir / "app.log",
            'error': self.log_dir / "error.log",
            'api': self.log_dir / "api_requests.log",
            'sql': self.log_dir / "sql_queries.log",
            'chat': self.log_dir / "chat_sessions.log",
            'auth': self.log_dir / "authentication.log"
        }
    
    def parse_log_entry(self, line: str) -> Optional[Dict[str, Any]]:
        """JSON 로그 항목 파싱"""
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError:
            # 일반 텍스트 로그인 경우
            return {"message": line.strip(), "timestamp": None}
    
    def read_log_file(self, log_type: str, lines: int = None) -> List[Dict[str, Any]]:
        """로그 파일 읽기"""
        log_file = self.log_files.get(log_type)
        if not log_file or not log_file.exists():
            print(f"로그 파일을 찾을 수 없습니다: {log_file}")
            return []
        
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                log_lines = f.readlines()
                
                # 최근 N개 라인만 읽기
                if lines:
                    log_lines = log_lines[-lines:]
                
                for line in log_lines:
                    entry = self.parse_log_entry(line)
                    if entry:
                        entries.append(entry)
        
        except Exception as e:
            print(f"로그 파일 읽기 오류: {e}")
        
        return entries
    
    def analyze_errors(self, hours: int = 24) -> Dict[str, Any]:
        """에러 로그 분석"""
        print(f"📊 최근 {hours}시간 에러 분석 중...")
        
        error_logs = self.read_log_file('error')
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = []
        error_counts = Counter()
        error_types = defaultdict(list)
        
        for entry in error_logs:
            try:
                log_time = datetime.fromisoformat(entry.get('timestamp', ''))
                if log_time >= cutoff_time:
                    recent_errors.append(entry)
                    
                    # 에러 타입별 분류
                    error_msg = entry.get('message', '')
                    module = entry.get('module', 'unknown')
                    
                    error_counts[module] += 1
                    error_types[module].append({
                        'message': error_msg,
                        'timestamp': entry.get('timestamp'),
                        'function': entry.get('function')
                    })
            except:
                continue
        
        return {
            'total_errors': len(recent_errors),
            'error_by_module': dict(error_counts),
            'error_details': dict(error_types),
            'analysis_period': f"{hours} hours"
        }
    
    def analyze_api_performance(self, hours: int = 24) -> Dict[str, Any]:
        """API 성능 분석"""
        print(f"🚀 최근 {hours}시간 API 성능 분석 중...")
        
        api_logs = self.read_log_file('api')
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        response_times = []
        status_codes = Counter()
        endpoint_performance = defaultdict(list)
        slow_requests = []
        
        for entry in api_logs:
            try:
                log_time = datetime.fromisoformat(entry.get('timestamp', ''))
                if log_time >= cutoff_time and entry.get('event_type') == 'api_response':
                    response_time = entry.get('response_time_ms', 0)
                    status_code = entry.get('status_code')
                    path = entry.get('request_path', 'unknown')
                    
                    response_times.append(response_time)
                    status_codes[status_code] += 1
                    endpoint_performance[path].append(response_time)
                    
                    # 느린 요청 (2초 이상)
                    if response_time > 2000:
                        slow_requests.append({
                            'path': path,
                            'response_time': response_time,
                            'timestamp': entry.get('timestamp'),
                            'status_code': status_code
                        })
            except:
                continue
        
        # 엔드포인트별 평균 응답시간
        avg_response_times = {}
        for endpoint, times in endpoint_performance.items():
            avg_response_times[endpoint] = {
                'avg_ms': sum(times) / len(times) if times else 0,
                'max_ms': max(times) if times else 0,
                'min_ms': min(times) if times else 0,
                'request_count': len(times)
            }
        
        return {
            'total_requests': len(response_times),
            'avg_response_time_ms': sum(response_times) / len(response_times) if response_times else 0,
            'max_response_time_ms': max(response_times) if response_times else 0,
            'status_code_distribution': dict(status_codes),
            'endpoint_performance': avg_response_times,
            'slow_requests': slow_requests[:10],  # 상위 10개
            'analysis_period': f"{hours} hours"
        }
    
    def analyze_sql_queries(self, hours: int = 24) -> Dict[str, Any]:
        """SQL 쿼리 분석"""
        print(f"🗄️ 최근 {hours}시간 SQL 쿼리 분석 중...")
        
        sql_logs = self.read_log_file('sql')
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        query_times = []
        slow_queries = []
        failed_queries = []
        query_patterns = Counter()
        
        for entry in sql_logs:
            try:
                log_time = datetime.fromisoformat(entry.get('timestamp', ''))
                if log_time >= cutoff_time and entry.get('event_type') == 'sql_execution':
                    execution_time = entry.get('execution_time', 0)
                    success = entry.get('success', True)
                    sql_query = entry.get('sql_query', '')
                    
                    if success:
                        query_times.append(execution_time)
                        
                        # 느린 쿼리 (1초 이상)
                        if execution_time > 1.0:
                            slow_queries.append({
                                'query': sql_query[:100] + '...' if len(sql_query) > 100 else sql_query,
                                'execution_time': execution_time,
                                'timestamp': entry.get('timestamp'),
                                'user_id': entry.get('user_id')
                            })
                        
                        # 쿼리 패턴 분석
                        query_type = self._extract_query_type(sql_query)
                        query_patterns[query_type] += 1
                    else:
                        failed_queries.append({
                            'query': sql_query[:100] + '...' if len(sql_query) > 100 else sql_query,
                            'error': entry.get('error_message'),
                            'timestamp': entry.get('timestamp'),
                            'user_id': entry.get('user_id')
                        })
            except:
                continue
        
        return {
            'total_queries': len(query_times) + len(failed_queries),
            'successful_queries': len(query_times),
            'failed_queries': len(failed_queries),
            'avg_execution_time_s': sum(query_times) / len(query_times) if query_times else 0,
            'max_execution_time_s': max(query_times) if query_times else 0,
            'slow_queries': slow_queries[:10],
            'failed_queries': failed_queries[:10],
            'query_type_distribution': dict(query_patterns),
            'analysis_period': f"{hours} hours"
        }
    
    def analyze_user_activity(self, hours: int = 24) -> Dict[str, Any]:
        """사용자 활동 분석"""
        print(f"👥 최근 {hours}시간 사용자 활동 분석 중...")
        
        auth_logs = self.read_log_file('auth')
        chat_logs = self.read_log_file('chat')
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        user_activity = defaultdict(lambda: {
            'login_count': 0,
            'chat_messages': 0,
            'last_activity': None
        })
        
        # 인증 로그 분석
        for entry in auth_logs:
            try:
                log_time = datetime.fromisoformat(entry.get('timestamp', ''))
                if log_time >= cutoff_time:
                    user_id = entry.get('user_id')
                    event_type = entry.get('event_type', '')
                    
                    if user_id and 'login_success' in event_type:
                        user_activity[user_id]['login_count'] += 1
                        user_activity[user_id]['last_activity'] = entry.get('timestamp')
            except:
                continue
        
        # 채팅 로그 분석
        for entry in chat_logs:
            try:
                log_time = datetime.fromisoformat(entry.get('timestamp', ''))
                if log_time >= cutoff_time:
                    user_id = entry.get('user_id')
                    event_type = entry.get('event_type', '')
                    
                    if user_id and 'chat_message' in event_type:
                        user_activity[user_id]['chat_messages'] += 1
                        if not user_activity[user_id]['last_activity'] or \
                           entry.get('timestamp') > user_activity[user_id]['last_activity']:
                            user_activity[user_id]['last_activity'] = entry.get('timestamp')
            except:
                continue
        
        # 활성 사용자 순으로 정렬
        sorted_users = sorted(
            user_activity.items(),
            key=lambda x: x[1]['chat_messages'] + x[1]['login_count'],
            reverse=True
        )
        
        return {
            'total_active_users': len(user_activity),
            'top_active_users': dict(sorted_users[:10]),
            'total_logins': sum(user['login_count'] for user in user_activity.values()),
            'total_chat_messages': sum(user['chat_messages'] for user in user_activity.values()),
            'analysis_period': f"{hours} hours"
        }
    
    def _extract_query_type(self, sql_query: str) -> str:
        """SQL 쿼리 타입 추출"""
        query_upper = sql_query.upper().strip()
        if query_upper.startswith('SELECT'):
            if 'JOIN' in query_upper:
                return 'SELECT_WITH_JOIN'
            elif 'GROUP BY' in query_upper:
                return 'SELECT_WITH_GROUP'
            else:
                return 'SELECT_SIMPLE'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def generate_report(self, hours: int = 24, output_file: str = None) -> Dict[str, Any]:
        """종합 리포트 생성"""
        print(f"📋 최근 {hours}시간 종합 리포트 생성 중...")
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'analysis_period_hours': hours,
            'error_analysis': self.analyze_errors(hours),
            'api_performance': self.analyze_api_performance(hours),
            'sql_analysis': self.analyze_sql_queries(hours),
            'user_activity': self.analyze_user_activity(hours)
        }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"리포트가 저장되었습니다: {output_file}")
        
        return report
    
    def cleanup_old_logs(self, days: int = 30):
        """오래된 로그 파일 정리"""
        print(f"🧹 {days}일 이전 로그 파일 정리 중...")
        
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned_files = []
        
        for log_type, log_file in self.log_files.items():
            if not log_file.exists():
                continue
            
            # 백업 파일들도 정리
            log_pattern = f"{log_file.stem}.*"
            for backup_file in self.log_dir.glob(log_pattern):
                try:
                    file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_mtime < cutoff_date:
                        if backup_file.suffix == '.gz':
                            backup_file.unlink()
                        else:
                            # 압축 후 삭제
                            with open(backup_file, 'rb') as f_in:
                                with gzip.open(f"{backup_file}.gz", 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            backup_file.unlink()
                        
                        cleaned_files.append(str(backup_file))
                except Exception as e:
                    print(f"파일 정리 실패 {backup_file}: {e}")
        
        print(f"정리된 파일 수: {len(cleaned_files)}")
        return cleaned_files
    
    def tail_log(self, log_type: str, lines: int = 50):
        """실시간 로그 모니터링 (tail -f 유사)"""
        log_file = self.log_files.get(log_type)
        if not log_file or not log_file.exists():
            print(f"로그 파일을 찾을 수 없습니다: {log_file}")
            return
        
        print(f"📡 실시간 로그 모니터링: {log_file}")
        print("Ctrl+C로 종료하세요.\n")
        
        # 최근 N개 라인 먼저 출력
        recent_entries = self.read_log_file(log_type, lines)
        for entry in recent_entries:
            self._print_log_entry(entry)
        
        # 실시간 모니터링 (간단한 구현)
        try:
            import time
            with open(log_file, 'r', encoding='utf-8') as f:
                f.seek(0, 2)  # 파일 끝으로 이동
                while True:
                    line = f.readline()
                    if line:
                        entry = self.parse_log_entry(line)
                        if entry:
                            self._print_log_entry(entry)
                    else:
                        time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n로그 모니터링을 종료합니다.")
    
    def _print_log_entry(self, entry: Dict[str, Any]):
        """로그 엔트리 출력"""
        timestamp = entry.get('timestamp', 'N/A')
        level = entry.get('level', 'INFO')
        message = entry.get('message', '')
        
        # 색상 코드 (터미널 지원 시)
        colors = {
            'ERROR': '\033[91m',  # 빨간색
            'WARNING': '\033[93m',  # 노란색
            'INFO': '\033[92m',     # 초록색
            'DEBUG': '\033[94m',    # 파란색
            'RESET': '\033[0m'      # 리셋
        }
        
        color = colors.get(level, colors['RESET'])
        reset = colors['RESET']
        
        print(f"{color}[{timestamp}] {level}: {message}{reset}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='로그 분석 및 관리 도구')
    parser.add_argument('--log-dir', default='logs', help='로그 디렉토리 경로')
    parser.add_argument('--hours', type=int, default=24, help='분석 기간 (시간)')
    parser.add_argument('--report', action='store_true', help='종합 리포트 생성')
    parser.add_argument('--output', help='리포트 출력 파일')
    parser.add_argument('--cleanup', type=int, help='오래된 로그 정리 (일 수)')
    parser.add_argument('--tail', choices=['app', 'error', 'api', 'sql', 'chat', 'auth'], 
                       help='실시간 로그 모니터링')
    parser.add_argument('--lines', type=int, default=50, help='tail에서 표시할 라인 수')
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer(args.log_dir)
    
    if args.report:
        report = analyzer.generate_report(args.hours, args.output)
        if not args.output:
            # 터미널에 간단한 요약 출력
            print("\n=== 로그 분석 리포트 ===")
            print(f"분석 기간: {args.hours}시간")
            print(f"총 에러: {report['error_analysis']['total_errors']}개")
            print(f"총 API 요청: {report['api_performance']['total_requests']}개")
            print(f"평균 API 응답시간: {report['api_performance']['avg_response_time_ms']:.1f}ms")
            print(f"총 SQL 쿼리: {report['sql_analysis']['total_queries']}개")
            print(f"활성 사용자: {report['user_activity']['total_active_users']}명")
    
    elif args.cleanup:
        analyzer.cleanup_old_logs(args.cleanup)
    
    elif args.tail:
        analyzer.tail_log(args.tail, args.lines)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()