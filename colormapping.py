#!/usr/bin/env python

"""
Lab: 3-ColorMapping
Authors: Claude-André Alves, Luc Wachter
Description: Provide a visualization pipeline able to generate a colored raised-relief map using only height data.
Date: 21.04.2020
Python version: 3.7.4
"""

import vtk
from math import cos, sin, radians

# Earth radius (meters)
EARTH_RADIUS = 6371009
# Latitude north (degrees)
LAT_MIN = 45
LAT_MAX = 47.5
# Longitude east (degrees)
LONG_MIN = 5
LONG_MAX = 7.5


def read_height_matrix(filename):
    """Read a file that has two integers on the first line (width, height) and then the values of a matrix"""
    with open(filename, 'r') as file:
        rows, cols = [int(x) for x in next(file).split()]
        matrix = [[int(x) for x in line.split()] for line in file]

    return rows, cols, matrix


def coord_to_idx(i, j, width):
    """Get the 1D index of a matrix element"""
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


# Main instructions
def main():
    colors = vtk.vtkNamedColors()

    rows, cols, heights = read_height_matrix('altitudes.txt')

    # Create geometry and topology
    points = vtk.vtkPoints()
    polys = vtk.vtkCellArray()

    for i in range(rows):
        for j in range(cols):
            points.InsertNextPoint(spherical_coordinates(i, j, heights[i][j], rows, cols))

            if i != 0 and j != 3000:
                quad = (coord_to_idx(i, j, cols), coord_to_idx(i, j + 1, cols),
                        coord_to_idx(i - 1, j + 1, cols), coord_to_idx(i - 1, j, cols))
                polys.InsertNextCell(4, quad)

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)
    polydata.SetPolys(polys)

    # Map data and create actors
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(polydata)

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    renderer.SetBackground(colors.GetColor3d("Cornsilk"))

    # Window properties
    ren_win = vtk.vtkRenderWindow()
    ren_win.SetWindowName("The good map")
    ren_win.SetSize(800, 800)
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
