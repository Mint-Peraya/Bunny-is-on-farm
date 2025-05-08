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

        # Buttons
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)

        load_btn = tk.Button(btn_frame, text="Load CSV", command=self.load_csv)
        load_btn.pack()

        # Table
        self.tree = ttk.Treeview(root)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side=tk.LEFT, fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Matplotlib figure
        self.figure = plt.Figure(figsize=(5, 5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

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

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVApp(root)
    root.mainloop()
