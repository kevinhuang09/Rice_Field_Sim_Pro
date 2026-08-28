from strategies.base import MovementStrategy
from strategies.spiral_dash import SpiralDashStrategy
from strategies.zigzag import ZigzagStrategy

class AdaptiveOptimalStrategy(MovementStrategy):
    name = "adaptive optimal"

    def __init__(self, grid):
        self.best_strategy_name = None
        self.chosen_strategy = None

    def _evaluate_strategy(self, grid, car):
        W = grid.max_x
        H = grid.max_y
        s = grid.car_size

        start_x = car.x
        start_y = car.y

        tx, ty = grid.nearest_exit(start_x, start_y)

        zigzag_rows = (H // s) + 1
        steps_per_row = (W // s) + (1 if W % s != 0 else 0)
        zigzag_scan_steps = (zigzag_rows * steps_per_row) + zigzag_rows

        end_z_x = 0 if zigzag_rows % 2 == 0 else W
        end_z_y = H
        zigzag_dash_steps = max(abs(end_z_x - tx), abs(end_z_y - ty)) // s

        total_zigzag_steps = zigzag_scan_steps + zigzag_dash_steps

        spiral_scan_steps = (W * H) // (s * s)

        end_s_x = W // 2
        end_s_y = H // 2
        spiral_dash_steps = max(abs(end_s_x - tx), abs(end_s_y - ty)) // s

        total_spiral_steps = spiral_scan_steps + spiral_dash_steps

        if total_zigzag_steps < total_spiral_steps:
            self.best_strategy_name = "Zigzag"
        else:
            self.best_strategy_name = "Spiral"

        print("\n=============================================")
        print(f"📐 數學幾何預估步數 -> Zigzag: ~{int(total_zigzag_steps)} 步 | Spiral: ~{int(total_spiral_steps)} 步")
        print(f"===> 100% 預判選擇最優走法: [{self.best_strategy_name}] <===")
        print("=============================================\n")

        if self.best_strategy_name == "Zigzag":
            return ZigzagStrategy(grid)
        else:
            return SpiralDashStrategy(grid)

    def step(self, grid, car):
        if self.chosen_strategy is None:
            self.chosen_strategy = self._evaluate_strategy(grid, car)

        return self.chosen_strategy.step(grid, car)
