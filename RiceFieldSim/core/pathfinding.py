import heapq
import math

# 8 個方向：上下左右 + 對角線
_DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def find_path(grid, start, goal):
    """在以 1 格為單位的細粒度網格上做 A* 尋路，避開邊界與障礙物。

    回傳從 start 到 goal（含頭尾）的座標點列；若找不到路徑則回傳 None。
    """
    if start == goal:
        return [start]

    def heuristic(p):
        dx = abs(p[0] - goal[0])
        dy = abs(p[1] - goal[1])
        # octile distance：直走成本 1，斜走成本 sqrt(2)
        return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)

    open_heap = [(heuristic(start), start)]
    g_score = {start: 0}
    came_from = {}
    visited = set()

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current in visited:
            continue
        visited.add(current)

        if current == goal:
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path

        cx, cy = current
        for dx, dy in _DIRS:
            neighbor = (cx + dx, cy + dy)
            if neighbor in visited:
                continue
            if grid.is_blocked(*neighbor):
                continue

            step_cost = math.sqrt(2) if dx != 0 and dy != 0 else 1
            tentative = g_score[current] + step_cost
            if tentative < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = tentative
                came_from[neighbor] = current
                heapq.heappush(open_heap, (tentative + heuristic(neighbor), neighbor))

    return None


def simplify_path(path):
    """把連續同方向的點壓縮成轉折點，減少要走的路徑點數量（純粹路徑化簡，
    不會改變實際行走的路線，因為原本就是連續同方向的直線）。"""
    if len(path) <= 2:
        return list(path)

    simplified = [path[0]]
    prev_dir = (path[1][0] - path[0][0], path[1][1] - path[0][1])
    for i in range(2, len(path)):
        cur_dir = (path[i][0] - path[i - 1][0], path[i][1] - path[i - 1][1])
        if cur_dir != prev_dir:
            simplified.append(path[i - 1])
            prev_dir = cur_dir
    simplified.append(path[-1])
    return simplified


class PathWalker:
    """依序沿著一串轉折點（simplify_path 的結果）逐步移動車子，每次最多走
    step_size 格，走法內部的計時器（每個 tick 呼叫一次 step）會自然把長距離
    的路線拆成好幾個 tick 慢慢走完，畫出來的每一段箭頭都貼著真正安全的路線，
    不會有一步直接跳過障礙物、看起來像穿過去的狀況。"""

    def __init__(self, waypoints):
        self.waypoints = waypoints
        self.idx = 0

    def done(self):
        return self.idx >= len(self.waypoints)

    def step(self, car, step_size):
        if self.done():
            return
        x, y = car.x, car.y
        tx, ty = self.waypoints[self.idx]
        dx, dy = tx - x, ty - y

        step_x = min(abs(dx), step_size) * (1 if dx > 0 else -1) if dx else 0
        step_y = min(abs(dy), step_size) * (1 if dy > 0 else -1) if dy else 0

        car.move_to(x + step_x, y + step_y)
        if car.x == tx and car.y == ty:
            self.idx += 1
