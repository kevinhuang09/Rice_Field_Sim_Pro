class Grid:
    def __init__(self, grid_width = 40, grid_height = 30, cell_pixel = 20, car_size = 3, offset = 10,
                 exits = None, obstacles = None):
        # self.grid_size = grid_size
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.cell_pixel = cell_pixel
        self.car_size = car_size
        self.offset = offset

        if exits is None:
            exits = [(0, self.max_y)]
        if isinstance(exits, tuple):
            exits = [exits]
        self.exits = list(exits)

        # 障礙物：可以是長方形，也可以是任意多邊形（例如梯形）。
        #   長方形：兩個對角座標 (x1, y1, x2, y2)，格子座標，含頭尾兩格都算障礙物。
        #     例如 (10, 12, 16, 20)。
        #   多邊形／梯形：頂點座標列表 [(x1, y1), (x2, y2), (x3, y3), ...]，
        #     依序連接成一個封閉形狀，格子中心點落在形狀內就算是障礙物。
        #     梯形範例（下寬上窄）：[(10, 12), (18, 12), (15, 20), (13, 20)]。
        if obstacles is None:
            obstacles = []
        if isinstance(obstacles, tuple):
            obstacles = [obstacles]
        self.obstacle_shapes = [self._normalize_obstacle(o) for o in obstacles]

        self._blocked_cells = set()
        for kind, data in self.obstacle_shapes:
            self._blocked_cells |= self._rasterize(kind, data)

        for ex, ey in self.exits:
            if self.is_blocked(ex, ey):
                print(f"警告：出口 ({ex}, {ey}) 被障礙物擋住，請確認障礙物座標！")

    def _normalize_obstacle(self, obs):
        """回傳 (kind, data)。kind 是 'rect' 或 'polygon'。"""
        items = list(obs)
        if len(items) == 4 and all(not isinstance(v, (list, tuple)) for v in items):
            x1, y1, x2, y2 = items
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
            return ("rect", (x1, y1, x2, y2))

        points = [(float(px), float(py)) for px, py in items]
        return ("polygon", points)

    def _rasterize(self, kind, data):
        """把一個障礙物形狀轉成它涵蓋到的格子座標集合。"""
        cells = set()
        if kind == "rect":
            x1, y1, x2, y2 = data
            for gx in range(int(x1), int(x2) + 1):
                for gy in range(int(y1), int(y2) + 1):
                    cells.add((gx, gy))
            return cells

        xs = [p[0] for p in data]
        ys = [p[1] for p in data]
        min_x, max_x = int(min(xs)), int(max(xs))
        min_y, max_y = int(min(ys)), int(max(ys))
        for gx in range(min_x, max_x + 1):
            for gy in range(min_y, max_y + 1):
                if self._point_in_polygon(gx + 0.5, gy + 0.5, data):
                    cells.add((gx, gy))
        return cells

    @staticmethod
    def _point_in_polygon(px, py, poly):
        """標準 ray casting 演算法，檢查點 (px, py) 是否落在多邊形 poly 內。"""
        inside = False
        n = len(poly)
        j = n - 1
        for i in range(n):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if (yi > py) != (yj > py):
                x_at_py = (xj - xi) * (py - yi) / (yj - yi) + xi
                if px < x_at_py:
                    inside = not inside
            j = i
        return inside

    def obstacle_bounds(self):
        """回傳每個障礙物大致的外接格子範圍 (min_x, min_y, max_x, max_y)，
        給只需要「障礙物大概在哪幾列/幾欄」的走法邏輯用（不需要精確形狀）。"""
        bounds = []
        for kind, data in self.obstacle_shapes:
            if kind == "rect":
                bounds.append(tuple(int(v) for v in data))
            else:
                xs = [p[0] for p in data]
                ys = [p[1] for p in data]
                bounds.append((int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))))
        return bounds

    @property
    def canvas_width(self):
        return self.grid_width * self.cell_pixel + (self.offset * 2)

    @property
    def canvas_height(self):
        return self.grid_height * self.cell_pixel + (self.offset * 2)

    @property
    def max_x(self):
        return self.grid_width - self.car_size

    @property
    def max_y(self):
        return self.grid_height - self.car_size

    def nearest_exit(self, x, y):
        """回傳離 (x, y) 曼哈頓距離最近的出口。"""
        return min(self.exits, key=lambda e: abs(e[0] - x) + abs(e[1] - y))

    def is_obstacle_cell(self, x, y):
        """檢查單一格子 (x, y) 本身是不是障礙物（不考慮車身大小）。"""
        return (x, y) in self._blocked_cells

    def is_blocked(self, x, y):
        """檢查車子（佔用 car_size x car_size 格，以 (x, y) 為左下角）若停在這裡，
        是否超出邊界，或是跟任何障礙物重疊。"""
        if x < 0 or y < 0 or x > self.max_x or y > self.max_y:
            return True

        for cx in range(x, x + self.car_size):
            for cy in range(y, y + self.car_size):
                if (cx, cy) in self._blocked_cells:
                    return True
        return False

    def to_canvas_coords(self, grid_x, grid_y):
        canvas_x1 = self.offset + (grid_x * self.cell_pixel)
        canvas_y1 = self.offset + (self.grid_height - (grid_y + self.car_size)) * self.cell_pixel
        canvas_x2 = canvas_x1 + (self.car_size * self.cell_pixel)
        canvas_y2 = canvas_y1 + (self.car_size * self.cell_pixel)
        return canvas_x1, canvas_y1, canvas_x2, canvas_y2

    def point_to_canvas(self, vx, vy):
        """把一個連續座標的格線點 (vx, vy) 轉成畫布像素座標。"""
        canvas_x = self.offset + vx * self.cell_pixel
        canvas_y = self.offset + (self.grid_height - vy) * self.cell_pixel
        return canvas_x, canvas_y

    def obstacle_polygon_canvas(self, kind, data):
        """把一個障礙物形狀轉成畫布像素座標的頂點列表，給畫圖用。"""
        if kind == "rect":
            x1, y1, x2, y2 = data
            corners = [(x1, y1), (x2 + 1, y1), (x2 + 1, y2 + 1), (x1, y2 + 1)]
        else:
            corners = data
        return [self.point_to_canvas(vx, vy) for vx, vy in corners]
