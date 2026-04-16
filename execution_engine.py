import logging

from broker_client import BrokerClient
from broker_models import OrderSubmission


def get_market_session_status(client: BrokerClient) -> dict:
    return client.get_market_session_status().to_dict()


def submit_market_order(
    client: BrokerClient,
    symbol: str,
    qty: int,
    side: str = "buy",
) -> OrderSubmission:
    logging.info("APPROVED — sending LIVE PAPER order")
    response = client.submit_market_order(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force="day",
    )
    logging.info(f"Order submitted with status: {response.status}")
    return response
