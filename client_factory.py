from alpaca_broker import AlpacaBrokerClient


def create_trading_client_for_settings(settings):
    return AlpacaBrokerClient(
        settings.alpaca_api_key,
        settings.alpaca_secret_key,
        paper=True,
    )


def create_trading_client():
    from config import ALPACA_API_KEY, ALPACA_SECRET_KEY

    class _ConfigBackedSettings:
        alpaca_api_key = ALPACA_API_KEY
        alpaca_secret_key = ALPACA_SECRET_KEY

    return create_trading_client_for_settings(_ConfigBackedSettings())
