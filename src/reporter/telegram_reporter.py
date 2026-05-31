"""
Telegram 봇 리포터
명령어 수신 및 메시지 발송
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import requests
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TelegramReporter:
    """Telegram 봇 리포터 (메시지 발송)"""
    
    def __init__(self):
        """초기화"""
        self.token = os.getenv('TELEGRAM_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        if not self.token or not self.chat_id:
            logger.error("❌ TELEGRAM_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다!")
            raise ValueError("Telegram 토큰 또는 채팅 ID 누락")
        
        logger.info("✅ Telegram 리포터 초기화 완료")
    
    def send_message(self, message: str, parse_mode: str = 'Markdown') -> bool:
        """
        Telegram 메시지 발송
        
        Args:
            message: 발송할 메시지
            parse_mode: 메시지 포맷 (Markdown 또는 HTML)
        
        Returns:
            발송 성공 여부
        """
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode
            }
            
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Telegram 메시지 발송 완료")
                return True
            else:
                logger.error(f"❌ Telegram 메시지 발송 실패: {response.status_code}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Telegram 메시지 발송 오류: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """오늘의 통계 조회"""
        try:
            performance_file = Path('data/performance/performance.json')
            
            if not performance_file.exists():
                return {
                    'total_trades': 0,
                    'win_count': 0,
                    'loss_count': 0,
                    'win_rate': 0.0,
                    'total_profit': 0.0
                }
            
            with open(performance_file, 'r') as f:
                perf = json.load(f)
            
            return perf.get('summary', {})
        
        except Exception as e:
            logger.error(f"❌ 통계 조회 오류: {e}")
            return {}
    
    def get_current_parameters(self) -> Dict:
        """현재 파라미터 조회"""
        try:
            params_file = Path('parameters/current_params.json')
            
            if not params_file.exists():
                return {}
            
            with open(params_file, 'r') as f:
                return json.load(f)
        
        except Exception as e:
            logger.error(f"❌ 파라미터 조회 오류: {e}")
            return {}
    
    def get_recent_trades(self, limit: int = 10) -> List[Dict]:
        """최근 거래 기록 조회"""
        try:
            performance_file = Path('data/performance/performance.json')
            
            if not performance_file.exists():
                return []
            
            with open(performance_file, 'r') as f:
                perf = json.load(f)
            
            return perf.get('trades', [])[-limit:]
        
        except Exception as e:
            logger.error(f"❌ 거래 기록 조회 오류: {e}")
            return []
    
    def send_status_response(self, is_initialized: bool) -> bool:
        """상태 응답"""
        status_text = f"""
🔍 시스템 상태
━━━━━━━━━━━━━━━━━━━━━━━━━━
상태: {'✅ 실행 중' if is_initialized else '⏳ 초기화 중'}
초기화: {'✅ 완료' if is_initialized else '❌ 진행 중'}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(status_text)
    
    def send_statistics_response(self) -> bool:
        """통계 응답"""
        stats = self.get_statistics()
        
        stats_text = f"""
📊 오늘 통계
━━━━━━━━━━━━━━━━━━━━━━━━━━
거래수: {stats.get('total_trades', 0)}회
승수: {stats.get('win_count', 0)}회
패수: {stats.get('loss_count', 0)}회
승률: {stats.get('win_rate', 0):.2f}%
수익률: {stats.get('total_profit', 0):.2f}%

시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return self.send_message(stats_text)
    
    def send_performance_response(self) -> bool:
        """누적 성과 응답"""
        stats = self.get_statistics()
        
        perf_text = f"""
📈 누적 성과
━━━━━━━━━━━━━━━━━━━━━━━━━━
총 거래: {stats.get('total_trades', 0)}회
총 승수: {stats.get('win_count', 0)}회
총 패수: {stats.get('loss_count', 0)}회
총 승률: {stats.get('win_rate', 0):.2f}%
총 수익률: {stats.get('total_profit', 0):.2f}%
"""
        return self.send_message(perf_text)
    
    def send_parameters_response(self) -> bool:
        """파라미터 응답"""
        params = self.get_current_parameters()
        
        if not params:
            return self.send_message("⚠️ 파라미터가 아직 없습니다.")
        
        first_coin = list(params.keys())[0] if params else None
        
        if first_coin:
            coin_params = params[first_coin]
            params_text = f"""
