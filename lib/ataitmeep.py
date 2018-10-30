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


_field_artist = None
def liveplot(sim):
    ''' You must put ``mp.at_beginning(liveplot)`` in your arguments to run!
        Make sure to turn the progress_interval up before using this
    '''
    if sim.meep_time() == 0.:
        eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
        dielectric_artist = plt.imshow(eps_data.transpose(), interpolation='spline36', cmap='binary')
    # now do the field
    ez_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Ez)
    global _field_artist
    if sim.meep_time() == 0.:
        _field_artist = plt.imshow(ez_data.transpose(), interpolation='spline36', cmap='RdBu',
                                   alpha=0.9, vmin=-.1, vmax=.1)
    else:
        _field_artist.set_data(ez_data.transpose())
    plt.title(f't = {sim.meep_time()}')
    display.display(plt.gcf())
    display.clear_output(wait=True)