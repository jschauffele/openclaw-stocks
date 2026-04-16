from bot_service import OpenClawBot
from runtime_settings import load_runtime_settings
from utils import setup_logging


def _create_trading_client(settings):
    return None


def _create_market_data_provider():
    from alpaca_data_provider import AlpacaMarketDataProvider

    return AlpacaMarketDataProvider()


def main():
    settings = load_runtime_settings()
    setup_logging(settings.log_file)

    bot = OpenClawBot(
        settings=settings,
        trading_client_factory=lambda: _create_trading_client(settings),
        market_data_provider_factory=_create_market_data_provider,
    )
    bot.run()


if __name__ == "__main__":
    main()
