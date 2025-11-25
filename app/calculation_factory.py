from abc import ABC, abstractmethod
from .schemas import CalculationType

class BaseOperation(ABC):
    def __init__(self, a: float, b: float):
        self.a = a
        self.b = b
    @abstractmethod
    def compute(self) -> float:
        ...

class AddOperation(BaseOperation):
    def compute(self) -> float:
        return self.a + self.b

class SubOperation(BaseOperation):
    def compute(self) -> float:
        return self.a - self.b

class MulOperation(BaseOperation):
    def compute(self) -> float:
        return self.a * self.b

class DivOperation(BaseOperation):
    def compute(self) -> float:
        return self.a / self.b

def get_operation(calc_type: CalculationType, a: float, b: float) -> BaseOperation:
    if calc_type == CalculationType.add:
        return AddOperation(a, b)
    if calc_type == CalculationType.sub:
        return SubOperation(a, b)
    if calc_type == CalculationType.mul:
        return MulOperation(a, b)
    if calc_type == CalculationType.div:
        return DivOperation(a, b)
    raise ValueError(f"Unsupported type: {calc_type}")
