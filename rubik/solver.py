# ---------- 求解器依赖和动作数据 ----------
from dataclasses import dataclass  # 使用不可变数据记录每个教学动作。
from magiccube import BasicSolver  # 使用初学者层先法，不使用两阶段算法。
from rubik.model import CubeState, SOLVED, FACE_ORDER, FACE_COLORS, library_cube, read_cube  # 导入状态适配接口。
from rubik.validation import validate  # 在求解前先检查物理合法性。
@dataclass(frozen=True)  # 一个生成后的步骤不会被其他模块意外修改。
class SolutionStep:  # 用统一的数据结构连接算法与播放器。
    move: str  # 单面 90 度动作，例如 R 或 R'。
    stage: str  # 当前层先法阶段的中文说明。
STAGE_NAMES = {'stage_white_cross': '1 / 7  白色底面十字', 'stage_white_corner': '2 / 7  白色底层角块', 'stage_2nd_layer': '3 / 7  中间层棱块', 'stage_top_cross': '4 / 7  黄色顶面十字', 'stage_order_top_cross': '5 / 7  顶层棱块归位', 'stage_order_top_corners': '6 / 7  顶层角块归位', 'stage_turn_top_corners': '7 / 7  顶层角块转向'}  # 与实际使用的层先法阶段一一对应。

# ---------- 保留教学阶段的第三方适配 ----------
class TeachingSolver(BasicSolver):  # 只扩展阶段记录，复用第三方的算法规则。
    def __init__(self, cube):  # 在魔方副本上建立求解器。
        self.stage_actions = []  # 收集原始动作与对应阶段。
        super().__init__(cube)  # 初始化初学者层先法的各阶段。
    def _solve_pattern_stage(self, stage):  # 适配固定版本 1.2.0 的阶段扩展点。
        actions = super()._solve_pattern_stage(stage)  # 执行该阶段，得到实际动作。
        label = next((title for prefix, title in STAGE_NAMES.items() if stage.name.startswith(prefix)), '调整算法参考朝向')  # 把算法内部阶段转换为教学说明。
        self.stage_actions.extend((action, label) for action in actions)  # 保留每个动作的阶段，不跨阶段压缩公式。
        return actions  # 保持基础求解器原有返回协议。

# ---------- 固定朝向、拆分 180 度并验证解法 ----------
def solve_layer_by_layer(facelets):  # 根据当前 54 个颜色计算完整层先法。
    error = validate(facelets)  # 在进入算法之前检查合法性。
    if error:  # 对错误涂色立即终止求解。
        raise ValueError(error)  # 让界面展示可修正的原因。
    if facelets == SOLVED:  # 已经复原时不生成多余公式。
        return []  # 播放器可以直接显示完成状态。
    solver = TeachingSolver(library_cube(facelets))  # 始终在独立模型上求解，保持当前画面不变。
    solver.solve(optimize=False)  # 保留原始阶段，避免跨阶段动作优化影响教学。
    orientation = library_cube(SOLVED)  # 用一个虚拟复原魔方跟踪算法内部的整块旋转。
    reverse_colors = {value: face for face, value in FACE_COLORS.items()}  # 建立中心颜色到固定面的映射。
    steps = []  # 存放最终可以直接播放的单面动作。
    for action, label in solver.stage_actions:  # 按实际计算顺序处理全部动作。
        if action.type.is_cube_rotation():  # 算法可能为了套公式而旋转整个参考魔方。
            orientation.rotate([action])  # 只更新虚拟参考朝向，不改变用户观察角度。
            continue  # 整块参考旋转不是用户的一次复原动作。
        local_face = action.type.value  # 获取算法当前参考系中的转动面。
        if local_face not in FACE_ORDER or action.wide or action.layer != 1:  # 明确拒绝当前界面不支持的算法动作。
            raise RuntimeError('层先法返回了不支持的切片动作。')  # 防止第三方版本变化被静默忽略。
        center = read_cube(orientation)[FACE_ORDER.index(local_face) * 9 + 4]  # 找出这个面的中心在原参考系中的身份。
        move = reverse_colors[center] + ("'" if action.is_reversed else '')  # 正常旋转保持顺逆时针，转换为固定朝向的动作。
        steps.extend(SolutionStep(move, label) for _ in range(action.count))  # 将 180 度动作拆成两次 90 度。
    check = CubeState(facelets)  # 创建另一份副本验证最终输出。
    for step in steps:  # 对实际将播放的动作进行完整重放。
        check.move(step.move)  # 只执行单面动作，不依赖算法内部状态。
    if not check.is_solved():  # 如果参考朝向转换出现问题，禁止播放错误结果。
        raise RuntimeError('复原步骤校验失败，未开始播放。')  # 确保求解输出确实恢复固定配色。
    return steps  # 返回供自动和单步模式共用的步骤队列。
