import copy
from strategies.base import MovementStrategy
from strategies.spiral_dash import SpiralDashStrategy
from strategies.zigzag import ZigzagStrategy

class AdaptiveOptimalStrategy(MovementStrategy):
    name = "adaptive optimal"

    def __init__(self, grid):
        self.best_strategy_name = None
        self.chosen_strategy = None

    def _evaluate_strategy(self, grid, car):
        strategies_to_list = {
            "Zigzag" : lambda g : ZigzagStrategy(g),
            "Spiral" : lambda g : SpiralDashStrategy(g),
        }

        results = {}

        for name, StrategyClass in strategies_to_list.items():
            sim_grid = copy.deepcopy(grid)
            sim_car = copy.deepcopy(car)

            strat = StrategyClass(sim_grid)

            steps = 0
            max_steps = 5000
            success = False

            while steps < max_steps:
                # 完成與否要看走法自己 step() 回傳的訊號（跟 Simulator._tick
                # 判斷是否停止的方式一致），不能自己另外檢查「車子座標是否
                # 剛好等於出口」。掃描/螺旋階段車子有可能只是路過出口格子，
                # 並不代表該走法真的已經掃完全場、抵達出口；用座標巧合來判斷
                # 完成，會讓某個走法因為掃描路徑「剛好經過」出口而被誤判成
                # 提早完成，導致比較出錯誤的走法。
                still_running = strat.step(sim_grid, sim_car)
                steps += 1

                if not still_running:
                    success = True
                    break

            # 真正該比較的是「總移動距離」而不是「步數」：
            # 每一步移動的格數不一定相同（直走一步 = car_size，
            # 衝刺階段 x、y 同時動屬於斜線 = car_size*sqrt2），
            # 用步數當作路徑長短的依據，會讓「斜線走得多、步數少」的走法
            # 被誤判為距離比較短，導致選錯走法。
            results[name] = sim_car.total_distance if success else float("inf")
        self.best_strategy_name = min(results, key = results.get)

        if self.best_strategy_name == "Zigzag":
            return ZigzagStrategy(grid)
        else:
            return SpiralDashStrategy(grid)
        
    def step(self, grid, car):
        if self.chosen_strategy is None:
            self.chosen_strategy = self._evaluate_strategy(grid, car)

        return self.chosen_strategy.step(grid, car)