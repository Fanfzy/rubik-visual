# ---------- 棱块与角块编号约定 ----------
from collections import Counter  # 统计颜色以及块的数量。
from rubik.model import SOLVED, CENTERS, FACE_COLORS, COLOR_NAMES  # 导入固定配色和中心位置。
CORNERS = ((8, 9, 20), (6, 18, 38), (0, 36, 47), (2, 45, 11), (29, 26, 15), (27, 44, 24), (33, 53, 42), (35, 17, 51))  # 按 URF、UFL、ULB、UBR、DFR、DLF、DBL、DRB 记录角块贴片。
CORNER_NAMES = ('URF', 'UFL', 'ULB', 'UBR', 'DFR', 'DLF', 'DBL', 'DRB')  # 记录复原状态角块颜色对应的面。
EDGES = ((5, 10), (7, 19), (3, 37), (1, 46), (32, 16), (28, 25), (30, 43), (34, 52), (23, 12), (21, 41), (50, 39), (48, 14))  # 记录十二条棱块的贴片索引。
EDGE_NAMES = ('UR', 'UF', 'UL', 'UB', 'DR', 'DF', 'DL', 'DB', 'FR', 'FL', 'BL', 'BR')  # 记录棱块的标准颜色顺序。
def parity(permutation):  # 计算块的交换次数是奇数还是偶数。
    return sum(permutation[i] > permutation[j] for i in range(len(permutation)) for j in range(i + 1, len(permutation))) % 2  # 每对逆序贡献一次交换，最后只保留奇偶性。

# ---------- 完整的物理可复原性检查 ----------
def validate(facelets):  # 合法时返回 None，错误时返回中文原因。
    if len(facelets) != 54 or any(value not in COLOR_NAMES for value in facelets):  # 检查输入长度和颜色范围。
        return '魔方需要完整的 54 个有效色块。'  # 拒绝格式错误。
    counts = Counter(facelets)  # 统计每种颜色的贴片数量。
    errors = [f'{name}有 {counts[value]} 块' for value, name in COLOR_NAMES.items() if counts[value] != 9]  # 收集数量不正确的颜色。
    if errors:  # 数量不正确时先提示最容易修正的问题。
        return '每种颜色必须有 9 块；' + '，'.join(errors) + '。'  # 明确显示实际数量。
    if any(facelets[index] != SOLVED[index] for index in CENTERS):  # 检查六个固定中心。
        return '中心色块必须保持白底黄顶蓝前左橙右红。'  # 解释配色约束。
    reverse_colors = {value: face for face, value in FACE_COLORS.items()}  # 把颜色转换为固定的面字母。
    faces = ''.join(reverse_colors[value] for value in facelets)  # 后续检查独立于具体颜色字符。
    corner_permutation, corner_twists = [], []  # 保存角块位置和扭转次数。
    for indices in CORNERS:  # 读取每个角块的三个贴片。
        values = ''.join(faces[index] for index in indices)  # 按角块标准环绕顺序读取颜色。
        orientations = [index for index, value in enumerate(values) if value in 'UD']  # 找到白色或黄色贴片朝向。
        if len(orientations) != 1:  # 一个角块应当只有一个白色或黄色贴片。
            return '角块颜色组合不合法，请检查白色或黄色附近的三个色块。'  # 指出角块输入问题。
        orientation = orientations[0]  # 保存这个角块的扭转状态。
        canonical = values[orientation:] + values[:orientation]  # 将白黄贴片转到首位，再比对块的身份。
        if canonical not in CORNER_NAMES:  # 同时检查颜色组合和环绕顺序。
            return '角块颜色组合或排列方向不合法，请检查相邻的三个色块。'  # 拒绝不存在或镜像的角块。
        corner_permutation.append(CORNER_NAMES.index(canonical))  # 记录该位置放了哪一个角块。
        corner_twists.append(orientation)  # 记录角块扭转次数。
    if len(set(corner_permutation)) != 8:  # 检查八个不同角块是否全部出现。
        return '有重复或缺失的角块，请检查角块的颜色组合。'  # 防止同一个角块被输入多次。
    edge_permutation, edge_flips = [], []  # 保存棱块位置和翻转次数。
    for indices in EDGES:  # 依次读取十二条棱块。
        values = ''.join(faces[index] for index in indices)  # 获取两片颜色的标准顺序。
        canonical = values if values in EDGE_NAMES else values[::-1]  # 棱块可以正向或反向放置。
        if canonical not in EDGE_NAMES:  # 某些两色组合在真实魔方上不存在。
            return '棱块颜色组合不合法，请检查相邻的两个色块。'  # 返回可读的输入错误。
        edge_permutation.append(EDGE_NAMES.index(canonical))  # 记录棱块身份。
        edge_flips.append(int(values != canonical))  # 反向顺序表示翻转一次。
    if len(set(edge_permutation)) != 12:  # 检查棱块是否重复或缺失。
        return '有重复或缺失的棱块，请检查棱块的颜色组合。'  # 拒绝重复块。
    if sum(edge_flips) % 2:  # 正常转动只能产生偶数条棱块翻转。
        return '棱块翻转状态不合法，例如单独翻转一条棱无法通过转动复原。'  # 解释翻棱限制。
    if sum(corner_twists) % 3:  # 全部角块扭转数之和必须是三的倍数。
        return '角块扭转状态不合法，例如单独扭转一个角无法通过转动复原。'  # 解释扭角限制。
    if parity(corner_permutation) != parity(edge_permutation):  # 角块与棱块的交换奇偶性必须一致。
        return '块的位置交换不合法，例如只交换两条棱无法通过转动复原。'  # 解释位置交换限制。
    return None  # 全部约束通过，该状态可以通过正常转动复原。
