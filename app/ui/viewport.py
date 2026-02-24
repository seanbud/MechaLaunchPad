import math
from PySide6.QtOpenGLWidgets import QOpenGLWidget
import json
import os
import math
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import Qt, QPoint, QTimer
from OpenGL.GL import *
from OpenGL.GLU import *
from app.core.mesh_manager import MeshManager

class ModularViewport(QOpenGLWidget):
    """Interactive 3D viewport for previewing mech parts."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.mesh_manager = MeshManager()
        self.camera_rot = QPoint(15, 25) # Pitch, Yaw (orbited closer to front)
        self.camera_dist = 5.0 # Zoomed in
        self.camera_pan = QPoint(0, -75) # Panned up slightly
        self.last_mouse_pos = QPoint()
        
        # Animation
        self.animation_data = None
        self.current_frame = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_anim_timer)
        self.load_animation()

    def load_animation(self):
        anim_path = os.path.join("validation", "animation.json")
        if os.path.exists(anim_path):
            try:
                with open(anim_path, "r") as f:
                    self.animation_data = json.load(f)
                self.timer.start(33) # ~30 FPS
                print(f"DEBUG: Loaded animation with {len(self.animation_data['frames'])} frames.")
            except Exception as e:
                print(f"DEBUG: Failed to load animation: {e}")

    def on_anim_timer(self):
        if not self.animation_data:
            return
            
        frames = self.animation_data["frames"]
        self.current_frame = (self.current_frame + 1) % len(frames)
        
        # Update MeshManager pose
        self.mesh_manager.set_pose(frames[self.current_frame])
        self.update()

    def load_fbx_data(self, category, fbx_data):
        """Loads mesh data into the mesh manager and updates the viewport."""
        self.mesh_manager.clear_part(category)
        self.mesh_manager.add_part_meshes(category, fbx_data.meshes)
        self.update()
        
    def initializeGL(self):
        glClearColor(0.1, 0.1, 0.12, 1.0) # Match GitHub Desktop-ish background
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_NORMALIZE) # Fixes scaling lighting artifacts
        glShadeModel(GL_SMOOTH)
        
        # Simple directional light
        glLightfv(GL_LIGHT0, GL_POSITION, [1, 2, 1, 0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [1, 1, 1, 1])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.3, 1])

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        aspect = w / h if h > 0 else 1
        gluPerspective(45, aspect, 0.1, 200.0) # Increased far plane
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # 1. Camera Base Translation (Zoom)
        glTranslatef(0, 0, -self.camera_dist)
        
        # 2. Camera Panning (Applied in view space)
        glTranslatef(self.camera_pan.x() * 0.01, self.camera_pan.y() * 0.01, 0)
        
        # 3. Camera Rotation (Orbit)
        glRotatef(self.camera_rot.x(), 1, 0, 0)
        glRotatef(self.camera_rot.y(), 0, 1, 0)
        
        # 4. Grid and Axes in "Modern Y-Up" space
        self.draw_grid()
        self.draw_axes()
        
        # 5. Compensate for Blender Z-Up -> OpenGL Y-Up
        glPushMatrix() # Isolate robot transform from grid
        glRotatef(-90, 1, 0, 0)
        
        # 6. Apply the overall Armature world transform (handles FBX 100x scale)
        if self.animation_data and "armature_world_matrix" in self.animation_data:
            mat = self.animation_data["armature_world_matrix"]
            glMultMatrixf(mat)
        
        # 7. Draw MeshManager parts
        self.mesh_manager.draw_all()
        glPopMatrix()

    def draw_grid(self, size=10, step=1):
        glDisable(GL_LIGHTING)
        glColor3f(0.3, 0.3, 0.3)
        glBegin(GL_LINES)
        for i in range(-size, size + 1, step):
            glVertex3f(i, 0, -size)
            glVertex3f(i, 0, size)
            glVertex3f(-size, 0, i)
            glVertex3f(size, 0, i)
        glEnd()
        glEnable(GL_LIGHTING)

    def draw_axes(self):
        glDisable(GL_LIGHTING)
        glLineWidth(2)
        glBegin(GL_LINES)
        # X - Red
        glColor3f(1, 0, 0); glVertex3f(0, 0, 0); glVertex3f(1, 0, 0)
        # Y - Green
        glColor3f(0, 1, 0); glVertex3f(0, 0, 0); glVertex3f(0, 1, 0)
        # Z - Blue
        glColor3f(0, 0, 1); glVertex3f(0, 0, 0); glVertex3f(0, 0, 1)
        glEnd()
        glLineWidth(1)
        glEnable(GL_LIGHTING)

    def draw_cube(self):
        """Draws a simple unit cube at the origin."""
        glColor3f(0.5, 0.5, 0.5)
        glBegin(GL_QUADS)
        # Front
        glNormal3f(0, 0, 1)
        glVertex3f(-0.5, 0, 0.5); glVertex3f(0.5, 0, 0.5); glVertex3f(0.5, 1, 0.5); glVertex3f(-0.5, 1, 0.5)
        # Back
        glNormal3f(0, 0, -1)
        glVertex3f(-0.5, 0, -0.5); glVertex3f(-0.5, 1, -0.5); glVertex3f(0.5, 1, -0.5); glVertex3f(0.5, 0, -0.5)
        # Top
        glNormal3f(0, 1, 0)
        glVertex3f(-0.5, 1, -0.5); glVertex3f(-0.5, 1, 0.5); glVertex3f(0.5, 1, 0.5); glVertex3f(0.5, 1, -0.5)
        # Bottom
        glNormal3f(0, -1, 0)
        glVertex3f(-0.5, 0, -0.5); glVertex3f(0.5, 0, -0.5); glVertex3f(0.5, 0, 0.5); glVertex3f(-0.5, 0, 0.5)
        # Left
        glNormal3f(-1, 0, 0)
        glVertex3f(-0.5, 0, -0.5); glVertex3f(-0.5, 0, 0.5); glVertex3f(-0.5, 1, 0.5); glVertex3f(-0.5, 1, -0.5)
        # Right
        glNormal3f(1, 0, 0)
        glVertex3f(0.5, 0, -0.5); glVertex3f(0.5, 1, -0.5); glVertex3f(0.5, 1, 0.5); glVertex3f(0.5, 0, 0.5)
        glEnd()

    def mousePressEvent(self, event):
        self.last_mouse_pos = event.pos()

    def mouseMoveEvent(self, event):
        delta = event.pos() - self.last_mouse_pos
        self.last_mouse_pos = event.pos()
        
        if event.buttons() & Qt.LeftButton:
            # Orbit
            self.camera_rot.setX(self.camera_rot.x() + delta.y() * 0.5)
            self.camera_rot.setY(self.camera_rot.y() + delta.x() * 0.5)
        elif event.buttons() & Qt.MiddleButton:
            # Pan
            self.camera_pan.setX(self.camera_pan.x() + delta.x())
            self.camera_pan.setY(self.camera_pan.y() - delta.y())
            
        self.update()

    def wheelEvent(self, event):
        # Zoom
        delta = event.angleDelta().y()
        self.camera_dist -= delta * 0.01
        self.camera_dist = max(0.1, min(self.camera_dist, 50.0))
        self.update()
