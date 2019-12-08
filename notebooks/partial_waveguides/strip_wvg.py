import meep as mp
from meep import mpb

resolution = 64  # pixels/um

w = 0.50  # Si width
h = 0.22  # Si height

sc_y = 2  # supercell width
sc_z = 2  # supercell height

geometry_lattice = mp.Lattice(size=mp.Vector3(0,sc_y,sc_z))

Si = mp.Medium(index=3.45)
SiO2 = mp.Medium(index=1.45)

geometry = [mp.Block(size=mp.Vector3(mp.inf, w, h),
                     center=mp.Vector3(), material=Si),
            mp.Block(size=mp.Vector3(mp.inf, mp.inf, 0.5*(sc_z-h)),
                     center=mp.Vector3(z=0.25*(sc_z+h)), material=SiO2)]

num_bands = 4

num_k = 20
k_min = 0.1
k_max = 2.0
k_points = mp.interpolate(num_k, [mp.Vector3(k_min), mp.Vector3(k_max)])

ms = mpb.ModeSolver(
    geometry_lattice=geometry_lattice,
    geometry=geometry,
    k_points=k_points,
    resolution=resolution,
    num_bands=num_bands)

ms.run(mpb.display_yparities)

f_mode = 1/1.55  # frequency corresponding to 1.55 um
band_min = 1
band_max = 1
kdir = mp.Vector3(1)
tol = 1e-6
kmag_guess = f_mode*3.45
kmag_min = f_mode*0.1
kmag_max = f_mode*4.0

ms.find_k(mp.ODD_Y, f_mode, band_min, band_max, kdir, tol, kmag_guess,
          kmag_min, kmag_max, mpb.output_poynting_x, mpb.display_group_velocities)