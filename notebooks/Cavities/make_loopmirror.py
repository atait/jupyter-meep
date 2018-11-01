from nc_library import loop_mirror_terminator, kqp, lys
from phidl import geometry as pg, Device


D = Device('test')
loop = D << loop_mirror_terminator()
access = D << pg.compass([10, .35], layer=lys['wg_deep'])
access.connect('E', loop.ports['wg_in_1'])

port = D << pg.rectangle([.1, 1], layer=1)
source = D << pg.rectangle([.1, 1], layer=2)
port.y = 0
source.y = 0
port.x = loop.xmin - 6
source.x = loop.xmin - 7

cell = D << pg.rectangle([28, 20], layer=11)
cell.xmin = source.x - 1
cell.y = 0

D.flatten()
D.write_gds('loopmirror.gds')