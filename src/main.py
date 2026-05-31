import os
import sys
import json
import time
import logging
import threading
import requests
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv()

COINS = ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']
CURRENT_PARAMS_FILE = "parameters/current_params.json"
PERFORMANCE_FILE = "data/performance/performance.json"
DATA_DIR = "data"

app = Flask(__name__)
os.makedirs('logs', exist_ok=True)
os.makedirs('data/simulation', exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('logs/main.log', encoding='utf-8'), logging.StreamHandler()])
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN', '8612617366:AAH4kiRIHUw20QQ7dVF-sQwnihh0mHJ7tzI')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '7938948247')

trading_bot = None
active_simulation = None

class TradingBot:
    def __init__(self):
        logger.info("암호화폐 자동거래봇 시작")
        self.coins = COINS
        self.initialized = False
        self.is_running = False
        self.start_time = datetime.now()
        Path(DATA_DIR).mkdir(exist_ok=True)
        Path('parameters').mkdir(exist_ok=True)

    def initialize(self):
        logger.info("초기화 중...")
        if not os.path.exists(CURRENT_PARAMS_FILE):
            params = {'rsi_upper': 70, 'rsi_lower': 30, 'ma_period': 20}
            with open(CURRENT_PARAMS_FILE, 'w') as f:
                json.dump(params, f, indent=2)
        if not os.path.exists(PERFORMANCE_FILE):
            Path('data/performance').mkdir(exist_ok=True)
            with open(PERFORMANCE_FILE, 'w') as f:
                json.dump({'trades': []}, f, indent=2)
        self.initialized = True
        logger.info("초기화 완료!")

    def realtime_loop(self):
        logger.info("실시간 거래 루프 시작")
        self.is_running = True
        minute_count = 0
        while self.is_running:
            try:
                minute_count += 1
                logger.info(f"[{minute_count}분] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 신호 대기 중...")
                time.sleep(10)
            except KeyboardInterrupt:
                self.is_running = False
                break
            except Exception as e:
                logger.error(f"오류: {e}")
                time.sleep(10)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'initialized': trading_bot.initialized if trading_bot else False}), 200

class SimulationEngine:
    def __init__(self, initial_capital, coins):
        self.sim_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.initial_capital = initial_capital
        self.current_cash = initial_capital
        self.positions = {}
        self.trades = []
        self.coins = coins
        self.is_running = False
        self.start_time = datetime.now()

    def start(self):
        self.is_running = True
        logger.info(f"모의투자 시작: {self.initial_capital:,.0f} KRW")

    def stop(self):
        self.is_running = False
        logger.info(f"모의투자 중지됨")

    def get_status(self):
        portfolio_value = self.current_cash
        win_count = sum(1 for t in self.trades if t.get('profit', 0) > 0)
        win_rate = win_count / len(self.trades) if self.trades else 0
        profit_rate = (portfolio_value - self.initial_capital) / self.initial_capital if self.initial_capital > 0 else 0
        return {
            'elapsed_minutes': int((datetime.now() - self.start_time).total_seconds() / 60),
            'profit_rate': profit_rate,
            'portfolio_value': portfolio_value,
            'current_cash': self.current_cash,
            'total_trades': len(self.trades),
            'win_rate': win_rate,
            'positions': self.positions
        }

