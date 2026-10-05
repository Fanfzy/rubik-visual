# ---------- 三维显示依赖与视觉配色 ----------
from ursina import Entity, Vec3, color  # 显示层只依赖引擎和状态约定。
from ursina.shaders import unlit_shader  # 让六种颜色保持稳定，不受光照变暗影响。
from rubik.geometry import facelet_geometry, TURN_AXES  # 使用统一的贴片位置和转动方向约定。
from rubik.model import CENTERS  # 区分固定中心与可以编辑的贴片。
PALETTE = dict(W=color.rgb32(241, 244, 250), Y=color.rgb32(255, 210, 51), B=color.rgb32(42, 120, 236), G=color.rgb32(40, 182, 121), R=color.rgb32(230, 68, 83), O=color.rgb32(255, 143, 54))  # 使用易于区分的魔方六色。
def render_position(position):  # 适配模型的右手坐标与引擎前向坐标。
    return Vec3(position[0], position[1], -position[2])  # 模型的正前方在画面中朝向负 z。

# ---------- 完整魔方的几何、色块及动画 ----------
class CubeView:  # 只负责显示，不计算解法或改变魔方状态。
    def __init__(self, facelets):  # 根据初始状态创建二十六个小方块和五十四个贴片。
        self.root = Entity()  # 用户拖动这个父节点可以观察整个魔方。
        self.pivot = Entity(parent=self.root)  # 某层转动时临时使用的旋转轴。
        self.bodies = {}  # 用整数小方块位置查找三维实体。
        self.stickers = []  # 贴片顺序始终对应模型的 54 个颜色。
        self.selected = None  # 保存当前编辑选择，用于视觉高亮。
        for x in range(-1, 2):  # 遍历横向位置。
            for y in range(-1, 2):  # 遍历竖向位置。
                for z in range(-1, 2):  # 遍历前后位置。
                    position = (x, y, z)  # 建立唯一的小方块坐标键。
                    if position != (0, 0, 0):  # 内部不可见的核心不需要绘制。
                        self.bodies[position] = Entity(parent=self.root, model='cube', position=render_position(position), scale=.96, color=color.rgb32(23, 27, 35), shader=unlit_shader, collider='box')  # 黑色主体显示缝隙，并阻止从缝隙误选背面的色块。
        for index in range(54):  # 按统一贴片顺序创建全部六个面。
            position, normal = facelet_geometry(index)  # 获取贴片所属小方块及朝向。
            dimensions = tuple(.026 if value else .86 for value in normal)  # 沿法向保持薄片厚度，其他两边保持方形。
            tile = Entity(parent=self.bodies[position], model='cube', position=render_position(normal) * .502 / .96, scale=Vec3(*dimensions) / .96, color=PALETTE[facelets[index]], shader=unlit_shader, collider='box')  # 每片都有独立碰撞盒供鼠标选取。
            tile.sticker_index = index  # 点击时直接映射回模型贴片。
            tile.base_scale = Vec3(tile.scale)  # 记录未高亮时的原始尺寸。
            self.stickers.append(tile)  # 保留顺序供后续同步颜色。
            if index in CENTERS:  # 给固定中心增加小标记。
                Entity(parent=tile, model='sphere', position=render_position(normal) * .8, scale=(.11, .11, .11), color=color.rgb32(28, 33, 42), shader=unlit_shader)  # 标记只用于识别，不接受编辑输入。
    def sync(self, facelets):  # 用模型快照更新颜色，不猜测状态。
        for tile, value in zip(self.stickers, facelets):  # 按贴片索引逐一同步。
            tile.color = PALETTE[value]  # 保证画面与内部模型一致。
    def select(self, index=None):  # 编辑时高亮所选择的贴片。
        if self.selected is not None:  # 取消上一个贴片的尺寸高亮。
            tile = self.stickers[self.selected]  # 找到上次被选中的实体。
            tile.scale = tile.base_scale  # 恢复原始尺寸。
        self.selected = index  # 保存新的选择。
        if index is not None:  # 新选中一个可编辑色块时增加轮廓大小。
            tile = self.stickers[index]  # 取得当前贴片。
            tile.scale = tile.base_scale * 1.06  # 放大少许，使选中目标清晰可见。
    def begin(self, notation):  # 为某一次 90 度动作建立临时旋转组。
        self.select()  # 复原动画开始时清除编辑高亮。
        self.axis, layer, self.direction = TURN_AXES[notation[0]]  # 读取面动作对应的轴和层。
        self.direction *= -1 if notation.endswith("'") else 1  # 逆时针动作使用反向。
        for position, body in self.bodies.items():  # 遍历全部小方块。
            if position[self.axis] == layer:  # 只有被选层的九个小方块需要转动。
                body.parent = self.pivot  # 将该层暂时挂到统一旋转轴。
    def pose(self, progress):  # 用归一化动画进度设置当前层角度。
        eased = progress * progress * (3 - 2 * progress)  # 使用平滑起停曲线，避免动作突然开始或结束。
        setattr(self.pivot, 'rotation_' + 'xyz'[self.axis], -self.direction * 90 * eased)  # 三个引擎轴都已通过真实坐标测试校准。
    def finish(self, facelets):  # 动画完成后把几何恢复到标准整数位置。
        for position, body in self.bodies.items():  # 重置所有主体，避免浮点误差累计。
            body.parent = self.root  # 从旋转轴移回用户观察节点。
            body.position = render_position(position)  # 恢复固定的三维网格位置。
            body.rotation = Vec3(0, 0, 0)  # 恢复小方块局部朝向。
        self.pivot.rotation = Vec3(0, 0, 0)  # 下次动画从零角度开始。
        self.sync(facelets)  # 用已经转动后的模型颜色更新贴片。
    def orbit(self, horizontal, vertical):  # 鼠标拖动改变观察角度，不触碰模型状态。
        self.root.rotation_y -= horizontal * 180  # 按用户要求反转横向拖动的观察旋转。
        self.root.rotation_x += vertical * 180  # 同时反转竖向拖动的观察旋转。
