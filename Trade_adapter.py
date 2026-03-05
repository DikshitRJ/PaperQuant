import os
import time
import zmq
import json
import uuid
import logging
import csv
from datetime import datetime
from diskcache import Cache

# -------------------------------------------------
# Configuration
# -------------------------------------------------

ZMQ_BIND_ENDPOINT = os.getenv("SIM_TRADE_BIND_ENDPOINT", "tcp://127.0.0.1:5555")
STATE_CACHE_PATH = os.getenv("SIM_STATE_CACHE_PATH", "./Temporary/state")
LIVEPRICES_CACHE_PATH = os.getenv("SIM_LIVEPRICES_CACHE_PATH", "./Temporary/cache_liveprices")
ORDER_HISTORY_FILE = os.getenv("SIM_ORDER_HISTORY_FILE", "./Temporary/order_history.csv")

# -------------------------------------------------
# Logging
# -------------------------------------------------

logger = logging.getLogger("trade_adapter")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

# -------------------------------------------------
# Helpers
# -------------------------------------------------

def _ok(data):
    return {
        "status": "ok",
        "data": data
    }

def _pending(data):
    return {
        "status": "pending",
        "data": data
    }

def _error(code, message=None):
    return {
        "status": "error",
        "code": code,
        "message": message
    }

def _now_s():
    return time.time()

def log_trade(strategy_id, symbol, action, quantity, price):
    file_exists = os.path.isfile(ORDER_HISTORY_FILE)
    try:
        with open(ORDER_HISTORY_FILE, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['Timestamp', 'Strategy_ID', 'Symbol', 'Action', 'Executed_Quantity', 'Executed_Price'])
            
            timestamp_str = datetime.utcfromtimestamp(_now_s()).isoformat()
            writer.writerow([timestamp_str, strategy_id, symbol, action, quantity, price])
    except Exception as e:
        logger.error(f"Failed to write to order history: {e}")

def update_position(state_cache, strategy_id, symbol, action_type, quantity, execution_price):
    """
    Updates the position and avg_price inside diskcache.
    Supports short selling and properly weights average cost bases.
    """
    state_key = f"{strategy_id}:{symbol}"
    
    current_state = state_cache.get(state_key, {"qty": 0, "avg_price": 0.0})
    
    # Handle older version of diskcache that might just store integers
    if isinstance(current_state, int):
        current_state = {"qty": current_state, "avg_price": 0.0}
        
    current_qty = current_state.get("qty", 0)
    current_avg = current_state.get("avg_price", 0.0)
    
    is_increasing_position = False
    is_flipping_position = False
    
    if action_type == "buy":
        new_qty = current_qty + quantity
        
        if current_qty >= 0:
            is_increasing_position = True
        elif new_qty > 0:
            is_flipping_position = True
            
    elif action_type == "sell":
        new_qty = current_qty - quantity
        
        if current_qty <= 0:
            # -2 - 1 = -3 (increasing short)
            is_increasing_position = True
        elif new_qty < 0:
            is_flipping_position = True

    new_avg = current_avg
    if is_increasing_position:
        # Weighted average
        total_cost = (abs(current_qty) * current_avg) + (quantity * execution_price)
        new_avg = total_cost / abs(new_qty)
    elif is_flipping_position:
        # Starting fresh in the other direction
        new_avg = execution_price
        
    # If position reduces to exactly 0, preserve 0.0 avg
    if new_qty == 0:
        new_avg = 0.0
        
    new_state = {"qty": new_qty, "avg_price": new_avg}
    state_cache.set(state_key, new_state)
    
    return new_qty, new_avg

# -------------------------------------------------
# Main Loop Setup
# -------------------------------------------------

