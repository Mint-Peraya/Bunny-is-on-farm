
# store data

class Config:
    __ALL_CONFIGS = {
        'window': (800,600),
        'wx' : 800,
        'wy' : 600,
        'grid': 10,
        'bun_size': 64,
        'black': (0,0,0),
        'white': (255,255,255),
        'red': (255,0,0),
        'green': (0,255,0),
        'peach': (255,200,200),
        'sky': (200,255,255),
        'purple':(200,0,210),
        'maze': 50*64,
        # Maze size (50*50 grid)
        'grid': 50
    }

    @classmethod
    def get(cls,key):
        return cls.__ALL_CONFIGS[key]


# Use pygame.mixer.init() to initialize the mixer.

# Use pygame.mixer.music.load("file") to load music into the mixer.

# Use pygame.mixer.music.play(loops, start) to play the music loaded into the mixer.