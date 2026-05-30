import os
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

from simulator_v2 import SimulatorV2
from modules.telegram_bot import TelegramBotHandler

tg = TelegramBotHandler()

def run_simulation():
    if not tg.is_running:
        return {"status": "paused"}
    
    print("\n🚀 시뮬레이션")
    simulator = SimulatorV2(initial_balance=100000)
    results = simulator.run_live_simulation()
    simulator.save_results(results)
    tg.update_results(results)
    
    return {"status": "success"}


import functions_framework

@functions_framework.http
def crypto_bot(request):
    return json.dumps(run_simulation())


if __name__ == "__main__":
    run_simulation()
