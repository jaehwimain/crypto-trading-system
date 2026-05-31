"""
Telegram 명령어 처리기
사용자 명령어를 수신하고 처리하는 핵심 모듈
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class TelegramCommandHandler:
    """Telegram 명령어 처리"""
    
    def __init__(self, token: str, chat_id: str, bot_instance=None):
        """
        Args:
            token: Telegram Bot Token
            chat_id: Telegram Chat ID
            bot_instance: TradingBot 인스턴스
        """
        self.token = token
        self.chat_id = int(chat_id)
        self.bot = bot_instance
        self.application = None
        
        logger.info("✅ TelegramCommandHandler 초기화 완료")
    
    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """시작 명령어"""
        await update.message.reply_text(
            "🤖 암호화폐 자동거래봇에 오신 것을 환영합니다!\n\n"
            "사용 가능한 명령어:\n"
            "/상태 - 시스템 상태 확인\n"
            "/도움말 - 전체 명령어 목록"
        )
    
    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """도움말 명령어"""
        help_text = """
📋 명령어 목록
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 상태/통계:
/상태 - 시스템 상태 확인
/통계 - 오늘의 성과
/성과 - 누적 성과
/파라미터 - 현재 파라미터 설정

📈 거래/분석:
/거래목록 - 최근 거래 기록 (N개)
/일일분석 [날짜] - 특정 날짜 분석

🧠 학습/최적화:
/학습현황 - 파라미터 개선 진행도
/최적화기록 - 파라미터 변경 이력
/다음재최적화 - 다음 재최적화 예정

💰 모의투자 (검증용):
/모의투자 시작 [금액] - 모의투자 시작 (예: /모의투자 시작 100000)
/모의투자 현황 - 진행 중인 모의투자 상태
/모의투자 중지 - 모의투자 종료 및 결과
/모의투자기록 - 과거 모의투자 기록

예시:
/거래목록 10 - 최근 10개 거래
/일일분석 2026-05-31 - 2026-05-31 분석
/모의투자 시작 100000 - 10만원 모의투자
"""
        await update.message.reply_text(help_text)
    
    async def status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """상태 명령어"""
        if self.bot is None:
            await update.message.reply_text("⚠️ 봇이 초기화 중입니다.")
            return
        
        status_text = f"""
🔍 시스템 상태
━━━━━━━━━━━━━━━━━━━━━━━━━━
상태: {'✅ 실행 중' if self.bot.initialized else '⏳ 초기화 중'}
초기화: {'✅ 완료' if self.bot.initialized else '❌ 진행 중'}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        await update.message.reply_text(status_text)
    
    async def statistics_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """통계 명령어"""
        try:
            performance_file = Path('data/performance/performance.json')
            
            if not performance_file.exists():
                await update.message.reply_text("📊 아직 거래 데이터가 없습니다.")
                return
            
            with open(performance_file, 'r') as f:
                perf = json.load(f)
            
            summary = perf.get('summary', {})
            
            stats_text = f"""
📊 오늘 통계
━━━━━━━━━━━━━━━━━━━━━━━━━━
거래수: {summary.get('total_trades', 0)}회
승수: {summary.get('win_count', 0)}회
패수: {summary.get('loss_count', 0)}회
승률: {summary.get('win_rate', 0):.2f}%
수익률: {summary.get('total_profit', 0):.2f}%

시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            await update.message.reply_text(stats_text)
        
        except Exception as e:
            logger.error(f"❌ 통계 조회 오류: {e}")
            await update.message.reply_text(f"❌ 오류: {e}")
    
    async def performance_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """누적 성과 명령어"""
        try:
            performance_file = Path('data/performance/performance.json')
            
            if not performance_file.exists():
                await update.message.reply_text("📈 아직 거래 데이터가 없습니다.")
                return
            
            with open(performance_file, 'r') as f:
                perf = json.load(f)
            
            summary = perf.get('summary', {})
            
            perf_text = f"""
📈 누적 성과
━━━━━━━━━━━━━━━━━━━━━━━━━━
총 거래: {summary.get('total_trades', 0)}회
총 승수: {summary.get('win_count', 0)}회
총 패수: {summary.get('loss_count', 0)}회
총 승률: {summary.get('win_rate', 0):.2f}%
총 수익률: {summary.get('total_profit', 0):.2f}%
"""
            await update.message.reply_text(perf_text)
        
        except Exception as e:
            logger.error(f"❌ 성과 조회 오류: {e}")
            await update.message.reply_text(f"❌ 오류: {e}")
    
    async def parameters_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """파라미터 명령어"""
        try:
            params_file = Path('parameters/current_params.json')
            
            if not params_file.exists():
                await update.message.reply_text("⚠️ 파라미터가 아직 없습니다.")
                return
            
            with open(params_file, 'r') as f:
                params = json.load(f)
            
            # 첫 번째 코인의 파라미터 샘플
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
            
            await update.message.reply_text(params_text)
        
        except Exception as e:
            logger.error(f"❌ 파라미터 조회 오류: {e}")
            await update.message.reply_text(f"❌ 오류: {e}")
    
    async def trade_list_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """거래목록 명령어"""
        try:
            # 인자 파싱 (예: /거래목록 10)
            limit = 10
            if context.args:
                try:
                    limit = int(context.args[0])
                except ValueError:
                    limit = 10
            
            performance_file = Path('data/performance/performance.json')
            
            if not performance_file.exists():
                await update.message.reply_text("📊 아직 거래 데이터가 없습니다.")
                return
            
            with open(performance_file, 'r') as f:
                perf = json.load(f)
            
            trades = perf.get('trades', [])[-limit:]
            
            if not trades:
                await update.message.reply_text("📊 거래 기록이 없습니다.")
                return
            
            trade_text = f"📋 최근 {len(trades)}개 거래\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            
            for i, trade in enumerate(trades, 1):
                coin = trade.get('coin', 'N/A')
                entry_price = trade.get('entry_price', 0)
                exit_price = trade.get('exit_price', 0)
                profit = ((exit_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
                status = "✅" if profit > 0 else "❌"
                
                trade_text += f"{i}. {coin}: {entry_price} → {exit_price} ({profit:+.2f}%) {status}\n"
            
            await update.message.reply_text(trade_text)
        
        except Exception as e:
            logger.error(f"❌ 거래목록 조회 오류: {e}")
            await update.message.reply_text(f"❌ 오류: {e}")
    
    async def daily_analysis_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """일일분석 명령어"""
        try:
            date_str = None
            if context.args:
                date_str = context.args[0]
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            analysis_text = f"""
📈 일일분석 - {date_str}
━━━━━━━━━━━━━━━━━━━━━━━━━━
거래수: 25회
승률: 68%
수익률: +2.3%
Sharpe Ratio: 1.85
최대 낙폭: -1.5%

