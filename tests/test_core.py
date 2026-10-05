# ---------- 标准库和项目导入 ----------
import os  # 读取随机测试数量，允许快速检查和完整验收使用同一套测试。
import unittest  # 使用 Python 自带的测试框架，避免额外测试依赖。
from rubik.model import CubeState, SOLVED, FACE_COLORS  # 导入状态模型和默认配色。
from rubik.validation import validate  # 导入可复原性检查入口。
from rubik.solver import solve_layer_by_layer  # 导入层先法求解入口。
from rubik.geometry import facelet_geometry, rotated  # 导入画面与模型共用的几何约定。
from rubik.validation import CORNERS  # 使用真实角块组合检查顶层归位阶段。

# ---------- 模型与输入合法性测试 ----------
class ModelTests(unittest.TestCase):  # 集中测试不依赖界面的魔方规则。
    def test_default_orientation(self):  # 检查用户指定的六个面颜色。
        self.assertEqual(FACE_COLORS, dict(U='Y', R='R', F='B', D='W', L='O', B='G'))  # 固定白底黄顶蓝前左橙右红。
        self.assertTrue(CubeState().is_solved())  # 默认魔方必须已经复原。
        self.assertIsNone(validate(SOLVED))  # 默认状态必须合法。
    def test_move_and_inverse(self):  # 检查每个动作都有正确的逆动作。
        for face in 'URFDLB':  # 遍历全部六个可转动面。
            cube = CubeState()  # 每个案例使用独立状态。
            cube.move(face)  # 执行顺时针转动。
            cube.move(face + "'")  # 执行同一面的逆时针转动。
            self.assertEqual(cube.facelets, SOLVED)  # 两个动作应相互抵消。
    def test_four_quarter_turns(self):  # 检查一整圈转动保持原状。
        for face in 'URFDLB':  # 每个面都要接受同样的检查。
            cube = CubeState()  # 从复原状态开始。
            for _ in range(4):  # 四次 90 度等于一圈。
                cube.move(face)  # 执行一次四分之一圈转动。
            self.assertEqual(cube.facelets, SOLVED)  # 所有色块应回到原位。
    def test_geometry_matches_model(self):  # 防止模型正确但动画转向相反。
        geometry = [facelet_geometry(index) for index in range(54)]  # 获取全部贴片的位置和法向量。
        for face in 'URFDLB':  # 分别检查六个面的动画置换。
            cube = CubeState()  # 初始化参考模型。
            cube.move(face)  # 让真实模型执行一次动作。
            expected = list(SOLVED)  # 建立几何规则计算的结果。
            for index, (position, normal) in enumerate(geometry):  # 遍历原来的全部色块。
                destination = geometry.index(rotated(position, normal, face))  # 根据旋转规则确定目的位置。
                expected[destination] = SOLVED[index]  # 把原颜色放到新的位置。
            self.assertEqual(cube.facelets, ''.join(expected), face)  # 模型和显示必须完全一致。
    def test_scramble_reproducible_and_legal(self):  # 检查随机打乱可复现且合法。
        first, second = CubeState(), CubeState()  # 创建两个独立魔方。
        self.assertEqual(first.scramble(seed=123), second.scramble(seed=123))  # 同种子必须生成同样动作。
        self.assertEqual(first.facelets, second.facelets)  # 最终状态也必须一致。
        self.assertIsNone(validate(first.facelets))  # 正常转动生成的状态必须合法。
    def test_centers_locked(self):  # 检查不能修改中心块。
        with self.assertRaises(ValueError):  # 固定中心时应明确拒绝修改。
            CubeState().paint(4, 'B')  # 尝试把顶面中心涂成蓝色。
    def test_impossible_states(self):  # 颜色数量正确也可能无法复原。
        cases = [(5, 10), (8, 9, 20), (5, 7, 10, 19)]  # 分别构造翻棱、扭角和仅交换两条棱的情况。
        for indices in cases:  # 遍历三种典型非法状态。
            stickers = list(SOLVED)  # 从一个合法魔方复制贴片颜色。
            colors = [stickers[index] for index in indices]  # 保存待交换的颜色。
            shifted = colors[1:] + colors[:1] if len(indices) != 4 else [colors[1], colors[0], colors[3], colors[2]]  # 循环扭转或成对交换。
            for index, value in zip(indices, shifted):  # 将错误颜色写回对应位置。
                stickers[index] = value  # 保持每种颜色总数不变。
            self.assertIsNotNone(validate(''.join(stickers)), indices)  # 可复原性检查必须发现错误。

