# ---------- 界面依赖与公共样式 ----------
from concurrent.futures import ThreadPoolExecutor  # 把求解计算放到后台，保持窗口响应。
from collections import Counter  # 在编辑时显示六色数量。
import textwrap  # 给较长提示自动换行。
from ursina import Entity, Button, Text, camera, color, mouse, time  # 导入界面、输入和帧时间组件。
from rubik.model import CubeState, CENTERS, FACE_ORDER, COLOR_NAMES  # 导入模型与固定中心约定。
from rubik.view import CubeView, PALETTE  # 导入三维显示与六色视觉配色。
from rubik.playback import Playback  # 自动和单步模式共用同一个播放器。
from rubik.solver import solve_layer_by_layer  # 导入真正的层先法求解器。
from rubik.validation import validate  # 编辑结束及求解前检查状态是否合法。
INK = color.rgb32(235, 241, 252)  # 主要文字使用高对比浅色。
MUTED = color.rgb32(139, 156, 184)  # 辅助信息使用较柔和的文字色。
SURFACE = color.rgb32(25, 36, 54)  # 信息卡片和次要按钮的背景。
ACCENT = color.rgb32(58, 155, 218)  # 主操作使用蓝色强调。
FACE_NAMES = dict(U='顶面', R='右面', F='前面', D='底面', L='左面', B='后面')  # 使用固定参考系解释公式。
def label(text, x, y, scale=.75, ink=INK, parent=camera.ui, origin=(-.5, .5)):  # 统一文字尺寸和颜色。
    return Text(text=text, parent=parent, x=x, y=y, z=-.05, scale=scale, color=ink, origin=origin, use_tags=False)  # 将文字放在卡片前方，标准文字不使用富文本标签。

