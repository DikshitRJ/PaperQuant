import os
import time
import zmq
import json
import logging
from diskcache import Cache

# -------------------------------------------------
# Configuration
# -------------------------------------------------

ZMQ_BIND_ENDPOINT = os.getenv("SIM_TRADE_BIND_ENDPOINT", "tcp://127.0.0.1:5555")
STATE_CACHE_PATH = os.getenv("SIM_STATE_CACHE_PATH", "./Temporary/state")
LIVEPRICES_CACHE_PATH = os.getenv("SIM_LIVEPRICES_CACHE_PATH", "./Temporary/cache_liveprices")

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

# -------------------------------------------------
# Main Loop Setup
# -------------------------------------------------

def main():
    logger.info("Initializing Trade Adapter...")
    
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
    
    pending_orders = []
    
    logger.info("Trade Adapter is running and listening for orders.")
    
    try:
        while True:
            try:
                # 1. Process pending limit orders
                still_pending = []
                for order in pending_orders:
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
                            state_key = f"{strategy_id}:{symbol}"
                            with Cache(STATE_CACHE_PATH) as state:
                                current_qty = state.get(state_key, 0)
                                new_qty = current_qty + quantity
                                state.set(state_key, new_qty)
                                logger.info(f"PENDING BUY EXECUTION: {strategy_id} bought {quantity} {symbol} @ {live_price}. (Limit: {requested_price}) New Pos: {new_qty}")
                            executed = True
                        elif action_type == "sell" and live_price >= requested_price:
                            state_key = f"{strategy_id}:{symbol}"
                            with Cache(STATE_CACHE_PATH) as state:
                                current_qty = state.get(state_key, 0)
                                if current_qty < quantity:
                                    logger.warning(f"PENDING SELL REJECTED - INSUFFICIENT POSITION: {strategy_id} tried to sell {quantity} {symbol} but only owns {current_qty}. Dropping order.")
                                else:
                                    new_qty = current_qty - quantity
                                    state.set(state_key, new_qty)
                                    logger.info(f"PENDING SELL EXECUTION: {strategy_id} sold {quantity} {symbol} @ {live_price}. (Limit: {requested_price}) New Pos: {new_qty}")
                            executed = True
                            
                    if not executed:
                        still_pending.append(order)
                
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
                    strategy_id = payload.get("strategy_id")
                    symbol = payload.get("symbol")
                    action_type = payload.get("action")
                    quantity = payload.get("quantity")
                    requested_price = payload.get("price")
                    
                    if not strategy_id or not symbol or not action_type or not quantity:
                        socket.send_multipart([identity, json.dumps(_error("MISSING_FIELDS", "Must provide strategy_id, symbol, action, quantity")).encode('utf-8')])
                        continue
                        
                    state_key = f"{strategy_id}:{symbol}"
                    
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
                            pending_orders.append(payload)
                            logger.info(f"ORDER QUEUED: {action_type} {quantity} {symbol} @ limit {requested_price} for {strategy_id}")
                            response_data = _pending({
                                "symbol": symbol,
                                "action": action_type,
                                "quantity": quantity,
                                "limit_price": requested_price,
                                "message": "Order placed in pending queue"
                            })
                            socket.send_multipart([identity, json.dumps(response_data).encode('utf-8')])
                            continue
                    
                    # Execute immediately
                    execution_price = live_price if requested_price is None else requested_price
                    # If we have no price at all (market order but no live price), reject.
                    if execution_price is None:
                        response_data = _error("NO_PRICE_AVAILABLE", f"No live price available for {symbol}")
                        socket.send_multipart([identity, json.dumps(response_data).encode('utf-8')])
                        continue
                        
                    with Cache(STATE_CACHE_PATH) as state:
                        current_qty = state.get(state_key, 0)
                        
                        if action_type == "buy":
                            new_qty = current_qty + quantity
                            state.set(state_key, new_qty)
                            logger.info(f"IMMEDIATE BUY EXECUTION: {strategy_id} bought {quantity} {symbol} @ {execution_price}. New Pos: {new_qty}")
                            response_data = _ok({
                                "symbol": symbol,
                                "action": "buy",
                                "executed_quantity": quantity,
                                "executed_price": execution_price,
                                "current_position": new_qty,
                                "ts": _now_s()
                            })
                            
                        elif action_type == "sell":
                            if current_qty < quantity:
                                logger.warning(f"IMMEDIATE SELL REJECTED - INSUFFICIENT POSITION: {strategy_id} tried to sell {quantity} {symbol} but owns {current_qty}")
                                response_data = _error("INSUFFICIENT_POSITION", f"Cannot sell {quantity}, position is {current_qty}")
                            else:
                                new_qty = current_qty - quantity
                                state.set(state_key, new_qty)
                                logger.info(f"IMMEDIATE SELL EXECUTION: {strategy_id} sold {quantity} {symbol} @ {execution_price}. New Pos: {new_qty}")
                                response_data = _ok({
                                    "symbol": symbol,
                                    "action": "sell",
                                    "executed_quantity": quantity,
                                    "executed_price": execution_price,
                                    "current_position": new_qty,
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
