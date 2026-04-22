from alpaca.trading.client import TradingClient


def create_trading_client(alpaca_api_key: str, alpaca_secret_key: str):
    return TradingClient(
        alpaca_api_key,
        alpaca_secret_key,
        paper=True,
    )
