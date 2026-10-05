# ---------- 命令行与图形配置 ----------
from pathlib import Path  # 使用可靠的绝对路径寻找项目资源。
import os  # 允许使用者指定自己已有的中文字体。
from panda3d.core import loadPrcFileData  # 在创建窗口之前设置引擎选项。
loadPrcFileData('', 'audio-library-name null\nframebuffer-multisample 1\nmultisamples 4\nsync-video 1')  # 程序不需要声音，启用抗锯齿改善色块边缘。
from ursina import Ursina, Text, camera, window, color, Vec3, application  # 导入图形引擎配置接口。

# ---------- 可重用的窗口初始化 ----------
def create_app(window_type='onscreen'):  # 集中构建窗口和界面，默认创建正常桌面窗口。
    application.asset_folder = Path(__file__).resolve().parent  # 资源位置不受启动目录影响。
    font = Path(os.environ.get('RUBIK_FONT', 'C:/Windows/Fonts/simhei.ttf')).expanduser().resolve()  # 默认使用 Windows 黑体，也接受已有字体的完整路径。
    if not font.is_file():  # 提前检查中文字体，避免启动后界面出现空白方框。
        raise RuntimeError('Chinese font not found. Set RUBIK_FONT to an existing Chinese .ttf font; see README.md.')  # 错误提示使用不依赖中文字体的普通文本。
    application.fonts_folder = font.parent  # 资源目录与使用者选择的字体保持一致。
    app = Ursina(title='三阶魔方 · 层先法复原', size=(1280, 800), window_type=window_type, development_mode=False, editor_ui_enabled=False, fullscreen=False, borderless=False)  # 创建普通桌面窗口。
    window.update_aspect_ratio()  # 初始化界面镜头比例，使文字与控件正确排布。
    window.color = color.rgb32(15, 23, 37)  # 深色背景使六个魔方颜色更清楚。
    Text.default_font = font.name  # 使用已有中文字体，不把系统字体复制进开源仓库。
    camera.position = (10.2, 7.9, -17)  # 留出任意观察角度下的完整魔方空间，避免遮挡下方提示。
    camera.look_at(Vec3(0, -.7, 0))  # 将魔方略微放在主体区域上方，避免遮挡操作提示。
    camera.fov = 40  # 在三维区域两侧留出状态卡的位置。
    from rubik.ui import RubikUI  # 在引擎初始化后加载界面，避免默认父节点尚未就绪。
    ui = RubikUI()  # 构建完整魔方和四个操作按钮。
    return app, ui  # 返回引擎与界面对象，便于启动和退出时统一管理。

# ---------- 程序入口与退出清理 ----------
if __name__ == '__main__':  # 直接运行才打开窗口，作为模块导入时不自动启动。
    app, ui = create_app()  # 创建正常的可交互桌面窗口。
    try:  # 确保用户关闭窗口时可以释放后台线程。
        app.run()  # 进入引擎事件循环，接收鼠标操作和更新动画。
    finally:  # 正常退出或发生异常时都执行清理。
        ui.close()  # 关闭后台求解器。
