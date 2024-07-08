import heapq
import logging

# ロギングの設定
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def heuristic(a, b):
    """
    2つの点間のヒューリスティック距離（マンハッタン距離）を計算する。
    
    引数:
    a (tuple): 最初の点 (行, 列)。
    b (tuple): 2つ目の点 (行, 列)。
    
    戻り値:
    int: 2つの点間のマンハッタン距離。
    """
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star(grid, start, goal):
    """
    グリッド内の最短経路を見つけるためのA*アルゴリズム。
    
    引数:
    grid (list of list of int): グリッド（0は空きスペース、1は障害物）。
    start (tuple): スタート地点 (行, 列)。
    goal (tuple): ゴール地点 (行, 列)。
    
    戻り値:
    list of tuple: スタート地点からゴール地点までの最短経路。
    """
    logging.info(f"Starting A* search from {start} to {goal} with grid:\n{grid}")

    open_list = []
    heapq.heappush(open_list, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}

    while open_list:
        current = heapq.heappop(open_list)[1]

        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path = path[::-1]
            logging.info(f"Path found: {path}")
            return path

        neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for direction in neighbors:
            neighbor = (current[0] + direction[0], current[1] + direction[1])

            if 0 <= neighbor[0] < len(grid) and 0 <= neighbor[1] < len(grid[0]) and grid[neighbor[0]][neighbor[1]] == 0:
                tentative_g_score = g_score[current] + 1

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_list, (f_score[neighbor], neighbor))

    logging.info("No path found.")
    return []

def load_grid_from_file(filename):
    """
    ファイルからグリッドを読み込む。

    引数:
    filename (str): ファイルのパス。

    戻り値:
    tuple: (grid, start, goal)
    """
    with open(filename, 'r') as file:
        lines = file.readlines()
        
        # StartとGoalの初期値を設定（従来の固定位置）
        start = (0, 0)
        goal = (len(lines) - 1, len(lines[0].strip().split()) - 1)

        grid = []
        for line in lines:
            if line.startswith("Start:"):
                start = tuple(map(int, line.strip().split(':')[1].split(',')))
            elif line.startswith("Goal:"):
                goal = tuple(map(int, line.strip().split(':')[1].split(',')))
            else:
                row = [int(cell) for cell in line.strip().split()]
                grid.append(row)

    logging.info(f"Grid loaded from {filename}:\n{grid}")
    logging.info(f"Start: {start}, Goal: {goal}")
    return grid, start, goal