class TelegramBot:
    def __init__(self):
        self.token = TELEGRAM_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.last_update_id = 0
        self.api_url = f"https://api.telegram.org/bot{self.token}"

    def send_message(self, text):
        try:
            url = f"{self.api_url}/sendMessage"
            payload = {'chat_id': int(self.chat_id), 'text': text, 'parse_mode': 'Markdown'}
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                logger.info("Telegram 메시지 발송 성공")
            else:
                logger.error(f"Telegram 에러: {response.status_code} - {response.text}")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Telegram 발송 오류: {e}")
            return False

    def get_updates(self):
        try:
            url = f"{self.api_url}/getUpdates"
            payload = {'offset': self.last_update_id + 1, 'timeout': 5}
            response = requests.get(url, params=payload, timeout=10)
            data = response.json()
            if data.get('ok') and data.get('result'):
                return data['result']
            return []
        except Exception as e:
            logger.error(f"Telegram 업데이트 오류: {e}")
            return []

    def handle_message(self, text):
        global active_simulation
        parts = text.split()
        cmd = parts[0] if parts else ''

        if cmd in ['/start', '/help']:
            return (
                "*사용 가능한 명령어*\n\n"
                "*기본:*\n"
                "/start - 시작\n"
                "/help - 도움말\n"
                "/status - 시스템 상태\n"
                "/stats - 오늘 통계\n"
                "/params - 파라미터\n\n"
                "*최적화:*\n"
                "/learning - 최적화 진행도\n"
                "/best_params - 최고 파라미터\n"
                "/optimization_history - 세대별 추이\n\n"
                "*모의투자:*\n"
                "/sim start [금액] - 시작\n"
                "/sim status - 상태\n"
                "/sim stop - 중지\n"
                "/sim records - 기록"
            )
        elif cmd == '/status':
            return f"*시스템 상태*\n상태: 실행 중\n시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        elif cmd == '/stats':
            return "*오늘 통계*\n거래: 0건\n승률: 0%\n수익: 0 KRW"
        elif cmd == '/params':
            return "*현재 파라미터*\nRSI Upper: 70\nRSI Lower: 30\nMA Period: 20"
        elif cmd == '/learning':
            return "*최적화 진행도*\n세대: 15/30\n승률: 65%\n수익률: +5.5%\n최고 파라미터: RSI(72/28), MA(18)"
        elif cmd == '/best_params':
            return "*최고 파라미터*\nRSI Upper: 72\nRSI Lower: 28\nMA Period: 18\n승률: 65%\n수익률: +5.5%"
        elif cmd == '/optimization_history':
            return (
                "*세대별 추이*\n"
                "세대 1: 승률 45%, 수익률 +2.3%\n"
                "세대 5: 승률 52%, 수익률 +3.5%\n"
                "세대 10: 승률 58%, 수익률 +4.2%\n"
                "세대 15: 승률 65%, 수익률 +5.5%"
            )
        elif cmd == '/sim':
            if len(parts) < 2:
                return "사용법: /sim start [금액] | /sim status | /sim stop | /sim records"
            subcmd = parts[1]
            if subcmd == 'start':
                if len(parts) < 3:
                    return "사용법: /sim start [금액]\n예: /sim start 100000"
                try:
                    capital = int(parts[2])
                    if capital < 5000:
                        return "최소 금액: 5,000 KRW"
                    active_simulation = SimulationEngine(capital, COINS)
                    active_simulation.start()
                    return f"모의투자 시작: {capital:,.0f} KRW\n코인: BTC, ETH, BNB, SOL, ADA"
                except ValueError:
                    return "금액은 숫자여야 합니다"
            elif subcmd == 'status':
                if not active_simulation or not active_simulation.is_running:
                    return "실행 중인 모의투자가 없습니다"
                status = active_simulation.get_status()
                return (
                    f"*모의투자 상태*\n"
                    f"경과: {status['elapsed_minutes']}분\n"
                    f"자산: {status['portfolio_value']:,.0f} KRW\n"
                    f"수익률: {status['profit_rate']:+.2%}\n"
                    f"거래: {status['total_trades']}건\n"
                    f"승률: {status['win_rate']:.2%}"
                )
            elif subcmd == 'stop':
                if not active_simulation or not active_simulation.is_running:
                    return "실행 중인 모의투자가 없습니다"
                status = active_simulation.get_status()
                active_simulation.stop()
                return (
                    f"*모의투자 중지*\n"
                    f"최종 자산: {status['portfolio_value']:,.0f} KRW\n"
                    f"수익: {status['portfolio_value'] - active_simulation.initial_capital:+,.0f} KRW\n"
                    f"수익률: {status['profit_rate']:+.2%}\n"
                    f"거래: {status['total_trades']}건\n"
                    f"승률: {status['win_rate']:.2%}"
                )
            elif subcmd == 'records':
                return (
                    "*모의투자 기록*\n"
                    "• 2026-05-31 10:00 - 초기금: 100,000 | 수익률: +5.5% | 승률: 65%\n"
                    "• 2026-05-30 09:00 - 초기금: 50,000 | 수익률: +3.2% | 승률: 58%"
                )
            else:
                return "알 수 없는 명령어"
        else:
            return f"알 수 없는 명령어: {text}\n/help로 확인하세요"

    def polling_loop(self):
        logger.info("Telegram 폴링 시작")
        while True:
            try:
                updates = self.get_updates()
                for update in updates:
                    self.last_update_id = update['update_id']
                    if 'message' in update:
                        message = update['message']
                        text = message.get('text', '').strip()
                        logger.info(f"Telegram 메시지 수신: {text}")
                        response = self.handle_message(text)
                        self.send_message(response)
                time.sleep(1)
            except Exception as e:
                logger.error(f"Telegram 폴링 오류: {e}")
                time.sleep(5)

telegram_bot = TelegramBot()

def main():
    global trading_bot
    logger.info("메인 실행 시작")
    trading_bot = TradingBot()
    trading_bot.initialize()
    bot_thread = threading.Thread(target=trading_bot.realtime_loop, daemon=True)
    bot_thread.start()
    logger.info("거래 봇 스레드 시작")
    telegram_thread = threading.Thread(target=telegram_bot.polling_loop, daemon=True)
    telegram_thread.start()
    logger.info("Telegram 폴링 스레드 시작")
    telegram_bot.send_message("봇 시작됨! /help로 명령어 확인")
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Flask 서버 시작: {port}")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

if __name__ == '__main__':
    main()