# ---------- 层先法求解测试 ----------
class SolverTests(unittest.TestCase):  # 集中检查求解器的输入、结果和阶段信息。
    def test_solved_cube(self):  # 已复原的魔方不应产生多余动作。
        self.assertEqual(solve_layer_by_layer(SOLVED), [])  # 直接返回空步骤列表。
    def test_manual_state_without_scramble_history(self):  # 求解必须根据当前色块，而不是倒放打乱记录。
        original = CubeState()  # 创建并打乱一个真实状态。
        original.scramble(seed=99)  # 使用固定种子便于重现失败。
        supplied = original.facelets  # 仅把 54 个颜色传给求解器。
        steps = solve_layer_by_layer(supplied)  # 根据无历史的状态计算解法。
        self.assertEqual(original.facelets, supplied)  # 求解时不能修改界面上的状态。
        for step in steps:  # 按单步顺序重放完整解法。
            self.assertIn(step.move, [face + suffix for face in 'URFDLB' for suffix in ('', "'")])  # 每步只能是单面 90 度。
            self.assertTrue(step.stage)  # 每一步应带有教学阶段说明。
            original.move(step.move)  # 执行当前动作。
        self.assertTrue(original.is_solved())  # 重放结束后必须完全复原。
    def test_invalid_input_rejected(self):  # 非法状态不能进入可能无法结束的求解流程。
        with self.assertRaises(ValueError):  # 对不完整输入应立即抛出明确错误。
            solve_layer_by_layer('Y' * 54)  # 使用颜色数量错误的状态。
    def test_layer_milestones(self):  # 不仅检查最后复原，还检查算法确实按层先法推进。
        for seed in (7, 23, 82, 314, 999):  # 选取可重复的多个完整解法。
            cube = CubeState()  # 从默认配色开始。
            cube.scramble(seed=seed)  # 建立合法随机输入。
            steps = solve_layer_by_layer(cube.facelets)  # 计算保留阶段说明的解法。
            for index, step in enumerate(steps):  # 逐步重放并观察阶段边界。
                cube.move(step.move)  # 提交该动作。
                if index + 1 < len(steps) and steps[index + 1].stage == step.stage:  # 同一个阶段没有结束时无需检查完整里程碑。
                    continue  # 等待该阶段最后一步。
                stage = int(step.stage[0])  # 从教学标签读取阶段编号。
                state = cube.facelets  # 获取本阶段结束时的颜色快照。
                cross = (28, 30, 32, 34, 16, 25, 43, 52)  # 底面十字与四个侧面底部对应贴片。
                self.assertTrue(all(state[position] == SOLVED[position] for position in cross), (seed, stage, '底面十字'))  # 完成十字后所有后续阶段都必须保持它。
                if stage >= 2:  # 完成底层角块以后验证整层。
                    bottom = tuple(range(27, 36)) + tuple(base + offset for base in (9, 18, 36, 45) for offset in (6, 7, 8))  # 包含底面与侧面的底层行。
                    self.assertTrue(all(state[position] == SOLVED[position] for position in bottom), (seed, stage, '底层'))  # 后续公式不能破坏已复原底层。
                if stage >= 3:  # 完成中层以后验证前两层。
                    middle = tuple(base + offset for base in (9, 18, 36, 45) for offset in (3, 4, 5))  # 四个侧面的中间行。
                    self.assertTrue(all(state[position] == SOLVED[position] for position in middle), (seed, stage, '中层'))  # 后续顶层公式保持前两层。
                if stage >= 4:  # 顶面十字阶段结束后验证黄色朝向。
                    self.assertTrue(all(state[position] == 'Y' for position in (1, 3, 5, 7)), (seed, stage, '顶面十字'))  # 四条顶层棱的黄色面必须朝上。
                if stage >= 5:  # 顶层棱块归位后检查侧面颜色对齐。
                    self.assertTrue(all(state[position] == SOLVED[position] for position in (10, 19, 37, 46)), (seed, stage, '顶层棱块'))  # 顶层棱位置与中心色一致。
                if stage >= 6:  # 角块归位允许朝向尚未修正，但身份必须正确。
                    self.assertTrue(all(set(state[position] for position in corner) == set(SOLVED[position] for position in corner) for corner in CORNERS[:4]), (seed, stage, '顶层角块'))  # 按颜色集合验证四个顶层角块位置。
                if stage == 7:  # 最后转向完成后验证完整状态。
                    self.assertEqual(state, SOLVED)  # 全部六面必须恢复固定配色。
    def test_random_scrambles(self):  # 使用完整随机回归验收层先法。
        count = int(os.environ.get('RUBIK_TEST_CASES', '1000'))  # 默认测试一千个打乱案例。
        for seed in range(count):  # 使用确定性的种子序列，失败后可以复现。
            with self.subTest(seed=seed):  # 将失败信息关联到具体种子。
                cube = CubeState()  # 每个案例从复原状态开始。
                cube.scramble(seed=seed)  # 执行合法随机转动。
                self.assertIsNone(validate(cube.facelets))  # 检查合法性模块不会误报正常状态。
                steps = solve_layer_by_layer(cube.facelets)  # 计算真实的层先法解法。
                self.assertLess(len(steps), 1000)  # 为异常重复动作设置合理上限。
                for step in steps:  # 逐个执行求解动作。
                    cube.move(step.move)  # 每次执行一个 90 度动作。
                self.assertEqual(cube.facelets, SOLVED)  # 不仅同色成面，还必须恢复固定配色。

# ---------- 直接运行入口 ----------
if __name__ == '__main__':  # 允许直接运行，也允许测试发现器加载。
    unittest.main(verbosity=2)  # 输出每项测试的名称和结果。
