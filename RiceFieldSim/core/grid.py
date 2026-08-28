class Grid:
    def __init__(self, grid_width = 40, grid_height = 30, cell_pixel = 20, car_size = 3, offset = 10,
                 exits = None):
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
    
    def to_canvas_coords(self, grid_x, grid_y):
        canvas_x1 = self.offset + (grid_x * self.cell_pixel)
        canvas_y1 = self.offset + (self.grid_height - (grid_y + self.car_size)) * self.cell_pixel
        canvas_x2 = canvas_x1 + (self.car_size * self.cell_pixel)
        canvas_y2 = canvas_y1 + (self.car_size * self.cell_pixel)
        return canvas_x1, canvas_y1, canvas_x2, canvas_y2