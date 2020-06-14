import meep as mp

import numpy as np
import matplotlib.pyplot as plt
import subprocess
import inspect
import shutil
import os
from functools import wraps
from IPython import display
from IPython.utils.capture import capture_output
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
    with capture_output():
        sim.run(until=0.1)
    eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
    plt.figure(dpi=100)
    plt.plot(eps_data)
    return eps_data


def show_geometry_2d(sim_or_solver, **mpb_kwargs):
    if isinstance(sim_or_solver, mp.Simulation):
        print('Deprecation: use sim.plot2D for mp.Simulation objects')
        sim = sim_or_solver
        sim.plot2D()
        # if not sim._is_initialized:
        #     sim.init_sim()
        # # sim.run(until=.0)
        # eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
        # if len(eps_data.shape) == 3:
        #     eps_data = eps_data[:, :, int(eps_data.shape[2] / 2)]
        #     # eps_data = eps_data[:, int(eps_data.shape[1] / 2), :]  # for x-z plane
    elif isinstance(sim_or_solver, mpb.ModeSolver):
        ms = sim_or_solver
        if not any(p in mpb_kwargs.keys() for p in ['periods', 'x', 'y', 'z']):
            mpb_kwargs['periods'] = 3
        md = mpb.MPBData(rectify=True, resolution=ms.resolution[1], **mpb_kwargs)
        eps = ms.get_epsilon()
        # eps_data = md.convert(eps)  # make aspect ratios right
        eps_data = eps
    # plt.figure(dpi=100)
    # plt.imshow(eps_data.transpose()[::-1], interpolation='spline36', cmap='binary')
    # return eps_data


def show_mode(solver):
    pass


_field_artist = None
def liveplot(sim, component=mp.Ez, vmax=0.1):
    ''' You must put ``mp.at_beginning(liveplot)`` in your arguments to run!
        Make sure to turn the progress_interval up before using this
    '''
    global _field_artist
    field_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=component)
    if sim.meep_time() == 0.:
        ax = sim.plot2D()
        extent = ax.get_images()[0].get_extent()
        _field_artist = plt.imshow(field_data.transpose()[::-1], interpolation='spline36', cmap='RdBu',
                                   alpha=0.8, vmin=-vmax, vmax=vmax, extent=extent)
    else:
        _field_artist.set_data(field_data.transpose())

    plt.title(f't = {sim.meep_time()}')
    display.clear_output(wait=True)
    display.display(plt.gcf())


_eline = None
def liveplot_1D(sim, component=mp.Ey):
    global _eline
    xspan = sim.cell_size.x/2 * np.linspace(-1, 1, int(sim.cell_size.x * sim.resolution))
    comp_name = 'Ey' if component == mp.Ey else 'Ez' if component == mp.Ez else 'Ex'
    if sim.meep_time() == 0.:
        eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
        # if eps_data.ndim > 1:
        #     eps_data = eps_data[:, :, int(eps_data.shape[2] / 2)]
        # todo dielectric artist

        _eline, = plt.gca().plot(xspan, np.zeros_like(xspan), 'r', label=comp_name)
        return
    # now do the field
    e_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=component)
    _eline.set_data(xspan, e_data)
    plt.title(f't = {sim.meep_time()}')
    plt.legend()
    display.clear_output(wait=True)
    display.display(plt.gcf())


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
