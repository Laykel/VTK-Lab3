#!/usr/bin/env python

"""
Lab: 3-ColorMapping
Authors: Claude-André Alves, Luc Wachter
Description: Provide a visualization pipeline able to generate a colored raised-relief map using only height data.
Date: 21.04.2020
Python version: 3.7.4
"""

import vtk


def read_height_matrix(filename):
    """Read a file that has two integers on the first line (width, height) and then the values of a matrix"""
    with open(filename, 'r') as file:
        width, height = [int(x) for x in next(file).split()]
        matrix = [[int(x) for x in line.split()] for line in file]

    return width, height, matrix


# Main instructions
def main():
    colors = vtk.vtkNamedColors()

    width, height, heights = read_height_matrix('altitudes.txt')

    points = vtk.vtkPoints()

    for i in range(width):
        for j in range(height):
            points.InsertNextPoint(i, j, heights[i][j])

    polydata = vtk.vtkPolyData()
    polydata.SetPoints(points)

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
