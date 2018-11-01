from nc_library import loop_mirror_terminator, kqp, lys
from phidl import geometry as pg, Device
import meep as mp

silicon = mp.Medium(epsilon=12)
cell_material = dict()

def to_meep(device, mapping):
    geometry = list()
    for poly_grp in device.polygons:
        layer = poly_grp.layers[0]
        try:
            material = mapping[layer]
        except KeyError:
            print('layer {} not in meep mapping'.format(layer))
            continue
        if material is cell_material:
            # import pdb; pdb.set_trace()
            cell = mp.Vector3(poly_grp.xsize, poly_grp.ysize)
            continue
        for poly in poly_grp.polygons:
            vertex_list = list()
            for vertex in poly:
                vertex_list.append(mp.Vector3(vertex[0], vertex[1]))
            geometry.append(mp.Prism(vertex_list, height=0, material=material))
    return cell, geometry


Device.to_meep = to_meep


def give_geom():
    D = Device('test')

    cell = D << pg.rectangle([31, 15], layer=lys['FLOORPLAN'])
    cell.center = (0, 0)

    access = D << pg.compass([8, .35], layer=lys['wg_deep'])
    access.y = cell.y
    access.xmin = cell.xmin

    loop = D << loop_mirror_terminator()
    loop.connect('wg_in_1', access.ports['E'])

    medium_map = dict()
    medium_map[lys['wg_deep'].gds_layer] = silicon
    medium_map[lys['FLOORPLAN'].gds_layer] = cell_material

    port = D << pg.rectangle([.1, 1], layer=1)
    source = D << pg.rectangle([.1, 1], layer=2)
    port.y = 0
    source.y = 0
    port.x = loop.xmin - 6
    source.x = loop.xmin - 7


    D.flatten()
    kqp(D, fresh=True)
    geometry = D.to_meep(medium_map)
    return geometry

if __name__ == '__main__':
    print(give_geom())