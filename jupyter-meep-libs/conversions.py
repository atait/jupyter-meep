import numpy as np
from phidl import geometry as pg, path as pp, Device, Layer, LayerSet, CrossSection, Path
import meep as mp

silicon = mp.Medium(epsilon=12)
cell_material = dict()  # for floorplanning
port_source = dict()  # for metadata layers
LAYER_SOURCE = 1
LAYER_PORT = 2

def get_layer_mapping(layerset):
    # Gets the silicon layer and the floorplan layer for the cell
    medium_map = dict()
    medium_map[layerset['wg_deep'].gds_layer] = silicon
    medium_map[layerset['FLOORPLAN'].gds_layer] = cell_material
    medium_map[LAYER_SOURCE] = port_source
    medium_map[LAYER_PORT] = port_source
    return medium_map


def device_to_meep(device, mapping):
    # converts PHIDL to MEEP. You must give a layer mapping that can be derived from get_layer_mapping
    # TODO: partial etches. Currently this is only 2D
    geometry = list()
    for poly_grp in device.polygons:
        layer = poly_grp.layers[0]
        try:
            material = mapping[layer]
        except KeyError:
            print('layer {} not in meep mapping'.format(layer))
            continue
        if material is cell_material:
            cell = mp.Vector3(poly_grp.xsize, poly_grp.ysize)
            continue
        elif material is port_source:
            continue
        for poly in poly_grp.polygons:
            vertex_list = list()
            for vertex in poly:
                vertex_list.append(mp.Vector3(vertex[0], vertex[1]))
            geometry.append(mp.Prism(vertex_list, height=0, material=material))
    return cell, geometry


def gds_to_meep(filename):
    D = Device('gdsext')
    D.load_gds(filename)
    D.flatten()
    return device_to_meep(D)


def put_cell_on_reflector(reflector_device, entry_length=8, cell_buffer=1):
    ''' Returns a Device with a simulation cell and ports placed around a Device
        That has one port called wg_in_1 '''
    D = Device('Simulation Cell')
    entry = D << default_wgX.extrude(entry_length)
    entry.y = 0
    entry.xmin = 0
    ref = D << reflector_device
    ref.connect('wg_in_1', entry.ports['out'])

    sim_cell = D << pg.bbox([
        [entry.xmin, ref.ymin - cell_buffer],
        [ref.xmax + cell_buffer, ref.ymax + cell_buffer]
    ], layer=lys['FLOORPLAN'])
    source = D << pg.rectangle([.1, 1], layer=LAYER_SOURCE)
    source.y = entry.y
    source.x = entry.xmin + 1
    port = D << pg.rectangle([.1, 1], layer=LAYER_PORT)
    port.y = entry.y
    port.x = entry.xmin + 2
    return D.flatten()


# --- Examples of creating geometry with phidl and converting to MEEP

lys = LayerSet()
lys.add_layer('wg_shallow', gds_layer=21)
lys.add_layer('wg_deep', gds_layer=22)
lys.add_layer('FLOORPLAN', gds_layer=99)

default_wgX = CrossSection().add(0.35, layer=lys['wg_deep'], ports=('in', 'out'), name='Rib')

def mmi1x2(length_port=0.2, length_mmi=2.8, width_mmi=1.55, gap_mmi=0.65):
    D=Device('MMI')
    wg_width = default_wgX['Rib']['width']
    body = D << pg.compass((length_mmi, width_mmi), layer=lys['wg_deep'])
    Port_wg = pg.compass((length_port, wg_width), layer=lys['wg_deep'])
    port_in = D << Port_wg
    port_out1 = D << Port_wg
    port_out2 = D << Port_wg
    port_in.connect('E', body.ports['W'])
    port_out1.connect('W', body.ports['E'])
    port_out2.connect('W', body.ports['E'])
    port_out1.y += (wg_width + gap_mmi) / 2
    port_out2.y -= (wg_width + gap_mmi) / 2

    D.add_port('wg_in_1', port=port_in.ports['W'])
    D.add_port('wg_out_1', port=port_out1.ports['E'])
    D.add_port('wg_out_2', port=port_out2.ports['E'])
    D.flatten()
    return D

def loop_mirror_terminator(y_splitter=None, theta_exit=35, R_exit=5, R_min_check=3):
    ''' A loop mirror (or Sagnac interferometer) consisting of a splitter with connected outputs.
        Performance should be pretty broad band, determined by the MMI.

        The only port is 'wg_in_1'
    '''
    if R_exit < R_min_check:
        raise ValueError('Exit radius cannot be less than specified minimum radius [{:.3f} < {}]'.format(R_exit, R_min_check))
    D = Device('LoopMirror')
    if y_splitter is None:
        y_splitter = mmi1x2()
    split = D << y_splitter

    P_exit = pp.euler(radius=R_exit, angle=theta_exit, p=.7)
    loop_arcangle = 180 + 2*theta_exit
    dy = abs(split.ports['wg_out_1'].y - split.ports['wg_out_2'].y) / 2
    dy += P_exit.ysize
    Reff = dy / np.cos(np.pi / 180 * theta_exit)

    P_loop = pp.euler(radius=Reff, angle=-loop_arcangle, p=.3, use_eff=True)
    if P_loop.info['Rmin'] < R_min_check:
        raise ValueError('Loop radius is too tight [{:.3f} < {}]. Try increasing theta_exit or R_exit'.format(P_loop.info['Rmin'], R_min_check))
    loop = D << Path([P_exit, P_loop, P_exit]).extrude(default_wgX)
    loop.connect('in', split.ports['wg_out_1'])
    assert np.allclose(loop.ports['out'].midpoint, split.ports['wg_out_2'].midpoint)  # Math check

    D.add_port('wg_in_1', port=split.ports['wg_in_1'])
    return D

def give_loopmirror(gap_mmi=.5):
    # just an example of augmenting a normal phidl device (loop_mirror_terminator)
    # giving it as a phidl Device as well as port, bounding box, and source things used by MEEP
    D = Device('loopmirror')

    cell = D << pg.rectangle([31, 15], layer=lys['FLOORPLAN'])
    cell.center = (0, 0)

    access = D << pg.compass([8, .35], layer=lys['wg_deep'])
    access.y = cell.y
    access.xmin = cell.xmin

    mmi = mmi1x2(gap_mmi=.5)
    loop = D << loop_mirror_terminator(y_splitter=mmi)
    loop.connect('wg_in_1', access.ports['E'])

    # medium_map = get_layer_mapping(lys)

    port = D << pg.rectangle([.1, 1], layer=1)
    source = D << pg.rectangle([.1, 1], layer=2)
    port.y = 0
    source.y = 0
    port.x = loop.xmin - 6
    source.x = loop.xmin - 7

    D.flatten()
    return D
