import meep as mp
from meep import mpb
import numpy as np
Si = mp.Medium(index=3.45)
ColdSi = mp.Medium(index=3.49)
SiO2 = mp.Medium(index=1.45)
Cladding = mp.Medium(index=1)
# Cladding = SiO2  # comment for air

t_si = 0.220
t_ped = 0.050
w_ped = 3
t_box = 1.2
t_top = 1.2  # air

resolution = 64  # pixels/um
sc_y = 3.5
sc_z = t_box + t_top
geometry_lattice = mp.Lattice(size=mp.Vector3(0,sc_y,sc_z))

def get_xs(wg_width=0.35, two_wg_gap=None, encapsulation=None):
    geometry = []
    # Cladding
    geometry.append(mp.Block(size=mp.Vector3(mp.inf, mp.inf, t_top),
                     center=mp.Vector3(z=t_top/2), material=Cladding))
    # BOX
    geometry.append(mp.Block(size=mp.Vector3(mp.inf, mp.inf, t_box),
                     center=mp.Vector3(z=-t_box/2), material=SiO2))
    if encapsulation is not None:
        t_ped_encap = t_ped + encapsulation
        t_rib_encap = t_si + encapsulation
        geometry.append(mp.Block(size=mp.Vector3(mp.inf, mp.inf, t_ped_encap),
                        center=mp.Vector3(z=t_ped_encap/2), material=SiO2))
        geometry.append(mp.Block(size=mp.Vector3(mp.inf, wg_width + 2*encapsulation, t_rib_encap),
                        center=mp.Vector3(z=t_rib_encap/2), material=SiO2))
    # partial
    geometry.append(mp.Block(size=mp.Vector3(mp.inf, w_ped, t_ped),
                     center=mp.Vector3(z=t_ped/2), material=ColdSi))
    # core
    if two_wg_gap is None:
        offsets = [0]
    else:
        offsets = np.array([-1, 1]) * (wg_width + two_wg_gap)/2
    for offset in offsets:
        geometry.append(mp.Block(size=mp.Vector3(mp.inf, wg_width, t_si),
                        center=mp.Vector3(y=offset, z=t_si/2), material=ColdSi))
    return geometry


def get_ms(geom = None, k_points=[0,1], num_bands=1):
    if geom is None:
        geom = get_xs()
    ms = mpb.ModeSolver(geometry_lattice=geometry_lattice,
                        geometry=geom,
                        k_points=k_points,
                        resolution=resolution,
                        num_bands=num_bands)
    return ms


def cutoff_k(freq):
    # light line in glass
    return freq * np.sqrt(SiO2.epsilon_diag[0])


def get_ks(xs=None, freq=1/1.218, num_bands=1):
    if xs is None:
        xs = get_xs()
    ms = get_ms(xs)

    band_min = 1
    band_max = num_bands
    kdir = mp.Vector3(1)
    tol = 1e-6
    kmag_guess = freq*3.45
    kmag_min = freq*0.1
    kmag_max = freq*4.0

    k_calc = ms.find_k(mp.ODD_Y,
                       freq, band_min, band_max, kdir, tol,
                       kmag_guess, kmag_min, kmag_max,)
                       # mpb.output_poynting_x)#, mpb.display_group_velocities)
    return k_calc
