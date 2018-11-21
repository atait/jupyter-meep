import meep as mp

import numpy as np
import matplotlib.pyplot as plt
import subprocess
import shutil
from IPython import display
import meep as mp
from meep import mpb

class objview(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def show_geometry(sim_or_solver):
    if isinstance(sim_or_solver, mp.Simulation):
        sim = sim_or_solver
        sim.run(until=.0)
        eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
    elif isinstance(sim_or_solver, mpb.ModeSolver):
        ms = sim_or_solver
        md = mpb.MPBData(rectify=True, periods=3, resolution=32)
        eps = ms.get_epsilon()
        eps_data = md.convert(eps)  # make aspect ratios right
    plt.figure(dpi=100)
    plt.imshow(eps_data.transpose()[::-1], interpolation='spline36', cmap='binary')
    return eps_data

def show_mode(solver):
    pass


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

