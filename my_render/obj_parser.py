import numpy as np
from skimage.io import imread


class Model:
    def __init__(self, obj_path, text_path=None, normal_map_path=None, spec_map_path=None):
        self.obj_path = obj_path
        self.text_path = text_path

        self.triangles = None
        self.texture_coord = None
        self.texture = None
        self.norms = None

        self.read_obj(self.obj_path)
        if text_path is not None:
            self.texture = imread(self.text_path)[:, :, :3]

        if normal_map_path is not None:
            self.normal_map = imread(normal_map_path)
            self.normal_map = self.normal_map[:,:,:-1]
        
        if spec_map_path is not None:
            self.spec_map = imread(spec_map_path)[:,:,0]

    def read_obj(self, obj_path):
        with open(obj_path) as f:
            lines = f.readlines()

        vert = [x for x in lines if x.startswith("v ")]
        vert = [list(map(float, x[1:].strip().split())) for x in vert]

        text = [x for x in lines if x.startswith("vt ")]
        text = [list(map(float, x.strip().split()[1:-1])) for x in text]

        norms = [x for x in lines if x.startswith("vn ")]
        norms = [list(map(float, x.strip().split()[1:])) for x in norms]

        faces = [x for x in lines if x.startswith("f")]
        faces = [
            [
                x.split("/")[0].split()[1],
                x.split("/")[2].split()[1],
                x.split("/")[4].split()[1],
            ]
            for x in faces
        ]
        faces = [[int(y) - 1 for y in x] for x in faces]

        text_coord = [x for x in lines if x.startswith("f")]
        text_coord = [
            [x.split("/")[1], x.split("/")[3], x.split("/")[5]] for x in text_coord
        ]
        text_coord = [[int(y) - 1 for y in x] for x in text_coord]

        norm_coord = [x for x in lines if x.startswith("f")]
        norm_coord = [
            [
                x.split("/")[2].split(" ")[0],
                x.split("/")[4].split(" ")[0],
                x.split("/")[6].split(" ")[0].strip(),
            ]
            for x in norm_coord
        ]
        norm_coord = [[int(y) - 1 for y in x] for x in norm_coord]

        triangles = []
        trian_text = []
        normals = []
        for cur_face, cur_texture, cur_norm in zip(faces, text_coord, norm_coord):
            pts = []
            pts_text = []
            pts_norm = []
            for cur_vert, cur_one_text, cur_one_norm in zip(
                cur_face, cur_texture, cur_norm
            ):
                pts_text.append(text[cur_one_text])
                pts_norm.append(norms[cur_one_norm])
                pts.append(vert[cur_vert])

            triangles.append(pts)
            trian_text.append(pts_text)
            normals.append(pts_norm)

        self.triangles = np.array(triangles)
        self.texture_coord = np.array(trian_text)
        self.norms = -np.array(normals)
