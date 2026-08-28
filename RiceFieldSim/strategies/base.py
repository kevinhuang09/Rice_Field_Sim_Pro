from abc import ABC, abstractmethod

class MovementStrategy(ABC):
    name = "undefine method"

    @abstractmethod
    def step(self, grid, car):
        raise NotImplementedError
    
    def on_finish(self, grid, car):
        print(f"method {self.name} is complete!\nfinal coordination : {car.position}\ntotal distance : {car.total_distance}")