from strategies.base import MovementStrategy

class ZigzagStrategy(MovementStrategy):
    name = "Zigzag"

    def __init__(self, grid):
        self.mode = "scan"
        self.scan_dir = "RIGHT"
    
    def step(self, grid, car):
        target_x, target_y = grid.nearest_exit(car.x, car.y)
        if self.mode == "dash" and car.x == target_x and car.y == target_y:
            return False
        if self.mode == "scan":
            self._scan_step(grid, car)
        elif self.mode == "dash":
            self._dash_step(grid, car)
        return True
    
    def _scan_step(self, grid, car):
        s = grid.car_size
        x, y = car.x, car.y
        
        if self.scan_dir == "RIGHT":
            # to right
            if x + s <= grid.max_x:
                car.move_to(x + s, y)
            elif x < grid.max_x:
                car.move_to(grid.max_x, y)
            else:
                self._go_up_or_finish(grid, car)
        else:
            # to left
            if x - s >= 0:
                car.move_to(x - s, y)
            elif x > 0:
                car.move_to(0, y)
            else:
                self._go_up_or_finish(grid, car)

    def _go_up_or_finish(self, grid, car):
        s = grid.car_size
        if car.y + s <= grid.max_y:
            car.move_to(car.x, car.y + s)
            self.scan_dir = "LEFT" if self.scan_dir == "RIGHT" else "RIGHT"
        elif car.y < grid.max_y:
            car.move_to(car.x, grid.max_y)
            self.scan_dir = "LEFT" if self.scan_dir == "RIGHT" else "RIGHT"
        else:
            self.mode = "dash"
            print("全圖掃描完成！切換為直線衝刺！")
   
    def _dash_step(self, grid, car):
        s = grid.car_size
        tx, ty = grid.nearest_exit(car.x, car.y)
        nx, ny = car.x, car.y
        if car.x != tx:
            if car.x < tx:
                nx = min(tx, car.x + s)
            else:
                nx = max(tx, car.x - s)
        # revise elif -> if let x, y可同時移動
        if car.y != ty:
            if car.y < ty:
                ny = min(ty, car.y + s)
            else:
                ny = max(ty, car.y - s)
        car.move_to(nx, ny)
