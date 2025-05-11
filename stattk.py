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
        self.title("Bunny is on farm Statistics")
        self.geometry("1000x800")

        # Create main frame
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create left navigation frame with buttons
        self.nav_frame = ttk.Frame(self.main_frame, width=150)
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
            ("Statistics Table", self.show_table),
        ]

        for text, command in self.nav_buttons:
            button = ttk.Button(self.nav_frame, text=text, command=command, width=20)
            button.pack(fill=tk.X, pady=5)

    def show_movement_graph(self):
        # Clear the previous graph
        self.clear_graph_frame()

        # Create and display the movement graph
        try:
            # Read data
            df = pd.read_csv("Data/bunny_positions.csv")
            
            # Group by x and y coordinates to count occurrences
            heatmap_data = df.groupby(['x', 'y']).size().unstack(fill_value=0)
            
            # Create figure and axis
            fig, ax = plt.subplots(figsize=(6, 4))
            
            # Plot heatmap
            sns.heatmap(heatmap_data, annot=False, cmap='YlGnBu', fmt='.0f', cbar=True, ax=ax)
            
            # Set titles and labels
            ax.set_xlabel('Map Grid (X)', fontsize=8)
            ax.set_ylabel('Map Grid (Y)', fontsize=8)
            ax.set_title('Player Movement Heatmap every 5 seconds', fontsize=10)
            
            # Set x and y axis ticks to show only every 5th number
            x_ticks = range(0, heatmap_data.shape[1], 5)  # Adjust this based on the number of columns in the data
            y_ticks = range(0, heatmap_data.shape[0], 5)  # Adjust this based on the number of rows in the data

            ax.set_xticks(x_ticks)
            ax.set_yticks(y_ticks)

            # Rotate x-axis and y-axis labels for better readability
            plt.xticks(rotation=45, fontsize=8)  # Rotate x-axis labels
            plt.yticks(rotation=0, fontsize=8)   # Rotate y-axis labels (if needed)

            ax.set_xticklabels(x_ticks, fontsize=8)
            ax.set_yticklabels(y_ticks, fontsize=8) 
            # Increase space around the plot for better readability
            plt.tight_layout()

            # Display the plot
            self.display_plot(fig)
            
        except Exception as e:
            self.show_error_message(f"Could not load movement data: {str(e)}")

    def show_kdr_boxplot(self):
        # Clear previous plot
        self.clear_graph_frame()

        try:
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
            sns.boxplot(x='Enemy Type', y='KDR', data=grouped, hue='Enemy Type', palette='Set2', ax=ax,width=0.5)

            ax.set_title('Enemy Difficulty (KDR per Type)')
            ax.set_xlabel('Enemy Type')
            ax.set_ylabel('KDR Value')
            ax.title.set_fontsize(10)  # Set font size for the title
            ax.xaxis.label.set_fontsize(8)  # Set font size for the x-axis label
            ax.yaxis.label.set_fontsize(8)  # Set font size for the y-axis label
            plt.xticks(rotation=0, fontsize=6)  # Set font size for x-ticks
            self.display_plot(fig)
        except Exception as e:
            self.show_error_message(f"Could not load combat data: {str(e)}")

    def show_cropbar(self):
        self.clear_graph_frame()
        try:
            # Load data
            df = pd.read_csv("Data/Crop.csv")
            df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce')

            # Group by Week, Season and Crop, then normalize to proportions
            grouped = df.groupby(['Week', 'Season', 'Crop'])['Amount'].sum().unstack(fill_value=0)
            
            # Sort by Season to arrange the data in seasonal order
            grouped = grouped.sort_index(level='Season', ascending=True)

            # Normalize to proportions
            proportions = grouped.div(grouped.sum(axis=1), axis=0)

            # Plot - larger width for clarity, short height for fit
            fig, ax = plt.subplots(figsize=(6, 4))

            # Create a stacked bar plot with season/week labels
            proportions.plot(kind='bar', stacked=True, cmap='Set3', ax=ax)

            # Customize x-axis labels to show both week and season
            labels = [f"{idx[0]} {idx[1]}" for idx in proportions.index]
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=90, ha='right')

            # Set titles and labels
            ax.set_title("Crop Preference by Week and Season")
            ax.set_xlabel("Session Week and Season")
            ax.set_ylabel("Proportion")
            ax.xaxis.label.set_fontsize(6)
            ax.yaxis.label.set_fontsize(8)
            plt.xticks(rotation=90, fontsize=6)  # Rotate x-axis labels
            plt.yticks(rotation=0, fontsize=6)

            # Smaller legend, place inside plot area
            ax.legend(
                title="Crop Type",
                loc='upper right',
                bbox_to_anchor=(1.3, 1),
                ncol=1,
                fontsize=6,
                title_fontsize=7
            )

            fig.tight_layout()  # fixes overlap
            self.display_plot(fig)
        except Exception as e:
            self.show_error_message(f"Could not load crop data: {str(e)}")

    def show_table(self):
        # Clear the previous graph
        self.clear_graph_frame()

        positions = pd.read_csv("Data/bunny_positions.csv")

        # Ensure 'x' and 'y' columns are numeric
        positions['x'] = pd.to_numeric(positions['x'], errors='coerce')
        positions['y'] = pd.to_numeric(positions['y'], errors='coerce')

        # Drop rows with NaN values (in case there were any non-numeric values)
        positions = positions.dropna()

        # Get positions as a numpy array
        positions_array = positions[['x', 'y']].values

        # Calculate distances between consecutive positions
        distances = np.linalg.norm(positions_array[1:] - positions_array[:-1], axis=1)
        
        # Calculate average movement
        average_movement = np.mean(distances)

        # === KDR (by type) ===
        enemy_df = pd.read_csv('Data/Enemy_difficulty.csv')

        # Group by Enemy Type and Kills/Deaths, and count occurrences
        kdr_grouped = enemy_df.groupby(['Enemy Type', 'Kills/Deaths']).size().unstack(fill_value=0)

        # Calculate KDR
        kdr_grouped['KDR'] = kdr_grouped['kill'] / kdr_grouped['fainted'].replace(0, 1)

        # Prepare KDR text
        kdr_text = "\n".join([f"{etype}: {row['KDR']:.2f}" for etype, row in kdr_grouped.iterrows()])

        # === Crops Harvested (by type) ===
        crop_summary = pd.read_csv('Data/Crop.csv').assign(Amount=lambda x: pd.to_numeric(x["Amount"], errors='coerce')).groupby("Crop")["Amount"].sum().to_dict()
        crop_text = ",\n".join([f"{k}: {v}" for k, v in crop_summary.items()])

        # === Combat Accuracy ===
        acc_text = pd.read_csv('Data/combat_accuracy.csv')["Hit"].agg(['mean', 'std']).mul(100).round(2).pipe(lambda x: f"Mean: {x['mean']:.2f}%, SD: {x['std']:.2f}%")

        # === Data for Table ===
        data = {
                "Feature": ["Player Movement", "Deaths vs Kills", "Crops Harvested", "Combat Accuracy"],
                "Statistical Value": [
                    f"Average movement: {average_movement:.2f} pixels",
                    f"KDR: {kdr_text}",
                    f"{crop_text}",
                    acc_text
                ]
            }

        # Create table plot
        df = pd.DataFrame(data)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.axis('off')
        table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center', colColours=["#CF8080"]*2, cellColours=[["#C3E2E0"]*2]*len(df))
        table.auto_set_font_size(True)
        table.set_fontsize(6)
        table.scale(1.5, 4)

        plt.title("Game Feature Analysis Summary", fontsize=10, pad=15)
        self.display_plot(fig)

    def clear_graph_frame(self):
        # Clear the graph frame before drawing new content
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        for canvas in self.canvas_list:
            canvas.get_tk_widget().destroy()
        self.canvas_list = []

    def display_plot(self, fig):
        # Create a canvas from the figure
        canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
        canvas.draw()
        
        # Get the Tkinter widget and pack it
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        
        # Store canvas for future switching if needed
        self.canvas_list.append(canvas)

    def show_error_message(self, message):
        # Clear the frame first
        self.clear_graph_frame()
        
        # Create error label
        error_label = ttk.Label(
            self.graph_frame,
            text=message,
            foreground='red',
            font=('Arial', 12),
            wraplength=800
        )
        error_label.pack(pady=50)


if __name__ == "__main__":
    app = StatsApp()
    app.mainloop()