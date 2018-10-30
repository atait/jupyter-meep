import meep as mp

import numpy as np
import matplotlib.pyplot as plt
import subprocess
import shutil
from IPython import display


def show_geometry(sim):
    sim.run(until=1)
    eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
    plt.figure(dpi=100)
    plt.imshow(eps_data.transpose(), interpolation='spline36', cmap='binary')
    return eps_data