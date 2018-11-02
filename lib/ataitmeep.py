import meep as mp

import numpy as np
import matplotlib.pyplot as plt
import subprocess
import shutil
from IPython import display


class objview(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def show_geometry(sim):
    sim.run(until=.0)
    eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
    plt.figure(dpi=100)
    plt.imshow(eps_data.transpose()[::-1], interpolation='spline36', cmap='binary')
    return eps_data


_field_artist = None
def liveplot(sim, component=mp.Ez):
    ''' You must put ``mp.at_beginning(liveplot)`` in your arguments to run!
        Make sure to turn the progress_interval up before using this
    '''
    # component=mp.Ey
    if sim.meep_time() == 0.:
        eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
        dielectric_artist = plt.imshow(eps_data.transpose()[::-1], interpolation='spline36', cmap='binary')
    # now do the field
    field_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=component)
    global _field_artist
    if sim.meep_time() == 0.:
        _field_artist = plt.imshow(field_data.transpose()[::-1], interpolation='spline36', cmap='RdBu',
                                   alpha=0.9, vmin=-.02, vmax=.02)
        return
    else:
        _field_artist.set_data(field_data.transpose())
    plt.title(f't = {sim.meep_time()}')
    display.display(plt.gcf())
    display.clear_output(wait=True)

