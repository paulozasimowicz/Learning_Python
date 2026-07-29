from vedo import *

c1 = Cylinder(pos=(0,0,0), r=2, height=3, axis=(1,.0,0), alpha=.1).triangulate()
c2 = Plane(pos=(0,0,0), normal=(1,0,0),s=(6,6)).triangulate()
intersect = c1.intersect_with(c2).join(reset=True)
line = Line(intersect).c('green').lw(5)
spline = Spline(intersect).c('blue').lw(5)
cspline = CSpline(intersect).c('red').lw(5)
length_line = line.length()
length_spline = spline.length()
length_cspline = cspline.length()
circunference = 2 * np.pi * 2
diff_percent_line_circunference = (length_line - circunference)/circunference * 100
diff_percent_line_spline = (length_spline - circunference)/circunference * 100
diff_percent_line_cspline = (length_cspline - circunference)/circunference * 100
print(f'Length of the line: {length_line}')
print(f'Length of the spline: {length_spline}')
print(f'Length of the bezier curve: {length_cspline}')
print(f'Circunference of the cylinder: {circunference}')
print(f'Difference between line and spline: {diff_percent_line_spline}')
print(f'Difference between line and bezier curve: {diff_percent_line_cspline}')   
show(c1, c2, spline, cspline, line, intersect.labels('id'), axes=1).close()
