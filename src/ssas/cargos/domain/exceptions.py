class CargoError(Exception):
    """Error base del modulo cargos."""


class CargoAlreadyExistsError(CargoError):
    pass


class CargoNotFoundError(CargoError):
    pass


class CargoInUseError(CargoError):
    pass


class InvalidDepartamentoForCargoError(CargoError):
    pass
