from alpaca_broker_adapter import AlpacaBrokerAdapter
from client_factory import create_trading_client


SUPPORTED_BROKERS = {"alpaca"}


def create_broker_adapter(
    broker_name: str,
    *,
    alpaca_api_key: str,
    alpaca_secret_key: str,
):
    normalized_broker = broker_name.strip().lower()

    if normalized_broker == "alpaca":
        client = create_trading_client(alpaca_api_key, alpaca_secret_key)
        return AlpacaBrokerAdapter(client)

    supported = ", ".join(sorted(SUPPORTED_BROKERS))
    raise ValueError(
        f"Unsupported OPENCLAW_BROKER={broker_name!r}; supported brokers: {supported}"
    )
