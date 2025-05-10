import tkinter as tk
from tkinter import ttk
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class StatsApp(tk.Tk):
    def __init__(self):
        super().__init__()  # Initialize the Tkinter window
        self.title("Game Statistics")
        self.geometry("800x600")

        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create left navigation frame with buttons
        self.nav_frame = ttk.Frame(self.main_frame, width=200)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y)

        # Create the frame for all graphs
        self.graph_frame = ttk.Frame(self.main_frame)
        self.graph_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_nav_buttons()

        # Store canvas objects so we can manage which is displayed
        self.canvas_list = []

        # Initially show all graphs
        self.show_movement_graph()
        self.show_kdr_boxplot()
        self.show_cropbar()
        self.show_table()

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
        # Clear the previous graph
        self.clear_graph_frame()

        # Create and display the movement graph
        df = pd.read_csv("Data/bunny_positions.csv")
        heatmap_data = df.groupby(['x', 'y']).size().unstack(fill_value=0)
        fig, ax = plt.subplots(figsize=(6, 4))  # Smaller size (6x4 inches)
        sns.heatmap(heatmap_data, annot=False, cmap='YlGnBu', fmt='.0f', cbar=True, ax=ax)
        ax.set_xlabel('Map Grid (X)')
        ax.set_ylabel('Map Grid (Y)')
        ax.set_title('Player Movement Heatmap')
        self.display_plot(fig)

    def show_kdr_boxplot(self):
        import pandas as pd
        import matplotlib.pyplot as plt
        import seaborn as sns

        # Clear previous plot
        self.clear_graph_frame()

        # Load data
        df = pd.read_csv("Data/Enemy_difficulty.csv")

        df['Session'] = (df.index // 10) + 1  # 10 events per session

        # Count kills/faints per enemy per session
        grouped = df.groupby(['Session', 'Enemy Type', 'Kills/Deaths']).size().unstack(fill_value=0)

        # Make sure both columns exist
        if 'kill' not in grouped.columns:
            grouped['kill'] = 0
        if 'fainted' not in grouped.columns:
            grouped['fainted'] = 0

        # Calculate KDR per session per enemy type
        grouped['KDR'] = grouped['kill'] / grouped['fainted'].replace(0, 1)
        grouped = grouped.reset_index()

        # Plot boxplot
        fig, ax = plt.subplots(figsize=(3, 2))
        sns.boxplot(x='Enemy Type', y='KDR', data=grouped, palette='Set2', ax=ax)

        ax.set_title('Enemy Difficulty (KDR per Type)')
        ax.set_xlabel('Enemy Type')
        ax.set_ylabel('KDR Value')

        self.display_plot(fig)

    def show_cropbar(self):
        # Clear the previous graph
        self.clear_graph_frame()

        # Create and display the crop preference bar chart
        data = {
            'Session Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
            'Wheat': [10, 15, 12, 20, 25],
            'Corn': [5, 7, 9, 8, 10],
            'Carrot': [2, 3, 4, 3, 2]
        }
        df = pd.DataFrame(data)
        df.set_index('Session Week', inplace=True)
        fig, ax = plt.subplots(figsize=(4, 3))  # Smaller size (6x4 inches)
        df.plot(kind='bar', stacked=True, figsize=(4, 3), cmap='Set3', ax=ax)  # Adjusted size
        ax.set_title('Crop Type Preference (Stacked by Type)')
        ax.set_xlabel('Session Week')
        ax.set_ylabel('Crop Count (stacked by type)')
        self.display_plot(fig)

    def show_table(self):
        # Clear the previous graph
        self.clear_graph_frame()

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
        fig, ax = plt.subplots(figsize=(6, 4))  # Smaller size (6x4 inches)
        ax.axis('off')  # Hide axes
        table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center', colColours=["lightblue"]*len(df.columns))
        table.auto_set_font_size(True)
        table.set_fontsize(10)
        table.scale(1.5, 2)
        plt.title("Game Feature Analysis Table", fontsize=14)
        self.display_plot(fig)

    def clear_graph_frame(self):
        # Clear the graph frame before drawing new content
        for widget in self.graph_frame.winfo_children():
            widget.pack_forget()

    def display_plot(self, fig):
        # Create a canvas from the figure
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        
        # Get the Tkinter widget and pack it, but without expansion
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=False)  # Prevents expansion to fit window
        
        # Store canvas for future switching if needed
        self.canvas_list.append(canvas)


if __name__ == "__main__":
    app = StatsApp()
    app.mainloop()
