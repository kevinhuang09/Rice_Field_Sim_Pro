import tkinter as tk
from core.grid import Grid
from core.simulator import Simulator
from strategies.spiral_dash import SpiralDashStrategy
from strategies.zigzag import ZigzagStrategy
from strategies.best import AdaptiveOptimalStrategy
from strategies.capacity_limited import CapacityLimitedStrategy

STRATEGY_REGISTRY = {
    "spiral_dash" : lambda grid : SpiralDashStrategy(grid),
    "zigzag" : lambda grid : ZigzagStrategy(grid),
    "select_best" : lambda grid : AdaptiveOptimalStrategy(grid),
}

def build_strategy(strategy_key, grid, rice_capacity = None):
    if strategy_key not in STRATEGY_REGISTRY:
        raise ValueError(f"找不到走法 '{strategy_key}'，可用的有：{list(STRATEGY_REGISTRY)}")
    strategy = STRATEGY_REGISTRY[strategy_key](grid)   # ← 在這裡才真正呼叫 lambda(grid)

    # 稻米容量：車子累積移動 rice_capacity 格距離（跟「總移動距離」同一個單位）
    # 之後，會先開回原點（0, 0）卸貨，再走最短的斜線路徑（自動避開障礙物）
    # 回到剛剛停下的地方，繼續原本的走法。不需要這個限制的話，設成 None 就好。
    if rice_capacity is not None:
        strategy = CapacityLimitedStrategy(grid, strategy, capacity = rice_capacity)
    return strategy

def main(strategy_key = "spiral_dash", rice_capacity = 200):
    grid = Grid(grid_width = 30, grid_height = 32, cell_pixel = 20, car_size = 3, offset = 10,
                exits = [(27, 27)],
                # 障礙物：可自行修改/新增，只要不把出口或整個場地完全封死即可。
                #   長方形：兩個對角座標 (x1, y1, x2, y2)，格子座標，含頭尾兩格。
                #   梯形／任意多邊形：頂點座標列表 [(x1, y1), (x2, y2), ...]，依序連接成封閉形狀。
                obstacles = [
                    (10, 12, 16, 20),                          # 長方形範例
                    [(1, 12), (5, 12), (3, 10) , (2, 10)],     # 梯形範例（下寬上窄）

                ])
    strategy = build_strategy(strategy_key, grid, rice_capacity = rice_capacity)
    root = tk.Tk()
    sim = Simulator(root, strategy = strategy, grid = grid,
                    delay_ms = 100, results_dir = "results")
    
    sim.run()
    root.mainloop()

if __name__ == "__main__":
    # main("zigzag")
    main("spiral_dash")
    # main("select_best")