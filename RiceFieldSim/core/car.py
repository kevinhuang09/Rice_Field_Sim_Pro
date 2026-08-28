class Car:
    def __init__(self, grid, x = 0, y = 0):
        self.grid = grid
        self.x = x
        self.y = y
        self.total_distance = 0
    
    def move_to(self, new_x, new_y):
        if new_x == self.x and new_y == self.y:
            return False
        
        x_changed = (new_x != self.x)
        y_changed = (new_y != self.y)

        if x_changed and y_changed:
            actual_move = self.grid.car_size * 1.4142135
        else:
            actual_move = self.grid.car_size
               
        self.x = new_x
        self.y = new_y
        self.total_distance = round(self.total_distance + actual_move, 1)
        return True

    @property
    def position(self):
        return self.x, self.y