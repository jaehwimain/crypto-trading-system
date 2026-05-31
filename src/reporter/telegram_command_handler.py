"""
src/reporter/telegram_command_handler.py
Telegram 명령어 핸들러 – 모의투자 엔진과 실제 거래 데이터 연동
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from typing import Optional

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler
)

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reporter.telegram_reporter import TelegramReporter
from simulator.simulation_engine import SimulationEngine, SimulationConfig
from api.upbit_client import UpbitClient

logger = logging.getLogger(__name__)


class TelegramCommandHandler:
    """Telegram 명령어 처리 및 모의투자 엔진 연동"""

    def __init__(self, token: str, chat_id: str, trading_bot_instance=None):
        """
        Args:
            token: Telegram Bot Token
            chat_id: Telegram Chat ID
            trading_bot_instance: TradingBot 인스턴스 (신호 생성용)
        """
        self.token = token
        self.chat_id = chat_id
        self.reporter = TelegramReporter()
        self.trading_bot = trading_bot_instance
        self.upbit_client = UpbitClient()
        self.application = None
        
        logger.info("[Telegram] 명령어 핸들러 초기화")

    async def start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /시작 명령어
        봇 시작 메시지 및 도움말
        """
        welcome_message = (
            "🤖 *암호화폐 자동거래 AI 봇에 오신 것을 환영합니다!*\n\n"
            "이 봇은 다음 기능을 제공합니다:\n"
            "• 실시간 거래 상태 모니터링\n"
            "• 일일/주간 거래 분석\n"
            "• 파라미터 최적화 추적\n"
            "• 금액 지정 모의투자\n\n"
            "`/도움말` 을 입력하여 전체 명령어 목록을 확인하세요."
        )
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        logger.info(f"[Telegram] /시작 – 사용자: {update.effective_user.id}")

    async def help_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /도움말 명령어
        전체 명령어 목록
        """
        help_text = (
            "📋 *전체 명령어 목록*\n\n"
            "*상태 & 통계*\n"
            "`/상태` – 시스템 상태\n"
            "`/통계` – 오늘 거래 통계\n"
            "`/성과` – 누적 성과\n"
            "`/파라미터` – 현재 거래 파라미터\n\n"
            "*거래 정보*\n"
            "`/거래목록` – 최근 거래 목록 (최근 10건)\n"
            "`/일일분석 [YYYY-MM-DD]` – 특정 날짜 분석\n\n"
            "*학습 & 최적화*\n"
            "`/학습현황` – 파라미터 최적화 진행 상태\n"
            "`/최적화기록` – 최근 최적화 변경 기록\n"
            "`/다음재최적화` – 다음 재최적화 예정 시간\n\n"
            "*모의투자 (금액 지정)*\n"
            "`/모의투자 시작 [금액]` – 모의투자 시작 (예: /모의투자 시작 100000)\n"
            "`/모의투자 현황` – 진행 중인 모의투자 상태\n"
            "`/모의투자 중지` – 모의투자 중지\n"
            "`/모의투자 기록` – 과거 모의투자 기록\n"
        )
        await update.message.reply_text(help_text, parse_mode='Markdown')
        logger.info(f"[Telegram] /도움말 – 사용자: {update.effective_user.id}")

    async def status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /상태 명령어
        시스템 및 거래 상태
        """
        try:
            status_info = self._get_system_status()
            response = (
                "🟢 *시스템 상태*\n\n"
                f"상태: {status_info['status']}\n"
                f"현재 시간: {status_info['current_time']}\n"
                f"가동 시간: {status_info['uptime']}\n"
                f"활성 포지션: {status_info['active_positions']}개\n"
                f"오늘 거래 횟수: {status_info['today_trades']}건\n\n"
                f"📊 *수익 현황*\n"
                f"오늘 수익률: {status_info['daily_profit_rate']:+.2%}\n"
                f"누적 수익률: {status_info['total_profit_rate']:+.2%}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /상태 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /상태 오류: {e}")
            await update.message.reply_text("❌ 상태 조회 중 오류가 발생했습니다.")

    async def statistics_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /통계 명령어
        오늘 거래 통계
        """
        try:
            stats = self._get_today_statistics()
            response = (
                "📊 *오늘 거래 통계*\n\n"
                f"거래 횟수: {stats['total_trades']}건\n"
                f"승리: {stats['win_count']}건\n"
                f"패배: {stats['loss_count']}건\n"
                f"승률: {stats['win_rate']:.2%}\n"
                f"총 수익: {stats['total_profit']:+,.0f} KRW\n"
                f"수익률: {stats['profit_rate']:+.2%}\n"
                f"최대 수익 거래: {stats['max_profit_trade']}\n"
                f"최대 손실 거래: {stats['max_loss_trade']}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /통계 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /통계 오류: {e}")
            await update.message.reply_text("❌ 통계 조회 중 오류가 발생했습니다.")

    async def performance_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /성과 명령어
        누적 성과
        """
        try:
            perf = self._get_cumulative_performance()
            response = (
                "🏆 *누적 성과*\n\n"
                f"운영 기간: {perf['operation_days']}일\n"
                f"총 거래 횟수: {perf['total_trades']}건\n"
                f"누적 승률: {perf['win_rate']:.2%}\n"
                f"누적 수익: {perf['total_profit']:+,.0f} KRW\n"
                f"누적 수익률: {perf['profit_rate']:+.2%}\n"
                f"최고 일일 수익률: {perf['best_daily_rate']:+.2%}\n"
                f"최저 일일 수익률: {perf['worst_daily_rate']:+.2%}\n"
                f"Sharpe 지수: {perf['sharpe_ratio']:.2f}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /성과 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /성과 오류: {e}")
            await update.message.reply_text("❌ 성과 조회 중 오류가 발생했습니다.")

    async def parameters_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /파라미터 명령어
        현재 거래 파라미터
        """
        try:
            params = self._load_current_parameters()
            param_text = "\n".join([
                f"• {k}: {v}" for k, v in params.items()
            ])
            response = (
                "⚙️ *현재 거래 파라미터*\n\n"
                f"{param_text}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /파라미터 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /파라미터 오류: {e}")
            await update.message.reply_text("❌ 파라미터 조회 중 오류가 발생했습니다.")

    async def trade_list_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /거래목록 명령어
        최근 거래 목록 (최근 10건)
        """
        try:
            trades = self._get_recent_trades(limit=10)
            if not trades:
                await update.message.reply_text("최근 거래가 없습니다.")
                return
            
            trade_text = "\n".join([
                f"• {t['coin']} – {t['side']} @ {t['price']:,.0f} | "
                f"수익: {t['profit']:+,.0f} ({t['profit_rate']:+.2%}) | "
                f"{t['time']}"
                for t in trades[:10]
            ])
            
            response = (
                "📋 *최근 거래 목록 (최근 10건)*\n\n"
                f"{trade_text}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /거래목록 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /거래목록 오류: {e}")
            await update.message.reply_text("❌ 거래 목록 조회 중 오류가 발생했습니다.")

    async def daily_analysis_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /일일분석 [YYYY-MM-DD] 명령어
        특정 날짜 분석
        """
        try:
            # 날짜 파싱
            if context.args and len(context.args) > 0:
                date_str = context.args[0]
            else:
                date_str = datetime.now().strftime('%Y-%m-%d')
            
            analysis = self._get_daily_analysis(date_str)
            response = (
                f"📅 *{date_str} 분석*\n\n"
                f"거래 횟수: {analysis['trade_count']}건\n"
                f"승률: {analysis['win_rate']:.2%}\n"
                f"수익: {analysis['profit']:+,.0f} KRW\n"
                f"수익률: {analysis['profit_rate']:+.2%}\n"
                f"최대 수익 거래: {analysis['best_trade']}\n"
                f"최대 손실 거래: {analysis['worst_trade']}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /일일분석 {date_str} – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /일일분석 오류: {e}")
            await update.message.reply_text("❌ 일일 분석 조회 중 오류가 발생했습니다.")

    async def learning_status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /학습현황 명령어
        파라미터 최적화 진행 상태
        """
        try:
            status = self._get_learning_status()
            response = (
                "🧠 *파라미터 최적화 현황*\n\n"
                f"상태: {status['status']}\n"
                f"진행도: {status['progress']:.1%}\n"
                f"현재 세대: {status['current_generation']}/{status['total_generations']}\n"
                f"최고 승률: {status['best_win_rate']:.2%}\n"
                f"최고 수익률: {status['best_profit_rate']:+.2%}\n"
                f"마지막 업데이트: {status['last_update']}\n"
                f"다음 업데이트: {status['next_update']}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /학습현황 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /학습현황 오류: {e}")
            await update.message.reply_text("❌ 학습 현황 조회 중 오류가 발생했습니다.")

    async def optimization_record_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /최적화기록 명령어
        최근 파라미터 최적화 변경 기록
        """
        try:
            records = self._get_optimization_records(limit=5)
            if not records:
                await update.message.reply_text("최적화 기록이 없습니다.")
                return
            
            record_text = "\n".join([
                f"• {r['timestamp']} – 승률 {r['win_rate']:.2%}, "
                f"수익률 {r['profit_rate']:+.2%} (RSI: {r['params'].get('rsi_upper', 'N/A')}/{r['params'].get('rsi_lower', 'N/A')})"
                for r in records
            ])
            
            response = (
                "📈 *최적화 변경 기록 (최근 5건)*\n\n"
                f"{record_text}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /최적화기록 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /최적화기록 오류: {e}")
            await update.message.reply_text("❌ 최적화 기록 조회 중 오류가 발생했습니다.")

    async def next_optimization_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /다음재최적화 명령어
        다음 재최적화 예정 시간
        """
        try:
            info = self._get_next_optimization_time()
            response = (
                "⏰ *다음 재최적화*\n\n"
                f"현재 시간: {info['current_time']}\n"
                f"예정 시간: {info['next_optimization_time']}\n"
                f"남은 시간: {info['time_remaining']}\n"
                f"최적화 유형: {info['optimization_type']}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /다음재최적화 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /다음재최적화 오류: {e}")
            await update.message.reply_text("❌ 다음 재최적화 조회 중 오류가 발생했습니다.")

    async def simulation_start_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /모의투자 시작 [금액] 명령어
        금액 지정 모의투자 시작
        """
        try:
            # 금액 파싱
            if not context.args or len(context.args) == 0:
                await update.message.reply_text(
                    "❌ 사용법: `/모의투자 시작 [금액]`\n"
                    "예: `/모의투자 시작 100000`",
                    parse_mode='Markdown'
                )
                return
            
            try:
                initial_capital = int(context.args[0])
            except ValueError:
                await update.message.reply_text(
                    "❌ 금액은 숫자여야 합니다.\n"
                    "예: `/모의투자 시작 100000`",
                    parse_mode='Markdown'
                )
                return
            
            if initial_capital < 5000:
                await update.message.reply_text(
                    "❌ 최소 거래 금액은 5,000 KRW입니다.",
                    parse_mode='Markdown'
                )
                return
            
            # 현재 파라미터 로드
            current_params = self._load_current_parameters()
            
            # 모의투자 시작
            success = await SimulationEngine.start_simulation(
                initial_capital=initial_capital,
                coins=['BTC', 'ETH', 'SOL', 'ADA', 'XRP', 'LINK', 'DOGE', 'MATIC'],
                params=current_params,
                trading_bot_instance=self.trading_bot
            )
            
            if success:
                response = (
                    f"🚀 *모의투자 시작*\n\n"
                    f"초기 자본: {initial_capital:,.0f} KRW\n"
                    f"현재 파라미터: {json.dumps(current_params, ensure_ascii=False, indent=2)}\n\n"
                    f"모의투자가 시작되었습니다. "
                    f"`/모의투자 현황` 으로 진행 상황을 확인하세요."
                )
                await update.message.reply_text(response, parse_mode='Markdown')
                logger.info(f"[Telegram] /모의투자 시작 {initial_capital} – 사용자: {update.effective_user.id}")
            else:
                await update.message.reply_text(
                    "❌ 모의투자 시작 실패 – 이미 진행 중인 시뮬레이션이 있을 수 있습니다.",
                    parse_mode='Markdown'
                )
        except Exception as e:
            logger.error(f"[Telegram] /모의투자 시작 오류: {e}")
            await update.message.reply_text("❌ 모의투자 시작 중 오류가 발생했습니다.")

    async def simulation_status_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /모의투자 현황 명령어
        진행 중인 모의투자 상태
        """
        try:
            simulation = SimulationEngine.get_active_simulation()
            
            if simulation is None:
                await update.message.reply_text(
                    "❌ 현재 진행 중인 모의투자가 없습니다.",
                    parse_mode='Markdown'
                )
                return
            
            status = await simulation.get_status()
            
            positions_text = "\n".join([
                f"• {coin}: {pos['quantity']:.4f} 수량 @ {pos['entry_price']:,.0f} KRW "
                f"| 현재 {pos['profit_rate']:+.2%}"
                for coin, pos in status.get('positions', {}).items()
            ]) if status.get('positions') else "없음"
            
            response = (
                f"📊 *모의투자 현황*\n\n"
                f"경과 시간: {status['elapsed_minutes']}분\n"
                f"현재 수익률: {status['profit_rate']:+.2%}\n"
                f"현재 자산: {status['portfolio_value']:,.0f} KRW\n"
                f"현금: {status['current_cash']:,.0f} KRW\n"
                f"거래 횟수: {status['total_trades']}건\n"
                f"승률: {status['win_rate']:.2%}\n\n"
                f"*보유 포지션*\n"
                f"{positions_text}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /모의투자 현황 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /모의투자 현황 오류: {e}")
            await update.message.reply_text("❌ 모의투자 현황 조회 중 오류가 발생했습니다.")

    async def simulation_stop_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /모의투자 중지 명령어
        모의투자 중지 및 결과 보고
        """
        try:
            summary = await SimulationEngine.stop_simulation("사용자 요청")
            
            if summary is None:
                await update.message.reply_text(
                    "❌ 현재 진행 중인 모의투자가 없습니다.",
                    parse_mode='Markdown'
                )
                return
            
            response = (
                f"🛑 *모의투자 중지*\n\n"
                f"최종 자산: {summary['final_value']:,.0f} KRW\n"
                f"수익: {summary['profit']:+,.0f} KRW\n"
                f"수익률: {summary['profit_rate']:+.2%}\n"
                f"거래 횟수: {summary['total_trades']}건\n"
                f"승리: {summary['win_count']}건\n"
                f"패배: {summary['loss_count']}건\n"
                f"승률: {summary['win_rate']:.2%}\n"
                f"소요 시간: {summary.get('elapsed_time_minutes', 0):.1f}분"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /모의투자 중지 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /모의투자 중지 오류: {e}")
            await update.message.reply_text("❌ 모의투자 중지 중 오류가 발생했습니다.")

    async def simulation_record_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        /모의투자 기록 명령어
        과거 모의투자 기록
        """
        try:
            records = self._get_simulation_records(limit=5)
            if not records:
                await update.message.reply_text("모의투자 기록이 없습니다.")
                return
            
            record_text = "\n".join([
                f"• {r['timestamp']} – "
                f"초기금: {r['initial_capital']:,.0f} KRW | "
                f"수익률: {r['profit_rate']:+.2%} | "
                f"승률: {r['win_rate']:.2%} | "
                f"소요: {r['elapsed_time']:.1f}분 | "
                f"결과: {'✅ 성공' if r['success'] else '❌ 실패'}"
                for r in records
            ])
            
            response = (
                "📜 *모의투자 기록 (최근 5건)*\n\n"
                f"{record_text}"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            logger.info(f"[Telegram] /모의투자 기록 – 사용자: {update.effective_user.id}")
        except Exception as e:
            logger.error(f"[Telegram] /모의투자 기록 오류: {e}")
            await update.message.reply_text("❌ 모의투자 기록 조회 중 오류가 발생했습니다.")

    # ======================== 헬퍼 메서드 ========================

    def _get_system_status(self) -> dict:
        """시스템 상태 조회"""
        try:
            perf_file = "data/performance/daily.json"
            if os.path.exists(perf_file):
                with open(perf_file, 'r') as f:
                    today_data = json.load(f)
            else:
                today_data = {'trades': [], 'profit': 0, 'profit_rate': 0}
            
            return {
                'status': '🟢 정상 운영 중',
                'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'uptime': '24시간 (Cloud Run)',
                'active_positions': len(today_data.get('positions', [])),
                'today_trades': len(today_data.get('trades', [])),
                'daily_profit_rate': today_data.get('profit_rate', 0),
                'total_profit_rate': self._load_total_profit_rate()
            }
        except Exception as e:
            logger.error(f"시스템 상태 조회 오류: {e}")
            return {}

    def _get_today_statistics(self) -> dict:
        """오늘 거래 통계 조회"""
        try:
            perf_file = "data/performance/daily.json"
            if os.path.exists(perf_file):
                with open(perf_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {'trades': []}
            
            trades = data.get('trades', [])
            win_count = sum(1 for t in trades if t.get('profit', 0) > 0)
            loss_count = len(trades) - win_count
            
            return {
                'total_trades': len(trades),
                'win_count': win_count,
                'loss_count': loss_count,
                'win_rate': win_count / len(trades) if trades else 0,
                'total_profit': sum(t.get('profit', 0) for t in trades),
                'profit_rate': data.get('profit_rate', 0),
                'max_profit_trade': max((t.get('profit', 0) for t in trades), default=0),
                'max_loss_trade': min((t.get('profit', 0) for t in trades), default=0)
            }
        except Exception as e:
            logger.error(f"오늘 통계 조회 오류: {e}")
            return {}

    def _get_cumulative_performance(self) -> dict:
        """누적 성과 조회"""
        try:
            perf_file = "data/performance/cumulative.json"
            if os.path.exists(perf_file):
                with open(perf_file, 'r') as f:
                    data = json.load(f)
                return data
            else:
                return {
                    'operation_days': 0,
                    'total_trades': 0,
                    'win_rate': 0,
                    'total_profit': 0,
                    'profit_rate': 0,
                    'best_daily_rate': 0,
                    'worst_daily_rate': 0,
                    'sharpe_ratio': 0
                }
        except Exception as e:
            logger.error(f"누적 성과 조회 오류: {e}")
            return {}

    def _load_current_parameters(self) -> dict:
        """현재 파라미터 로드"""
        try:
            params_file = "parameters/current_params.json"
            if os.path.exists(params_file):
                with open(params_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'rsi_upper': 70,
                    'rsi_lower': 30,
                    'ma_period': 20,
                    'stop_loss': -0.025,
                    'take_profit': 0.05
                }
        except Exception as e:
            logger.error(f"파라미터 로드 오류: {e}")
            return {}

    def _get_recent_trades(self, limit: int = 10) -> list:
        """최근 거래 목록 조회"""
        try:
            perf_file = "data/performance/daily.json"
            if os.path.exists(perf_file):
                with open(perf_file, 'r') as f:
                    data = json.load(f)
                trades = data.get('trades', [])
                return [
                    {
                        'coin': t.get('coin'),
                        'side': t.get('side'),
                        'price': t.get('price'),
                        'profit': t.get('profit', 0),
                        'profit_rate': t.get('profit_rate', 0),
                        'time': t.get('timestamp', 'N/A')
                    }
                    for t in trades[-limit:]
                ]
            else:
                return []
        except Exception as e:
            logger.error(f"최근 거래 조회 오류: {e}")
            return []

    def _get_daily_analysis(self, date_str: str) -> dict:
        """일일 분석 조회"""
        try:
            perf_file = f"data/performance/daily/{date_str}.json"
            if os.path.exists(perf_file):
                with open(perf_file, 'r') as f:
                    data = json.load(f)
                trades = data.get('trades', [])
                win_count = sum(1 for t in trades if t.get('profit', 0) > 0)
                return {
                    'trade_count': len(trades),
                    'win_rate': win_count / len(trades) if trades else 0,
                    'profit': sum(t.get('profit', 0) for t in trades),
                    'profit_rate': data.get('profit_rate', 0),
                    'best_trade': max((t.get('profit', 0) for t in trades), default=0),
                    'worst_trade': min((t.get('profit', 0) for t in trades), default=0)
                }
            else:
                return {
                    'trade_count': 0,
                    'win_rate': 0,
                    'profit': 0,
                    'profit_rate': 0,
                    'best_trade': 0,
                    'worst_trade': 0
                }
        except Exception as e:
            logger.error(f"일일 분석 조회 오류: {e}")
            return {}

    def _get_learning_status(self) -> dict:
        """학습 현황 조회"""
        try:
            learning_file = "data/params/learning_status.json"
            if os.path.exists(learning_file):
                with open(learning_file, 'r') as f:
                    return json.load(f)
            else:
                return {
                    'status': '준비 중',
                    'progress': 0,
                    'current_generation': 0,
                    'total_generations': 30,
                    'best_win_rate': 0,
                    'best_profit_rate': 0,
                    'last_update': 'N/A',
                    'next_update': 'N/A'
                }
        except Exception as e:
            logger.error(f"학습 현황 조회 오류: {e}")
            return {}

    def _get_optimization_records(self, limit: int = 5) -> list:
        """최적화 기록 조회"""
        try:
            records_file = "data/params/optimization_records.json"
            if os.path.exists(records_file):
                with open(records_file, 'r') as f:
                    records = json.load(f)
                return records[-limit:]
            else:
                return []
        except Exception as e:
            logger.error(f"최적화 기록 조회 오류: {e}")
            return []

    def _get_next_optimization_time(self) -> dict:
        """다음 재최적화 예정 시간 조회"""
        now = datetime.now()
        # 매주 월요일 0시, 매달 1일 0시
        next_weekly = now + timedelta(days=(7 - now.weekday()))
        next_weekly = next_weekly.replace(hour=0, minute=0, second=0, microsecond=0)
        
        return {
            'current_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'next_optimization_time': next_weekly.strftime('%Y-%m-%d %H:%M:%S'),
            'time_remaining': str(next_weekly - now),
            'optimization_type': '주간 + 월간'
        }

    def _get_simulation_records(self, limit: int = 5) -> list:
        """모의투자 기록 조회"""
        try:
            import os
            sim_dir = "data/simulation"
            if not os.path.exists(sim_dir):
                return []
            
            files = sorted(os.listdir(sim_dir), reverse=True)[:limit]
            records = []
            
            for fname in files:
                try:
                    with open(f"{sim_dir}/{fname}", 'r') as f:
                        data = json.load(f)
                        records.append({
                            'timestamp': data.get('end_time', 'N/A'),
                            'initial_capital': data.get('initial_capital', 0),
                            'profit_rate': data.get('profit_rate', 0),
                            'win_rate': data.get('win_rate', 0),
                            'elapsed_time': data.get('elapsed_time_minutes', 0),
                            'success': data.get('profit_rate', 0) >= 0.05
                        })
                except Exception as e:
                    logger.error(f"시뮬레이션 파일 로드 오류 ({fname}): {e}")
                    continue
            
            return records
        except Exception as e:
            logger.error(f"모의투자 기록 조회 오류: {e}")
            return []

    def _load_total_profit_rate(self) -> float:
        """누적 수익률 조회"""
        try:
            cumulative_file = "data/performance/cumulative.json"
            if os.path.exists(cumulative_file):
                with open(cumulative_file, 'r') as f:
                    data = json.load(f)
                return data.get('profit_rate', 0)
            else:
                return 0
        except Exception as e:
            logger.error(f"누적 수익률 조회 오류: {e}")
            return 0

    async def setup_handlers(self):
        """Telegram 명령어 핸들러 설정"""
        self.application = Application.builder().token(self.token).build()
        
        # 기본 명령어
        self.application.add_handler(CommandHandler("시작", self.start_handler))
        self.application.add_handler(CommandHandler("start", self.start_handler))
        self.application.add_handler(CommandHandler("도움말", self.help_handler))
        self.application.add_handler(CommandHandler("help", self.help_handler))
        
        # 상태 & 통계
        self.application.add_handler(CommandHandler("상태", self.status_handler))
        self.application.add_handler(CommandHandler("통계", self.statistics_handler))
        self.application.add_handler(CommandHandler("성과", self.performance_handler))
        self.application.add_handler(CommandHandler("파라미터", self.parameters_handler))
        
        # 거래 정보
        self.application.add_handler(CommandHandler("거래목록", self.trade_list_handler))
        self.application.add_handler(CommandHandler("일일분석", self.daily_analysis_handler))
        
        # 학습 & 최적화
        self.application.add_handler(CommandHandler("학습현황", self.learning_status_handler))
        self.application.add_handler(CommandHandler("최적화기록", self.optimization_record_handler))
        self.application.add_handler(CommandHandler("다음재최적화", self.next_optimization_handler))
        
        # 모의투자
        self.application.add_handler(CommandHandler("모의투자", self._handle_simulation_commands))
        
        logger.info("[Telegram] 모든 명령어 핸들러 등록 완료")

    async def _handle_simulation_commands(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """모의투자 명령어 분기"""
        if not context.args:
            await update.message.reply_text(
                "❌ 사용법: `/모의투자 [시작|현황|중지|기록] [금액(시작시에만)]`\n"
                "예: `/모의투자 시작 100000`\n"
                "예: `/모의투자 현황`",
                parse_mode='Markdown'
            )
            return
        
        subcmd = context.args[0]
        
        if subcmd == "시작":
            # /모의투자 시작 [금액]
            context.args = context.args[1:]  # 서브명령어 제거
            await self.simulation_start_handler(update, context)
        elif subcmd == "현황":
            await self.simulation_status_handler(update, context)
        elif subcmd == "중지":
            await self.simulation_stop_handler(update, context)
        elif subcmd == "기록":
            await self.simulation_record_handler(update, context)
        else:
            await update.message.reply_text(
                "❌ 알 수 없는 모의투자 명령어입니다.",
                parse_mode='Markdown'
            )

    async def start(self):
        """Telegram 봇 시작"""
        try:
            await self.setup_handlers()
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            logger.info("[Telegram] 봇 시작 – polling 모드")
        except Exception as e:
            logger.error(f"[Telegram] 봇 시작 오류: {e}")

    async def stop(self):
        """Telegram 봇 중지"""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()
            logger.info("[Telegram] 봇 중지")
        except Exception as e:
            logger.error(f"[Telegram] 봇 중지 오류: {e}")
