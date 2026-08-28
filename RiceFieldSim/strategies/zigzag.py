from strategies.base import MovementStrategy
from core.pathfinding import find_path, simplify_path, PathWalker

class ZigzagStrategy(MovementStrategy):
    name = "Zigzag"

    def __init__(self, grid):
        self.mode = "scan"  # scan / reroute / dash
        self.scan_dir = "RIGHT"
        self._walker = None
        self._row_targets = self._build_row_targets(grid)

    def _build_row_targets(self, grid):
        """要造訪的列（y 座標）清單：除了原本每隔 car_size 一列之外，
        每個障礙物的上緣、下緣也各加一列，讓車子會貼著障礙物上下兩側各多掃一次，
        即使剩下的空隙比車寬還窄，也會走過去而不是直接跳過。"""
        s = grid.car_size
        targets = set()
        y = 0
        while y < grid.max_y:
            targets.add(y)
            y += s
        targets.add(grid.max_y)

        for (_, oy1, _, oy2) in grid.obstacles:
            hug_before = oy1 - s
            hug_after = oy2 + 1
            if 0 <= hug_before <= grid.max_y:
                targets.add(hug_before)
            if 0 <= hug_after <= grid.max_y:
                targets.add(hug_after)

        return sorted(targets)

    def step(self, grid, car):
        target_x, target_y = grid.nearest_exit(car.x, car.y)
        if self.mode == "dash" and car.x == target_x and car.y == target_y:
            return False

        if self.mode == "scan":
            self._scan_step(grid, car)
        elif self.mode == "reroute":
            self._reroute_step(grid, car)
        elif self.mode == "dash":
            self._dash_step(grid, car)
        return True

    def _scan_step(self, grid, car):
        s = grid.car_size
        direction = 1 if self.scan_dir == "RIGHT" else -1
        limit = grid.max_x if direction == 1 else 0
        x, y = car.x, car.y

        target = min(x + direction * s, limit) if direction > 0 else max(x + direction * s, limit)
        if target == x:
            self._go_up_or_finish(grid, car)
            return

        if not grid.is_blocked(target, y):
            car.move_to(target, y)
            return

        # 直接走會撞到障礙物：先貼齊障礙物近側，把剩下不足一步的空隙走完
        # （這一步一定緊貼著現在的位置，不會跨過障礙物）
        hug = self._hug_toward(grid, x, target, y, direction)
        if hug is not None:
            car.move_to(hug, y)
            return

        # 已經貼到障礙物邊上了：改用尋路繞過去，而不是直接「跳」到對面，
        # 這樣車子走出來的路線才不會像是直接穿過障礙物
        far_x = self._find_far_clear_x(grid, target, y, direction, limit)
        if far_x is None:
            self._go_up_or_finish(grid, car)
            return
        self._start_reroute(grid, car, (far_x, y))

    def _hug_toward(self, grid, x, target, y, direction):
        """在 x（不含）跟 target（不含，因為已知被擋住）之間，找離 target
        最近、還沒被擋住的位置，讓車子盡量貼近障礙物再過去。"""
        for v in range(target - direction, x, -direction):
            if not grid.is_blocked(v, y):
                return v
        return None

    def _find_far_clear_x(self, grid, start_x, y, direction, limit):
        v = start_x
        while (direction > 0 and v <= limit) or (direction < 0 and v >= limit):
            if not grid.is_blocked(v, y):
                return v
            v += direction
        return None

    def _find_clear_x_near(self, grid, x, y, max_x):
        """在同一列 (row=y) 找離 x 最近的一個不會撞到障礙物的欄位，兩側都找。"""
        if not grid.is_blocked(x, y):
            return x
        for delta in range(1, max_x + 1):
            for cand in (x - delta, x + delta):
                if 0 <= cand <= max_x and not grid.is_blocked(cand, y):
                    return cand
        return None

    def _go_up_or_finish(self, grid, car):
        remaining = [t for t in self._row_targets if t > car.y]

        for target_y in remaining:
            clear_x = self._find_clear_x_near(grid, car.x, target_y, grid.max_x)
            if clear_x is not None:
                self.scan_dir = "LEFT" if self.scan_dir == "RIGHT" else "RIGHT"
                self._start_reroute(grid, car, (clear_x, target_y))
                return

        self.mode = "dash"
        self._walker = None
        print("全圖掃描完成！切換為直線衝刺！")

    def _start_reroute(self, grid, car, dest):
        raw = find_path(grid, (car.x, car.y), dest)
        if raw is None:
            # 真的被障礙物封死走不過去，放棄這個目標，改找下一列
            self._go_up_or_finish(grid, car)
            return
        self._walker = PathWalker(simplify_path(raw)[1:])
        self.mode = "reroute"
        self._reroute_step(grid, car)

    def _reroute_step(self, grid, car):
        self._walker.step(car, grid.car_size)
        if self._walker.done():
            self.mode = "scan"

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
