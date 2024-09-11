import MetaTrader5 as mt5
import json
import time
from datetime import datetime
from collections import deque
from colorama import Fore, init, Style

# Initialize colorama for colored terminal output
init(autoreset=True)

# Initialize MetaTrader 5
if not mt5.initialize(path="C:\Program Files\Deriv\\terminal64.exe"):
    print("Failed to initialize MetaTrader 5")
    quit()

# Define constants and variables
TICKS_BUFFER_SIZE = 1000
symbols = {
    # Crash symbols
    "Crash 300 Index": {"json_file": "c3.json", "ratio": 300, "type": "crash"},
    "Crash 500 Index": {"json_file": "c5.json", "ratio": 500, "type": "crash"},
    "Crash 1000 Index": {"json_file": "c1.json", "ratio": 1000, "type": "crash"},
    
    # Boom symbols
    "Boom 300 Index": {"json_file": "b3.json", "ratio": 300, "type": "boom"},
    "Boom 500 Index": {"json_file": "b5.json", "ratio": 500, "type": "boom"},
    "Boom 1000 Index": {"json_file": "b1.json", "ratio": 1000, "type": "boom"}
}
tick_buffers = {symbol: deque(maxlen=TICKS_BUFFER_SIZE) for symbol in symbols}

# Function to save tick data and algorithm adjustments
def save_to_json(symbol, tick_data):
    with open(symbols[symbol]["json_file"], 'w') as f:
        json.dump(tick_data, f, indent=4)

# Function to load tick data for continuity on restart
def load_tick_data(symbol):
    try:
        with open(symbols[symbol]["json_file"], 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Initialize tick data for all symbols
tick_data = {symbol: load_tick_data(symbol) for symbol in symbols}

# Function to print the monitoring heading
def print_heading():
    print(Fore.BLUE + "==== MONITORING ====")

# Function to calculate and display the average ratio for Crash symbols
def calculate_crash_ratios():
    for symbol in symbols:
        if symbols[symbol]['type'] != 'crash':
            continue
        
        total_up_ticks = sum(1 for tick in tick_data[symbol] if tick['movement'] == 'up')
        total_down_ticks = sum(1 for tick in tick_data[symbol] if tick['movement'] == 'down')
        
        # Avoid division by zero
        if total_down_ticks == 0:
            total_down_ticks = 1
        
        # Calculate average ratio
        if total_up_ticks == 0:
            average_ratio = 0
        else:
            average_ratio = total_up_ticks / total_down_ticks
        
        # Calculate the rounded ratio for display
        rounded_ratio = round(average_ratio)
        
        # Determine if the ratio exceeds the threshold
        threshold = symbols[symbol]["ratio"]
        
        display_ratio = f"{Fore.RED}1{Fore.RESET}:{Fore.GREEN}{rounded_ratio}{Fore.RESET}"

        if rounded_ratio >= threshold:
            print(Fore.YELLOW + symbol)
            print(display_ratio + Fore.MAGENTA + " *")
        else:
            print(Fore.YELLOW + symbol)
            print(display_ratio)

# Function to calculate and display the average ratio for Boom symbols
def calculate_boom_ratios():
    for symbol in symbols:
        if symbols[symbol]['type'] != 'boom':
            continue
        
        total_up_ticks = sum(1 for tick in tick_data[symbol] if tick['movement'] == 'up')
        total_down_ticks = sum(1 for tick in tick_data[symbol] if tick['movement'] == 'down')
        
        # Avoid division by zero
        if total_up_ticks == 0:
            total_up_ticks = 1
        
        # Calculate average ratio
        if total_down_ticks == 0:
            average_ratio = 0
        else:
            average_ratio = total_down_ticks / total_up_ticks
        
        # Calculate the rounded ratio for display
        rounded_ratio = round(average_ratio)
        
        # Determine if the ratio exceeds the threshold
        threshold = symbols[symbol]["ratio"]
        
        display_ratio = f"{Fore.GREEN}1{Fore.RESET}:{Fore.RED}{rounded_ratio}{Fore.RESET}"

        if rounded_ratio >= threshold:
            print(Fore.YELLOW + symbol)
            print(display_ratio + Fore.MAGENTA + " *")
        else:
            print(Fore.YELLOW + symbol)
            print(display_ratio)

# Function to record tick and calculate stats
def record_tick(symbol, tick):
    if not tick_buffers[symbol]:
        tick_buffers[symbol].append({'ask': tick['ask'], 'bid': tick['bid']})
        return
    
    last_tick = tick_buffers[symbol][-1]
    price_change = tick['ask'] - last_tick['ask']
    
    # Determine tick movement based on price_change
    if symbols[symbol]['type'] == 'boom':
        movement = 'up' if price_change > 0.0 else 'down'
    elif symbols[symbol]['type'] == 'crash':
        movement = 'up' if price_change >= 0.0 else 'down'
    
    # Record tick with timestamp
    tick_data[symbol].append({
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'movement': movement,
        'ask': tick['ask'],
        'bid': tick['bid'],
        'price_change': price_change
    })
    
    # Save tick data for persistence
    save_to_json(symbol, tick_data[symbol])
    
    # Print current average up/down tick ratio
    print_heading()
    calculate_crash_ratios()
    calculate_boom_ratios()
    
    tick_buffers[symbol].append({'ask': tick['ask'], 'bid': tick['bid']})

# Function to handle incoming ticks from the market
def monitor_ticks():
    last_ticks = {symbol: None for symbol in symbols}
    
    while True:
        for symbol in symbols:
            # Check if symbol exists and is valid
            if not mt5.symbol_info(symbol):
                print(f"Symbol '{symbol}' not found.")
                continue
            
            # Retrieve the latest tick data
            tick = mt5.symbol_info_tick(symbol)
            
            if tick:
                if last_ticks[symbol] is not None and (tick.ask != last_ticks[symbol].ask or tick.bid != last_ticks[symbol].bid):
                    price_change = tick.ask - last_ticks[symbol].ask
                    record_tick(symbol, {'ask': tick.ask, 'bid': tick.bid, 'price_change': price_change})
                
                last_ticks[symbol] = tick
            else:
                print(f"No ticks received for {symbol}.")
        
        time.sleep(0.8)  # Check for new ticks every 10 seconds

# Main function
def main():
    try:
        while True:
            monitor_ticks()
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
    finally:
        mt5.shutdown()

if __name__ == '__main__':
    main()
