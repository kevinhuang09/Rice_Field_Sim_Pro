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

        # 障礙物：長方體清單，每個障礙物用兩個對角座標 (x1, y1, x2, y2) 表示，
        # 座標為「格子座標」，兩個角落格子涵蓋的範圍（含頭尾）都算障礙物。
        if obstacles is None:
            obstacles = []
        if isinstance(obstacles, tuple):
            obstacles = [obstacles]
        self.obstacles = [
            (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))
            for (x1, y1, x2, y2) in obstacles
        ]

        for ex, ey in self.exits:
            if self.is_blocked(ex, ey):
                print(f"警告：出口 ({ex}, {ey}) 被障礙物擋住，請確認障礙物座標！")

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

    def is_blocked(self, x, y):
        """檢查車子（佔用 car_size x car_size 格，以 (x, y) 為左下角）若停在這裡，
        是否超出邊界，或是跟任何障礙物重疊。"""
        if x < 0 or y < 0 or x > self.max_x or y > self.max_y:
            return True

        car_x1, car_y1 = x, y
        car_x2, car_y2 = x + self.car_size - 1, y + self.car_size - 1

        for (ox1, oy1, ox2, oy2) in self.obstacles:
            if car_x1 <= ox2 and car_x2 >= ox1 and car_y1 <= oy2 and car_y2 >= oy1:
                return True
        return False

    def to_canvas_coords(self, grid_x, grid_y):
        canvas_x1 = self.offset + (grid_x * self.cell_pixel)
        canvas_y1 = self.offset + (self.grid_height - (grid_y + self.car_size)) * self.cell_pixel
        canvas_x2 = canvas_x1 + (self.car_size * self.cell_pixel)
        canvas_y2 = canvas_y1 + (self.car_size * self.cell_pixel)
        return canvas_x1, canvas_y1, canvas_x2, canvas_y2

    def rect_to_canvas(self, x1, y1, x2, y2):
        """把「格子座標」的長方形 (x1, y1, x2, y2)（含頭尾兩格）轉成畫布像素座標。"""
        gx1, gx2 = min(x1, x2), max(x1, x2) + 1
        gy1, gy2 = min(y1, y2), max(y1, y2) + 1

        canvas_x1 = self.offset + gx1 * self.cell_pixel
        canvas_x2 = self.offset + gx2 * self.cell_pixel
        canvas_y1 = self.offset + (self.grid_height - gy2) * self.cell_pixel
        canvas_y2 = self.offset + (self.grid_height - gy1) * self.cell_pixel
        return canvas_x1, canvas_y1, canvas_x2, canvas_y2