import sys
import logging
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLineEdit, QLabel, QTableWidget,
                               QTableWidgetItem, QMessageBox, QFileDialog, QSpinBox, QScrollArea,
                               QAbstractScrollArea)
from PySide6.QtCore import Qt
from core import a_star, load_grid_from_file

# ロギングの設定
logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 定数の定義
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 600

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("経路探索ツール")
        self.setGeometry(50, 50, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.grid_size = 5  # 例えば、グリッドサイズを5x5に設定

        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.start = (0, 0)
        self.goal = (4, 4)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.grid_layout = QHBoxLayout()
        self.grid_layout.setAlignment(Qt.AlignCenter)  # テーブルを中央に配置
        self.layout.addLayout(self.grid_layout)

        # self.scroll_area = QScrollArea()
        self.table = QTableWidget(self.grid_size, self.grid_size)
        # self.scroll_area.setWidget(self.table)
        # self.scroll_area.setWidgetResizable(True)
        self.grid_layout.addWidget(self.table)

        self.table.cellClicked.connect(self.cell_clicked)

        self.control_layout = QVBoxLayout()
        self.grid_layout.addLayout(self.control_layout)

        self.start_label = QLabel("スタート (行,列):")
        self.control_layout.addWidget(self.start_label)

        self.start_input = QLineEdit("0,0")
        self.control_layout.addWidget(self.start_input)
        self.start_input.textChanged.connect(self.update_start_goal_display)

        self.goal_label = QLabel("ゴール (行,列):")
        self.control_layout.addWidget(self.goal_label)

        self.goal_input = QLineEdit("4,4")
        self.control_layout.addWidget(self.goal_input)
        self.goal_input.textChanged.connect(self.update_start_goal_display)

        self.find_path_button = QPushButton("経路を見つける")
        self.find_path_button.clicked.connect(self.find_path)
        self.control_layout.addWidget(self.find_path_button)

        self.reset_button = QPushButton("初期化")
        self.reset_button.clicked.connect(self.reset_grid)
        self.control_layout.addWidget(self.reset_button)

        self.load_button = QPushButton("ファイルから読み込む")
        self.load_button.clicked.connect(self.load_grid_from_file)
        self.control_layout.addWidget(self.load_button)

        self.grid_size_label = QLabel("グリッドサイズ:")
        self.control_layout.addWidget(self.grid_size_label)

        self.grid_size_spinbox = QSpinBox()
        self.grid_size_spinbox.setRange(5, 50)
        self.grid_size_spinbox.setValue(self.grid_size)
        self.grid_size_spinbox.valueChanged.connect(self.change_grid_size)
        self.control_layout.addWidget(self.grid_size_spinbox)

        # 操作説明を追加
        self.instructions = QLabel(
            "操作説明:\n"
            "- グリッドのセルをクリックして障害物を設定できます（黒色）。\n"
            "- 再度クリックすると障害物を消去できます。\n"
            "- スタート地点とゴール地点を入力し、'経路を見つける'ボタンをクリックしてください。\n"
            "- 緑色で表示されるのが最短経路です。\n"
            "- '初期化'ボタンをクリックすると、グリッドがリセットされます。\n"
            "- 'ファイルから読み込む'ボタンをクリックして、グリッドをファイルから読み込みます。\n"
            "- 'グリッドサイズ'スピンボックスでグリッドサイズを変更できます。\n"
        )
        self.layout.addWidget(self.instructions)

        self.update_table()

    def update_table(self):
        """
        Updates the table to match the current grid size.
        """
        table_width = self.central_widget.width()
        table_height = self.central_widget.height() - self.control_layout.sizeHint().height()
        optimal_cell_size = min(table_width // self.grid_size, table_height // self.grid_size)

        self.table.setRowCount(self.grid_size)
        self.table.setColumnCount(self.grid_size)

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                item = self.table.item(row, col)
                if item is None:
                    item = QTableWidgetItem("")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row, col, item)
                self.update_cell_display(row, col)  # セルの表示を更新

        self.table.verticalHeader().setDefaultSectionSize(optimal_cell_size)
        self.table.horizontalHeader().setDefaultSectionSize(optimal_cell_size)

    def update_cell_display(self, row, col):
        """
        Updates the display of a cell in the grid based on its state.

        Args:
            row (int): The row index of the cell.
            col (int): The column index of the cell.
        """
        item = self.table.item(row, col)
        if item is None:
            item = QTableWidgetItem("")
            item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, col, item)

        if self.grid[row][col] == 1:
            item.setBackground(Qt.black)
            item.setText("#")
        elif (row, col) == self.start:
            item.setBackground(Qt.blue)
            item.setText("S")
        elif (row, col) == self.goal:
            item.setBackground(Qt.red)
            item.setText("G")
        else:
            item.setBackground(Qt.white)
            item.setText("")


    def cell_clicked(self, row, col):
        if (row, col) == self.start or (row, col) == self.goal:
            return
        
        self.grid[row][col] = 1 - self.grid[row][col]
        self.update_cell_display(row, col)
        logging.info(f"Cell ({row}, {col}) clicked. State changed to: {self.grid[row][col]}")

    def find_path(self):
        try:
            self.start = tuple(map(int, self.start_input.text().split(',')))
            self.goal = tuple(map(int, self.goal_input.text().split(',')))
            logging.info(f"Finding path from {self.start} to {self.goal}")

            path = a_star(self.grid, self.start, self.goal)

            if not path:
                logging.info("No path found.")
                QMessageBox.information(self, "結果", "経路が見つかりませんでした。")
                return

            for row in range(self.grid_size):
                for col in range(self.grid_size):
                    item = self.table.item(row, col)
                    if (row, col) in path:
                        if (row, col) == self.start:
                            item.setBackground(Qt.blue)
                            item.setText("S")
                        elif (row, col) == self.goal:
                            item.setBackground(Qt.red)
                            item.setText("G")
                        else:
                            item.setBackground(Qt.green)
                            item.setText("")
                    else:
                        self.update_cell_display(row, col)

            logging.info(f"Path found: {path}")
            QMessageBox.information(self, "結果", "経路が見つかりました。")
        except Exception as e:
            logging.error(f"Error finding path: {str(e)}")
            QMessageBox.warning(self, "エラー", str(e))

    def reset_grid(self):
        """
        Resets the grid to its initial state.
        """
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.start = (0, 0)
        self.goal = (self.grid_size - 1, self.grid_size - 1)
        self.start_input.setText(f"{self.start[0]},{self.start[1]}")  # 既に存在するコード
        self.goal_input.setText(f"{self.goal[0]},{self.goal[1]}")  # goalのテキストボックスを更新
        self.update_table()
        logging.info("Grid reset to initial state.")

    def update_start_goal_display(self):
        """
        Updates the display of the start and goal cells based on input values.
        """
        try:
            self.start = tuple(map(int, self.start_input.text().split(',')))
            self.goal = tuple(map(int, self.goal_input.text().split(',')))
            self.update_table()  # テーブル全体を更新
            logging.info(f"Start and goal updated to: {self.start}, {self.goal}")
        except ValueError:
            logging.warning("Invalid input for start or goal.")

    def load_grid_from_file(self):
        """
        Opens a file dialog to load a grid from a file.
        CAUTION: This method loads the grid twice as a temporary workaround to ensure that obstacles are correctly displayed.
        This should be fixed in the future to correctly update the table in a single load.
        """
        filename, _ = QFileDialog.getOpenFileName(self, "ファイルを開く", "", "Text Files (*.txt);;All Files (*)")
        if filename:
            try:
                # Load the grid for the first time
                self.grid, self.start, self.goal = load_grid_from_file(filename)
                self.grid_size = len(self.grid)
                self.start_input.setText(f"{self.start[0]},{self.start[1]}")
                self.goal_input.setText(f"{self.goal[0]},{self.goal[1]}")
                self.grid_size_spinbox.setValue(self.grid_size)
                self.update_table()  # First update to the table

                # Load the grid for the second time (workaround for proper display)
                self.grid, self.start, self.goal = load_grid_from_file(filename)
                self.update_table()  # Second update to the table

                logging.info(f"Grid loaded from file: {filename}")
            except Exception as e:
                logging.error(f"Error loading grid from file: {str(e)}")
                QMessageBox.warning(self, "エラー", f"ファイルの読み込み中にエラーが発生しました: {str(e)}")

    def change_grid_size(self):
        """
        Changes the grid size based on the spinbox value.
        """
        self.grid_size = self.grid_size_spinbox.value()
        self.grid = [[0 for _ in range(self.grid_size)] for _ in range(self.grid_size)]
        self.start = (0, 0)
        self.goal = (self.grid_size - 1, self.grid_size - 1)
        self.update_table()
        logging.info(f"Grid size changed to: {self.grid_size}")

    def resizeEvent(self, event):
        """
        Ensures the table cells remain square when the window is resized.
        """
        super().resizeEvent(event)
        table_width = self.central_widget.width()
        table_height = self.central_widget.height() - self.control_layout.sizeHint().height()
        optimal_cell_size = min(table_width // self.grid_size, table_height // self.grid_size)
        self.table.verticalHeader().setDefaultSectionSize(optimal_cell_size)
        self.table.horizontalHeader().setDefaultSectionSize(optimal_cell_size)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
