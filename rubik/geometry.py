# ---------- 贴片的位置与转动约定 ----------
from rubik.model import FACE_ORDER  # 与模型共用统一的六面顺序。
NORMALS = dict(U=(0, 1, 0), R=(1, 0, 0), F=(0, 0, 1), D=(0, -1, 0), L=(-1, 0, 0), B=(0, 0, -1))  # x 向右、y 向上、z 向前。
TURN_AXES = dict(U=(1, 1, -1), R=(0, 1, -1), F=(2, 1, -1), D=(1, -1, 1), L=(0, -1, 1), B=(2, -1, 1))  # 保存坐标轴、被选层和右手系转动方向。
def facelet_geometry(index):  # 给出贴片所在小方块的位置及朝外法向量。
    face = FACE_ORDER[index // 9]  # 根据每面九个贴片确定所属面。
    row, column = divmod(index % 9, 3)  # 确定面内的行列。
    positions = dict(U=(column - 1, 1, row - 1), R=(1, 1 - row, 1 - column), F=(column - 1, 1 - row, 1), D=(column - 1, -1, 1 - row), L=(-1, 1 - row, column - 1), B=(1 - column, 1 - row, -1))  # 使用面对每个面的标准行列方向。
    return positions[face], NORMALS[face]  # 返回整数几何，避免浮点误差。
def quarter_rotate(vector, axis, direction):  # 对整数向量执行精确的 90 度旋转。
    x, y, z = vector  # 分离三维坐标。
    if axis == 0:  # 处理绕 x 轴旋转。
        return x, -direction * z, direction * y  # 实现右手系旋转矩阵在 90 度时的简化形式。
    if axis == 1:  # 处理绕 y 轴旋转。
        return direction * z, y, -direction * x  # x 和 z 分量交换并按方向改变符号。
    return -direction * y, direction * x, z  # 处理绕 z 轴旋转。
def rotated(position, normal, notation):  # 计算一个单步转动后的贴片几何。
    axis, layer, direction = TURN_AXES[notation[0]]  # 读取当前面的层位置和转动方向。
    if position[axis] != layer:  # 不在被转动层的贴片保持不变。
        return position, normal  # 返回原几何。
    direction *= -1 if notation.endswith("'") else 1  # 撇号表示反向转动。
    return quarter_rotate(position, axis, direction), quarter_rotate(normal, axis, direction)  # 同时旋转位置和朝向。
