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
        self.show_maze_stats()

    def create_nav_buttons(self):
        # Add buttons for each graph/table
        self.nav_buttons = [
            ("Movement Heatmap", self.show_movement_graph),
            ("KDR Boxplot", self.show_kdr_boxplot),
            ("Crop Preference", self.show_cropbar),
            ("Statistics Table", self.show_table),
            ("Maze Performance", self.show_maze_stats)
        ]

        for text, command in self.nav_buttons:
            button = ttk.Button(self.nav_frame, text=text, command=command, width=20)
            button.pack(fill=tk.X, pady=5)

    def show_movement_graph(self):
        # Clear the previous graph
        self.clear_graph_frame()

        # Create and display the movement graph
        try:
            df = pd.read_csv("Data/bunny_positions.csv", names=['x', 'y'])
            heatmap_data = df.groupby(['x', 'y']).size().unstack(fill_value=0)
            
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.heatmap(heatmap_data, annot=False, cmap='YlGnBu', fmt='.0f', cbar=True, ax=ax)
            ax.set_xlabel('Map Grid (X)')
            ax.set_ylabel('Map Grid (Y)')
            ax.set_title('Player Movement Heatmap')
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
            fig, ax = plt.subplots(figsize=(8, 6))
            sns.boxplot(x='Enemy Type', y='KDR', data=grouped, hue='Enemy Type', palette='Set2', ax=ax)

            ax.set_title('Enemy Difficulty (KDR per Type)')
            ax.set_xlabel('Enemy Type')
            ax.set_ylabel('KDR Value')
            plt.xticks(rotation=45)
            self.display_plot(fig)
        except Exception as e:
            self.show_error_message(f"Could not load combat data: {str(e)}")

    def show_cropbar(self):
        self.clear_graph_frame()

        try:
            # Load data
            df = pd.read_csv("Data/Crop.csv", names=['Week', 'Season', 'Crop', 'Amount'])
            df["Amount"] = pd.to_numeric(df["Amount"], errors='coerce')

            # Group by Week, Season and Crop, then normalize to proportions
            grouped = df.groupby(['Week', 'Season', 'Crop'])['Amount'].sum().unstack(fill_value=0)
            proportions = grouped.div(grouped.sum(axis=1), axis=0)  # Normalize to proportions

            # Plot - larger width for clarity, short height for fit
            fig, ax = plt.subplots(figsize=(10, 6))

            # Create a stacked bar plot with season/week labels
            proportions.plot(kind='bar', stacked=True, cmap='Set3', ax=ax)

            # Customize x-axis labels to show both week and season
            labels = [f"Week {idx[0]}\n{idx[1]}" for idx in proportions.index]
            ax.set_xticks(range(len(labels)))
            ax.set_xticklabels(labels, rotation=45, ha='right')

            ax.set_title("Crop Type Preference by Week and Season")
            ax.set_xlabel("Session Week and Season")
            ax.set_ylabel("Proportion")

            # Smaller legend, place inside plot area
            ax.legend(
                title="Crop Type",
                loc='upper right',
                bbox_to_anchor=(1.3, 1),
                ncol=1,
                fontsize=8,
                title_fontsize=9
            )

            fig.tight_layout()  # fixes overlap
            self.display_plot(fig)
        except Exception as e:
            self.show_error_message(f"Could not load crop data: {str(e)}")

    def show_maze_stats(self):
        self.clear_graph_frame()

        try:
            # Load maze completion data
            df = pd.read_csv("Data/maze_log.csv")
            
            # Calculate success rate and average time
            success_rate = df['result'].value_counts(normalize=True).get('win', 0) * 100
            avg_time = df[df['result'] == 'win']['time_taken'].mean()
            
            # Create figure with two subplots
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
            
            # Success rate pie chart
            df['result'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax1)
            ax1.set_title('Maze Completion Rate')
            ax1.set_ylabel('')
            
            # Time distribution for successful attempts
            if not df[df['result'] == 'win'].empty:
                sns.histplot(df[df['result'] == 'win']['time_taken'], bins=10, ax=ax2)
                ax2.set_title('Completion Time Distribution (Successful Attempts)')
                ax2.set_xlabel('Time (seconds)')
                ax2.set_ylabel('Count')
            else:
                ax2.text(0.5, 0.5, 'No successful attempts', 
                        ha='center', va='center')
                ax2.set_title('No Data Available')
            
            fig.suptitle('Maze Performance Statistics')
            fig.tight_layout()
            self.display_plot(fig)
        except Exception as e:
            self.show_error_message(f"Could not load maze data: {str(e)}")

    def show_table(self):
        # Clear the previous graph
        self.clear_graph_frame()

        try:
            # === Player Movement ===
            player_positions = pd.read_csv("Data/bunny_positions.csv", names=['x', 'y'])
            positions = player_positions[['x', 'y']].values
            distances = [np.linalg.norm(positions[i] - positions[i - 1]) for i in range(1, len(positions))]
            average_movement = np.mean(distances)

            # === KDR (by type) ===
            enemy_df = pd.read_csv('Data/Enemy_difficulty.csv')
            kdr_grouped = enemy_df.groupby(['Enemy Type', 'Kills/Deaths']).size().unstack(fill_value=0)
            kdr_grouped['KDR'] = kdr_grouped['kill'] / kdr_grouped['fainted'].replace(0, 1)

            kdr_text = ",\n".join([f"{etype}: {row['KDR']:.2f}" for etype, row in kdr_grouped.iterrows()])

            # === Crops Harvested (by type) ===
            crop_df = pd.read_csv('Data/Crop.csv', names=['Week', 'Season', 'Crop', 'Amount'])
            crop_df["Amount"] = pd.to_numeric(crop_df["Amount"], errors='coerce')
            crop_summary = crop_df.groupby("Crop")["Amount"].sum().to_dict()
            crop_text = ",\n".join([f"{k}: {v}" for k, v in crop_summary.items()])

            # === Combat Accuracy ===
            combat_df = pd.read_csv('Data/combat_accuracy.csv', names=['Hit'])
            mean_acc = combat_df["Hit"].mean() * 100
            std_acc = combat_df["Hit"].std() * 100
            acc_text = f"Mean: {mean_acc:.2f}%, SD: {std_acc:.2f}%"

            # === Maze Performance ===
            try:
                maze_df = pd.read_csv("Data/maze_log.csv")
                maze_success = maze_df['result'].value_counts().get('win', 0)
                maze_attempts = len(maze_df)
                maze_text = f"Success: {maze_success}/{maze_attempts}"
            except:
                maze_text = "No data available"

            # === Combine into table ===
            data = {
                "Feature": [
                    "Player Movement", 
                    "Deaths vs Kills", 
                    "Crops Harvested", 
                    "Combat Accuracy",
                    "Maze Performance"
                ],
                "Statistical Value": [
                    f"Average movement: {average_movement:.2f} pixels",
                    f"KDR (by type): {kdr_text}",
                    f"Total harvested (by type): {crop_text}",
                    acc_text,
                    maze_text
                ]
            }

            df = pd.DataFrame(data)
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.axis('off')
            table = ax.table(
                cellText=df.values, 
                colLabels=df.columns, 
                loc='center', 
                cellLoc='left',
                colColours=["#f0f0f0"]*2,
                cellColours=[["#f9f9f9"]*2]*len(df)
            )
            table.auto_set_font_size(False)
            table.set_fontsize(10)
            table.scale(1.5, 2)
            plt.title("Game Feature Analysis Summary", fontsize=12, pad=20)
            self.display_plot(fig)
        except Exception as e:
            self.show_error_message(f"Could not load data for table: {str(e)}")

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