from ataitmeep import objview, silicon, oxide, liveplot
import meep as mp
import time

# geo is the parameters, while geometry is the MEEP geometry list
default_geo = objview(
                        sm_width = 0.35,  # um
                        pitch = .21,
                        duty = .5,
                        dw = .25,
                        n_periods = 50,
                        buffer = 4,  # um
                        cavity = 1.25,  # ratio of pitch, such as 0.25
                        thickness = 0.,  # change to 0 for 2D
                       )


def set_sim1():
    # level 1 is very rough used for locating wavelength resonance
    global default_geo, resolution
    default_geo.update(n_periods=10, buffer=2, dw=.3)
    resolution = 20


def set_sim2():
    # level 2 is used for getting decent resonance shapes
    global default_geo, resolution
    default_geo.update(buffer=4)
    resolution = 30


def set_sim3():
    # level 2 is used for getting loss profile
    global default_geo, resolution
    default_geo.update(buffer=14)
    resolution = 40


# 3D
if False:
    default_geo.update(pitch = .264, thickness=0.22)


def kwargs_to_geo(geo=None, **kwargs):
    if geo is None:
        geo = default_geo
    this_geo = geo.copy()
    this_geo.update(**kwargs)
    return this_geo


fcen = 1 / 1.22
df = fcen / 5
nfreq = 1001
def bragg_source(geo=None, **kwargs):
    geo = kwargs_to_geo(geo, **kwargs)
    # sources = []
    # sources = [mp.Source(mp.GaussianSource(fcen, fwidth=df),
    #                  component=mp.Ey,
    #                  center=mp.Vector3(-monitor_x(geo)-.5, 0),
    #                  size=mp.Vector3(0, geo.sm_width, geo.thickness))]
    sources = [mp.EigenModeSource(mp.GaussianSource(fcen, fwidth=df),
                                  eig_band=2,
                                  direction=mp.X,
                                  # eig_parity=mp.ODD_Y,
                                  component=mp.Ey,
                                  center=mp.Vector3(-monitor_x(geo)-.5, 0),
                                  size=mp.Vector3(0, bragg_cell(geo).y, bragg_cell(geo).z))]
    return sources


dpml = 1.
pml_layers = [mp.PML(dpml)]
resolution = 30
# this should be replaced by an eigenmode
def sim_kwargs(geo=None, **kwargs):
    geo = kwargs_to_geo(geo, **kwargs)
    symms = [mp.Mirror(mp.Y, phase=-1)]
    if geo.thickness != 0:
        symms.append(mp.Mirror(mp.Z, phase=1))
    return dict(
                  cell_size=bragg_cell(geo),
                  geometry=bragg_geometry(geo),
                  sources=bragg_source(geo),
                  boundary_layers=pml_layers,
                  resolution=resolution,
                  default_material=oxide,
                  symmetries=symms,
                  # progress_interval=1e6,
                  )


def cell_x(geo=None, **kwargs):
    geo = kwargs_to_geo(geo, **kwargs)
    return geo.pitch * geo.n_periods + geo.cavity * geo.pitch + 2 * geo.buffer


def bragg_cell(geo=None, **kwargs):
    geo = kwargs_to_geo(geo, **kwargs)
    cell_y = 3
    cell_z = 0 if geo.thickness == 0 else geo.thickness + 3
    cell = mp.Vector3(cell_x(geo), cell_y, cell_z)
    return cell


def bragg_geometry(geo=None, **kwargs):
    geo = kwargs_to_geo(geo, **kwargs)
    cellx = cell_x(geo)

    geometry = []
    for side_sign in [-1, 1]:
        geometry.append(mp.Block(mp.Vector3(geo.buffer, geo.sm_width, geo.thickness),
                                 center=mp.Vector3((cellx - geo.buffer) * side_sign/2),
                                 material=silicon))
    # the teeth of the grating
    x0 = geo.buffer - cellx/2
    for iPeriod in range(geo.n_periods):
        if iPeriod == int(geo.n_periods / 2):
            tooth_len = geo.cavity * geo.pitch
            wg_wid = geo.sm_width + geo.dw / 2
            geometry.append(mp.Block(mp.Vector3(tooth_len, wg_wid, geo.thickness),
                                     center=mp.Vector3(x0 + tooth_len/2),
                                     material=silicon))
            x0 += tooth_len
        for iTooth in range(2):
            tooth_len = geo.pitch * (geo.duty if iTooth == 0 else (1 - geo.duty))
            wg_wid = geo.sm_width + geo.dw / 2 * (1 if iTooth == 0 else -1)
            geometry.append(mp.Block(mp.Vector3(tooth_len, wg_wid, geo.thickness),
                                     center=mp.Vector3(x0 + tooth_len/2),
                                     material=silicon))
            x0 += tooth_len
    return geometry


def monitor_x(geo=None, **kwargs):
    geo = kwargs_to_geo(geo, **kwargs)
    return cell_x(geo) / 2 - dpml - .5


def add_monitors(simulation, geo=None, **kwargs):
    geo = kwargs_to_geo(geo, **kwargs)

    # reflected flux
    refl_fr = mp.FluxRegion(center=mp.Vector3(-monitor_x(geo) ,0, 0),
                            size=mp.Vector3(0, 2*geo.sm_width, 2*geo.thickness))
    refl = simulation.add_flux(fcen, df, nfreq, refl_fr)

    # transmitted flux
    tran_fr = mp.FluxRegion(center=mp.Vector3(monitor_x(geo) ,0, 0),
                            size=mp.Vector3(0, 2*geo.sm_width, 2*geo.thickness))
    tran = simulation.add_flux(fcen, df, nfreq, tran_fr)

    return refl, tran


def livefield(sim):
    liveplot(sim, mp.Ey)


def monitor_until(geo=None, until=None, **kwargs):
    geo = kwargs_to_geo(geo, **kwargs)
    stop_kwarg = dict()
    if until is None:
        monitor_point = mp.Vector3(monitor_x(geo), 0, 0)
        stop_kwarg['until_after_sources'] = mp.stop_when_fields_decayed(20, mp.Ey, monitor_point, 1e-3)
    else:
        stop_kwarg['until'] = until
    return stop_kwarg


def do_simrun(base_refl_data=None, do_live=True, geo=None, **kwargs):
    sim = mp.Simulation(
                        progress_interval=1e6 if do_live else 4,
                        **sim_kwargs(geo=geo, **kwargs))
    sim.reset_meep()

    # Now put in some flux monitors. Make sure the pulse source was selected
    refl, tran = add_monitors(sim)

    # for normal run, load negated fields to subtract incident from refl. fields
    if base_refl_data is not None:
        sim.load_minus_flux_data(refl, base_refl_data)

    run_args = (mp.at_beginning(livefield), mp.at_every(5, livefield), ) if do_live else tuple()
    t0 = time.time()
    sim.run(*run_args,
            **monitor_until(geo=geo, **kwargs))
    print('Realtime duration = {:.2f} seconds'.format(time.time() - t0))
    return sim, refl, tran
