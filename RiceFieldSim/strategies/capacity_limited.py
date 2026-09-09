from strategies.base import MovementStrategy
from core.pathfinding import find_path, simplify_path, PathWalker


class CapacityLimitedStrategy(MovementStrategy):
    """幫任何走法加上「稻米容量」限制：車子累積移動 capacity 格距離之後，稻米就會滿，
    必須先開回原點 (0, 0) 卸貨，再用最短的斜線路徑（尋路，會自動避開障礙物）
    走回剛剛停下來的地方，然後繼續原本的走法，直到走完全場。

    容量用的單位是「總移動距離」（跟 Simulator 畫面上顯示的、跟比較走法優劣用的
    同一個單位：每次移動 car_size 格，斜線移動是 car_size*sqrt2 格），不是移動次數
    ——這樣 capacity=100 才會跟「總移動距離 400 多」這種數字有直接對得起來的關係，
    不會因為每次移動實際涵蓋好幾格，導致真正回去卸貨的次數比預期少很多。"""

    def __init__(self, grid, inner_strategy, capacity=100):
        self.inner = inner_strategy
        self.capacity = capacity
        self.distance_since_unload = 0
        self.trip_index = 0  # 目前第幾趟（每次稻米滿了要回去卸貨就 +1），給畫圖換色用
        self.mode = "normal"  # normal / returning / resuming
        self.just_arrived_home = False  # 這個 tick 剛好卸貨完成，給 Simulator 存一張快照用
        self._walker = None
        self._resume_point = None

    @property
    def name(self):
        return f"{self.inner.name}（稻米容量 {self.capacity} 格）"

    def step(self, grid, car):
        if self.mode == "returning":
            return self._travel_step(grid, car, self._start_resuming)
        if self.mode == "resuming":
            return self._travel_step(grid, car, self._finish_resuming)

        distance_before = car.total_distance
        still_running = self.inner.step(grid, car)
        self.distance_since_unload += car.total_distance - distance_before

        if not still_running:
            return False

        if self.distance_since_unload >= self.capacity:
            self._start_returning(grid, car)
        return True

    def _start_returning(self, grid, car):
        print(f"稻米已滿（累積走了 {round(self.distance_since_unload, 1)} 格），先開回原點卸貨！")
        self.trip_index += 1
        self._resume_point = (car.x, car.y)
        self._start_travel(grid, car, (0, 0))
        self.mode = "returning"

    def _start_resuming(self, grid, car):
        print(f"卸貨完成，回到剛剛停下的地方，繼續第 {self.trip_index + 1} 趟！")
        self.distance_since_unload = 0
        self.just_arrived_home = True
        self._start_travel(grid, car, self._resume_point)
        self.mode = "resuming"

    def _finish_resuming(self, grid, car):
        self.mode = "normal"

    def _start_travel(self, grid, car, dest):
        raw = find_path(grid, (car.x, car.y), dest)
        if raw is None:
            print(f"警告：找不到往 {dest} 的路徑，障礙物可能把路完全擋住了！")
            self._walker = PathWalker([])
        else:
            self._walker = PathWalker(simplify_path(raw)[1:])

    def _travel_step(self, grid, car, on_arrive):
        # 跟其他走法一樣，這個函式每個 tick 最多只能讓車子移動一次
        # （Simulator 每個 tick 只畫一條箭頭，多動幾次畫面會被壓縮成一條直線，
        # 可能直接切過障礙物）。
        if self._walker.done():
            on_arrive(grid, car)
            return True
        self._walker.step(car, grid.car_size)
        if self._walker.done():
            on_arrive(grid, car)
        return True
