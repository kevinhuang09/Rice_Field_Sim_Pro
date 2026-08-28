from strategies.base import MovementStrategy

class SpiralDashStrategy(MovementStrategy):
    name = "spiral + dash"

    def __init__(self, grid):
        self.mode = "spiral"
        self.spiral_dir = "RIGHT"
        self.min_x = 0
        self.max_x = grid.max_x
        self.min_y = 0
        self.max_y = grid.max_y

    def step(self, grid, car):
        target_x, target_y = grid.nearest_exit(car.x, car.y)

        # 抵達終點
        if self.mode == "dash" and car.x == target_x and car.y == target_y:
            return False
        
        # 螺旋階段
        if self.mode == "spiral":
            self._spiral_step(grid, car)
        # 衝刺階段
        elif self.mode == "dash":
            return self._dash_step(grid, car)    
        return True
    
    def _spiral_step(self, grid, car):
        s = grid.car_size
        x, y = car.x, car.y
        moved = False
        d = self.spiral_dir

        # 嘗試用大步（3格）前進
        if d == "RIGHT" and x + s <= self.max_x:
            car.move_to(x + s, y); moved = True
        elif d == "UP" and y + s <= self.max_y:
            car.move_to(x, y + s); moved = True
        elif d == "LEFT" and x - s >= self.min_x:
            car.move_to(x - s, y); moved = True
        elif d == "DOWN" and y - s >= self.min_y:
            car.move_to(x, y - s); moved = True

        # 大步走不動了，檢查是不是因為「最後一格不夠大」，是的話就小步貼邊
        if not moved:
            if d == "RIGHT" and x < self.max_x:
                car.move_to(self.max_x, y); moved = True
            elif d == "UP" and y < self.max_y:
                car.move_to(x, self.max_y); moved = True
            elif d == "LEFT" and x > self.min_x:
                car.move_to(self.min_x, y); moved = True
            elif d == "DOWN" and y > self.min_y:
                car.move_to(x, self.min_y); moved = True

        # 如果大步走不動、小步也已經貼到牆了，這時才「安全轉向」並「縮減邊界」
        if not moved:
            if d == "RIGHT":
                self.spiral_dir = "UP"; self.min_y += s
            elif d == "UP":
                self.spiral_dir = "LEFT"; self.max_x -= s
            elif d == "LEFT":
                self.spiral_dir = "DOWN"; self.max_y -= s
            elif d == "DOWN":
                self.spiral_dir = "RIGHT"; self.min_x += s
            
            # 轉向並縮圈後，立刻在新方向嘗試走一步），防止原地空轉
            d = self.spiral_dir
            if d == "RIGHT":
                if x + s <= self.max_x: car.move_to(x + s, y); moved = True
                elif x < self.max_x: car.move_to(self.max_x, y); moved = True
            elif d == "UP":
                if y + s <= self.max_y: car.move_to(x, y + s); moved = True
                elif y < self.max_y: car.move_to(x, self.max_y); moved = True
            elif d == "LEFT":
                if x - s >= self.min_x: car.move_to(x - s, y); moved = True
                elif x > self.min_x: car.move_to(self.min_x, y); moved = True
            elif d == "DOWN":
                if y - s >= self.min_y: car.move_to(x, y - s); moved = True
                elif y > self.min_y: car.move_to(x, self.min_y); moved = True
            
            # 如果轉向縮圈後，依然連一步都動彈不得
            if not moved:
                print("核心螺旋完成！切換為直線衝刺！")
                self.mode = "dash"

    def _dash_step(self, grid, car):
        s = grid.car_size
        target_x, target_y = grid.nearest_exit(car.x, car.y)
        new_x, new_y = car.x, car.y

        if target_x == car.x and target_y == car.y:
            return False

        if car.x != target_x:
            if car.x > target_x:
                new_x = max(target_x, car.x - s)
            else:
                new_x = min(target_x, car.x + s)
        if car.y != target_y:
            if car.y > target_y:
                new_y = max(target_y, car.y - s)
            else:
                new_y = min(target_y, car.y + s)

        return car.move_to(new_x, new_y)