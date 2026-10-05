# ---------- 独立于界面的动作播放器 ----------
class Playback:  # 控制动作顺序和时间，不依赖 Ursina。
    def __init__(self, cube, view, duration=.3, interval=1.0):  # 接收模型与显示接口，让计时规则独立于三维绘制。
        self.cube, self.view = cube, view  # 保存状态与动画接收者。
        self.duration, self.interval = duration, interval  # 设定动画时长和相邻动作开始的间隔。
        self.auto_speed, self._step_speed = 1, 1  # 默认自动速度为一倍，每个动作保存开始时的倍率。
        self.steps, self.index = [], 0  # 保存完整解法和已经完成的动作数。
        self.active, self.auto, self.hold = False, False, False  # 分别记录动画中、自动播放、长按状态。
        self.elapsed, self.cooldown = 0.0, 0.0  # 记录当前动画进度与动作之间的等待。
    def set_auto_speed(self, speed):  # 只修改自动模式的速度选择，不改变单步和长按。
        if speed not in (1, 5, 10):  # 仅接受界面提供的三个档位。
            raise ValueError('自动速度只能选择 1 倍、5 倍或 10 倍。')  # 拒绝不支持的速度。
        self.auto_speed = speed  # 正在转动的动作保留原倍率，后续动作读取新值。
    def invalidate(self):  # 编辑或重新打乱后清除旧解法。
        if self.active:  # 不允许半层动画时修改模型或队列。
            raise RuntimeError('请等待当前转动完成。')  # 让控制层明确知道操作时机错误。
        self.steps, self.index = [], 0  # 丢弃不再对应当前状态的解法。
        self.auto, self.hold, self.cooldown = False, False, 0.0  # 同时停止所有连续播放来源。
    def set_plan(self, steps):  # 设置从当前状态计算出的完整复原步骤。
        self.invalidate()  # 新队列必须从空闲状态开始。
        self.steps = list(steps)  # 复制步骤，防止外部修改列表。
    @property  # 提供界面可以读取的完成标志。
    def complete(self):  # 判断步骤队列是否已经执行完。
        return self.index >= len(self.steps)  # 空队列同样表示没有待执行动作。
    def request_step(self):  # 只启动一个动作，连续点击不会叠加动画。
        if self.active or self.complete:  # 动画进行中或没有下一步时拒绝启动。
            return False  # 返回值可用于按钮处理。
        self.view.begin(self.steps[self.index].move)  # 通知显示层准备当前面动画。
        self._step_speed = self.auto_speed if self.auto else 1  # 自动动作使用选择倍率，手动动作始终一倍。
        self.active, self.elapsed = True, 0.0  # 开始计时，但此时不修改模型。
        return True  # 一次单步请求只创建一次转动。
    def tick(self, delta):  # 根据本帧经过的秒数推进动画和等待。
        remaining, epsilon = max(0.0, delta), 1e-10  # 保存本帧剩余真实时间，并容忍极小浮点误差。
        while True:  # 动画或等待在一帧内结束时，将剩余时间继续交给下一阶段。
            if self.active:  # 有正在进行的层转动时优先推进它。
                if remaining <= epsilon:  # 当前帧已经没有可用于动画的时间。
                    break  # 下一帧继续，不跳过动画。
                needed = max(0.0, self.duration - self.elapsed) / self._step_speed  # 把剩余基础动画时间换算为真实时间。
                consumed = min(remaining, needed)  # 本阶段只能消耗自己需要的时间。
                self.elapsed += consumed * self._step_speed  # 在基础时间轴上按选定倍率推进。
                remaining = max(0.0, remaining - consumed)  # 保留未消耗时间，避免每一步多等一帧。
                finished = self.duration - self.elapsed <= epsilon  # 判断是否完整完成一个 90 度动作。
                self.view.pose(1.0 if finished else self.elapsed / self.duration)  # 动画结束时确保几何精确达到终点。
                if not finished:  # 动画尚未完成时不能修改模型。
                    break  # 等待下一帧继续绘制。
                self.cube.move(self.steps[self.index].move)  # 每次动画只提交一次真实魔方动作。
                self.index += 1  # 更新已完成的动作数量。
                self.view.finish(self.cube.facelets)  # 将画面同步到提交后的颜色状态。
                self.active = False  # 进入动作之间的等待阶段。
                self.cooldown = max(0.0, self.interval - self.duration)  # 保存一倍下的基础等待时间。
                if self.complete:  # 最后一步结束后停止所有连续播放。
                    self.auto, self.hold = False, False  # 完成后不再启动新动作。
                continue  # 同一帧剩余时间还可以推进等待。
            if not (self.auto or self.hold) or self.complete:  # 暂停和单击都不自动启动后续动作。
                self.cooldown = max(0.0, self.cooldown - remaining)  # 手动空闲时间仍按一倍流逝。
                break  # 无连续播放请求时结束本帧。
            speed = self.auto_speed if self.auto else 1  # 自动等待随档位加速，长按等待保持一倍。
            consumed = min(remaining, self.cooldown / speed)  # 只消耗直到等待结束所需的真实时间。
            self.cooldown = max(0.0, self.cooldown - consumed * speed)  # 同步推进基础等待时间。
            remaining = max(0.0, remaining - consumed)  # 保留可以交给下一个动作的时间。
            if self.cooldown > epsilon:  # 当前帧还没有等到下一步开始时刻。
                break  # 保持静止到下一帧。
            self.cooldown = 0.0  # 消除浮点误差残留的极小等待。
            self.request_step()  # 到时只启动一次动作，并读取新的自动倍率。
            if remaining <= epsilon:  # 时间恰好落在动作边界时只完成启动。
                break  # 下一帧再显示动画进度。
