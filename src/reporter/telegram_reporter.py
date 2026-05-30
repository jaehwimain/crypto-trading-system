"""
Telegram 봇 리포터
일일/주간/월간 보고를 Telegram으로 발송합니다.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List
import requests
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
    """Telegram 봇 리포터"""
    
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
""".format(datetime=datetime)
        
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
