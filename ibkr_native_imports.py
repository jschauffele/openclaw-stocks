from __future__ import annotations

from dataclasses import dataclass


class IBKRDependencyUnavailable(ImportError):
    pass


@dataclass(frozen=True, slots=True)
class IBKRNativeAPI:
    e_client: type
    e_wrapper: type
    contract: type
    order: type


def load_ibkr_native_api() -> IBKRNativeAPI:
    try:
        from ibapi.client import EClient
        from ibapi.contract import Contract
        from ibapi.order import Order
        from ibapi.wrapper import EWrapper
    except ImportError as exc:
        raise IBKRDependencyUnavailable(
            "Native IBKR support requires the optional ibapi package; "
            "IBKR runtime support is not enabled yet."
        ) from exc

    return IBKRNativeAPI(
        e_client=EClient,
        e_wrapper=EWrapper,
        contract=Contract,
        order=Order,
    )
