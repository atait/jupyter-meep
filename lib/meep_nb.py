import meep as mp

import numpy as np
import matplotlib.pyplot as plt
import subprocess
import shutil
import os
from IPython import display
import meep as mp
from meep import mpb, materials

silicon = mp.Medium(epsilon=12)
oxide = mp.Medium(epsilon=2.25)
# silicon = materials.cSi
# oxide = materials.SiO2


class objview(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def update(self, *dicts, **kwargs):
        for di in dicts:
            self.__dict__.update(di)
        self.__dict__.update(kwargs)

    def copy(self):
        new_obj = objview(**self.__dict__)
        return new_obj


def show_geometry(sim_or_solver, **mpb_kwargs):
    if isinstance(sim_or_solver, mpb.ModeSolver):
        # hope it works
        return show_geometry_2d(sim_or_solver, **mpb_kwargs)
    if not isinstance(sim_or_solver, mp.Simulation):
        raise TypeError('{} not supported'.format(type(sim_or_solver)))
    if sim_or_solver.dimensions == 1 or sim_or_solver.cell_size.y == 0 and sim_or_solver.cell_size.z == 0:
        return show_geometry_1d(sim_or_solver)


def show_geometry_1d(sim):
    # raise NotImplementedError('1D Not supported yet')
    sim.run(until=0.1)
    eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
    plt.figure(dpi=100)
    plt.plot(eps_data)
    return eps_data


def show_geometry_2d(sim_or_solver, **mpb_kwargs):
    if isinstance(sim_or_solver, mp.Simulation):
        sim = sim_or_solver
        sim.run(until=.0)
        eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
        if len(eps_data.shape) == 3:
            eps_data = eps_data[:, :, int(eps_data.shape[2] / 2)]
            # eps_data = eps_data[:, int(eps_data.shape[1] / 2), :]  # for x-z plane
    elif isinstance(sim_or_solver, mpb.ModeSolver):
        ms = sim_or_solver
        if not any(p in mpb_kwargs.keys() for p in ['periods', 'x', 'y', 'z']):
            mpb_kwargs['periods'] = 3
        md = mpb.MPBData(rectify=True, resolution=32, **mpb_kwargs)
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
        if len(eps_data.shape) == 3:
            eps_data = eps_data[:, :, int(eps_data.shape[2] / 2)]
        dielectric_artist = plt.imshow(eps_data.transpose()[::-1], interpolation='spline36', cmap='binary')
    # now do the field
    field_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=component)
    if len(field_data.shape) == 3:
            field_data = field_data[:, :, int(field_data.shape[2] / 2)]
    global _field_artist
    if sim.meep_time() == 0.:
        _field_artist = plt.imshow(field_data.transpose()[::-1], interpolation='spline36', cmap='RdBu',
                                   alpha=0.9, vmin=-.1, vmax=.1)
        return
    else:
        _field_artist.set_data(field_data.transpose())
    plt.title(f't = {sim.meep_time()}')
    display.display(plt.gcf())
    display.clear_output(wait=True)


def to_gif(output_dir, field_type='ez'):
    # Converts pngs from your simulation into a nice gif
    # You must have imagemagik in order to use convert
    gif_name = field_type + '.gif'
    simdata_glob = os.path.join(output_dir, field_type + '-*.png')
    subprocess.check_call(['convert', simdata_glob, gif_name])
    try:
        subprocess.check_call(['open', '-a', 'Safari', gif_name])  # open it if you have Safari
    except:
        pass
    return gif_name
