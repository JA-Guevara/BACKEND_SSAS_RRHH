class VacanteError(Exception):
    pass


class VacanteNotFoundError(VacanteError):
    pass


class VacanteInvalidStateError(VacanteError):
    pass


class VacanteReferenceError(VacanteError):
    pass
