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
        self.main_frame.pack(fill=tk.BOTH, expand=False)
        
        # Create left navigation frame with buttons
        self.nav_frame = ttk.Frame(self.main_frame, width=100)
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
        fig, ax = plt.subplots(figsize=(2, 2))
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
        fig, ax = plt.subplots(figsize=(2, 2))
        sns.boxplot(x='Enemy Type', y='KDR', data=grouped, hue='Enemy Type', palette='Set2', ax=ax)

        ax.set_title('Enemy Difficulty (KDR per Type)')
        ax.set_xlabel('Enemy Type')
        ax.set_ylabel('KDR Value')

        self.display_plot(fig)

    def show_cropbar(self):
        self.clear_graph_frame()

        # Load data
        df = pd.read_csv("Data/Crop.csv")
        df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce')

        # Group by Week and Crop, then normalize to proportions
        grouped = df.groupby(['Week', 'Crop'])['Amount'].sum().unstack(fill_value=0)
        proportions = grouped.div(grouped.sum(axis=1), axis=0)  # Normalize to proportions

        # Plot - larger width for clarity, short height for fit
        fig, ax = plt.subplots(figsize=(5, 3))  # balanced for 800x600

        proportions.plot(kind='bar', stacked=True, cmap='Set3', ax=ax)

        ax.set_title("Crop Type Preference")
        ax.set_xlabel("Session Week")
        ax.set_ylabel("Proportion")

        # Smaller legend, place inside plot area
        ax.legend(
            title="Crop Type",
            loc='upper center',
            bbox_to_anchor=(0, -0.1),
            ncol=2,
            fontsize=8,
            title_fontsize=9
        )

        fig.tight_layout()  # fixes overlap
        self.display_plot(fig)


    def show_table(self):
        # Clear the previous graph
        self.clear_graph_frame()

        # === Player Movement ===
        player_positions = pd.read_csv("Data/bunny_positions.csv")
        positions = player_positions[['x', 'y']].values
        distances = [np.linalg.norm(positions[i] - positions[i - 1]) for i in range(1, len(positions))]
        average_movement = np.mean(distances)

        # === KDR (by type) ===
        enemy_df = pd.read_csv('Data/Enemy_difficulty.csv')
        kdr_grouped = enemy_df.groupby(['Enemy Type', 'Kills/Deaths']).size().unstack(fill_value=0)
        kdr_grouped['KDR'] = kdr_grouped['kill'] / kdr_grouped['fainted'].replace(0, 1)

        kdr_text = ",\n".join([f"{etype}: {row['KDR']:.2f}" for etype, row in kdr_grouped.iterrows()])

        # === Crops Harvested (by type) ===
        crop_df = pd.read_csv('Data/Crop.csv')
        crop_df["Amount"] = pd.to_numeric(crop_df["Amount"], errors='coerce')
        crop_summary = crop_df.groupby("Crop")["Amount"].sum().to_dict()
        crop_text = ",\n".join([f"{k}: {v}" for k, v in crop_summary.items()])

        # === Combat Accuracy ===
        combat_df = pd.read_csv('Data/combat_accuracy.csv')
        mean_acc = combat_df["Hit"].mean() * 100
        std_acc = combat_df["Hit"].std() * 100
        acc_text = f"Mean: {mean_acc:.2f}%, SD: {std_acc:.2f}%"

        # === Combine into table ===
        data = {
            "Feature": ["Player Movement", "Deaths vs Kills", "Crops Harvested", "Combat Accuracy"],
            "Statistical Value": [
                f"Average ({average_movement:.2f} pixels)",
                f"KDR (by type): {kdr_text}",
                f"Sum (by type): {crop_text}",
                acc_text
            ]
        }

        df = pd.DataFrame(data)
        fig, ax = plt.subplots(figsize=(2, 2))
        ax.axis('off')
        table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center', colColours=["lightblue"]*2)
        table.auto_set_font_size(True)
        table.set_fontsize(10)
        table.scale(1.5, 2)
        plt.title("Game Feature Analysis Table", fontsize=12)
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
        canvas_widget.pack(fill=tk.BOTH, expand=True)  # Prevents expansion to fit window
        
        # Store canvas for future switching if needed
        self.canvas_list.append(canvas)


if __name__ == "__main__":
    app = StatsApp()
    app.mainloop()
