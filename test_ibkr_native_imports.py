from __future__ import annotations

import sys
import types
import unittest
from contextlib import contextmanager
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec


class BlockingIbapiFinder(MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "ibapi" or fullname.startswith("ibapi."):
            raise ImportError("blocked test ibapi import")
        return None


@contextmanager
def without_ibapi_modules():
    original_modules = {
        name: module for name, module in sys.modules.items() if name == "ibapi" or name.startswith("ibapi.")
    }
    for name in original_modules:
        sys.modules.pop(name, None)
    finder = BlockingIbapiFinder()
    sys.meta_path.insert(0, finder)
    try:
        yield
    finally:
        sys.meta_path.remove(finder)
        for name in list(sys.modules):
            if name == "ibapi" or name.startswith("ibapi."):
                sys.modules.pop(name, None)
        sys.modules.update(original_modules)


@contextmanager
def with_fake_ibapi_modules():
    original_modules = {
        name: module for name, module in sys.modules.items() if name == "ibapi" or name.startswith("ibapi.")
    }
    for name in original_modules:
        sys.modules.pop(name, None)

    class EClient:
        pass

    class EWrapper:
        pass

    class Contract:
        pass

    class Order:
        pass

    package = types.ModuleType("ibapi")
    package.__path__ = []
    package.__spec__ = ModuleSpec("ibapi", loader=None, is_package=True)

    client = types.ModuleType("ibapi.client")
    client.EClient = EClient
    wrapper = types.ModuleType("ibapi.wrapper")
    wrapper.EWrapper = EWrapper
    contract = types.ModuleType("ibapi.contract")
    contract.Contract = Contract
    order = types.ModuleType("ibapi.order")
    order.Order = Order

    sys.modules.update(
        {
            "ibapi": package,
            "ibapi.client": client,
            "ibapi.wrapper": wrapper,
            "ibapi.contract": contract,
            "ibapi.order": order,
        }
    )
    try:
        yield {
            "EClient": EClient,
            "EWrapper": EWrapper,
            "Contract": Contract,
            "Order": Order,
        }
    finally:
        for name in list(sys.modules):
            if name == "ibapi" or name.startswith("ibapi."):
                sys.modules.pop(name, None)
        sys.modules.update(original_modules)


class IBKRNativeImportsTests(unittest.TestCase):
    def test_importing_boundary_module_does_not_require_ibapi(self) -> None:
        with without_ibapi_modules():
            import ibkr_native_imports

        self.assertTrue(hasattr(ibkr_native_imports, "load_ibkr_native_api"))

    def test_missing_native_dependency_raises_explicit_error(self) -> None:
        from ibkr_native_imports import IBKRDependencyUnavailable, load_ibkr_native_api

        with without_ibapi_modules():
            with self.assertRaisesRegex(
                IBKRDependencyUnavailable,
                "Native IBKR support requires the optional ibapi package",
            ):
                load_ibkr_native_api()

    def test_fake_native_modules_return_api_container(self) -> None:
        from ibkr_native_imports import IBKRNativeAPI, load_ibkr_native_api

        with with_fake_ibapi_modules() as fake_classes:
            native_api = load_ibkr_native_api()

        self.assertIsInstance(native_api, IBKRNativeAPI)
        self.assertIs(native_api.e_client, fake_classes["EClient"])
        self.assertIs(native_api.e_wrapper, fake_classes["EWrapper"])
        self.assertIs(native_api.contract, fake_classes["Contract"])
        self.assertIs(native_api.order, fake_classes["Order"])


if __name__ == "__main__":
    unittest.main()
