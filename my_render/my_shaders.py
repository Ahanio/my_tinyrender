import numpy as np


class GouraudShader:
    var_intens = np.zeros(3)
    var_text_coord = np.zeros((3, 2))

    def __init__(self, model, view_port, intrinsic, minv, light_dir):
        self.view_port = view_port
        self.intrinsic = intrinsic
        self.minv = minv
        self.model = model
        self.light_dir = light_dir

    def add_1_to_vert(self, vert):
        vert = np.concatenate((vert, [1]))
        return vert

    def vertex(self, iface, nth_vert):
        self.var_intens[nth_vert] = np.maximum(
            0, (self.model.norms[iface, nth_vert] * self.light_dir).sum()
        )
        cur_vert = self.add_1_to_vert(self.model.triangles[iface, nth_vert])
        cur_vert = self.view_port.dot(self.intrinsic.dot(self.minv.dot(cur_vert.T)))
        return cur_vert

    def fragment(self, bar):
        intense = self.var_intens.dot(bar)
        color = np.array([255, 255, 255]) * intense

        return color


class GouraudShader_texture(GouraudShader):
    var_intens = np.zeros(3)
    var_text_coord = np.zeros((3, 2))

    def vertex(self, iface, nth_vert):
        self.var_intens[nth_vert] = np.maximum(
            0, (self.model.norms[iface, nth_vert] * self.light_dir).sum()
        )
        self.var_text_coord[nth_vert] = self.model.texture_coord[iface, nth_vert] * [
            self.model.texture.shape[1],
            self.model.texture.shape[0],
        ]
        cur_vert = self.add_1_to_vert(self.model.triangles[iface, nth_vert])
        cur_vert = self.view_port.dot(self.intrinsic.dot(self.minv.dot(cur_vert.T)))
        return cur_vert

    def fragment(self, bar):
        intense = self.var_intens.dot(bar)
        text_coord = self.var_text_coord.T.dot(bar).astype("int32")
        color = self.model.texture[-text_coord[1], text_coord[0]] * intense

        return color


class GouraudShader_normal(GouraudShader):
    var_intens = np.zeros(3)
    var_text_coord = np.zeros((3, 2))

    def vertex(self, iface, nth_vert):
        self.var_text_coord[nth_vert] = self.model.texture_coord[iface, nth_vert] * [
            self.model.texture.shape[1],
            self.model.texture.shape[0],
        ]
        cur_vert = self.add_1_to_vert(self.model.triangles[iface, nth_vert])
        cur_vert = self.view_port.dot(self.intrinsic.dot(self.minv.dot(cur_vert.T)))

        self.M = self.intrinsic.dot(self.minv)
        self.MIT = np.linalg.inv(self.M.T)
        return cur_vert

    def fragment(self, bar):
        text_coord = self.var_text_coord.T.dot(bar).astype("int32")
        norm = self.model.normal_map[-text_coord[1], text_coord[0]].astype("float32")
        norm = 2 * norm / 255 - 1
        norm = self.MIT.dot(self.add_1_to_vert(norm))
        norm = norm[:-1] / norm[-1]
        norm /= -np.linalg.norm(norm)

        light_dir = self.M.dot(self.add_1_to_vert(self.light_dir))
        light_dir = light_dir[:-1] / light_dir[-1]
        light_dir /= np.linalg.norm(light_dir)

        intense = np.maximum(0, (norm * light_dir).sum())
        color = self.model.texture[-text_coord[1], text_coord[0]] * intense
        return color

class GouraudShader_specular(GouraudShader):
    var_intens = np.zeros(3)
    var_text_coord = np.zeros((3, 2))

    def vertex(self, iface, nth_vert):
        self.var_text_coord[nth_vert] = self.model.texture_coord[iface, nth_vert] * [
            self.model.texture.shape[1],
            self.model.texture.shape[0],
        ]
        cur_vert = self.add_1_to_vert(self.model.triangles[iface, nth_vert])
        cur_vert = self.view_port.dot(self.intrinsic.dot(self.minv.dot(cur_vert.T)))
        
        self.M = self.intrinsic.dot(self.minv)
        self.MIT = np.linalg.inv(self.M.T)
        return cur_vert

    def fragment(self, bar):
        text_coord = self.var_text_coord.T.dot(bar).astype("int32")
        
        norm = self.model.normal_map[-text_coord[1], text_coord[0]].astype('float32')
        norm = 2*norm/255 - 1
        norm = self.MIT.dot(self.add_1_to_vert(norm))
        norm = norm[:-1]/norm[-1]
        norm /= -np.linalg.norm(norm)
        
        light_dir = self.M.dot(self.add_1_to_vert(self.light_dir))
        light_dir = light_dir[:-1]/light_dir[-1]
        light_dir /= np.linalg.norm(light_dir)
        
        r = 2 * norm * norm.dot(light_dir)- light_dir
        r /= np.linalg.norm(r)
        
        spec = self.model.spec_map[-text_coord[1], text_coord[0]].astype('float32')
        spec = np.maximum(-r[2], 0)**spec
        
        diffuse = np.maximum(0, (norm*light_dir).sum())
        color = self.model.texture[-text_coord[1], text_coord[0]]
        
        color = np.minimum(5 + color * ( diffuse + 0.6 * spec ), 255)
        return color