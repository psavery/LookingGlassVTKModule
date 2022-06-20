from functools import partial

import numpy as np

import vtk

from vtk import vtkRenderingLookingGlass

# Declare a VTK rendering process
ren = vtk.vtkRenderer()

# This is the one line to change to use a Looking Glass holographic display
#   Use the following line to render to your standard screen:
#     renWin = vtk.vtkRenderWindow()
#   Use the following line to render to the Looking Glass:
# renWin = vtk.vtkRenderWindow()
renWin = vtkRenderingLookingGlass.vtkLookingGlassInterface.CreateLookingGlassRenderWindow()

# Add the rendering process to the window
renWin.AddRenderer(ren)

class LookingGlassInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, renWin):
        self.renWin = renWin
        self.AddObserver('RightButtonPressEvent', self.right_button_press_event)
        self.AddObserver('KeyPressEvent', self.key_press_event)
        self.movement_function = None
        self.movement_factor = None
        self.default_movement_factor = 0.01

        self._slider_widget = None

    @property
    def interactor(self):
        return self.renWin.GetInteractor()

    @property
    def renderer(self):
        return self.renWin.GetRenderers().GetFirstRenderer()

    def render(self):
        self.renWin.Render()

    def remove_slider_widget(self):
        self._slider_widget = None

    def setup_slider_widget(self):
        self.remove_slider_widget()
        if self.movement_function is None:
            return

        slider_rep = vtk.vtkSliderRepresentation2D()
        slider_rep.SetMinimumValue(1.0)
        slider_rep.SetMaximumValue(100.0)
        slider_rep.SetValue(50.0)
        slider_rep.SetTitleText(self.movement_function.__name__)

        colors = vtk.vtkNamedColors()
        slider_rep.GetSelectedProperty().SetColor(colors.GetColor3d("Lime"))

        p1c = slider_rep.GetPoint1Coordinate()
        p1c.SetCoordinateSystemToDisplay()
        p1c.SetValue(40, 40)
        p2c = slider_rep.GetPoint2Coordinate()
        p2c.SetCoordinateSystemToDisplay()
        p2c.SetValue(100, 40)

        w = vtk.vtkSliderWidget()
        w.SetInteractor(self.interactor)
        w.SetRepresentation(slider_rep)
        w.SetAnimationModeToAnimate();
        w.EnabledOn()
        # w.AddObserver('InteractionEvent', self.on_slider_modified)

        self._slider_widget = w

    def on_slider_modified(self, obj, event):
        print(f'Slider modified: {obj=} {event=}')

    def key_press_event(self, obj, event):
        key = self.interactor.GetKeySym()
        print(f'{key=}')

        move_func = self.toggle_movement_function
        callbacks = {
            'c': self.toggle_clipping,
            'f': partial(move_func, func=self.move_far_clipping),
            'n': partial(move_func, func=self.move_near_clipping),
            'p': partial(move_func, func=self.move_focal_plane),
            'Up': self.on_up_pressed,
            'Down': self.on_down_pressed,
            'Left': self.on_left_pressed,
            'Right': self.on_right_pressed,
        }

        if key in callbacks:
            callbacks[key]()

    def right_button_press_event(self, obj, event):
        print('Point clicked:', self.interactor.GetEventPosition())

    def OnLeftButtonDown(self):
        print('Point clicked:', self.interactor.GetEventPosition())

    def toggle_clipping(self):
        b = self.renWin.GetUseClippingLimits()
        print(f'Toggling clipping to {not b}')
        self.renWin.SetUseClippingLimits(not b)
        self.render()

    def toggle_movement_function(self, func):
        factor = self.default_movement_factor

        # Python versions earlier than 3.8 do not allow us to check if
        # a function is the same as another function. So compare the names
        # instead.
        prev_func = self.movement_function
        if prev_func is not None and prev_func.__name__ == func.__name__:
            # Toggle it off
            func = None
            factor = None

        print(f'Toggling movement function to {func}')
        self.movement_function = func
        self.movement_factor = factor

        self.setup_slider_widget()

    def on_up_pressed(self):
        if self.movement_function is None:
            # Do nothing
            return

        # Move by the movement factor
        self.movement_function(self.movement_factor)

    def on_down_pressed(self):
        if self.movement_function is None:
            # Do nothing
            return

        # Move by the negative movement factor
        self.movement_function(-self.movement_factor)

    def on_left_pressed(self):
        if self.movement_factor is None:
            # Do nothing
            return

        # Decrease movement factor
        self.movement_factor *= 0.9
        print(f'Movement factor decreased to {self.movement_factor}')

    def on_right_pressed(self):
        if self.movement_factor is None:
            # Do nothing
            return

        # Increase movement factor
        self.movement_factor *= 1.1
        print(f'Movement factor increased to {self.movement_factor}')

    def move_far_clipping(self, factor):
        print(f'Moving far clipping plane by {factor}')
        value = self.renWin.GetFarClippingLimit()
        self.renWin.SetFarClippingLimit(value * factor + value)
        self.render()

    def move_near_clipping(self, factor):
        print(f'Moving near clipping plane by {factor}')
        value = self.renWin.GetNearClippingLimit()
        self.renWin.SetNearClippingLimit(value * factor + value)
        self.render()

    def move_focal_plane(self, factor):
        print(f'Moving focal plane by {factor * 100}%')
        camera = self.renderer.GetActiveCamera()
        fp = np.array(camera.GetFocalPoint())
        pos = np.array(camera.GetPosition())

        distance = np.linalg.norm(fp - pos)
        direction = (fp - pos) / distance

        distance = distance * factor + distance

        new_fp = pos + direction * distance
        camera.SetFocalPoint(new_fp)
        self.render()


# iren = vtk.vtkRenderWindowInteractor()
iren = renWin.GetInteractor()
style = LookingGlassInteractorStyle(renWin)
iren.SetInteractorStyle(style)
# iren.SetRenderWindow(renWin)

# style.toggle_movement_function(style.move_focal_plane)

# renWin.Render()


# The mouse controls the position of the camera

# Add some text to the display
text = vtk.vtkVectorText()
text.SetText('Hello VTK!')
textMapper = vtk.vtkPolyDataMapper()
textMapper.SetInputConnection(text.GetOutputPort())
textActor = vtk.vtkActor()
textActor.SetMapper(textMapper)
ren.AddActor(textActor)

# Position a cone above the text
cone = vtk.vtkConeSource()
cone.SetRadius(2)
cone.SetHeight(4)
cone.SetCenter(4,4,2)
cone.SetDirection(0,0,1)
coneMapper = vtk.vtkPolyDataMapper()
coneMapper.SetInputConnection(cone.GetOutputPort())
coneActor = vtk.vtkActor()
coneActor.SetMapper(coneMapper)
ren.AddActor(coneActor)

# Initialize the window
renWin.Initialize()
ren.ResetCamera()
ren.GetActiveCamera().SetViewAngle(30)

# The mouse controls the camera until 'q' is pressed to exit
iren.Start()
