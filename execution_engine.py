import logging

from broker_interface import BrokerOpenOrderState, BrokerPositionState
from alpaca_broker_adapter import AlpacaBrokerAdapter
from market_session_service import get_market_session_status


def build_market_order(symbol: str, qty: int):
    return AlpacaBrokerAdapter(None).build_market_order(symbol, qty)


def get_existing_position(client, symbol: str) -> BrokerPositionState:
    return AlpacaBrokerAdapter(client).get_existing_position(symbol)


def get_open_buy_order_qty(client, symbol: str) -> BrokerOpenOrderState:
    return AlpacaBrokerAdapter(client).get_open_buy_order_qty(symbol)


def submit_market_order(client, order):
    return AlpacaBrokerAdapter(client).submit_market_order(order)
