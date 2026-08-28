from strategies.base import MovementStrategy
from core.pathfinding import find_path, simplify_path, PathWalker

class SpiralDashStrategy(MovementStrategy):
    name = "spiral + dash"

    def __init__(self, grid):
        self.mode = "spiral"
        self.spiral_dir = "RIGHT"
        self.min_x = 0
        self.max_x = grid.max_x
        self.min_y = 0
        self.max_y = grid.max_y
        self._walker = None
        # 是否真的把核心螺旋掃完，而不是被障礙物擋住提早放棄剩下的區域
        self.full_coverage = True

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
            self._dash_step(grid, car)
        return True

    def _turn(self, s):
        d = self.spiral_dir
        if d == "RIGHT":
            self.spiral_dir = "UP"; self.min_y += s
        elif d == "UP":
            self.spiral_dir = "LEFT"; self.max_x -= s
        elif d == "LEFT":
            self.spiral_dir = "DOWN"; self.max_y -= s
        elif d == "DOWN":
            self.spiral_dir = "RIGHT"; self.min_x += s

    def _spiral_step(self, grid, car):
        # 注意：螺旋是靠 min_x/max_x/min_y/max_y 這組會逐圈內縮的邊界記錄目前掃到哪，
        # 一旦某一步因為障礙物只走了「不足一整步」的距離，這組邊界記錄就會跟車子
        # 實際位置對不上，圈與圈之間的內縮量就會算錯，繞了幾圈後可能導致邊界互相
        # 交錯甚至跑到 grid 範圍外，讓後面的判斷式進入無法跳出的迴圈。
        # 所以這裡刻意「不」貼著障礙物走完剩下的空隙——遇到障礙物就跟遇到邊界一樣，
        # 直接視為這個方向走不動、轉向縮圈；障礙物周圍真正需要「補走」沒掃到的地方，
        # 交給 Zigzag 走法處理（它的列是固定的，不會有這種邊界記錄跟實際位置兜不攏的問題）。
        s = grid.car_size
        x, y = car.x, car.y
        moved = False
        d = self.spiral_dir

        # 嘗試用大步（3格）前進：邊界跟障礙物都要擋
        if d == "RIGHT" and x + s <= self.max_x and not grid.is_blocked(x + s, y):
            car.move_to(x + s, y); moved = True
        elif d == "UP" and y + s <= self.max_y and not grid.is_blocked(x, y + s):
            car.move_to(x, y + s); moved = True
        elif d == "LEFT" and x - s >= self.min_x and not grid.is_blocked(x - s, y):
            car.move_to(x - s, y); moved = True
        elif d == "DOWN" and y - s >= self.min_y and not grid.is_blocked(x, y - s):
            car.move_to(x, y - s); moved = True

        # 大步走不動了，檢查是不是因為「最後一格不夠大」（貼邊距離本來就 < s），
        # 是的話才小步貼邊；如果貼邊距離其實還很長（代表大步是被障礙物擋住，
        # 不是快到邊界），就不能直接跳過去，不然會直接「穿過」障礙物。
        if not moved:
            if d == "RIGHT" and 0 < self.max_x - x < s and not grid.is_blocked(self.max_x, y):
                car.move_to(self.max_x, y); moved = True
            elif d == "UP" and 0 < self.max_y - y < s and not grid.is_blocked(x, self.max_y):
                car.move_to(x, self.max_y); moved = True
            elif d == "LEFT" and 0 < x - self.min_x < s and not grid.is_blocked(self.min_x, y):
                car.move_to(self.min_x, y); moved = True
            elif d == "DOWN" and 0 < y - self.min_y < s and not grid.is_blocked(x, self.min_y):
                car.move_to(x, self.min_y); moved = True

        # 大步、小步都走不動（邊界或障礙物擋住），這時才「安全轉向」並「縮圈」
        if not moved:
            self._turn(s)

            # 轉向並縮圈後，立刻在新方向嘗試走一步，防止原地空轉
            d = self.spiral_dir
            if d == "RIGHT":
                if x + s <= self.max_x and not grid.is_blocked(x + s, y): car.move_to(x + s, y); moved = True
                elif 0 < self.max_x - x < s and not grid.is_blocked(self.max_x, y): car.move_to(self.max_x, y); moved = True
            elif d == "UP":
                if y + s <= self.max_y and not grid.is_blocked(x, y + s): car.move_to(x, y + s); moved = True
                elif 0 < self.max_y - y < s and not grid.is_blocked(x, self.max_y): car.move_to(x, self.max_y); moved = True
            elif d == "LEFT":
                if x - s >= self.min_x and not grid.is_blocked(x - s, y): car.move_to(x - s, y); moved = True
                elif 0 < x - self.min_x < s and not grid.is_blocked(self.min_x, y): car.move_to(self.min_x, y); moved = True
            elif d == "DOWN":
                if y - s >= self.min_y and not grid.is_blocked(x, y - s): car.move_to(x, y - s); moved = True
                elif 0 < y - self.min_y < s and not grid.is_blocked(x, self.min_y): car.move_to(x, self.min_y); moved = True

            # 如果轉向縮圈後，依然連一步都動彈不得（不管是邊界還是障礙物擋住）
            if not moved:
                if self.min_x < self.max_x and self.min_y < self.max_y:
                    print("螺旋被障礙物擋住，提前切換為直線衝刺！")
                    self.full_coverage = False
                else:
                    print("核心螺旋完成！切換為直線衝刺！")
                self.mode = "dash"

    def _dash_step(self, grid, car):
        if self._walker is None:
            target = grid.nearest_exit(car.x, car.y)
            raw = find_path(grid, (car.x, car.y), target)
            if raw is None:
                print("警告：找不到通往出口的路徑，障礙物可能把出口完全擋住了！")
                self._walker = PathWalker([])
            else:
                self._walker = PathWalker(simplify_path(raw)[1:])
        self._walker.step(car, grid.car_size)
