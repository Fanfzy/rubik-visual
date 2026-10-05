# ---------- 依赖与配色约定 ----------
import random  # 使用独立随机生成器，避免污染其他模块的随机状态。
from magiccube import Cube  # 复用经过测试的魔方状态和转动实现。
from magiccube.cube_base import Face  # 使用库提供的面枚举读取状态。
FACE_ORDER = 'URFDLB'  # 内部统一采用上、右、前、下、左、后的贴片顺序。
FACE_COLORS = dict(U='Y', R='R', F='B', D='W', L='O', B='G')  # 固定用户指定的六个中心色。
COLOR_NAMES = dict(Y='黄色', R='红色', B='蓝色', W='白色', O='橙色', G='绿色')  # 提供可读的中文颜色名。
SOLVED = ''.join(FACE_COLORS[face] * 9 for face in FACE_ORDER)  # 保存严格的目标状态。
CENTERS = tuple(range(4, 54, 9))  # 每个面的第五个贴片是固定中心。
LIBRARY_ORDER = 'ULFRBD'  # magiccube 构造器使用另一种面顺序。

# ---------- 第三方模型适配 ----------
def library_cube(facelets):  # 将统一状态转换为 magiccube 模型。
    state = ''.join(facelets[FACE_ORDER.index(face) * 9:FACE_ORDER.index(face) * 9 + 9] for face in LIBRARY_ORDER)  # 只改变面的顺序，不改变面内贴片顺序。
    return Cube(3, state, hist=False)  # 关闭历史记录，求解只依赖当前状态。
def read_cube(cube):  # 将第三方状态转换回统一贴片顺序。
    return cube.get([Face[face] for face in FACE_ORDER])  # 通过公共接口读取六个面。

# ---------- 魔方状态和用户编辑 ----------
class CubeState:  # 封装库差异，其他模块只接触这个类。
    def __init__(self, facelets=SOLVED):  # 默认创建指定配色的复原状态。
        self.replace(facelets)  # 统一通过替换入口建立状态。
    @property  # 用只读属性提供当前的 54 个颜色。
    def facelets(self):  # 暴露状态快照，避免外部直接修改库内部数据。
        return read_cube(self._cube)  # 按统一顺序返回颜色字符串。
    def replace(self, facelets):  # 支持编辑中暂时无法复原的颜色状态。
        if len(facelets) != 54 or any(value not in COLOR_NAMES for value in facelets):  # 先检查最基本的格式。
            raise ValueError('需要 54 个色块，且颜色只能是白、黄、蓝、绿、红、橙。')  # 给出明确的输入错误。
        if any(facelets[index] != SOLVED[index] for index in CENTERS):  # 固定六个中心色，防止错误朝向。
            raise ValueError('六个中心色块固定，不能修改。')  # 拒绝更换中心。
        self._cube = library_cube(facelets)  # 将全部贴片一次性写入模型。
    def paint(self, index, value):  # 修改一个非中心贴片的颜色。
        if not 0 <= index < 54 or index in CENTERS or value not in COLOR_NAMES:  # 检查索引、固定中心和颜色值。
            raise ValueError('请选择非中心色块和有效颜色。')  # 让界面能够解释操作被拒绝的原因。
        facelets = list(self.facelets)  # 复制当前状态，不直接修改第三方内部结构。
        facelets[index] = value  # 替换被点击色块的颜色。
        self.replace(''.join(facelets))  # 重建状态，保留其他贴片。
    def move(self, notation):  # 执行标准单面动作，支持模型测试使用 180 度动作。
        if notation not in [face + suffix for face in FACE_ORDER for suffix in ('', "'", '2')]:  # 禁止整块旋转和切片动作进入播放器。
            raise ValueError('只能使用 U、R、F、D、L、B 的单面转动。')  # 保持统一操作语义。
        self._cube.rotate(notation)  # 由 magiccube 执行确定性的贴片置换。
    def is_solved(self):  # 检查是否严格恢复默认配色。
        return self.facelets == SOLVED  # 同时验证贴片和六个面方向。
    def scramble(self, seed=None, count=25):  # 从复原状态生成一个一定合法的打乱。
        generator = random.Random(seed)  # 指定种子时可以完全重现打乱。
        self.replace(SOLVED)  # 即使编辑状态非法，也能重新生成合法魔方。
        moves = []  # 保存本次打乱供学习和问题排查。
        for _ in range(count):  # 执行约定数量的随机面转动。
            choices = [face for face in FACE_ORDER if not moves or face != moves[-1][0]]  # 避免同一面连续转动。
            notation = generator.choice(choices) + generator.choice(('', "'", '2'))  # 随机选择方向和转动次数。
            self.move(notation)  # 通过合法转动生成下一状态。
            moves.append(notation)  # 记录本次动作。
        return moves  # 记录用于显示，不参与求解。
