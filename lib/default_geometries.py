import meep as mp

def give_1d_microring_geometry(n=3.4, w=1, r=1, pad=4):
    # background
    bg_radius = r + w + pad
    background = mp.Block(center=mp.Vector3(bg_radius/2),
                          size=mp.Vector3(bg_radius, mp.inf, mp.inf),
                          material=mp.Medium(index=1))

    # this turns arguments into a microring with index n
    waveguide = mp.Block(center=mp.Vector3(r + (w / 2)),
                         size=mp.Vector3(w, mp.inf, mp.inf),
                         material=mp.Medium(index=n))

    geometry = [background, waveguide]
    return geometry