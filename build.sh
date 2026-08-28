set -e 

PROJECT="${1:-RiceFieldSim}"

echo "開始建立專案 : $PROJECT"


echo "[1/4] 建立資料夾..."
mkdir -p "$PROJECT/core"
mkdir -p "$PROJECT/strategies"
mkdir -p "$PROJECT/results"


echo "[2/4] 建立 core/ 檔案..."
touch "$PROJECT/core/__init__.py"
touch "$PROJECT/core/grid.py"
touch "$PROJECT/core/car.py"
touch "$PROJECT/core/simulator.py"

echo "[3/4] 建立 strategies/ 檔案..."
touch "$PROJECT/strategies/__init__.py"
touch "$PROJECT/strategies/base.py"
touch "$PROJECT/strategies/spiral_dash.py"

echo "[4/4] 建立進入點與雜項檔案..."
touch "$PROJECT/main.py"
touch "$PROJECT/README.md"
touch "$PROJECT/results/.gitkeep"

# 印出整棵樹方便確認
echo ""
echo " 骨架建立完成！結構如下："
if command -v tree >/dev/null 2>&1; then
  tree "$PROJECT"
else
  find "$PROJECT" | sort | sed "s|[^/]*/|  |g"
fi
