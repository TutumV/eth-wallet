from decimal import Decimal


class AddressNotValidException(Exception):
    pass


class WalletNotFoundException(Exception):
    pass


class TargetWalletNotValidException(Exception):
    pass


class NodeException(Exception):
    pass


class InsufficientFundsException(Exception):
    def __init__(self, available: Decimal, required: Decimal):
        self.message = 'insufficient funds'
        self.available = available
        self.required = required
