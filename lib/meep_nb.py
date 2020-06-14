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

# decorator
def display_nb(func):
    # MEEP will introspect this signature for an argument, so we have to outrospect the wrapper
    spec = inspect.getfullargspec(func).args
    npositional = len(spec)
    if spec[0] == 'self':
        npositional -= 1
    @wraps(func)
    def wrap0arg(*args, **kwargs):
        retval = func(*args, **kwargs)
        display.clear_output(wait=True)
        display.display(plt.gcf())
        return retval
    @wraps(func)
    def wrap1arg(a, *args, **kwargs):
        retval = func(a, *args, **kwargs)
        display.clear_output(wait=True)
        display.display(plt.gcf())
        return retval
    @wraps(func)
    def wrap2arg(a, b, *args, **kwargs):
        retval = func(a, b, *args, **kwargs)
        display.clear_output(wait=True)
        display.display(plt.gcf())
        return retval
    @wraps(func)
    def wrap3arg(a, b, c, *args, **kwargs):
        retval = func(a, b, c, *args, **kwargs)
        display.clear_output(wait=True)
        display.display(plt.gcf())
        return retval

    if npositional == 0:
        return wrap0arg
    elif npositional == 1:
        return wrap1arg
    elif npositional == 2:
        return wrap2arg
    elif npositional == 3:
        return wrap3arg
    else:
        print(inspect.getfullargspec(func).args)
        raise ValueError('Too many arguments')


class Animate2D(mp.Animate2D):
    ''' Adjust the behavior of realtime and call signatures

        This is very, very slow to plot, so beware in the inner loop.
        It is still ok for coarse preview, and especially good for outputting videos
        Take note of to_mp4 and to_gif

        Note that sim can be None in the initializer; however,
        this means you can't save video or gifs
    '''
    def __init__(self,sim,fields,f=None,realtime=False,normalize=False,
                 plot_modifiers=None,**customization_args):
        super().__init__(sim,fields,f,False,normalize,  # their realtime to False
                         plot_modifiers,**customization_args)
        self._notebook_realtime = realtime

    def __call__(self,sim,todo='step'):
        super().__call__(sim, todo)
        if self._notebook_realtime:
            if self.f is None:
                self.f = plt.gcf()
            display.clear_output(wait=True)
            display.display(self.f)


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
        sim = sim_or_solver
        if not sim._is_initialized:
            sim.init_sim()
        # sim.run(until=.0)
        eps_data = sim.get_array(center=mp.Vector3(), size=sim.cell_size, component=mp.Dielectric)
        if len(eps_data.shape) == 3:
            eps_data = eps_data[:, :, int(eps_data.shape[2] / 2)]
            # eps_data = eps_data[:, int(eps_data.shape[1] / 2), :]  # for x-z plane
    elif isinstance(sim_or_solver, mpb.ModeSolver):
        ms = sim_or_solver
        if not any(p in mpb_kwargs.keys() for p in ['periods', 'x', 'y', 'z']):
            mpb_kwargs['periods'] = 3
        md = mpb.MPBData(rectify=True, resolution=ms.resolution[1], **mpb_kwargs)
        eps = ms.get_epsilon()
        # eps_data = md.convert(eps)  # make aspect ratios right
        eps_data = eps
    plt.figure(dpi=100)
    plt.imshow(eps_data.transpose()[::-1], interpolation='spline36', cmap='binary')
    return eps_data


def show_mode(solver):
    pass


_field_artist = None
# @display_nb
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


_field_axis = None
def liveplot_slow(sim, component=mp.Ez):
    ''' this uses the builtin functions in MEEP.
        It gets very slow after showing 5 frames
        Example: 59s vs. 12s for 40 frames
    '''
    global _field_axis, _field_artist
    if sim.meep_time() == 0.:
        _field_axis = sim.plot2D(fields=component)
    else:
        mp.plot_fields(sim, ax=_field_axis, fields=component)
    plt.title(f't = {sim.meep_time()}')
    display.clear_output(wait=True)
    display.display(plt.gcf())


_eline = None
@display_nb
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
