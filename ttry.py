import tkinter as tk
import pygame
import threading

# Function to run Pygame
def run_pygame():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption('Pygame Window')

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Fill the screen with a color (just as an example)
        screen.fill((0, 0, 255))
        pygame.display.flip()

    pygame.quit()

# Function to run Tkinter UI and periodically call Pygame's loop
def run_tkinter():
    root = tk.Tk()
    root.title("Tkinter Window")

    label = tk.Label(root, text="Tkinter Window")
    label.pack()

    quit_button = tk.Button(root, text="Quit", command=root.quit)
    quit_button.pack()

    # Set up a periodic call to the Pygame loop
    def update_pygame():
        # Call the Pygame loop to continue running
        run_pygame()
        root.after(100, update_pygame)  # Call update_pygame every 100ms

    update_pygame()  # Start the Pygame loop

    root.mainloop()

# Start Tkinter in the main thread
run_tkinter()
