import pygame
import tkinter as tk
from tkinter import ttk
import threading
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class StatsApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Statistics")
        self.root.geometry("800x600")

        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create left navigation frame with buttons
        self.nav_frame = ttk.Frame(self.main_frame, width=200)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y)

        self.graph_frame = ttk.Frame(self.main_frame)
        self.graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_nav_buttons()

    def create_nav_buttons(self):
        # Add buttons for each graph/table
        self.nav_buttons = [
            ("Movement Heatmap", self.show_movement_graph),
            ("KDR Boxplot", self.show_kdr_boxplot),
            ("Crop Preference", self.show_cropbar),
            ("Statistics Table", self.show_table)
        ]

        for text, command in self.nav_buttons:
            button = ttk.Button(self.nav_frame, text=text, command=command)
            button.pack(fill=tk.X)

    def show_movement_graph(self):
        # Create and display the movement graph
        df = pd.read_csv("Data/bunny_positions.csv")
        heatmap_data = df.groupby(['x', 'y']).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(heatmap_data, annot=False, cmap='YlGnBu', fmt='.0f', cbar=True, ax=ax)
        ax.set_xlabel('Map Grid (X)')
        ax.set_ylabel('Map Grid (Y)')
        ax.set_title('Player Movement Heatmap')
        self.display_plot(fig)

    def show_kdr_boxplot(self):
        # Create and display the KDR boxplot
        data = {
            'Enemy Type': ['Goblin', 'Goblin', 'Goblin', 'Goblin', 'Orc', 'Orc', 'Orc', 'Orc', 'Dragon', 'Dragon', 'Dragon'],
            'Kills': [10, 20, 15, 30, 25, 35, 40, 50, 100, 110, 120],
            'Deaths': [5, 7, 6, 8, 10, 12, 9, 15, 50, 55, 60]
        }
        df = pd.DataFrame(data)
        df['KDR'] = df['Kills'] / df['Deaths']
        fig, ax = plt.subplots(figsize=(8, 6))
        
        # Fixing the deprecation warning by adding `hue` and `legend=False`
        sns.boxplot(x='Enemy Type', y='KDR', data=df, hue='Enemy Type', palette='Set2', ax=ax, legend=False)
        
        ax.set_title('Enemy Difficulty (KDR per Type)')
        ax.set_xlabel('Enemy Type')
        ax.set_ylabel('KDR Value')
        self.display_plot(fig)

    def show_cropbar(self):
        # Create and display the crop preference bar chart
        data = {
            'Session Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
            'Wheat': [10, 15, 12, 20, 25],
            'Corn': [5, 7, 9, 8, 10],
            'Carrot': [2, 3, 4, 3, 2]
        }
        df = pd.DataFrame(data)
        df.set_index('Session Week', inplace=True)
        fig, ax = plt.subplots(figsize=(10, 6))
        df.plot(kind='bar', stacked=True, figsize=(10, 6), cmap='Set3', ax=ax)
        ax.set_title('Crop Type Preference (Stacked by Type)')
        ax.set_xlabel('Session Week')
        ax.set_ylabel('Crop Count (stacked by type)')
        self.display_plot(fig)

    def show_table(self):
        # Create and display the statistics table
        player_positions = [(10, 10), (20, 15), (30, 20), (40, 30)]  # Example (x, y) coordinates
        distances = [np.sqrt((player_positions[i][0] - player_positions[i-1][0])**2 +
                             (player_positions[i][1] - player_positions[i-1][1])**2)
                     for i in range(1, len(player_positions))]
        average_movement = np.mean(distances)

        kills = 50
        deaths = 25
        KDR = kills / deaths

        harvested_crops = ['wheat', 'corn', 'wheat', 'corn', 'carrot', 'wheat']
        crop_count = {crop: harvested_crops.count(crop) for crop in set(harvested_crops)}

        combat_data = {'hits': [50, 80, 75, 90, 65], 'total_shots': [100, 100, 100, 100, 100]}
        accuracies = [hit / total * 100 for hit, total in zip(combat_data['hits'], combat_data['total_shots'])]
        mean_accuracy = np.mean(accuracies)
        std_accuracy = np.std(accuracies)

        data = {
            "Feature": ["Player Movement", "Deaths vs Kills", "Crops Harvested", "Combat Accuracy"],
            "Statistical Value": [
                f"Average ({average_movement:.2f} pixels)",
                f"KDR: {KDR:.2f}",
                f"Sum: {crop_count}",
                f"Mean: {mean_accuracy:.2f}%, SD: {std_accuracy:.2f}%"
            ]
        }

        df = pd.DataFrame(data)
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.axis('off')  # Hide axes
        table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center', colColours=["lightblue"]*len(df.columns))
        table.auto_set_font_size(False)
        table.set_fontsize(12)
        table.scale(1.5, 1.5)
        plt.title("Game Feature Analysis Table", fontsize=16)
        self.display_plot(fig)

    def clear_graph_frame(self):
        # Clear the graph frame before drawing new content
        for widget in self.graph_frame.winfo_children():
            widget.destroy()

    def display_plot(self, fig):
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


class Game:
    def __init__(self):
        self.running = True

    def run(self):
        # Game logic here
        print("Game started...")

        # Simulate the game loop
        pygame.time.delay(3000)  # Simulate 3 seconds of game time
        
        # Once game ends, open the stats app
        self.end_game()

    def end_game(self):
        # End the game and run the Tkinter StatsApp
        print("Game ended. Opening StatsApp...")
        pygame.quit()  # Quit Pygame properly

        # Open Tkinter window after closing Pygame
        self.start_stats_app()

    def start_stats_app(self):
        # Run the Tkinter app in the same thread after Pygame is closed
        root = tk.Tk()
        app = StatsApp(root)
        root.mainloop()


if __name__ == "__main__":
    game = Game()
    game.run()

import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CSVApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV Table + Graph Viewer")
        self.root.geometry("1000x600")

        # Table
        self.tree = ttk.Treeview(root)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Matplotlib figure
        self.figure = plt.Figure(figsize=(5, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.load_csv()

    def load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return

        df = pd.read_csv(filepath)

        # Clear previous table
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = list(df.columns)
        self.tree["show"] = "headings"
        for col in df.columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')

        for _, row in df.iterrows():
            self.tree.insert("", "end", values=list(row))

        # Plot: try to use first two numeric columns
        numeric_cols = df.select_dtypes(include='number').columns
        self.ax.clear()
        if len(numeric_cols) >= 2:
            self.ax.plot(df[numeric_cols[0]], df[numeric_cols[1]], marker='o')
            self.ax.set_title(f"{numeric_cols[1]} vs {numeric_cols[0]}")
            self.ax.set_xlabel(numeric_cols[0])
            self.ax.set_ylabel(numeric_cols[1])
        else:
            self.ax.text(0.5, 0.5, "Not enough numeric data to plot", ha='center', va='center')
        self.canvas.draw()