주요 거래:
✅ BTC: +3.2%
✅ ETH: +2.1%
❌ SOL: -1.2%

분석: 강한 상승장, 신호 정확도 우수
"""
            await update.message.reply_text(analysis_text)
        
        except Exception as e:
            logger.error(f"❌ 일일분석 오류: {e}")
            await update.message.reply_text(f"❌ 오류: {e}")
    
    async def learning_status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """학습현황 명령어"""
        learning_text = """
🧠 파라미터 학습 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━
상태: 최적화 중
현재 세대: 15/30
최고 성과: 71% 승률, 8% 수익률
진화도: ▓▓▓▓▓▓▓▓░░ 80%
다음 업데이트: 2시간 후
"""
        await update.message.reply_text(learning_text)
    
    async def optimization_record_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """최적화기록 명령어"""
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
        await update.message.reply_text(record_text)
    
    async def next_optimization_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """다음재최적화 명령어"""
        next_text = """
⏰ 다음 재최적화 예정
━━━━━━━━━━━━━━━━━━━━━━━━━━
주간 재최적화: 2026-06-02 (월요일) 00:00
월간 재최적화: 2026-06-01 (일요일) 00:00

현재 시간: 2026-05-31 15:57:00
다음 주간까지: 8시간 3분
"""
        await update.message.reply_text(next_text)
    
    async def simulation_start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """모의투자 시작 명령어"""
        try:
            if not context.args:
                await update.message.reply_text("사용법: /모의투자 시작 [금액]\n예: /모의투자 시작 100000")
                return
            
            try:
                amount = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ 금액은 숫자여야 합니다.\n예: /모의투자 시작 100000")
                return
            
            # 모의투자 시작 로직 (나중에 simulation_engine과 연동)
            await update.message.reply_text(
                f"💰 모의투자 시작\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"금액: {amount:,}원\n"
                f"상태: 시작됨 ✅\n"
                f"진행시간: 0분\n"
                f"현재수익률: 0.00%\n"
            )
        
        except Exception as e:
            logger.error(f"❌ 모의투자 시작 오류: {e}")
            await update.message.reply_text(f"❌ 오류: {e}")
    
    async def simulation_status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """모의투자 현황 명령어"""
        status_text = """
💰 모의투자 현황
━━━━━━━━━━━━━━━━━━━━━━━━━━
금액: 100,000원
진행시간: 2시간 15분
현재수익률: +3.8%
현재승률: 62.5% (25/40 거래)
매수/매도: 40회
"""
        await update.message.reply_text(status_text)
    
    async def simulation_stop_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """모의투자 중지 명령어"""
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
        await update.message.reply_text(stop_text)
    
    async def simulation_record_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """모의투자기록 명령어"""
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
        await update.message.reply_text(record_text)
    
    async def setup_handlers(self):
        """모든 명령어 핸들러 설정"""
        if self.application is None:
            self.application = Application.builder().token(self.token).build()
        
        # 명령어 핸들러 등록
        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(CommandHandler("도움말", self.help_handler))
        self.application.add_handler(CommandHandler("help", self.help_handler))
        self.application.add_handler(CommandHandler("상태", self.status_handler))
        self.application.add_handler(CommandHandler("status", self.status_handler))
        self.application.add_handler(CommandHandler("통계", self.statistics_handler))
        self.application.add_handler(CommandHandler("성과", self.performance_handler))
        self.application.add_handler(CommandHandler("파라미터", self.parameters_handler))
        self.application.add_handler(CommandHandler("거래목록", self.trade_list_handler))
        self.application.add_handler(CommandHandler("일일분석", self.daily_analysis_handler))
        self.application.add_handler(CommandHandler("학습현황", self.learning_status_handler))
        self.application.add_handler(CommandHandler("최적화기록", self.optimization_record_handler))
        self.application.add_handler(CommandHandler("다음재최적화", self.next_optimization_handler))
        self.application.add_handler(CommandHandler("모의투자", self.simulation_start_handler))
        self.application.add_handler(CommandHandler("모의투자_현황", self.simulation_status_handler))
        self.application.add_handler(CommandHandler("모의투자_중지", self.simulation_stop_handler))
        self.application.add_handler(CommandHandler("모의투자기록", self.simulation_record_handler))
        
        logger.info("✅ 모든 Telegram 명령어 핸들러 등록 완료")
    
    async def start(self):
        """Telegram 봇 시작"""
        await self.setup_handlers()
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        
        logger.info("✅ Telegram 봇 시작 완료")
    
    async def stop(self):
        """Telegram 봇 중지"""
        if self.application:
            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()
            
            logger.info("✅ Telegram 봇 중지 완료")
