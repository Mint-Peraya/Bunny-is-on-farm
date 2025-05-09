# Movement graph
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def movement_graph():
    df = pd.read_csv("Data/bunny_positions.csv")

    # Count the frequency of each (x, y) pair
    heatmap_data = df.groupby(['x', 'y']).size().unstack(fill_value=0)


    # Create the heatmap from movement data
    plt.figure(figsize=(8, 6))  # Set the size of the plot
    sns.heatmap(heatmap_data, annot=False, cmap='YlGnBu', fmt='.0f', cbar=True)


    # Set labels and title
    plt.xlabel('Map Grid (X)')
    plt.ylabel('Map Grid (Y)')
    plt.title('Player Movement Heatmap')

    # Show the plot
    plt.show()

# Not fix
def table():
    # Example data for calculations

    # Player Movement - Example coordinates
    player_positions = [(10, 10), (20, 15), (30, 20), (40, 30)]  # Example (x, y) coordinates

    # Calculate average movement (distance between consecutive points)
    distances = []
    for i in range(1, len(player_positions)):
        x1, y1 = player_positions[i-1]
        x2, y2 = player_positions[i]
        distance = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
        distances.append(distance)

    average_movement = np.mean(distances)

    # Deaths vs Kills - Example kills and deaths
    kills = 50
    deaths = 25
    KDR = kills / deaths

    # Crops Harvested - Example harvest data
    harvested_crops = ['wheat', 'corn', 'wheat', 'corn', 'carrot', 'wheat']
    crop_count = {}
    for crop in harvested_crops:
        crop_count[crop] = crop_count.get(crop, 0) + 1

    # Combat Accuracy - Example combat data
    combat_data = {
        'hits': [50, 80, 75, 90, 65],
        'total_shots': [100, 100, 100, 100, 100]
    }

    accuracies = [hit / total * 100 for hit, total in zip(combat_data['hits'], combat_data['total_shots'])]
    mean_accuracy = np.mean(accuracies)
    std_accuracy = np.std(accuracies)

    # Store the data in a pandas DataFrame
    data = {
        "Feature": [
            "Player Movement", 
            "Deaths vs Kills", 
            "Crops Harvested", 
            "Combat Accuracy"
        ],
        "Statistical Value": [
            f"Average ({average_movement:.2f} pixels)", 
            f"KDR: {KDR:.2f}", 
            f"Sum: {crop_count}", 
            f"Mean: {mean_accuracy:.2f}%, SD: {std_accuracy:.2f}%"
        ]
    }

    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(data)

    # Display the DataFrame as a table in a plot
    fig, ax = plt.subplots(figsize=(10, 5))  # Set the figure size
    ax.axis('off')  # Hide axes

    # Create the table
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center', cellLoc='center', colColours=["lightblue"]*len(df.columns))

    # Customize the table (optional)
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.5, 1.5)  # Scale the table size

    # Show the plot
    plt.title("Game Feature Analysis Table", fontsize=16)
    plt.show()

def kdr_boxplot():
    # Example data: Kills and Deaths for different enemy types
    data = {
        'Enemy Type': ['Goblin', 'Goblin', 'Goblin', 'Goblin', 'Orc', 'Orc', 'Orc', 'Orc', 'Dragon', 'Dragon', 'Dragon'],
        'Kills': [10, 20, 15, 30, 25, 35, 40, 50, 100, 110, 120],
        'Deaths': [5, 7, 6, 8, 10, 12, 9, 15, 50, 55, 60]
    }

    # Create a DataFrame
    df = pd.DataFrame(data)

    # Calculate the KDR for each record (Kills / Deaths)
    df['KDR'] = df['Kills'] / df['Deaths']

    # Create the boxplot
    plt.figure(figsize=(8, 6))
    sns.boxplot(x='Enemy Type', y='KDR', data=df, palette='Set2')

    # Set the title and labels
    plt.title('Enemy Difficulty (KDR per Type)', fontsize=16)
    plt.xlabel('Enemy Type', fontsize=12)
    plt.ylabel('KDR Value', fontsize=12)

    # Show the plot
    plt.show()

def cropbar():
    # Example data: Crop types harvested in different session weeks
    data = {
        'Session Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
        'Wheat': [10, 15, 12, 20, 25],
        'Corn': [5, 7, 9, 8, 10],
        'Carrot': [2, 3, 4, 3, 2]
    }

    # Convert the data into a pandas DataFrame
    df = pd.DataFrame(data)

    # Set the Session Week as the index
    df.set_index('Session Week', inplace=True)

    # Plot the stacked bar chart
    plt.figure(figsize=(10, 6))
    df.plot(kind='bar', stacked=True, figsize=(10, 6), cmap='Set3')

    # Set labels and title
    plt.title('Crop Type Preference (Stacked by Type)', fontsize=16)
    plt.xlabel('Session Week', fontsize=12)
    plt.ylabel('Crop Count (stacked by type)', fontsize=12)

    # Show the plot
    plt.show()
