import threading
from decimal import Decimal


class InsufficientFunds(Exception):
    pass


class Account:
    def __init__(self, account_id: str, balance: Decimal) -> None:
        self.id = account_id
        self.balance = balance
        self.lock = threading.Lock()

    def __repr__(self) -> str:
        return f"Account({self.id}, {self.balance})"


class AccountBook:
    def __init__(self) -> None:
        self._accounts: dict[str, Account] = {}

    def open(self, account_id: str, balance: str | Decimal) -> Account:
        acct = Account(account_id, Decimal(balance))
        self._accounts[account_id] = acct
        return acct

    def get(self, account_id: str) -> Account:
        try:
            return self._accounts[account_id]
        except KeyError:
            raise KeyError(f"unknown account {account_id}") from None

    def total(self) -> Decimal:
        return sum((a.balance for a in self._accounts.values()), Decimal(0))
