import numpy as np

def get_trian_bbox(p0, p1, p2):
    bbox_y = [np.inf, 0]
    bbox_x = [np.inf, 0]
    for cur_p in [p0, p1, p2]:
        bbox_y[0] = int(min(cur_p[1], bbox_y[0]))
        bbox_y[1] = int(max(cur_p[1], bbox_y[1]))

        bbox_x[0] = int(min(cur_p[0], bbox_x[0]))
        bbox_x[1] = int(max(cur_p[0], bbox_x[1]))
    return bbox_x, bbox_y


def line(p0, p1, plane, color):
    trans = False
    if np.abs(p0[0] - p1[0]) < np.abs(p0[1] - p1[1]):
        p0 = p0[::-1]
        p1 = p1[::-1]
        trans = True

    if p0[0] > p1[0]:
        p0, p1 = p1, p0

    for x in np.arange(p0[0], p1[0], 1):
        t = (x - p0[0]) / (p1[0] - p0[0])
        y = int(p0[1] * (1.0 - t) + p1[1] * t)
        if trans:
            plane[y, x] = color
        else:
            plane[x, y] = color

    return plane


def draw_triangle(p0, p1, p2, plane, color):
    plane = line(p0, p1, plane, color)
    plane = line(p1, p2, plane, color)
    plane = line(p2, p0, plane, color)
    return plane

def barycentric_transform(points, grid):
    try:
        precomp_t_inv = np.linalg.inv(
            np.array(
                [
                    [points[0][0] - points[2][0], points[1][0] - points[2][0]],
                    [points[0][1] - points[2][1], points[1][1] - points[2][1]],
                ]
            )
        )
    except:
        return None

    barycent = precomp_t_inv.dot(grid.T - points[2][:2][:, None])
    barycent = np.concatenate([barycent, 1 - barycent.sum(axis=0)[None]])
    return barycent


def triangle(points, shader, plane, z_buffer):
    points = np.array([[x[1], x[0], x[2], x[3]] for x in points])
    bbox_x, bbox_y = get_trian_bbox(
        points[0][:2] / points[0][3],
        points[1][:2] / points[1][3],
        points[2][:2] / points[2][3],
    )

    mesh_grid = np.meshgrid(
        np.arange(bbox_x[0], bbox_x[1] + 1), np.arange(bbox_y[0], bbox_y[1] + 1)
    )

    grid = np.stack([mesh_grid[0].T, mesh_grid[1].T])
    grid = np.stack([grid[0].reshape(-1), grid[1].reshape(-1)]).T

    barycent = barycentric_transform(
        (points / points[:, 3][:, None]).astype("int32"), grid
    )

    if barycent is None:
        return plane, z_buffer

    z_plane = (points[:, 2][:, None] * barycent).sum(axis=0)
    w_plane = (points[:, 3][:, None] * barycent).sum(axis=0)
    z_plane /= w_plane

    good_pts = np.product(barycent >= 0, axis=0)
    good_idx = grid[np.where(good_pts != 0)][:, 0], grid[np.where(good_pts != 0)][:, 1]

    if np.sum(good_pts) == 0:
        return plane, z_buffer

    need_z_buffer_update = (
        z_buffer[good_idx[0], good_idx[1]] < z_plane[np.where(good_pts != 0)]
    )

    good_pts[good_pts != 0] = need_z_buffer_update
    good_idx = grid[np.where(good_pts != 0)][:, 0], grid[np.where(good_pts != 0)][:, 1]

    if np.sum(good_idx) == 0:
        return plane, z_buffer

    color = []
    barycent = barycent.T
    for cur_bar in barycent[np.where(good_pts != 0)]:
        new_color = shader.fragment(cur_bar)
        if new_color is None:
            continue
        color.append(new_color)
    color = np.array(color)

    plane[good_idx[0], good_idx[1]] = color

    z_buffer[good_idx[0], good_idx[1]] = z_plane[np.where(good_pts != 0)]

    return plane, z_buffer


def get_ModelView(eye, center, up):
    z = eye - center
    z = z / np.linalg.norm(z)

    x = np.cross(up, z)
    x = x / np.linalg.norm(x)

    y = np.cross(z, x)
    y = y / np.linalg.norm(y)

    minv = np.eye(4)
    tr = np.eye(4)
    minv[0][:-1] = x
    minv[1][:-1] = y
    minv[2][:-1] = z
    tr[:-1, 3] = -center

    minv = minv.dot(tr)
    return minv


def get_intrinsic(c):
    return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, -1 / c, 1]])


def get_view_port(cur_width, cur_height, cur_depth):
    view_port = np.array(
        [
            [cur_width / 2, 0, 0, cur_width / 2 + cur_width / 4],
            [0, -cur_height / 2, 0, -cur_height / 2 - cur_height / 4],
            [0, 0, cur_depth / 2, cur_depth / 2],
            [0, 0, 0, 1],
        ]
    )
    return view_port
