# ---------- 播放器测试依赖和替代显示层 ----------
import unittest  # 使用自带框架测试交互时序。
from rubik.model import CubeState, SOLVED  # 使用真实魔方模型检查状态。
from rubik.solver import SolutionStep  # 使用与成品完全一致的动作结构。
from rubik.playback import Playback  # 测试不依赖图形设备的播放器。
class FakeView:  # 用简单记录器替代三维实体。
    def __init__(self):  # 初始化动作记录。
        self.started, self.finished = [], []  # 保存所有开始和结束事件。
    def begin(self, notation):  # 接收一次动画开始。
        self.started.append(notation)  # 检查有没有重复启动。
    def pose(self, progress):  # 接收动画中间帧。
        assert 0 <= progress <= 1  # 任何中间进度都不能越界。
    def finish(self, state):  # 接收提交后的状态。
        self.finished.append(state)  # 保存可验证的颜色快照。

# ---------- 单步、暂停、长按和队列失效测试 ----------
class PlaybackTests(unittest.TestCase):  # 覆盖容易导致状态错乱的交互组合。
    def setUp(self):  # 每项测试使用独立魔方、显示记录器和播放器。
        self.cube, self.view = CubeState(), FakeView()  # 创建测试对象。
        self.player = Playback(self.cube, self.view)  # 使用真实的 0.3 秒动画和 1 秒节奏。
        self.player.set_plan([SolutionStep('R', '测试'), SolutionStep("R'", '测试')])  # 两步结束后应恢复原状。
    def test_single_click_and_reentry(self):  # 快速重复点击不能造成动作重叠。
        self.assertTrue(self.player.request_step())  # 第一次点击成功启动动作。
        self.assertFalse(self.player.request_step())  # 动画中第二次点击被拒绝。
        self.assertEqual(self.cube.facelets, SOLVED)  # 中途不得提前修改模型。
        self.player.tick(.3)  # 推进到单步完成。
        self.assertEqual(self.player.index, 1)  # 只能完成一个动作。
        self.player.tick(5)  # 无自动和长按时等待不会继续转动。
        self.assertEqual(self.player.index, 1)  # 保持在第一步。
        self.assertTrue(self.player.request_step())  # 下一次点击可以执行第二步。
        self.player.tick(.3)  # 完成逆动作。
        self.assertTrue(self.cube.is_solved())  # 两步恢复原状。
    def test_auto_pause_and_resume(self):  # 暂停应完成当前转动，再保持静止。
        self.player.auto = True  # 开启自动连续模式。
        self.player.tick(.01)  # 启动第一步。
        self.player.auto = False  # 在动画中暂停。
        self.player.tick(.3)  # 完成当前单步。
        self.player.tick(3)  # 暂停后无论等待多久都不开始下一步。
        self.assertEqual(self.player.index, 1)  # 验证暂停位置。
        self.player.auto = True  # 从同一队列继续播放。
        self.player.tick(.01)  # 启动第二步。
        self.player.tick(.3)  # 提交第二步。
        self.assertTrue(self.cube.is_solved())  # 继续后应正常完成。
        self.assertFalse(self.player.auto)  # 完成后自动关闭播放。
    def test_hold_release_and_interval(self):  # 长按使用每秒一次的节奏，松开停止后续转动。
        self.player.hold = True  # 模拟按住单步按钮。
        self.player.request_step()  # 按下立即执行第一步。
        self.player.tick(.3)  # 完成当前动画。
        self.player.tick(.69)  # 动作间隔尚未到达。
        self.assertFalse(self.player.active)  # 此时不能提前启动第二步。
        self.player.hold = False  # 在下一步之前松开鼠标。
        self.player.tick(5)  # 等待足够久也不会继续。
        self.assertEqual(self.player.index, 1)  # 保持单步位置。
    def test_edit_invalidates_old_queue(self):  # 编辑之后必须丢弃旧求解结果。
        self.player.invalidate()  # 模拟进入编辑或执行新打乱。
        self.assertEqual(self.player.steps, [])  # 队列完全清空。
        self.assertFalse(self.player.request_step())  # 不会播放过时步骤。
    def test_changes_blocked_mid_animation(self):  # 不能在半层状态下修改魔方。
        self.player.request_step()  # 启动转动。
        with self.assertRaises(RuntimeError):  # 操作必须被明确拒绝。
            self.player.invalidate()  # 模拟正在转动时试图重置队列。
    def test_auto_speed_choices_and_exact_interval(self):  # 验证三档速度都同时缩短动画和步间等待。
        for speed in (1, 5, 10):  # 覆盖用户要求的所有速度选项。
            with self.subTest(speed=speed):  # 失败时显示具体档位。
                cube, view = CubeState(), FakeView()  # 每档速度使用独立的模型和事件记录。
                player = Playback(cube, view)  # 使用默认一秒一步的基础节奏。
                player.set_plan([SolutionStep('R', '测试'), SolutionStep("R'", '测试')])  # 两个动作可检查间隔与最后复原。
                player.set_auto_speed(speed)  # 设置自动播放倍率。
                player.auto = True  # 倍率只能作用于自动模式。
                player.request_step()  # 第一步从虚拟时间零开始。
                player.tick(.299 / speed)  # 在缩放后的动画结束前停下。
                self.assertEqual(player.index, 0)  # 未完整转过 90 度时模型保持不变。
                player.tick(.700 / speed)  # 总时间到达 0.999 倍基础间隔。
                self.assertEqual(player.index, 1)  # 第一步完成，但第二步不应该提前开始。
                self.assertEqual(len(view.started), 1)  # 确认步间等待也严格缩放。
                player.tick(.002 / speed)  # 跨过下一次动作应开始的时刻。
                self.assertEqual(len(view.started), 2)  # 新一步按该档速度准时开始。
                player.tick(.3 / speed)  # 完成剩余逆动作。
                self.assertTrue(cube.is_solved())  # 加速不能改变最终结果。
    def test_auto_speed_does_not_accelerate_manual_hold(self):  # 选择十倍后单步与长按仍然保持一倍。
        self.player.set_auto_speed(10)  # 预先选择最快的自动速度。
        self.player.hold = True  # 模拟按住单步按钮，自动标志仍为关闭。
        self.player.request_step()  # 手动启动第一步。
        self.player.tick(.29)  # 手动动画尚未达到原来的 0.3 秒。
        self.assertEqual(self.player.index, 0)  # 自动档位不能提前提交手动动作。
        self.player.tick(.01)  # 完成手动动作。
        self.player.tick(.69)  # 长按的步间等待仍是原来的 0.7 秒。
        self.assertEqual(len(self.view.started), 1)  # 十倍选择不能让长按提前执行下一步。
        self.player.tick(.02)  # 跨过原来的一秒动作间隔。
        self.assertEqual(len(self.view.started), 2)  # 长按继续正常执行下一步。
    def test_speed_change_preserves_current_animation(self):  # 动画中切换速度不能跳过半层姿态或重复提交。
        self.player.auto = True  # 开始一倍自动播放。
        self.player.request_step()  # 启动第一个 90 度动作。
        self.player.tick(.15)  # 先转到动画中间。
        self.player.set_auto_speed(10)  # 动画中选择十倍，后续动作使用新档位。
        self.player.tick(.14)  # 当前动作保持开始时的速度，平滑完成。
        self.assertEqual(self.player.index, 0)  # 不得突然跳到完整转动。
        self.player.tick(.01)  # 当前动作正常完成一次。
        self.assertEqual(self.player.index, 1)  # 只提交一个动作。
        self.player.tick(.071)  # 下一次等待按十倍速度结束。
        self.assertEqual(len(self.view.started), 2)  # 新倍率应用到后续动作。
    def test_speed_is_independent_of_frame_boundaries(self):  # 60 帧下也要达到真实的五倍或十倍节奏。
        for speed in (1, 5, 10):  # 不能只用恰好对齐动画边界的时间测试。
            view = FakeView()  # 记录实际开始的动作数。
            player = Playback(CubeState(), view)  # 建立独立播放器。
            player.set_plan([SolutionStep('R', '测试') for _ in range(40)])  # 留足步骤，避免提前完成影响统计。
            player.set_auto_speed(speed)  # 指定自动速度。
            player.auto = True  # 开启自动播放。
            player.request_step()  # 时间零立即开始第一步。
            for _ in range(60):  # 模拟一秒内的六十帧。
                player.tick(1 / 60)  # 使用常见帧率，动画结束通常发生在两帧之间。
            self.assertEqual(len(view.started), speed + 1, speed)  # 时间零和每个完整间隔各启动一个动作。
    def test_unsupported_speed_rejected(self):  # 界面和播放器只接受三种约定档位。
        with self.assertRaises(ValueError):  # 不允许出现未知或负数的时间倍率。
            self.player.set_auto_speed(2)  # 用不存在的两倍速度测试输入检查。

# ---------- 直接运行入口 ----------
if __name__ == '__main__':  # 支持独立运行该测试模块。
    unittest.main(verbosity=2)  # 输出每个交互测试的结果。
