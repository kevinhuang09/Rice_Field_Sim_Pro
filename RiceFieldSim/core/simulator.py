import os
import datetime
import tkinter as tk
import math

from core.grid import Grid
from core.car import Car
from PIL import Image, ImageDraw, ImageFont

class Simulator:
    def __init__(self, root, strategy, grid = None, delay_ms = 100, results_dir = "results"):
        self.root = root
        self.grid = grid or Grid()
        self.car = Car(self.grid, x = 0, y = 0)
        self.strategy = strategy
        self.delay_ms = delay_ms

        self.results_dir = results_dir
        os.makedirs(self.results_dir, exist_ok = True)
        self.step_log = []
        self.step_count = 0
        self.finished = False

        self.root.title(f"Rice Field : {strategy.name}")

        self.distance_label = tk.Label(
            root, text = self._distance_text(),
            font = ("Arial", 12, "bold"), fg = "#333333", pady = 5,
        )
        self.distance_label.pack()

        # draw 
        self.canvas = tk.Canvas(root, width = self.grid.canvas_width,
                                 height = self.grid.canvas_height, bg = "white")
        self.canvas.pack()

        self._img = Image.new("RGB",
                              (self.grid.canvas_width, self.grid.canvas_height),
                              "white")
        self._draw = ImageDraw.Draw(self._img)
        # load traditional chinese font
        self._font = self._load_cjk_font(14)
        
        self._draw_grid()
        self._draw_exit()
        self.car_rect = self._draw_car()

        self.prev_xy = (self.car.x, self.car.y)

        

        # self.root.after(self.delay_ms, self._tick)

    def run(self):
        self.root.after(self.delay_ms, self._tick)

    def _distance_text(self):
        return (f"走法：{self.strategy.name}  |  "
                f"總移動距離：{self.car.total_distance} 格 "
                f"(每次移動 {self.grid.car_size} 格)")
    
    def _load_cjk_font(self, size):
        candidates = [
            "C:/Windows/Fonts/msjh.ttc",                                # Windows 微軟正黑體
            "C:/Windows/Fonts/mingliu.ttc",                             # Windows 細明體
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",   # Linux / WSL Noto CJK
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",   # Linux 另一種路徑
            "/System/Library/Fonts/PingFang.ttc",                       # macOS
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue
        # 全部找不到就用內建預設字型（可能無法顯示中文）
        return ImageFont.load_default()

    def _draw_pil_arrowhead(self, x1, y1, x2, y2, size=12, width=5, color="#ff6600"):

        angle = math.atan2(y2 - y1, x2 - x1)

        left_x = x2 - size * math.cos(angle) + width * math.sin(angle)
        left_y = y2 - size * math.sin(angle) - width * math.cos(angle)
        right_x = x2 - size * math.cos(angle) - width * math.sin(angle)
        right_y = y2 - size * math.sin(angle) + width * math.cos(angle)

        self._draw.polygon(
            [(x2, y2), (left_x, left_y), (right_x, right_y)],
            fill=color,
        )

    def _draw_text(self, xy, text, fill="#000000", anchor="mm"):
        self._draw.text(xy, text, fill=fill, font=self._font, anchor=anchor)

    def _draw_grid(self):
        g = self.grid

        for i in range(g.grid_width + 1):
            pos_x = g.offset + (i * g.cell_pixel)
            self.canvas.create_line(pos_x, g.offset, pos_x, g.canvas_height - g.offset, fill="#e0e0e0")
            self._draw.line([pos_x, g.offset, pos_x, g.canvas_height - g.offset], fill="#e0e0e0")

        for j in range(g.grid_height + 1):
            pos_y = g.offset + (j * g.cell_pixel)
            self.canvas.create_line(g.offset, pos_y, g.canvas_width - g.offset, pos_y, fill="#e0e0e0")
            self._draw.line([g.offset, pos_y, g.canvas_width - g.offset, pos_y], fill="#e0e0e0")

    def _draw_exit(self):
        g = self.grid
        for ex, ey in g.exits:
            x1, y1, x2, y2 = g.to_canvas_coords(ex, ey)
            
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#ccffcc", outline="#00aa00")
            self._draw.rectangle([x1, y1, x2, y2], fill="#ccffcc", outline="#00aa00")

            text_x = (x1 + x2) / 2
            text_y = (y1 + y2) / 2
            self.canvas.create_text(text_x, text_y, text="出口",
                                    font=("Arial", 10, "bold"), fill="#006600")
            self._draw_text((text_x, text_y), "終點", fill = "#006600", anchor = "mm")

    def _draw_car(self):
        x1, y1, x2, y2 = self.grid.to_canvas_coords(self.car.x, self.car.y)
        return self.canvas.create_rectangle(x1, y1, x2, y2, fill="#1e90ff", outline="#00008b")

    def _draw_move_arrow(self, old_x, old_y, new_x, new_y):
        ox1, oy1, ox2, oy2 = self.grid.to_canvas_coords(old_x, old_y)
        nx1, ny1, nx2, ny2 = self.grid.to_canvas_coords(new_x, new_y)


        start_x = (ox1 + ox2) / 2
        start_y = (oy1 + oy2) / 2
        end_x = (nx1 + nx2) / 2
        end_y = (ny1 + ny2) / 2

        # PRL draw
        self._draw.line([start_x, start_y, end_x, end_y], fill = "#ff6600", width = 2)
        self._draw_pil_arrowhead(start_x, start_y, end_x, end_y)

        # canvas draw
        self.canvas.create_line(
            start_x, start_y, end_x, end_y,
            fill = "#ff6600",
            width = 2,
            arrow = tk.LAST,
            arrowshape = (10, 12, 5),
        )

    def _tick(self):
        if self.finished: return

        old_x, old_y = self.car.x, self.car.y

        still_running = self.strategy.step(self.grid, self.car)
        self.step_count += 1

        line = (f"step {self.step_count:>4} | 座標 ({self.car.x:>2}, {self.car.y:>2}) "
                f"| 累計距離 {self.car.total_distance} 格")
        self.step_log.append(line)
        print(line)

        # update screen
        self.distance_label.config(text = self._distance_text())
        x1, y1, _, _ = self.grid.to_canvas_coords(self.car.x, self.car.y)
        self.canvas.moveto(self.car_rect, x1, y1)

        if (self.car.x, self.car.y) != (old_x, old_y):
            self._draw_move_arrow(old_x, old_y, self.car.x, self.car.y)

        if not still_running:
            self._finish()
            return 
        
        self.root.after(self.delay_ms, self._tick)

    def save_png(self, filename = None):
        picture_dir = os.path.join(self.results_dir, "picture")
        os.makedirs(picture_dir, exist_ok = True)

        # build a safe filename
        if filename is None:
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            safe = self.strategy.name.replace(" ", "_").replace("+", "plus")
            filename = os.path.join(picture_dir, f"{ts}_{safe}.png")
        
        if not filename.endswith(("png", "jpg")):
            filename += "png"

        # if only filename add this path
        if not os.path.isabs(filename) and os.path.dirname(filename) == "":
            filename = os.path.join(picture_dir, filename)

        self._img.save(filename)
        print(f"模擬路徑圖片已儲存 : {filename}")
        return filename

    # @property
    def _finish(self):
        self.finished = True
        self.strategy.on_finish(self.grid, self.car)
        self._write_results()
        # default is store png file
        self.save_png()

    # @property
    def _write_results(self):
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = self.strategy.name.replace(" ", "_").replace("+", "plus")

        # 1. step log
        log_path = os.path.join(self.results_dir, f"{ts}_{safe_name}_log.txt")
        with open(log_path, "w", encoding = "utf-8") as f:
            f.write(f"走法：{self.strategy.name}\n")
            f.write(f"時間：{ts}\n")
            f.write("=" * 40 + "\n")
            f.write("\n".join(self.step_log))
            f.write("\n")

        # 2. final summary
        
        reached = (self.car.x, self.car.y) in self.grid.exits

        summary_path = os.path.join(self.results_dir, f"{ts}_{safe_name}_summary.txt")
        with open(summary_path, "w", encoding = "utf-8") as f:
            f.write("==== 模擬結果摘要 ====\n")
            f.write(f"走法名稱   : {self.strategy.name}\n")
            f.write(f"總步數     : {self.step_count}\n")
            f.write(f"總移動距離 : {self.car.total_distance} 格\n")
            f.write(f"最終座標   : ({self.car.x}, {self.car.y})\n")
            f.write(f"是否抵達出口: {'是' if reached else '否'}\n")

        print(f"\nThe result write at : {log_path}\n - {summary_path}")            