import numpy as np
from my_render import get_ModelView, get_intrinsic, get_view_port, triangle
from my_shaders import GouraudShader, GouraudShader_texture
from obj_parser import Model
import cv2

width = 800
height = 800
depth = 255
eye = np.array([1, 1, 3])
center = np.array([0, 0, 0])
up = np.array([0, 1, 0])
c = np.linalg.norm(eye - center)
light_dir = np.array([0, 0, -1])

plane = np.zeros((width, height, 3))
z_buffer = np.ones((width, height)) * (-np.inf)
minv = get_ModelView(eye, center, up)
intrinsic = get_intrinsic(c)
view_port = get_view_port(width * 2 / 3, height * 2 / 3, depth)

model = Model("./obj/african_head.obj", "./obj/african_head_diffuse.png")
shader = GouraudShader_texture(model, view_port, intrinsic, minv, light_dir)

cv2.imwrite("render_res.png", plane.astype("uint8")[:, :, ::-1])

for i in range(len(model.triangles)):
    cur_trian = []
    for j in range(3):
        cur_trian.append(shader.vertex(i, j))

    plane, z_buffer = triangle(np.array(cur_trian), shader, plane, z_buffer)

cv2.imwrite("render_res.png", plane.astype("uint8")[:, :, ::-1])
