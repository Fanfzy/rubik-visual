# ---------- 测试报告与环境信息 ----------
from pathlib import Path  # 把报告保存到固定的项目输出目录。
import sys  # 配置中文输出并返回正确的测试退出码。
import io  # 在内存中收集测试框架的文字结果。
import argparse  # 明确区分核心测试与需要 OpenGL 的完整验收。
import unittest  # 使用 Python 自带测试框架。
from importlib.metadata import version  # 读取实际安装的依赖版本。
sys.stdout.reconfigure(encoding='utf-8')  # 使终端与保存的中文报告使用相同编码。
parser = argparse.ArgumentParser(description='魔方项目验收：默认完整测试，--core 仅运行核心与启动脚本测试。')  # 为新使用者提供可查看的帮助。
parser.add_argument('--core', action='store_true', help='跳过需要 OpenGL 和中文字体的三维测试。')  # GitHub 自动检查使用此模式。
arguments = parser.parse_args()  # 未知参数会显示帮助而不是悄悄忽略。
output = Path(__file__).resolve().parent / 'test_outputs'  # 使用绝对路径，不依赖命令行当前目录。
output.mkdir(exist_ok=True)  # 确保输出目录存在。
log = io.StringIO()  # 收集完整验收文本。
log.write(f'Python: {sys.version.split()[0]}\n环境: {sys.prefix}\n')  # 记录实际环境位置。
log.write(f'ursina: {version("ursina")}\nmagiccube: {version("magiccube")}\n\n')  # 记录关键第三方依赖。

# ---------- 先完成核心测试，再验收三维界面 ----------
loader = unittest.TestLoader()  # 初始化标准测试加载器。
suite = loader.loadTestsFromNames(['tests.test_core', 'tests.test_playback', 'tests.test_launchers'])  # 核心测试默认包含一千组随机打乱，并检查 Windows 启动脚本。
core = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)  # 验证模型、合法性、层先法和播放控制。
graphics = None  # 核心失败时不继续进入图形验收。
if core.wasSuccessful() and not arguments.core:  # 完整模式只有基础规则正确才运行真实三维界面。
    log.write('\n三维界面集成测试：\n')  # 在报告中分开两个验收阶段。
    graphics = unittest.TextTestRunner(stream=log, verbosity=2).run(loader.loadTestsFromName('tests.test_gui'))  # 在真实 OpenGL 缓冲测试四按钮和鼠标事件。
successful = core.wasSuccessful() and (arguments.core or (graphics is not None and graphics.wasSuccessful()))  # 核心与完整模式分别要求约定范围内全部通过。
log.write('\n验收范围：' + ('核心与 Windows 启动脚本，不包含图形界面' if arguments.core else '核心、Windows 启动脚本及三维界面') + '\n')  # 防止把核心通过误读为完整图形验收。
log.write('\n最终结果：' + ('全部通过' if successful else '存在失败，请查看上述原因') + '\n')  # 写入明确的验收结论。
report = output / ('core_report.txt' if arguments.core else 'test_report.txt')  # 两种报告分开保存，核心结果不覆盖完整验收。
report.write_text(log.getvalue(), encoding='utf-8')  # 保存 UTF-8 报告供阅读和复查。
print(log.getvalue())  # 同时在命令行显示全部测试结果。
print(f'报告位置：{report}')  # 提醒用户如何找到报告。
sys.exit(0 if successful else 1)  # 失败时返回非零状态，启动脚本不会误报成功。