# ---------- 四按钮与编辑面板 ----------
class RubikUI(Entity):  # 作为引擎实体接收每帧更新和全局鼠标事件。
    def __init__(self):  # 构建窗口内的完整交互。
        super().__init__(parent=camera.ui)  # 所有界面控件使用屏幕坐标。
        self.cube = CubeState()  # 默认使用白底黄顶蓝前的复原状态。
        self.view = CubeView(self.cube.facelets)  # 创建中央完整三维魔方。
        self.player = Playback(self.cube, self.view)  # 建立共用动作队列和动画节奏。
        self.editing, self.single_down = False, False  # 保存编辑模式和单步按钮按住状态。
        self.notice, self.error = '准备就绪，点击随机打乱开始体验。', False  # 默认提示。
        self.worker = ThreadPoolExecutor(max_workers=1)  # 同一时刻只计算一份解法。
        self.future, self.intent = None, None  # 保存后台任务与完成后的播放方式。
        self.dragging, self.drag_previous = False, None  # 记录右键拖动期间的鼠标位置。
        self._build_interface()  # 创建四个主要按钮、信息卡和颜色选择器。
        self.refresh()  # 根据当前状态初始化全部文字。
    def _build_interface(self):  # 将布局构建集中放在一个区域。
        label('三阶魔方', -.73, .44, 1.6, parent=self)  # 左上角显示程序名称。
        label('层先法复原  /  LAYER BY LAYER', -.73, .375, .65, MUTED, self)  # 标明使用的复原方法。
        label('白底 · 黄顶 · 蓝前 · 左橙 · 右红', .73, .415, .65, MUTED, self, origin=(.5, .5))  # 右上角提示固定配色。
        Entity(parent=self, model='quad', position=(0, .33), scale=(1.46, .002), color=color.rgb32(48, 63, 84))  # 分隔标题与主体区域。
        Entity(parent=self, model='quad', position=(-.60, .055), scale=(.30, .36), color=SURFACE)  # 左侧状态卡片。
        label('当前状态', -.72, .20, .68, MUTED, self)  # 状态卡标题。
        self.mode_text = label('', -.72, .145, .96, INK, self)  # 编辑、播放和完成状态。
        self.stage_text = label('', -.72, .077, .70, MUTED, self)  # 显示当前层先法阶段。
        self.progress_text = label('', -.72, -.018, .75, INK, self)  # 显示已完成动作数。
        self.action_text = label('', -.72, -.076, .70, MUTED, self)  # 显示当前动作的中文解释。
        Entity(parent=self, model='quad', position=(.60, .055), scale=(.30, .36), color=SURFACE)  # 右侧交互说明卡片。
        label('操作提示', .48, .20, .68, MUTED, self)  # 说明卡标题。
        self.help_text = label('右键按住拖动\n查看魔方各个面\n\n单步：点击转动一次\n按住：每秒执行一步\n\n六个中心色块固定', .48, .135, .68, INK, self)  # 用具体操作说明控制方法。
        label('自动复原速度', .48, -.035, .60, MUTED, self)  # 速度选择位于右侧提示卡的下部。
        self.speed_buttons = {}  # 三个速度选择独立于四个主要操作按钮。
        for index, speed in enumerate((1, 5, 10)):  # 创建用户要求的三个档位。
            button = Button(parent=self, text=f'{speed}倍', position=(.52 + index * .08, -.088, -.02), scale=(.071, .035), color=ACCENT if speed == 1 else color.rgb32(44, 58, 78), text_color=INK, text_size=.62)  # 所选档位使用蓝色高亮，按钮明确位于背景前方。
            button.on_click = lambda selected=speed: self.select_auto_speed(selected)  # 将当前档位固定到对应按钮回调。
            self.speed_buttons[speed] = button  # 保存按钮供当前速度的高亮状态更新。
        self.palette_root = Entity(parent=self, enabled=False, z=-.1)  # 颜色选择器覆盖说明卡，默认隐藏。
        Entity(parent=self.palette_root, model='quad', position=(.60, .055, .02), scale=(.30, .36), color=SURFACE)  # 将背景放到颜色按钮后方，避免共面绘制遮挡。
        self.palette_title = label('请选择颜色', .48, .20, .66, INK, self.palette_root)  # 显示当前被点击色块的位置。
        for index, value in enumerate('WYBGRO'):  # 显示六种可选颜色。
            x = .545 + (index % 2) * .11  # 两列排列避免挤占三维区域。
            y = .11 - (index // 2) * .085  # 三行排列，留足鼠标点击面积。
            button = Button(parent=self.palette_root, text=COLOR_NAMES[value][0], position=(x, y, -.02), scale=(.09, .062), color=PALETTE[value], text_color=color.black if value in 'WYO' else color.white, text_size=.70)  # 六种色样明确位于面板前方，保证白黄按钮也可见。
            button.on_click = lambda chosen=value: self.paint(chosen)  # 默认参数固定当前颜色，避免循环闭包错误。
        self.count_text = label('', 0, -.222, .60, MUTED, self, origin=(0, .5))  # 编辑时显示颜色数量，其余时候显示观察说明。
        self.notice_text = label('', 0, -.269, .78, INK, self, origin=(0, .5))  # 操作结果与错误提示放在中央下方。
        specifications = [('编辑魔方', self.toggle_edit, -.495), ('随机打乱', self.scramble, -.165), ('自动复原', self.toggle_auto, .165), ('单步复原', self.step_pressed, .495)]  # 四个主按钮保持明确固定的位置。
        self.buttons = []  # 保留主按钮列表用于动态更新文字与可用状态。
        for title, callback, x in specifications:  # 创建四个同尺寸主操作按钮。
            button = Button(parent=self, text=title, position=(x, -.375), scale=(.295, .074), color=ACCENT if title == '自动复原' else SURFACE, text_color=INK, text_size=.84)  # 主操作加深强调，其他按钮保持统一。
            button.on_click = callback  # 将操作绑定到独立的界面方法。
            self.buttons.append(button)  # 固定顺序为编辑、打乱、自动、单步。
        label('修改色块', -.495, -.438, .52, MUTED, self, origin=(0, .5))  # 为按钮添加简短解释。
        label('生成可复原状态', -.165, -.438, .52, MUTED, self, origin=(0, .5))  # 说明随机打乱保证合法。
        label('逐步播放 · 可暂停', .165, -.438, .52, MUTED, self, origin=(0, .5))  # 说明自动复原支持暂停。
        label('点击一步 · 按住连续', .495, -.438, .52, MUTED, self, origin=(0, .5))  # 说明单步长按行为。
    def say(self, text, error=False):  # 统一设置操作反馈。
        self.notice, self.error = text, error  # 保留反馈，避免下一帧被普通状态覆盖。
        self.refresh()  # 立即更新画面。
    def select_auto_speed(self, speed):  # 允许播放前或播放中选择自动复原速度。
        self.player.set_auto_speed(speed)  # 将倍率写入独立播放器，手动动作仍然使用一倍。
        self.say(f'自动复原速度：{speed} 倍；后续自动动作使用该速度。')  # 明确反馈所选档位与生效范围。
    def available(self):  # 编辑与重新打乱必须在完整转动之间执行。
        if self.future is not None or self.player.active:  # 防止在后台计算或半层动画时改动模型。
            self.say('请等待当前计算或转动完成。')  # 给出具体等待原因。
            return False  # 不执行会使步骤失效的操作。
        return True  # 当前可以安全修改魔方。

# ---------- 编辑颜色、打乱与后台求解 ----------
    def toggle_edit(self):  # 编辑按钮同时承担进入与结束编辑。
        if not self.available():  # 当前动作尚未结束时保持模型不变。
            return  # 结束本次点击处理。
        if self.editing:  # 结束编辑前检查输入状态。
            error = validate(self.cube.facelets)  # 验证用户录入的全部色块。
            if error:  # 不合法时保留编辑模式，方便继续修正。
                self.say(error, True)  # 明确解释为什么还不能复原。
                return  # 等待用户修正颜色或重新打乱。
        self.player.invalidate()  # 任何进入或离开编辑操作都会清除旧解法。
        self.editing = not self.editing  # 切换编辑模式。
        self.palette_root.enabled = False  # 模式切换后隐藏旧的选色面板。
        self.view.select()  # 清除之前的色块选择。
        self.say('左键点击非中心色块，再选择颜色；右键拖动查看其他面。' if self.editing else '颜色检查通过，可以自动复原或单步复原。')  # 展示当前模式的操作提示。
    def choose_sticker(self, index):  # 把三维色块点击映射到颜色选择面板。
        if not self.editing:  # 查看模式点击色块不会修改颜色。
            return  # 仅在编辑模式响应。
        if index in CENTERS:  # 六个固定中心始终不允许编辑。
            self.say('这是固定中心色块，请选择周围的色块。')  # 解释不能编辑的原因。
            return  # 不打开颜色面板。
        self.view.select(index)  # 高亮用户选择的色块。
        face, offset = FACE_ORDER[index // 9], index % 9  # 获取所在面和面内位置。
        self.palette_title.text = f'{FACE_NAMES[face]} · {offset // 3 + 1} 行 {offset % 3 + 1} 列'  # 明确显示即将修改的位置。
        self.palette_root.enabled = True  # 展示六种颜色按钮。
        self.say('选择右侧颜色，修改当前色块。')  # 提醒用户继续选择颜色。
    def paint(self, value):  # 写入当前选中色块的颜色。
        index = self.view.selected  # 读取三维显示层记录的选中索引。
        if not self.editing or index is None:  # 没有目标时颜色按钮不执行操作。
            return  # 避免误修改其他贴片。
        self.cube.paint(index, value)  # 模型负责固定中心和输入值检查。
        self.view.sync(self.cube.facelets)  # 立即更新三维颜色。
        self.view.select()  # 修改后取消选中标记。
        self.palette_root.enabled = False  # 完成一次涂色后收起面板。
        self.say('色块已修改；编辑完成后点击“完成编辑”。')  # 提供下一步操作。
    def scramble(self):  # 从复原状态生成新的合法随机魔方。
        if not self.available():  # 动画中不能覆盖当前状态。
            return  # 保持当前任务完整。
        self.player.invalidate()  # 新魔方不再使用旧步骤。
        self.editing = False  # 打乱后进入正常查看模式。
        self.palette_root.enabled = False  # 清除选色界面。
        self.view.select()  # 清除编辑高亮。
        self.last_scramble = self.cube.scramble()  # 打乱历史只供观察，不提供给求解器。
        self.view.sync(self.cube.facelets)  # 把新状态展示出来。
        self.say('已执行 25 次合法随机转动，可以开始层先法复原。')  # 确认当前状态可复原。
    def ensure_plan(self, intent):  # 自动与单步按钮共用求解入口。
        if self.editing:  # 未完成编辑时不能计算解法。
            self.say('请先点击“完成编辑”，检查录入的颜色。')  # 指出需要完成的前置操作。
            return False  # 不计算半成品输入。
        if self.future is not None:  # 后台已经有一份解法正在计算。
            return False  # 避免叠加后台任务。
        if not self.player.complete:  # 当前队列仍有未执行步骤。
            return True  # 继续使用同一份解法。
        error = validate(self.cube.facelets)  # 任何求解都先检查物理合法性。
        if error:  # 即使模型来自其他入口，也不能绕过检查。
            self.say(error, True)  # 输出可修正的原因。
            return False  # 不进入求解器。
        if self.cube.is_solved():  # 已经复原时不启动后台线程。
            self.say('魔方已经复原。')  # 反馈当前完成状态。
            return False  # 没有待执行动作。
        self.intent = intent  # 记录求解完成后是自动播放还是仅转一步。
        self.future = self.worker.submit(solve_layer_by_layer, self.cube.facelets)  # 把只读颜色快照提交后台求解。
        self.say('正在根据当前颜色计算层先法步骤……')  # 窗口继续响应右键观察。
        return False  # 计算完成后由每帧更新开始动作。
    def toggle_auto(self):  # 自动按钮依次支持开始、暂停与继续。
        if self.player.auto:  # 正在连续播放时点击即暂停。
            self.player.auto, self.player.hold = False, False  # 停止后续动作，当前 90 度动画正常完成。
            self.say('已暂停；当前转动完成后停下，可以单步或继续。')  # 明确暂停发生在完整动作之间。
            return  # 不重复求解。
        if self.ensure_plan('auto'):  # 有现成步骤时立即恢复播放。
            self.player.auto, self.player.hold = True, False  # 自动模式不依赖鼠标持续按住。
            self.say(f'正在以 {self.player.auto_speed} 倍速度复原，再次点击按钮可以暂停。')  # 显示自动倍率和暂停方法。
    def step_pressed(self):  # 单步按钮的按下事件同时启动长按检测。
        self.single_down = True  # 松开事件会清除这个标志。
        self.player.auto = False  # 单步操作切换到手动节奏。
        if self.ensure_plan('single'):  # 如果没有现成解法，先计算步骤。
            self.player.hold = True  # 按住期间每秒执行后续动作。
            self.player.request_step()  # 点击立即只启动一次 90 度动作。
            self.say('正在单步复原；松开停止连续执行。')  # 解释当前鼠标行为。

# ---------- 鼠标观察、输入分发与状态显示 ----------
    def input(self, key):  # 引擎会自动把键盘与鼠标事件传入。
        if key == 'left mouse up':  # 无论在哪里松开鼠标都应该停止长按。
            self.single_down, self.player.hold = False, False  # 已开始的动画正常完成，不启动下一步。
        elif key == 'right mouse down':  # 按住右键开始观察整个魔方。
            self.dragging, self.drag_previous = True, tuple(mouse.position)  # 从当前指针位置建立拖动起点。
        elif key == 'right mouse up':  # 右键松开后立即结束观察拖动。
            self.dragging, self.drag_previous = False, None  # 清除拖动状态。
        elif key == 'left mouse down' and self.editing and hasattr(mouse.hovered_entity, 'sticker_index'):  # 左键仅选择真正命中的三维贴片。
            self.choose_sticker(mouse.hovered_entity.sticker_index)  # 打开该贴片的颜色选择器。
        elif key == 'escape':  # Escape 收起颜色面板，不退出程序。
            self.palette_root.enabled = False  # 取消当前选色。
            self.view.select()  # 清除色块高亮。
    def update(self):  # 引擎每帧调用一次，保持显示与状态同步。
        if self.dragging and self.drag_previous is not None:  # 右键按住期间计算指针移动量。
            current = tuple(mouse.position)  # 保存本帧指针位置。
            self.view.orbit(current[0] - self.drag_previous[0], current[1] - self.drag_previous[1])  # 旋转观察节点，不改变颜色模型。
            self.drag_previous = current  # 下一帧从当前位置继续计算。
        if self.future is not None and self.future.done():  # 后台求解完成后只在主线程更新界面。
            future, intent = self.future, self.intent  # 暂存完成的任务和播放方式。
            self.future, self.intent = None, None  # 释放任务占用状态。
            try:  # 将计算异常转换成清晰的界面提示。
                self.player.set_plan(future.result())  # 取得已经通过完整重放验证的解法。
                self.player.auto = intent == 'auto'  # 自动按钮启动连续播放。
                self.player.hold = intent == 'single' and self.single_down  # 只在鼠标仍然按住时继续长按。
                self.player.request_step()  # 两种入口都立即开始第一步。
                self.say(f'已生成 {len(self.player.steps)} 个 90° 动作，使用初学者层先法。')  # 展示实际解法长度。
            except Exception as error:  # 后台异常不能导致窗口退出。
                self.say(f'无法生成复原步骤：{error}', True)  # 保留当前魔方，便于查看和修正。
        old_index = self.player.index  # 保存推进之前的已完成步数。
        self.player.tick(min(time.dt, .1))  # 每帧推进动作，限制窗口卡顿导致的时间跳跃。
        if self.player.index != old_index and self.player.complete:  # 只在最后一个动作完成时宣布复原。
            self.say('复原完成！白底黄顶蓝前，六个面全部归位。')  # 完成状态不会被下一帧覆盖。
        self.refresh()  # 更新当前动作、进度和按钮文字。
    def refresh(self):  # 所有界面状态统一从模型和播放器读取。
        busy = self.future is not None  # 后台计算时禁用会改变魔方的按钮。
        mode = '编辑颜色' if self.editing else '计算步骤' if busy else '自动复原' if self.player.auto else '单步转动' if self.player.active or self.player.hold else '已复原' if self.cube.is_solved() else '等待复原'  # 显示优先级明确的当前模式。
        index = min(self.player.index, len(self.player.steps) - 1)  # 动作完成后避免越界读取。
        step = self.player.steps[index] if self.player.steps else None  # 没有解法时显示操作说明。
        stage = step.stage.replace('  ', '\n', 1) if step else '先复原底层\n再处理中层和顶层'  # 将阶段信息分两行，适应状态卡宽度。
        action = f'{step.move}  {FACE_NAMES[step.move[0]]}\n' + ('逆时针 90°' if step.move.endswith("'") else '顺时针 90°') if step else '转动方向：\n正对该面观察'  # 用中文解释标准动作。
        updates = [(self.mode_text, mode), (self.stage_text, stage), (self.progress_text, f'{self.player.index} / {len(self.player.steps)}  步'), (self.action_text, action), (self.notice_text, textwrap.fill(self.notice, width=48))]  # 收集本帧应显示的文字。
        counts = Counter(self.cube.facelets)  # 编辑时显示每种颜色是否有九个。
        count_line = '   '.join(f'{COLOR_NAMES[value][0]} {counts[value]}/9' for value in 'WYBGRO') if self.editing else '右键拖动只改变观察角度，复原动作始终使用固定的六面方向。'  # 区分观察旋转和真实层转动。
        updates.append((self.count_text, count_line))  # 将颜色数量加入统一更新。
        for target, value in updates:  # 逐一检查哪些文字真的发生变化。
            if target.text != value:  # 避免每帧重新生成相同文字的几何。
                target.text = value  # 仅在变化时刷新文本。
        self.notice_text.color = color.rgb32(255, 151, 140) if self.error else INK  # 错误提示使用明显的暖色。
        edit_title = '完成编辑' if self.editing else '编辑魔方'  # 编辑按钮保留唯一的模式退出入口。
        auto_title = '暂停复原' if self.player.auto else '继续复原' if self.player.steps and not self.player.complete else '自动复原'  # 自动按钮文字反映当前动作。
        if self.buttons[0].text != edit_title:  # 只有模式变化时才重新绘制按钮文字。
            self.buttons[0].text = edit_title  # 更新编辑按钮。
        if self.buttons[2].text != auto_title:  # 避免逐帧重复构建相同文本。
            self.buttons[2].text = auto_title  # 更新自动按钮。
        self.buttons[0].disabled = busy or self.player.active  # 半层动画时禁止修改颜色。
        self.buttons[1].disabled = busy or self.player.active  # 半层动画时禁止生成新魔方。
        self.buttons[2].disabled = busy or self.editing  # 编辑完成前不允许自动求解。
        self.buttons[3].disabled = busy or self.editing  # 编辑完成前不允许单步求解。
        for speed, button in self.speed_buttons.items():  # 选中的自动速度始终保持清晰高亮。
            desired = ACCENT if speed == self.player.auto_speed else color.rgb32(44, 58, 78)  # 蓝色代表当前选择。
            if button.color != desired:  # 档位不变时不重复设置按钮材质。
                button.color = desired  # 更新按钮背景。
                button.highlight_color, button.pressed_color = desired.tint(.15), desired.tint(-.10)  # 同步悬停和按下颜色，避免残留旧档位样式。
    def close(self):  # 程序退出时释放后台计算资源。
        self.worker.shutdown(wait=False, cancel_futures=True)  # 不等待尚未开始的求解任务。
