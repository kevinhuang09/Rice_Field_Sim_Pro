"""
除錯用小工具：完全比照 best.py（AdaptiveOptimalStrategy._evaluate_strategy）
目前的評估邏輯，把每個走法評估過程中的細節印出來，方便確認 best.py
最後選出來的走法對不對。

評估邏輯（跟 best.py 一致）：
    - 用 strategy.step() 自己回傳的 still_running 訊號判斷走法是否真的
      跑完（跟 Simulator._tick 判斷停止的方式一致），不是用「car 座標
      是否剛好等於出口座標」這種可能在掃描/螺旋階段就巧合成立的判斷法。
    - 走法優劣用「總移動距離」(total_distance) 比較，不是用步數，
      因為直走一步跟衝刺階段的斜線一步走的距離不一樣
      (car_size vs car_size*sqrt2)。

執行方式：
    python -m strategies.best_debug
"""
import copy

from core.grid import Grid
from core.car import Car
from strategies.spiral_dash import SpiralDashStrategy
from strategies.zigzag import ZigzagStrategy

STRATEGIES = {
    "Zigzag": lambda g: ZigzagStrategy(g),
    "Spiral": lambda g: SpiralDashStrategy(g),
}


def evaluate_strategy(grid, car, max_steps=5000):
    """跟 best.py 的 _evaluate_strategy 完全同一套邏輯，多印出過程細節。"""
    results = {}

    for name, StrategyClass in STRATEGIES.items():
        sim_grid = copy.deepcopy(grid)
        sim_car = copy.deepcopy(car)

        strat = StrategyClass(sim_grid)

        steps = 0
        success = False

        while steps < max_steps:
            still_running = strat.step(sim_grid, sim_car)
            steps += 1

            if not still_running:
                success = True
                break

        distance = sim_car.total_distance if success else float("inf")
        results[name] = distance

        status = "完成" if success else "未完成(超過 max_steps)"
        print(f"  {name:8s} | {status:20s} | 步數={steps:5d} | "
              f"總移動距離={distance if success else float('inf'):>8} | "
              f"終點={(sim_car.x, sim_car.y)} | 結束時 mode={getattr(strat, 'mode', '?')}")

    best_strategy_name = min(results, key=results.get)
    print(f"\n  各走法總移動距離: {results}")
    print(f"  => best.py 會選擇: {best_strategy_name}")
    return best_strategy_name


def main():
    grid = Grid(grid_width=30, grid_height=32, cell_pixel=20, car_size=3, offset=10,
                exits=[(27, 27)])
    car = Car(grid, x=0, y=0)

    print("==== 依照 best.py 的評估邏輯執行 ====")
    evaluate_strategy(grid, car)


if __name__ == "__main__":
    main()