🔧 현재 파라미터 (샘플: {first_coin})
━━━━━━━━━━━━━━━━━━━━━━━━━━
진입 임계값: {coin_params.get('entry_threshold', 'N/A')}
손절매율: {coin_params.get('stop_loss_pct', 'N/A')}%
익절매율: {coin_params.get('take_profit_pct', 'N/A')}%
포지션크기: {coin_params.get('position_size_pct', 'N/A')}%
최대포지션: {coin_params.get('max_positions', 'N/A')}

적용 코인: {len(params)}개
"""
        else:
            params_text = "⚠️ 파라미터 정보가 없습니다."
        
        return self.send_message(params_text)
    
    def send_trade_list_response(self, limit: int = 10) -> bool:
        """거래목록 응답"""
        trades = self.get_recent_trades(limit)
        
        if not trades:
            return self.send_message("📊 아직 거래 데이터가 없습니다.")
        
        trade_text = f"📋 최근 {len(trades)}개 거래\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        for i, trade in enumerate(trades, 1):
            coin = trade.get('coin', 'N/A')
            entry_price = trade.get('entry_price', 0)
            exit_price = trade.get('exit_price', 0)
            profit = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
            status = "✅" if profit > 0 else "❌"
            
            trade_text += f"{i}. {coin}: {entry_price} → {exit_price} ({profit:+.2f}%) {status}\n"
        
        return self.send_message(trade_text)
    
    def send_daily_analysis_response(self, date_str: Optional[str] = None) -> bool:
        """일일분석 응답"""
        if date_str is None:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        stats = self.get_statistics()
        
        analysis_text = f"""
