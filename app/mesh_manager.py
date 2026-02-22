from OpenGL.GL import *
import numpy as np
import json
import os

def transpose_4x4(m):
    return [
        m[0], m[4], m[8], m[12],
        m[1], m[5], m[9], m[13],
        m[2], m[6], m[10], m[14],
        m[3], m[7], m[11], m[15]
    ]

class MeshObject:
    def __init__(self, name, vertices, normals, indices):
        self.name = name
        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.indices = np.array(indices, dtype=np.uint32)
        self.visible = True
        self.parent_bone = ""
        self.color = (0.7, 0.7, 0.7)

    def draw(self):
        if not self.visible or len(self.indices) == 0:
            return

        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        
        glVertexPointer(3, GL_FLOAT, 0, self.vertices)
        glNormalPointer(GL_FLOAT, 0, self.normals)
        
        glColor3f(*self.color)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, self.indices)
        
        glDisableClientState(GL_NORMAL_ARRAY)
        glDisableClientState(GL_VERTEX_ARRAY)

class MeshManager:
    """Manages 3D meshes for the viewport."""
    def __init__(self):
        self.parts = {} # category -> list of MeshObject
        self.current_pose = {} # bone_name -> 16 floats (column-major)

    def set_pose(self, pose_data):
        """Updates the current bone transforms for animation."""
        self.current_pose = pose_data

    def add_part_meshes(self, category, meshes_data):
        """Adds meshes extracted from an FBX to a specific category."""
        mesh_objs = []
        for m in meshes_data:
            obj = MeshObject(
                m["name"], 
                m["vertices"], 
                m["normals"], 
                m["indices"]
            )
            obj.parent_bone = m.get("parent_bone", "")
            mesh_objs.append(obj)
        
        self.parts[category] = mesh_objs

    def clear_part(self, category):
        if category in self.parts:
            del self.parts[category]

    def draw_all(self):
        for category, meshes in self.parts.items():
            for mesh in meshes:
                glPushMatrix()
                
                # Apply Stitching Transform (Armature-space matrix)
                if mesh.parent_bone in self.current_pose:
                    mat = self.current_pose[mesh.parent_bone]
                    # We already flattened to column-major in extraction script
                    glMultMatrixf(mat)
                
                mesh.draw()
                glPopMatrix()
