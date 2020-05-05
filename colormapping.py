#!/usr/bin/env python

"""
Lab: 3-ColorMapping
Authors: Claude-André Alves, Luc Wachter
Description: Provide a visualization pipeline able to generate a colored raised-relief map using only height data.
Date: 5.05.2020
Python version: 3.7.4
"""

import vtk
from math import cos, sin, radians

# Whether or not to save result as PNG file
DRAW_PNG = False

# Earth radius (meters)
EARTH_RADIUS = 6371009

# Latitude north (degrees)
LAT_MIN = 45
LAT_MAX = 47.5
# Longitude east (degrees)
LONG_MIN = 5
LONG_MAX = 7.5

# Number of identical height values needed to consider an area flat
NBR_VAL_FLAT = 8


def read_height_matrix(filename):
    """Read a file that has two integers on the first line (width, height) and then the values of a matrix"""
    with open(filename, 'r') as file:
        rows, cols = [int(x) for x in next(file).split()]
        matrix = [[int(x) for x in line.split()] for line in file]

    return rows, cols, matrix


def coord_to_idx(i, j, width):
    """Get the 1D index of a 2D matrix element"""
    return j + i * width


def spherical_coordinates(latitude, longitude, distance, rows, cols):
    """Take a simple grid-based coordinates point and convert it to a spherical coordinates point"""
    # Get the step between two points for both axes
    step_lat = (LAT_MAX - LAT_MIN) / (rows - 1)
    step_long = (LONG_MAX - LONG_MIN) / (cols - 1)

    # Transform coordinates using steps and starting long/lat
    delta = radians(LAT_MAX - latitude * step_lat)
    theta = radians(LONG_MIN + longitude * step_long)
    # Transform distance using earth's radius (approximation)
    rho = distance + EARTH_RADIUS

    # Get spherical coordinates using the formulas in:
    # https://fr.wikipedia.org/wiki/Coordonn%C3%A9es_sph%C3%A9riques#Convention_rayon-longitude-latitude
    x = rho * cos(delta) * cos(theta)
    y = rho * cos(delta) * sin(theta)
    z = rho * sin(delta)

    return x, y, z


def find_neighbours(m, i, j, dist=1):
    """Simple implementation of a neighbouring algorithm for a 2D matrix
    Returns the values of the neighbouring elements at distance `dist` of element `m[i][j]`
    """
    # Little help from:
    # https://stackoverflow.com/questions/15913489/python-find-all-neighbours-of-a-given-node-in-a-list-of-lists
    neighbours = [row[max(0, j - dist):j + dist + 1] for row in m[max(0, i - 1):i + dist + 1]]
    return [el for nl in neighbours for el in nl]


def is_neighbourhood_flat(m, i, j, nbr_neighbours, dist):
    """Returns True if the neighbouring points are mostly at exactly the same height"""
    heights = find_neighbours(m, i, j, dist)
    counts = [heights.count(height) for height in heights]
    return max(counts) > nbr_neighbours


def build_map(heights, rows, cols, sea_level=0):
    """Build a relief map from the raw heights and return a polydata object"""
    points = vtk.vtkPoints()
    cells = vtk.vtkCellArray()
    scalars = vtk.vtkFloatArray()

    for i in range(rows):
        for j in range(cols):
            height = sea_level if heights[i][j] <= sea_level else heights[i][j]
            points.InsertNextPoint(spherical_coordinates(i, j, height, rows, cols))

            is_flat = is_neighbourhood_flat(heights, i, j, nbr_neighbours=NBR_VAL_FLAT, dist=1)
            scalar = 0 if is_flat or heights[i][j] <= sea_level else heights[i][j]
            scalars.InsertTuple1(coord_to_idx(i, j, cols), scalar)

            if i != 0 and j != 3000:
                quad = (coord_to_idx(i, j, cols),
                        coord_to_idx(i, j + 1, cols),
                        coord_to_idx(i - 1, j + 1, cols),
                        coord_to_idx(i - 1, j, cols))
                cells.InsertNextCell(4, quad)

    # Create polydata and set geometry, topology and scalars
    relief_map = vtk.vtkPolyData()
    relief_map.SetPoints(points)
    relief_map.SetPolys(cells)
    relief_map.GetPointData().SetScalars(scalars)

    return relief_map


def map_to_png(filename, renderer):
    """Take a configured `renderer` and generate a PNG file as `filename`"""
    ren_win = vtk.vtkRenderWindow()
    ren_win.OffScreenRenderingOn()
    ren_win.AddRenderer(renderer)
    ren_win.Render()

    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(ren_win)
    w2if.SetScale(10)
    w2if.SetInputBufferTypeToRGBA()
    w2if.Update()

    writer = vtk.vtkPNGWriter()
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.SetFileName(filename)
    writer.Write()


# Main instructions
def main():
    rows, cols, heights = read_height_matrix('altitudes.txt')

    # Create geometry, topology and scalars and get our Polydata object
    relief_map = build_map(heights, rows, cols)
    # relief_map = build_map(heights, rows, cols, sea_level=370)  # Sea level at 370m

    # Configure lookup table
    # https://danstoj.pythonanywhere.com/article/vtk-1#_creating_custom_colour_gradients
    min_alt, max_alt = min([min(h) for h in heights]), max([max(h) for h in heights])
    mid_alt = (max_alt - min_alt) / 2
    nbr_colors = int(max_alt - min_alt)

    lut = vtk.vtkLookupTable()
    lut.SetNumberOfColors(nbr_colors)
    lut.SetTableRange(min_alt, max_alt)

    # On scalars below the minimum altitude, use blue (lakes and "sea")
    lut.UseBelowRangeColorOn()
    lut.SetBelowRangeColor(0.34, 0.35, 0.67, 1)

    # Design the colour gradient
    colour_trans = vtk.vtkColorTransferFunction()
    colour_trans.AddRGBPoint(min_alt, 0.25, 0.46, 0.24)  # Green
    colour_trans.AddRGBPoint(mid_alt - 1000, 0.73, 0.69, 0.55)  # Beige
    colour_trans.AddRGBPoint(max_alt - 1000, 1.0, 1.0, 1.0)  # White

    for alt in range(nbr_colors):
        col = colour_trans.GetColor(min_alt + alt)
        lut.SetTableValue(alt, *col)

    lut.Build()

    # Map data and create actors
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(relief_map)
    # Lookup table things
    mapper.SetLookupTable(lut)
    mapper.SetUseLookupTableScalarRange(True)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    # Set the renderer
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(0.5, 0.5, 0.5)

    # Move camera in position
    renderer.GetActiveCamera().Roll(-90)
    renderer.GetActiveCamera().Elevation(-32)
    renderer.GetActiveCamera().Roll(-5)
    renderer.ResetCamera()

    # Use the renderer to write a PNG file
    if DRAW_PNG:
        map_to_png("sea_level_map.png", renderer)

    # Window properties
    ren_win = vtk.vtkRenderWindow()
    ren_win.SetWindowName("The good map")
    ren_win.SetSize(1000, 1000)
    ren_win.AddRenderer(renderer)

    # Watch for events
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(ren_win)

    # Set the interactor style
    style = vtk.vtkInteractorStyleTrackballCamera()
    interactor.SetInteractorStyle(style)

    # Initialize and start the event loop
    interactor.Initialize()
    interactor.Start()


if __name__ == "__main__":
    main()