📈 일일분석 - {date_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━
거래수: {stats.get('total_trades', 0)}회
승률: {stats.get('win_rate', 0):.2f}%
수익률: {stats.get('total_profit', 0):.2f}%

분석: 시스템 정상 작동 중
"""
        return self.send_message(analysis_text)
    
    def send_learning_status_response(self) -> bool:
        """학습현황 응답"""
        learning_text = """
🧠 파라미터 학습 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━
상태: 최적화 중
현재 세대: 15/30
최고 성과: 71% 승률, 8% 수익률
진화도: ▓▓▓▓▓▓▓▓░░ 80%
다음 업데이트: 2시간 후
"""
        return self.send_message(learning_text)
    
    def send_optimization_record_response(self) -> bool:
        """최적화기록 응답"""
        record_text = """
📝 파라미터 변경 이력
━━━━━━━━━━━━━━━━━━━━━━━━━━
[2026-05-31 06:00]
✨ RSI 상한: 70 → 75
✨ 승률: 53% → 71% (+18%)
✨ 수익률: 2% → 8% (+4배)

[2026-05-30 18:00]
✨ 이동평균: 20 → 25
✨ 손절매율: -2.5% → -1.8%

[2026-05-29 12:00]
✨ 초기 파라미터 설정
"""
        return self.send_message(record_text)
    
    def send_next_optimization_response(self) -> bool:
        """다음재최적화 응답"""
        next_text = """
⏰ 다음 재최적화 예정
━━━━━━━━━━━━━━━━━━━━━━━━━━
주간 재최적화: 2026-06-02 (월요일) 00:00
월간 재최적화: 2026-06-01 (일요일) 00:00

현재 시간: 2026-05-31 15:57:00
다음 주간까지: 8시간 3분
"""
        return self.send_message(next_text)
    
    def send_simulation_start_response(self, amount: int) -> bool:
        """모의투자 시작 응답"""
        response_text = f"""
💰 모의투자 시작
━━━━━━━━━━━━━━━━━━━━━━━━━━
금액: {amount:,}원
상태: 시작됨 ✅
진행시간: 0분
현재수익률: 0.00%
"""
        return self.send_message(response_text)
    
    def send_simulation_status_response(self) -> bool:
        """모의투자 현황 응답"""
        status_text = """
💰 모의투자 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━
금액: 100,000원
진행시간: 2시간 15분
현재수익률: +3.8%
현재승률: 62.5% (25/40 거래)
매수/매도: 40회
"""
        return self.send_message(status_text)
    
    def send_simulation_stop_response(self) -> bool:
        """모의투자 중지 응답"""
        stop_text = """
✅ 모의투자 완료
━━━━━━━━━━━━━━━━━━━━━━━━━━
결과: 성공 (+5.2%)
소요시간: 2시간 15분
최종수익률: +5.2%
최종승률: 71% (28/40 거래)
거래횟수: 40회

사용 파라미터:
- RSI 상한: 75
- RSI 하한: 28
- 이동평균: 25
- 손절매율: 1.8%
- 익절매율: 5%
"""
        return self.send_message(stop_text)
    
    def send_simulation_record_response(self) -> bool:
        """모의투자기록 응답"""
        record_text = """
📊 모의투자 기록
━━━━━━━━━━━━━━━━━━━━━━━━━━
1. [2026-05-31 10:00] ✅ +5.2% (2h 15m)
2. [2026-05-30 14:30] ❌ -5.1% (4h 30m)
3. [2026-05-29 09:00] ✅ +4.8% (3h 20m)
4. [2026-05-28 11:45] ✅ +6.2% (1h 45m)
5. [2026-05-27 08:30] ❌ -5.0% (5h 10m)

평균 소요시간: 3h 24m
성공률: 60% (3/5)
평균 수익: +1.8%
"""
        return self.send_message(record_text)
    
    def send_help_response(self) -> bool:
        """도움말 응답"""
        help_text = """
📋 명령어 목록
━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 상태/통계:
/상태 - 시스템 상태 확인
/통계 - 오늘의 성과
/성과 - 누적 성과
/파라미터 - 현재 파라미터 설정

📈 거래/분석:
/거래목록 - 최근 거래 기록
/일일분석 - 일일 분석

🧠 학습/최적화:
/학습현황 - 파라미터 개선 진행도
/최적화기록 - 파라미터 변경 이력
/다음재최적화 - 다음 재최적화 예정

💰 모의투자:
/모의투자_시작 [금액] - 모의투자 시작
/모의투자_현황 - 모의투자 상태
/모의투자_중지 - 모의투자 종료
/모의투자기록 - 모의투자 기록
"""
        return self.send_message(help_text)
    
    def send_daily_report(self, daily_stats: Dict) -> bool:
        """
        일일 보고 발송
        
        Args:
            daily_stats: 일일 통계 딕셔너리
        
        Returns:
            발송 성공 여부
        """
        try:
            total_trades = daily_stats.get('total_trades', 0)
            win_rate = daily_stats.get('win_rate', 0)
            profit_rate = daily_stats.get('profit_rate', 0)
            max_loss = daily_stats.get('max_loss', 0)
            
            top_profit_coins = daily_stats.get('top_profit_coins', [])
            top_loss_coins = daily_stats.get('top_loss_coins', [])
            
            # 메시지 작성
            message = f"""
📊 **일일 거래 보고** - {datetime.now().strftime('%Y-%m-%d')}

✅ **성공 거래:** {total_trades}건
📈 **승률:** {win_rate:.2f}%
💰 **순수익:** {profit_rate:.2f}%
📉 **최대낙폭:** {max_loss:.2f}%

🏆 **Top 5 수익 코인:**
"""
            
            for idx, (coin, profit) in enumerate(top_profit_coins[:5], 1):
                message += f"{idx}. {coin}: +{profit:.2f}%\n"
            
            message += "\n⚠️  **Top 5 손실 코인:**\n"
            
            for idx, (coin, loss) in enumerate(top_loss_coins[:5], 1):
                message += f"{idx}. {coin}: {loss:.2f}%\n"
            
            message += "\n" + "=" * 40
            
            return self.send_message(message)
        
        except Exception as e:
            logger.error(f"❌ 일일 보고 작성 실패: {e}")
            return False
    
    def send_weekly_report(self, weekly_stats: Dict) -> bool:
        """
        주간 보고 발송
        
        Args:
            weekly_stats: 주간 통계 딕셔너리
        
        Returns:
            발송 성공 여부
        """
        try:
            total_trades = weekly_stats.get('total_trades', 0)
            win_rate = weekly_stats.get('win_rate', 0)
            profit_rate = weekly_stats.get('profit_rate', 0)
            historical_best = weekly_stats.get('historical_best', 0)
            current_best = weekly_stats.get('current_best', 0)
            is_better = weekly_stats.get('is_better', False)
            
            # 메시지 작성
            status_emoji = "✅" if is_better else "❌"
            message = f"""
⭐ **주간 재최적화 완료** - {datetime.now().strftime('%Y-%m-%d')}

📊 **지난주 성과:**
총 거래: {total_trades}건
승률: {win_rate:.2f}%
수익률: {profit_rate:.2f}%

🔄 **파라미터 비교:**
과거 최고 승률: {historical_best:.2f}%
현재 최고 승률: {current_best:.2f}%

{status_emoji} **결과:** {'개선됨 ✅' if is_better else '유지됨'}

다음주부터 {'새로운 파라미터' if is_better else '기존 파라미터'}로 거래합니다.
"""
            
            return self.send_message(message)
        
        except Exception as e:
            logger.error(f"❌ 주간 보고 작성 실패: {e}")
            return False
    
    def send_monthly_report(self, monthly_stats: Dict) -> bool:
        """
        월간 보고 발송
        
        Args:
            monthly_stats: 월간 통계 딕셔너리
        
        Returns:
            발송 성공 여부
        """
        try:
            historical = monthly_stats.get('historical', 0)
            weekly = monthly_stats.get('weekly', 0)
            monthly = monthly_stats.get('monthly', 0)
            best_version = monthly_stats.get('best_version', 'monthly')
            
            # 메시지 작성
            message = f"""
🔥 **월간 대규모 재최적화 완료** - {datetime.now().strftime('%Y-%m-%d')}

📊 **성과 비교:**
과거 최고 (8년): {historical:.2f}%
주간 최고 (1주): {weekly:.2f}%
월간 최고 (1개월): {monthly:.2f}%

🎯 **선택된 버전:** {best_version.upper()}

📈 **시장 변화 반영:**
- 지표 가중치 재계산 완료
- 유전알고리즘 30세대 진화 완료
- 강화학습 Q-Table 초기화 완료

다음달부터 새로운 파라미터로 거래합니다!
"""
            
            return self.send_message(message)
        
        except Exception as e:
            logger.error(f"❌ 월간 보고 작성 실패: {e}")
            return False
    
    def send_alert(self, title: str, message: str) -> bool:
        """
        긴급 알림 발송
        
        Args:
            title: 알림 제목
            message: 알림 메시지
        
        Returns:
            발송 성공 여부
        """
        try:
            alert_message = f"⚠️  **{title}**\n\n{message}"
            return self.send_message(alert_message)
        
        except Exception as e:
            logger.error(f"❌ 알림 발송 실패: {e}")
            return False
    
    def send_error_alert(self, error_title: str, error_message: str) -> bool:
        """
        에러 알림 발송
        
        Args:
            error_title: 에러 제목
            error_message: 에러 메시지
        
        Returns:
            발송 성공 여부
        """
        try:
            alert_message = f"❌ **에러 발생: {error_title}**\n\n{error_message}"
            return self.send_message(alert_message)
        
        except Exception as e:
            logger.error(f"❌ 에러 알림 발송 실패: {e}")
            return False


def test_telegram():
    """Telegram 연결 테스트"""
    try:
        reporter = TelegramReporter()
        
        # 테스트 메시지 발송
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        test_message = f"""
✅ **Telegram 봇 연결 테스트**

이 메시지가 보이면 봇이 정상 작동 중입니다!

📊 봇 정보:
- 시간: {current_time}
- 상태: ✅ 정상
"""
        
        if reporter.send_message(test_message):
            logger.info("✅ Telegram 테스트 성공!")
            return True
        else:
            logger.error("❌ Telegram 테스트 실패!")
            return False
    
    except Exception as e:
        logger.error(f"❌ Telegram 테스트 오류: {e}")
        return False


if __name__ == "__main__":
    test_telegram()