def main():
    logger.info("Initializing Advanced Trade Adapter...")
    
    # Ensure Temp directory exists
    os.makedirs(os.path.dirname(STATE_CACHE_PATH), exist_ok=True)
    
    # Initialize Diskcache
    logger.info(f"Connecting to State Cache: {STATE_CACHE_PATH}")
    state_cache = Cache(STATE_CACHE_PATH)
    
    logger.info(f"Connecting to Live Prices Cache: {LIVEPRICES_CACHE_PATH}")
    liveprices_cache = Cache(LIVEPRICES_CACHE_PATH)
    
    # Initialize ZeroMQ
    context = zmq.Context.instance()
    socket = context.socket(zmq.ROUTER)
    
    logger.info(f"Binding ROUTER socket to {ZMQ_BIND_ENDPOINT}")
    socket.bind(ZMQ_BIND_ENDPOINT)
    
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)
    
    pending_orders = [] # List of dicts
    
    logger.info(f"Writing history to: {ORDER_HISTORY_FILE}")
    logger.info("Trade Adapter is running and listening for orders.")
    
    try:
        while True:
            try:
                # 1. Process pending limit orders
                still_pending = []
                for pending_item in pending_orders:
                    identity = pending_item["identity"]
                    order = pending_item["payload"]
                    strategy_id = order["strategy_id"]
                    symbol = order["symbol"]
                    action_type = order["action"]
                    quantity = order["quantity"]
                    requested_price = order["price"]
                    
                    live_data = liveprices_cache.get(f"prices:{symbol}")
                    live_price = live_data.get("price") if live_data and isinstance(live_data, dict) else None
                    
                    executed = False
                    if live_price is not None:
                        if action_type == "buy" and live_price <= requested_price:
                            with Cache(STATE_CACHE_PATH) as state:
                                new_qty, new_avg = update_position(state, strategy_id, symbol, "buy", quantity, live_price)
                                logger.info(f"PENDING BUY EXECUTION: {strategy_id} bought {quantity} {symbol} @ {live_price}. (Limit: {requested_price}) New Pos: {new_qty} (Avg: {new_avg:.2f})")
                                log_trade(strategy_id, symbol, "buy", quantity, live_price)
                                response_data = _ok({
                                    "symbol": symbol,
                                    "action": "buy",
                                    "executed_quantity": quantity,
                                    "executed_price": live_price,
                                    "current_position": new_qty,
                                    "current_avg_price": new_avg,
                                    "ts": _now_s()
                                })
                                socket.send_multipart([identity, json.dumps(response_data).encode('utf-8')])
                            executed = True
                        elif action_type == "sell" and live_price >= requested_price:
                            with Cache(STATE_CACHE_PATH) as state:
                                new_qty, new_avg = update_position(state, strategy_id, symbol, "sell", quantity, live_price)
                                logger.info(f"PENDING SELL EXECUTION: {strategy_id} sold {quantity} {symbol} @ {live_price}. (Limit: {requested_price}) New Pos: {new_qty} (Avg: {new_avg:.2f})")
                                log_trade(strategy_id, symbol, "sell", quantity, live_price)
                                response_data = _ok({
                                    "symbol": symbol,
                                    "action": "sell",
                                    "executed_quantity": quantity,
                                    "executed_price": live_price,
                                    "current_position": new_qty,
                                    "current_avg_price": new_avg,
                                    "ts": _now_s()
                                })
                                socket.send_multipart([identity, json.dumps(response_data).encode('utf-8')])
                            executed = True
                            
                    if not executed:
                        still_pending.append(pending_item)
                
                pending_orders = still_pending
                
                # 2. Poll for new messages (100ms timeout)
                events = dict(poller.poll(100))
                if socket in events:
                    # Receive multipart message: [identity, payload]
                    message_parts = socket.recv_multipart()
                    
                    if len(message_parts) < 2:
                        continue
                        
                    identity = message_parts[0]
                    payload_bytes = message_parts[-1]
                    
                    try:
                        payload = json.loads(payload_bytes.decode('utf-8'))
                    except json.JSONDecodeError:
                        socket.send_multipart([identity, json.dumps(_error("INVALID_JSON", "Payload must be JSON")).encode('utf-8')])
                        continue

                    # Extract fields
                    action_type = payload.get("action")
                    


                    # ---------------------------------------------------------
                    # Buy/Sell Logic
                    # ---------------------------------------------------------
                    strategy_id = payload.get("strategy_id")
                    symbol = payload.get("symbol")
                    quantity = payload.get("quantity")
                    requested_price = payload.get("price")
                    
                    if not strategy_id or not symbol or not action_type or not quantity:
                        socket.send_multipart([identity, json.dumps(_error("MISSING_FIELDS", "Must provide strategy_id, symbol, action, quantity")).encode('utf-8')])
                        continue
                        
                    # Fetch immediate live price
                    live_data = liveprices_cache.get(f"prices:{symbol}")
                    live_price = live_data.get("price") if live_data and isinstance(live_data, dict) else None
                    
                    response_data = None
                    
                    if requested_price is not None:
                        # Limit order logic
                        can_execute_immediately = False
                        if live_price is not None:
                            if action_type == "buy" and live_price <= requested_price:
                                can_execute_immediately = True
                            elif action_type == "sell" and live_price >= requested_price:
                                can_execute_immediately = True
                                
                        if not can_execute_immediately:
                            # Queue order
                            pending_orders.append({"identity": identity, "payload": payload})
                            logger.info(f"ORDER QUEUED: {action_type} {quantity} {symbol} @ limit {requested_price} for {strategy_id}")
                            continue
                    
                    # Execute immediately
                    execution_price = live_price if requested_price is None else requested_price
                    # If we have no price at all (market order but no live price), reject.
                    if execution_price is None:
                        response_data = _error("NO_PRICE_AVAILABLE", f"No live price available for {symbol}")
                        socket.send_multipart([identity, json.dumps(response_data).encode('utf-8')])
                        continue
                        
                    with Cache(STATE_CACHE_PATH) as state:
                        if action_type == "buy":
                            new_qty, new_avg = update_position(state, strategy_id, symbol, "buy", quantity, execution_price)
                            logger.info(f"IMMEDIATE BUY EXECUTION: {strategy_id} bought {quantity} {symbol} @ {execution_price}. New Pos: {new_qty} (Avg: {new_avg:.2f})")
                            log_trade(strategy_id, symbol, "buy", quantity, execution_price)
                            
                            response_data = _ok({
                                "symbol": symbol,
                                "action": "buy",
                                "executed_quantity": quantity,
                                "executed_price": execution_price,
                                "current_position": new_qty,
                                "current_avg_price": new_avg,
                                "ts": _now_s()
                            })
                            
                        elif action_type == "sell":
                            new_qty, new_avg = update_position(state, strategy_id, symbol, "sell", quantity, execution_price)
                            logger.info(f"IMMEDIATE SELL EXECUTION: {strategy_id} sold {quantity} {symbol} @ {execution_price}. New Pos: {new_qty} (Avg: {new_avg:.2f})")
                            log_trade(strategy_id, symbol, "sell", quantity, execution_price)
                            
                            response_data = _ok({
                                "symbol": symbol,
                                "action": "sell",
                                "executed_quantity": quantity,
                                "executed_price": execution_price,
                                "current_position": new_qty,
                                "current_avg_price": new_avg,
                                "ts": _now_s()
                            })
                        else:
                            response_data = _error("INVALID_ACTION", f"Unknown action: {action_type}")
                            
                    socket.send_multipart([identity, json.dumps(response_data).encode('utf-8')])
                    
            except zmq.ZMQError as e:
                logger.error(f"ZMQ Error in main loop: {e}")
                
    except KeyboardInterrupt:
        logger.info("Trade Adapter shutting down...")
    finally:
        socket.close()
        context.term()
        state_cache.close()
        liveprices_cache.close()

if __name__ == "__main__":
    main()
