# ---------- 图形集成测试依赖 ----------
from pathlib import Path  # 保存实际界面的测试截图。
import time as clock  # 等待后台求解线程，并限制等待时长。
import unittest  # 使用统一测试框架输出验收结果。
from unittest.mock import patch  # 给没有桌面指针的离屏缓冲提供测试指针坐标。
from ursina import time, mouse, raycast, Vec3  # 使用真实引擎时间、鼠标命中和三维射线。
from main import create_app  # 测试与成品共用窗口和控件。
from rubik.model import SOLVED  # 以固定六面配色作为最终验收标准。
from rubik.geometry import facelet_geometry, rotated  # 检查真实实体转动后的三维位置。
from rubik.view import render_position  # 使用同一坐标映射进行比较。
from rubik.validation import validate  # 检查界面生成的状态是否合法。

# ---------- 真实三维实体与四按钮集成验收 ----------
class GraphicsTests(unittest.TestCase):  # 创建离屏真实图形缓冲，避免操作用户桌面。
    @classmethod  # 所有测试复用同一个图形上下文。
    def setUpClass(cls):  # 初始化完整成品界面。
        cls.app, cls.ui = create_app('offscreen')  # 使用真实窗口构建器和按钮，只隐藏显示输出。
        cls.output = Path('test_outputs')  # 集中保存截图。
        cls.output.mkdir(exist_ok=True)  # 输出目录可以重复使用。
    @classmethod  # 测试全部结束后统一释放资源。
    def tearDownClass(cls):  # 关闭后台线程和图形缓冲。
        cls.ui.close()  # 清理求解线程。
        cls.app.destroy()  # 释放 OpenGL 资源。
    def setUp(self):  # 每个测试从已复原状态开始。
        self.ui.player.active = False  # 清除前一案例可能留下的动画标志。
        self.ui.player.invalidate()  # 清除解法与连续播放模式。
        self.ui.select_auto_speed(1)  # 每个案例恢复默认一倍，避免档位选择相互影响。
        self.ui.cube.replace(SOLVED)  # 恢复固定的初始颜色。
        self.ui.view.finish(SOLVED)  # 复位真实三维实体。
        self.ui.view.root.rotation = Vec3(0, 0, 0)  # 恢复默认观察角度。
        self.ui.editing, self.ui.single_down = False, False  # 清除编辑和长按模式。
        self.ui.palette_root.enabled = False  # 隐藏选色面板。
        self.ui.say('准备就绪，点击随机打乱开始体验。')  # 恢复正常提示。
        time.dt = .05  # 使用可重复的虚拟帧间隔。
    def test_09_missing_font_reports_setup(self):  # 自定义字体路径错误时应在创建第二个窗口前明确失败。
        with patch.dict('os.environ', {'RUBIK_FONT': str(self.output / 'missing_font.ttf')}):  # 模拟使用者输入不存在的字体文件。
            with self.assertRaisesRegex(RuntimeError, 'Chinese font not found'):  # 使用者应获得安装说明提示而不是空白界面。
                create_app('offscreen')  # 字体检查发生在引擎窗口创建之前。
    def screenshot(self, name):  # 保存真实的渲染结果用于视觉验收。
        for _ in range(3):  # 确保几何、字体和缓冲都已更新。
            self.app.graphicsEngine.renderFrame()  # 每次绘制一帧真实图像。
        self.app.win.saveScreenshot(str(self.output / name))  # 保存 PNG 到项目输出目录。
    def wait_solution(self):  # 等待后台线程，并持续运行同一个界面更新入口。
        deadline = clock.monotonic() + 5  # 求解等待有明确超时，不允许测试挂起。
        while self.ui.future is not None and clock.monotonic() < deadline:  # 任务未完成时等待下一次检查。
            self.ui.update()  # 主线程完成后台结果接收与首次播放。
            clock.sleep(.005)  # 将执行权交给求解线程。
        self.assertIsNone(self.ui.future)  # 如果线程未及时结束，测试失败。
        self.assertFalse(self.ui.error, self.ui.notice)  # 后台异常不得被普通状态掩盖。
    def advance(self, frames):  # 不依赖真实等待时间地推进动画。
        for _ in range(frames):  # 每帧使用真实更新逻辑。
            self.ui.update()  # 控件、状态、动画一起更新。
    def test_01_initial_layout(self):  # 核对界面结构和默认配色。
        self.assertEqual(len(self.ui.buttons), 4)  # 只能有四个主要操作按钮。
        self.assertEqual(len(self.ui.view.stickers), 54)  # 六个面必须完整绘制。
        self.assertEqual(len(self.ui.view.bodies), 26)  # 外层主体数量应正确。
        self.screenshot('app_initial.png')  # 保存成品初始画面。
    def test_02_rendered_turns_match_model(self):  # 检查真实三维转动，而不只测试数学函数。
        for face in 'URFDLB':  # 逐一覆盖六个面。
            for suffix in ('', "'"):  # 两个转动方向都需要验证。
                notation = face + suffix  # 构造标准 90 度动作。
                self.ui.view.begin(notation)  # 让真实显示层选择正确的一层。
                self.ui.view.pose(1.0)  # 将动画推进到转动结束前的实际姿态。
                for index, tile in enumerate(self.ui.view.stickers):  # 检查所有受影响和未受影响的色块。
                    position, normal = rotated(*facelet_geometry(index), notation)  # 计算模型约定的目标几何。
                    expected = render_position(position) + render_position(normal) * .502  # 计算贴片中心的目标渲染位置。
                    self.assertLess((tile.world_position - expected).length(), .0001, (notation, index))  # 检查引擎实体与模型严格一致。
                self.ui.view.finish(SOLVED)  # 重置主体，准备下一个转动案例。
    def test_03_ray_picking_and_editing(self):  # 检查碰撞盒和真实输入分发。
        from ursina import camera  # 使用实际观察镜头的位置发射测试射线。
        target = self.ui.view.stickers[20]  # 选择默认视角下清楚可见的前面右上角。
        hit = raycast(camera.world_position, (target.world_position - camera.world_position).normalized(), distance=30)  # 使用引擎的真实碰撞检测。
        self.assertEqual(hit.entity, target)  # 鼠标射线必须能命中对应色块。
        self.ui.buttons[0].on_click()  # 通过真实按钮进入编辑模式。
        mouse.hovered_entity = self.ui.view.stickers[4]  # 模拟指针命中固定中心。
        self.ui.input('left mouse down')  # 使用实际界面的鼠标事件入口。
        self.assertIsNone(self.ui.view.selected)  # 固定中心不能成为涂色目标。
        mouse.hovered_entity = target  # 模拟指针命中可编辑贴片。
        self.ui.input('left mouse down')  # 打开该色块的选色面板。
        self.assertTrue(self.ui.palette_root.enabled)  # 六种颜色应该可供点击。
        self.screenshot('app_edit.png')  # 检查选色面板及目标位置说明的实际显示。
        self.ui.palette_buttons['G'].on_click()  # 使用真实绿色按钮修改选中色块。
        self.assertEqual(self.ui.cube.facelets[20], 'G')  # 点击结果必须进入内部模型。
        self.ui.buttons[0].on_click()  # 尝试结束非法颜色输入。
        self.assertTrue(self.ui.editing)  # 非法状态保留编辑，允许用户修正。
        self.assertTrue(self.ui.error)  # 显示明确的输入错误。
        self.screenshot('app_invalid_input.png')  # 保存非法输入提示的实际画面。
        self.ui.choose_sticker(20)  # 再次选择同一个色块。
        self.ui.palette_buttons['B'].on_click()  # 修正回蓝色。
        self.ui.buttons[0].on_click()  # 再次结束编辑。
        self.assertFalse(self.ui.editing)  # 正确输入应正常退出编辑。
        self.assertEqual(self.ui.cube.facelets, SOLVED)  # 颜色修正不能影响其他贴片。
    def test_04_auto_pause_single_resume(self):  # 检查自动与单步之间能否共用同一队列。
        self.ui.buttons[1].on_click()  # 使用真实随机打乱按钮。
        self.assertIsNone(validate(self.ui.cube.facelets))  # 生成的状态必须合法。
        self.ui.buttons[2].on_click()  # 使用真实自动复原按钮。
        self.wait_solution()  # 由界面主线程接收层先法结果。
        self.ui.buttons[2].on_click()  # 在第一步动画期间点击暂停。
        self.advance(10)  # 当前转动完成后应停下。
        self.assertEqual(self.ui.player.index, 1)  # 暂停必须停在一个完整动作之后。
        plan = self.ui.player.steps  # 保存队列引用验证不会重复求解。
        self.ui.buttons[3].on_click()  # 点击单步。
        self.ui.input('left mouse up')  # 立即释放按钮，只执行一次。
        self.advance(25)  # 等待超过一秒，观察有没有多执行动作。
        self.assertEqual(self.ui.player.index, 2)  # 单击只能再执行一次 90 度。
        self.assertIs(self.ui.player.steps, plan)  # 暂停与单步共用原来的解法。
        self.screenshot('app_solving.png')  # 保存教学阶段与进度显示。
        self.ui.buttons[2].on_click()  # 再次点击自动按钮继续。
        self.advance(len(plan) * 25)  # 在可重复虚拟时间里播放完整解法。
        self.assertTrue(self.ui.cube.is_solved())  # 自动与单步混合使用仍然正确复原。
        self.assertFalse(self.ui.player.auto)  # 完成后自动停止。
    def test_05_hold_and_release(self):  # 检查单步长按以及在按钮外松开。
        self.ui.cube.scramble(seed=321)  # 建立有多步解法的可复现输入，不能用一步就复原的案例测试长按。
        self.ui.view.sync(self.ui.cube.facelets)  # 让画面与当前模型同步。
        self.ui.buttons[3].on_click()  # 按住单步按钮，不立即释放。
        self.wait_solution()  # 等待第一份单步解法。
        self.advance(30)  # 按住超过一秒，应该开始后续动作。
        self.assertGreaterEqual(self.ui.player.index, 2)  # 长按不应该只执行首次点击。
        self.ui.input('left mouse up')  # 模拟在任意位置松开鼠标。
        self.advance(10)  # 让已经开始的动画完整结束。
        stopped = self.ui.player.index  # 记录松开后的稳定动作数。
        self.advance(40)  # 继续等待两秒。
        self.assertEqual(self.ui.player.index, stopped)  # 松开后不能继续自动转动。
    def test_06_view_rotation_keeps_state(self):  # 观察整个魔方不能改变求解状态。
        state = self.ui.cube.facelets  # 保存初始状态。
        self.ui.view.orbit(.3, -.2)  # 执行真实观察节点旋转。
        self.assertEqual(self.ui.cube.facelets, state)  # 颜色位置必须保持不变。
        self.assertNotEqual(self.ui.view.root.rotation, Vec3(0, 0, 0))  # 但画面中的观察角度确实变化。
        self.assertAlmostEqual(self.ui.view.root.rotation_y, -54, places=4)  # 横向拖动必须与原来的正向旋转相反。
        self.assertAlmostEqual(self.ui.view.root.rotation_x, -36, places=4)  # 竖向拖动也必须与原来反向。
        self.screenshot('app_rotated.png')  # 保存能看到其他颜色面的观察画面。
    def test_08_speed_selector_and_fast_solve(self):  # 三个速度按钮必须真正作用于自动复原。
        self.assertEqual(set(self.ui.speed_buttons), {1, 5, 10})  # 界面明确提供三档选择。
        self.assertEqual(self.ui.player.auto_speed, 1)  # 新窗口默认一倍。
        self.ui.speed_buttons[5].on_click()  # 通过真实按钮选择五倍。
        self.assertEqual(self.ui.player.auto_speed, 5)  # 选择必须进入播放器。
        self.screenshot('app_speed_5x.png')  # 保存速度选择器的真实界面。
        self.ui.speed_buttons[10].on_click()  # 通过真实按钮选择十倍。
        self.ui.cube.scramble(seed=83)  # 使用可重复的合法状态进行快速复原。
        self.ui.view.sync(self.ui.cube.facelets)  # 让画面与输入状态一致。
        self.ui.buttons[2].on_click()  # 启动真正的自动复原入口。
        self.wait_solution()  # 等待状态求解和首步播放。
        self.ui.buttons[2].on_click()  # 十倍模式中仍然可以暂停。
        self.advance(4)  # 等待当前 90 度动作完成。
        stopped = self.ui.player.index  # 保存暂停后的完整动作数。
        self.advance(10)  # 暂停期间速度档位不能让动作继续。
        self.assertEqual(self.ui.player.index, stopped)  # 确认暂停有效。
        self.ui.buttons[2].on_click()  # 从同一队列继续十倍播放。
        self.advance(len(self.ui.player.steps) * 3)  # 每个十倍动作只有 0.1 秒，三帧足够覆盖。
        self.assertTrue(self.ui.cube.is_solved())  # 快速模式必须完整复原。
        self.assertEqual(self.ui.player.auto_speed, 10)  # 完成后保留用户选择的速度。
    @patch.object(type(mouse), 'x', new=property(lambda instance: 0.0))  # 离屏缓冲没有系统鼠标接口，只替代指针的横坐标来源。
    @patch.object(type(mouse), 'y', new=property(lambda instance: 0.0))  # 纵坐标同样固定，按钮回调和事件分发仍使用真实引擎。
    def test_07_engine_mouse_events(self):  # 检查从引擎事件到真实按钮回调的完整路径。
        mouse.hovered_entity = self.ui.buttons[0]  # 将鼠标命中目标设为编辑按钮。
        self.app.input('mouse1')  # 使用引擎原生鼠标按下入口，不直接调用按钮函数。
        self.app.input_up('mouse1')  # 使用引擎原生鼠标松开入口。
        self.assertTrue(self.ui.editing)  # 完整事件路径必须真正进入编辑模式。
        mouse.hovered_entity = self.ui.view.stickers[18]  # 命中前面左上角色块。
        self.app.input('mouse1')  # 使用同一原生事件打开选色面板。
        self.app.input_up('mouse1')  # 结束一次点击。
        self.assertEqual(self.ui.view.selected, 18)  # 输入分发必须选择正确的贴片。
        mouse.hovered_entity = self.ui.palette_buttons['B']  # 命中选色面板的蓝色按钮。
        self.app.input('mouse1')  # 使用完整事件路径写入所选颜色。
        self.app.input_up('mouse1')  # 鼠标释放也会清除长按状态。
        self.assertIsNone(self.ui.view.selected)  # 完成颜色选择后应收起选择。
        self.assertEqual(self.ui.cube.facelets, SOLVED)  # 选择原颜色不能改变其他色块。
        self.app.input('mouse3')  # 使用引擎右键事件开始观察拖动。
        self.assertTrue(self.ui.dragging)  # 右键拖动入口必须正确响应。
        self.app.input_up('mouse3')  # 使用引擎松开事件结束拖动。
        self.assertFalse(self.ui.dragging)  # 松开后不能残留拖动标志。

# ---------- 直接运行入口 ----------
if __name__ == '__main__':  # 图形测试单独运行，不混入无窗口测试。
    unittest.main(verbosity=2)  # 输出所有图形集成验收项。
