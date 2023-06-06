import random
import pandas as pd
import matplotlib.pyplot as plt
from itertools import count
from matplotlib.animation import FuncAnimation

def animate(i):
    data = pd.read_csv('speed_profile.csv')

    x = data['Time']
    y1 = data['Forward Speed']
    y2 = data['powering']

    plt.cla()
    
    plt.plot(x, y2,"m-", label='powering')
    plt.plot(x, y1, label='Forward Speed')

    plt.xlabel('Time')
    plt.ylabel('Speed')

    plt.legend(loc='upper left')
    plt.tight_layout()

ani = FuncAnimation(plt.gcf(), animate, interval=1000)

plt.show()
