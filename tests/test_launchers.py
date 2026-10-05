# ---------- Windows 启动脚本回归测试 ----------
from pathlib import Path  # 检查原始文件字节，并在项目内建立独立的测试目录。
import os  # 给启动脚本传入独立的环境变量，避免依赖个人电脑路径。
import sys  # 使用运行测试的同一个 Python 解释器。
import subprocess  # 通过真正的 Windows cmd 解释器执行批处理。
import unittest  # 使用标准测试框架记录兼容性结果。
ROOT = Path(__file__).resolve().parents[1]  # 定位项目根目录，不依赖调用位置。
@unittest.skipUnless(os.name == 'nt', '批处理执行验收只适用于 Windows。')  # 其他系统不能执行 Windows cmd。
class LauncherTests(unittest.TestCase):  # 检查换行、编码和完整批处理控制流程。
    def test_windows_format(self):  # 两个启动入口都必须具有明确的 Windows 文件格式。
        for name in ('启动魔方.cmd', '运行测试.cmd', 'scripts/find_python.cmd'):  # 同时覆盖入口与共享环境定位器。
            data = (ROOT / name).read_bytes()  # 直接读取字节，防止文本读取自动转换换行。
            self.assertNotIn(b'\n', data.replace(b'\r\n', b''), name)  # 文件中不能残留单独的 LF 换行。
            self.assertTrue(all(value < 128 for value in data), name)  # 批处理本身只使用 ASCII，中文路径仍由 Windows 处理。
    def exercise(self, name, exit_code, mode='explicit'):  # 在包含空格和中文的目录里执行原样复制的脚本。
        folder = ROOT / 'test_outputs' / '启动脚本 验收'  # 覆盖用户目录中的中文及路径引用。
        folder.mkdir(parents=True, exist_ok=True)  # 所有测试文件都保存在项目内部。
        script = folder / name  # 使用与正式入口相同的中文文件名。
        script.write_bytes((ROOT / name).read_bytes())  # 不更改被测试脚本的任何字节。
        helper = folder / 'scripts' / 'find_python.cmd'  # 共享定位器也必须在真实目录结构中执行。
        helper.parent.mkdir(exist_ok=True)  # 创建测试副本的脚本目录。
        helper.write_bytes((ROOT / 'scripts' / 'find_python.cmd').read_bytes())  # 原样复制环境定位器。
        stub = "import sys  # Access the requested exit code.\nprint('LAUNCHER_ENTRY_OK')  # Confirm that the correct entry was executed.\nsys.exit(" + str(exit_code) + ")  # Return the test exit code.\n"  # 替代界面入口，避免错误脚本弹出窗口或挂起。
        for entry in ('main.py', 'run_tests.py'):  # 两个批处理调用各自的真实文件名。
            (folder / entry).write_text(stub, encoding='ascii')  # 使用简单可验证的入口程序。
        environment = os.environ.copy()  # 保留 Windows 所需的系统变量。
        environment.pop('RUBIK_PYTHON', None)  # 清除调用者可能设置的解释器覆盖。
        environment.pop('CONDA_PREFIX', None)  # 每项测试独立决定是否模拟激活环境。
        if mode == 'explicit':  # 显式配置应优先于活动 conda 环境。
            environment['RUBIK_PYTHON'] = sys.executable  # 使用实际验收环境，支持 GitHub 上不同的安装路径。
            environment['CONDA_PREFIX'] = str(folder / '不存在的 conda 环境')  # 故意设置错误次选项，检查优先级。
        elif mode == 'active':  # 模拟用户已经激活自己的 conda 环境。
            environment['CONDA_PREFIX'] = str(Path(sys.executable).parent)  # 将环境目录指向真实解释器所在目录。
        else:  # 无效的显式解释器不能悄悄回退到其他环境。
            environment['RUBIK_PYTHON'] = str(folder / 'missing python.exe')  # 构造一个一定不存在的解释器位置。
        result = subprocess.run(['cmd.exe', '/d', '/c', str(script)], cwd=ROOT, env=environment, input=b'\r\n\r\n', capture_output=True, timeout=10)  # 正常解释批处理，并给 pause 提供字节形式的回车。
        combined = result.stdout + result.stderr  # 同时检查标准输出和错误输出。
        if mode == 'missing':  # 缺少解释器时应停在明确的环境错误提示。
            self.assertNotIn(b'LAUNCHER_ENTRY_OK', combined)  # 不能启动错误的备用解释器。
            self.assertIn(b'Python interpreter not found', combined)  # 提示下一步应该修复环境设置。
        else:  # 有效环境必须执行正确入口。
            self.assertIn(b'LAUNCHER_ENTRY_OK', combined, combined.decode('utf-8', errors='replace'))  # Python 入口必须确实执行。
        self.assertEqual(result.stderr, b'', combined.decode('utf-8', errors='replace'))  # 注释或半截文字不能被当作命令执行。
        self.assertEqual(result.returncode, exit_code, combined.decode('utf-8', errors='replace'))  # 程序的失败码必须保留。
    def test_startup_success(self):  # 检查双击程序入口对应的正常路径。
        self.exercise('启动魔方.cmd', 0)  # 成功后不能继续进入缺少环境分支。
    def test_startup_error_preserved(self):  # 检查出错后暂停不会丢失退出码。
        self.exercise('启动魔方.cmd', 7)  # 保留具体失败码供排查。
    def test_test_launcher_success(self):  # 检查测试入口也可由 cmd 正常解释。
        self.exercise('运行测试.cmd', 0)  # 测试脚本完成后正常退出。
    def test_test_launcher_error_preserved(self):  # 检查测试失败不会显示为成功。
        self.exercise('运行测试.cmd', 7)  # 暂停后仍返回失败状态。
    def test_active_environment(self):  # 其他使用者可以从自己的 conda 环境启动。
        self.exercise('启动魔方.cmd', 0, 'active')  # 不能依赖 Fanfzy 电脑上的固定目录。
    def test_missing_explicit_environment(self):  # 错误的配置要明确失败，不能掩盖问题。
        self.exercise('启动魔方.cmd', 1, 'missing')  # 保留失败码并显示环境修复提示。

# ---------- 直接运行入口 ----------
if __name__ == '__main__':  # 支持单独复查 Windows 启动脚本。
    unittest.main(verbosity=2)  # 输出五项回归测试的结果。
