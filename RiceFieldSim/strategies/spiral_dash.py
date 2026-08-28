from strategies.base import MovementStrategy
from core.pathfinding import find_path, simplify_path, PathWalker

class SpiralDashStrategy(MovementStrategy):
    name = "spiral + dash"

    def __init__(self, grid):
        self.mode = "spiral"  # spiral / reroute / cleanup / dash
        self.spiral_dir = "RIGHT"
        self.min_x = 0
        self.max_x = grid.max_x
        self.min_y = 0
        self.max_y = grid.max_y
        self._walker = None
        self._resume_dir = None
        # 車子實際走過（車身涵蓋）的格子，用來在螺旋圈跑完之後檢查有沒有漏掃
        self.covered = set()
        self._unreachable = set()
        # 是否真的把核心螺旋掃完，而不是被障礙物擋住提早放棄剩下的區域
        self.full_coverage = True

    def step(self, grid, car):
        self._mark_covered(grid, car)

        target_x, target_y = grid.nearest_exit(car.x, car.y)

        # 抵達終點
        if self.mode == "dash" and car.x == target_x and car.y == target_y:
            return False

        if self.mode == "spiral":
            self._spiral_step(grid, car)
        elif self.mode == "reroute":
            self._reroute_step(grid, car)
        elif self.mode == "cleanup":
            self._cleanup_step(grid, car)
        elif self.mode == "dash":
            self._dash_step(grid, car)
        return True

    def _mark_covered(self, grid, car):
        s = grid.car_size
        for cx in range(car.x, car.x + s):
            for cy in range(car.y, car.y + s):
                self.covered.add((cx, cy))

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

    def _axis_info(self, d):
        if d == "RIGHT":
            return "x", 1, self.max_x
        if d == "LEFT":
            return "x", -1, self.min_x
        if d == "UP":
            return "y", 1, self.max_y
        return "y", -1, self.min_y  # DOWN

    def _spiral_step(self, grid, car):
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

        if moved:
            return

        # 大步、小步都走不動：如果是被障礙物擋住（還沒真的走到這個方向的邊界），
        # 先試著繞過障礙物繼續往同一個方向走，而不是馬上放棄、轉向縮圈——
        # 這樣障礙物旁邊才不會因為提早轉彎而漏掃一塊。
        if self._try_reroute_past_obstacle(grid, car, d):
            return

        # 繞不過去了（障礙物擋到邊界為止，或本來就已經在邊界上），這時才安全轉向並縮圈
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

        if moved:
            return

        if self._try_reroute_past_obstacle(grid, car, d):
            return

        # 如果轉向縮圈後，依然連一步都動彈不得（不管是邊界還是障礙物擋住）
        if self.min_x < self.max_x and self.min_y < self.max_y:
            print("螺旋被障礙物擋住，提前結束核心螺旋，先補掃剩下沒掃到的地方！")
            self.full_coverage = False
        else:
            print("核心螺旋跑完，檢查一下有沒有漏掃的地方！")
        self._enter_cleanup_or_dash(grid, car)

    def _try_reroute_past_obstacle(self, grid, car, d):
        """如果目前方向是被障礙物擋住（還沒到這個方向真正的邊界），
        就找同方向、同一條線上最近一個能走的位置，用尋路繞過去，
        繞完之後恢復原本的方向繼續掃，不會因為障礙物就放棄剩下的路。"""
        axis, direction, limit = self._axis_info(d)
        cur = car.x if axis == "x" else car.y
        if cur == limit:
            return False  # 已經在邊界上了，不是被障礙物擋住，沒有可以繞的空間

        far = self._find_far_clear(grid, car.x, car.y, axis, direction, limit)
        if far is None:
            return False  # 障礙物一路擋到邊界為止，真的繞不過去

        dest = (far, car.y) if axis == "x" else (car.x, far)
        raw = find_path(grid, (car.x, car.y), dest)
        if raw is None:
            return False

        self._walker = PathWalker(simplify_path(raw)[1:])
        self._resume_dir = d
        self.mode = "reroute"
        self._reroute_step(grid, car)
        return True

    def _find_far_clear(self, grid, x, y, axis, direction, limit):
        v = (x if axis == "x" else y) + direction

        def make(v):
            return (v, y) if axis == "x" else (x, v)

        while (direction > 0 and v <= limit) or (direction < 0 and v >= limit):
            if not grid.is_blocked(*make(v)):
                return v
            v += direction
        return None

    def _reroute_step(self, grid, car):
        self._walker.step(car, grid.car_size)
        if self._walker.done():
            self.mode = "spiral"
            self.spiral_dir = self._resume_dir

    # ---- 補掃階段：核心螺旋（含繞障礙物）跑完後，確認全場（扣掉障礙物）
    # 有沒有格子車身完全沒有經過，有的話就開車過去補上，直到補滿或確定
    # 剩下的格子真的到不了為止，這樣才不會因為障礙物旁邊繞不過去而永遠漏一塊。

    def _enter_cleanup_or_dash(self, grid, car):
        self.mode = "cleanup"
        self._walker = None
        self._cleanup_step(grid, car)

    def _cleanup_step(self, grid, car):
        # 重要：這個函式（連同它呼叫的 _start_next_cleanup_target）在同一個 tick
        # 裡最多只能讓車子移動一次。Simulator 每個 tick 只會畫一條箭頭，是從「這個
        # tick 開始前」的位置畫到「strategy.step() 跑完後」的位置；如果同一個
        # tick 裡連續補好幾格（每一段本身都安全），畫出來的箭頭會直接把這幾段安全的
        # 移動「壓縮」成一條直線，這條直線本身完全有可能直接切過障礙物——即使車子
        # 從頭到尾都沒有真的停在障礙物上，畫面看起來還是像穿過去一樣。
        # 所以「找下一個目標」跟「真的移動」必須分成不同 tick 各做一次。
        if self._walker is None:
            if not self._start_next_cleanup_target(grid, car):
                self.mode = "dash"
                self._walker = None
                return

        self._walker.step(car, grid.car_size)
        if self._walker.done():
            self._walker = None  # 這格補完了，下一個 tick 再挑下一個目標並移動

    def _start_next_cleanup_target(self, grid, car):
        """找下一個沒掃到的格子，準備好尋路的路徑，存進 self._walker。
        這裡只負責「規劃」，不會真的移動車子。找不到任何還沒掃到、
        也到得了的格子時回傳 False。"""
        while True:
            cell = self._find_missed_cell(grid)
            if cell is None:
                return False

            gx, gy = cell
            raw = None
            for anchor in self._anchor_candidates(grid, gx, gy):
                raw = find_path(grid, (car.x, car.y), anchor)
                if raw is not None:
                    break

            if raw is None:
                # 這格所有能涵蓋到它的車位都試過了，沒有一個到得了，真的補不到
                self._unreachable.add(cell)
                self.full_coverage = False
                continue

            self._walker = PathWalker(simplify_path(raw)[1:])
            return True

    def _find_missed_cell(self, grid):
        for gx in range(grid.grid_width):
            for gy in range(grid.grid_height):
                cell = (gx, gy)
                if cell in self.covered or cell in self._unreachable:
                    continue
                if any(ox1 <= gx <= ox2 and oy1 <= gy <= oy2 for (ox1, oy1, ox2, oy2) in grid.obstacles):
                    continue
                return cell
        return None

    def _anchor_candidates(self, grid, gx, gy):
        """列出所有沒被擋住、車身涵蓋 (gx, gy) 這格的合法車位。"""
        s = grid.car_size
        for ax in range(max(0, gx - s + 1), min(grid.max_x, gx) + 1):
            for ay in range(max(0, gy - s + 1), min(grid.max_y, gy) + 1):
                if not grid.is_blocked(ax, ay):
                    yield (ax, ay)

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
