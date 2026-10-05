# ---------- 项目格式与说明文件检查 ----------
from pathlib import Path  # 使用项目自身的位置，不依赖启动目录。
import ast  # 检查 Python 语法，不导入或运行项目模块。
import io  # 向分词器提供内存中的源代码。
import re  # 找出 Markdown 中的文件链接。
import sys  # 返回明确的成功或失败状态。
import tokenize  # 用语法分词区分真实注释与字符串中的井号。
from urllib.parse import unquote  # 兼容文档链接中编码后的空格和中文。
ROOT = Path(__file__).resolve().parents[1]  # 工具保存在 tools 中，父目录的父目录是项目根目录。
errors = []  # 集中记录检查失败，避免发现第一项后就遗漏其他项。
python_files = [ROOT / 'main.py', ROOT / 'run_tests.py']  # 两个入口也必须接受检查。
for folder in ('rubik', 'tests', 'tools'):  # 仅检查维护的源码，不扫描环境或临时输出。
    python_files.extend(sorted((ROOT / folder).glob('*.py')))  # 收集各逻辑模块与测试工具。

# ---------- 语法与逐行注释 ----------
for path in python_files:  # 每个源码文件独立检查。
    source = path.read_text(encoding='utf-8-sig')  # 读取 UTF-8，兼容历史文件的字节序标记。
    try:  # 把语法错误归入同一检查报告。
        ast.parse(source)  # 解析语法，不产生字节码也不创建窗口。
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))  # 获取精确的代码与注释位置。
    except (SyntaxError, tokenize.TokenError) as error:  # 损坏的文件不能继续做注释检查。
        errors.append(f'{path.relative_to(ROOT)}: 语法错误：{error}')  # 记录文件和原因。
        continue  # 继续检查其他文件。
    comments = {token.start[0] for token in tokens if token.type == tokenize.COMMENT}  # 真正的注释行才算解释位置。
    ignored = {tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT, tokenize.ENDMARKER, tokenize.ENCODING}  # 空行与布局标记不是代码。
    code = {token.start[0] for token in tokens if token.type not in ignored}  # 获得每个包含代码的行号。
    for line in sorted(code - comments):  # 当前约定要求代码行有同行解释性注释。
        errors.append(f'{path.relative_to(ROOT)}:{line}: 缺少逐行注释')  # 定位到需要补充说明的位置。

# ---------- 批处理换行与编码 ----------
for relative in ('启动魔方.cmd', '运行测试.cmd', 'scripts/find_python.cmd'):  # 主入口与共享定位器遵守相同规则。
    data = (ROOT / relative).read_bytes()  # 读取原始字节，避免文本读取替换换行。
    if b'\n' in data.replace(b'\r\n', b'') or any(value >= 128 for value in data):  # LF 和非 ASCII 内容可能引起 cmd 解析问题。
        errors.append(f'{relative}: 必须保持 ASCII 内容与 CRLF 换行')  # 明确指出格式要求。

# ---------- Markdown 内部链接与必要文件 ----------
documents = [ROOT / 'README.md', ROOT / 'CONTRIBUTING.md', ROOT / 'THIRD_PARTY_NOTICES.md', *sorted((ROOT / 'docs').glob('*.md'))]  # 检查面向使用者的主要说明。
for path in documents:  # 文档错误也会使项目难以学习使用。
    source = path.read_text(encoding='utf-8')  # 文档统一为 UTF-8。
    for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', source):  # 同时检查图片和普通 Markdown 链接。
        target = target.strip().strip('<>').split('#', 1)[0]  # 去掉锚点与可选尖括号，仅检查文件部分。
        if not target or re.match(r'^[A-Za-z][A-Za-z0-9+.-]*:', target):  # 网络地址交由发布时人工核对，不在本地联网。
            continue  # 当前工具只检查仓库内部文件是否存在。
        if not (path.parent / unquote(target)).is_file():  # 按相对文档位置解析，兼容克隆到其他目录。
            errors.append(f'{path.relative_to(ROOT)}: 链接目标不存在：{target}')  # 告诉维护者哪个链接失效。
for relative in ('LICENSE', 'environment.yml', '.gitattributes', '.github/workflows/core-tests.yml'):  # 发布所需配置不能遗漏。
    if not (ROOT / relative).is_file():  # 必要文件必须是真实文件。
        errors.append(f'缺少必要文件：{relative}')  # 记录配置缺失。
if 'prefix:' in (ROOT / 'environment.yml').read_text(encoding='utf-8'):  # 环境文件不能固定到作者的绝对安装路径。
    errors.append('environment.yml 不应绑定固定 prefix')  # 使用者应通过创建命令选择目录。

# ---------- 汇总与退出状态 ----------
sys.stdout.reconfigure(encoding='utf-8')  # 在 Windows 终端也输出可读中文。
if errors:  # 所有失败集中展示。
    print('\n'.join(errors))  # 一行一个问题，方便按位置修复。
    sys.exit(1)  # 自动测试需要非零状态识别失败。
print(f'项目检查通过：{len(python_files)} 个 Python 文件、3 个批处理、{len(documents)} 份文档。')  # 说明实际检查范围。
