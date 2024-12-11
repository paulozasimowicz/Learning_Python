# First steps with vedo.

import vedo


line =vedo.Line([(0,0,0), (1,1,1), (2,0,1), (3,1,0)])

tube =vedo.Tube(line, r=0.1)

vedo.show(tube, axes=3).close()