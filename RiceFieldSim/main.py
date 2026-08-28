import tkinter as tk
from core.grid import Grid
from core.simulator import Simulator
from strategies.spiral_dash import SpiralDashStrategy
from strategies.zigzag import ZigzagStrategy
from strategies.best import AdaptiveOptimalStrategy

STRATEGY_REGISTRY = {
    "spiral_dash" : lambda grid : SpiralDashStrategy(grid),
    "zigzag" : lambda grid : ZigzagStrategy(grid),
    "select_best" : lambda grid : AdaptiveOptimalStrategy(grid),
}

def build_strategy(strategy_key, grid):
    if strategy_key not in STRATEGY_REGISTRY:
        raise ValueError(f"找不到走法 '{strategy_key}'，可用的有：{list(STRATEGY_REGISTRY)}")
    return STRATEGY_REGISTRY[strategy_key](grid)   # ← 在這裡才真正呼叫 lambda(grid)

def main(strategy_key = "spiral_dash"):
    grid = Grid(grid_width = 30, grid_height = 32, cell_pixel = 20, car_size = 3, offset = 10,
                exits = [(27, 27)],
                # 障礙物（長方體）：每個用兩個對角座標 (x1, y1, x2, y2) 表示，座標是格子座標，
                # 可自行修改/新增，只要不把出口或整個場地完全封死即可。
                obstacles = [(10, 12, 16, 20)])
    strategy = build_strategy(strategy_key, grid)
    root = tk.Tk()
    sim = Simulator(root, strategy = strategy, grid = grid,
                    delay_ms = 100, results_dir = "results")
    
    sim.run()
    root.mainloop()

if __name__ == "__main__":
    # main("zigzag")
    main("spiral_dash")
    # main("select_best")