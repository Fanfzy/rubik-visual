**三阶魔方可视化层先法复原**

作者：Fanfzy。项目使用 Python、Ursina 和 magiccube，实现三维魔方编辑、随机打乱和层先法动画复原。主要操作通过鼠标完成，自写 Python 代码按逻辑分区逐行注释。

**功能与配色**

- 三阶魔方，固定白底、黄顶、蓝前、绿后、左橙、右红，六个中心色块不可编辑。
- 按住鼠标右键拖动观察魔方，上下与左右拖动方向均为反转设置。
- 编辑模式中，左键点击非中心色块，在右侧选择颜色。
- 随机打乱从复原状态执行 25 个合法动作，生成可复原状态。
- 自动复原按层先法推进，支持暂停、继续及 1 倍、5 倍、10 倍速度。
- 单步按钮每次点击转动一个面 90°，按住每秒执行一步，松开停止后续动作。
- 完成编辑时检查颜色数量、角块和棱块组合，以及物理可复原性。

**运行条件**

目前支持 Windows，需要 conda、Python 3.12 和能够运行 OpenGL 的图形环境。主要依赖为 Ursina 8.3.0、magiccube 1.2.0，全部固定版本保存在 `requirements.txt`。

默认使用电脑已有的 `C:\Windows\Fonts\simhei.ttf` 中文字体。项目不包含系统字体文件，也不自动安装字体。

**环境指南：已有环境直接启动**

作者的项目目录为 `C:\Users\LENOVO\Desktop\python魔方`，专用环境为 `D:\conda_envs\rubik_visual`。如果该环境已经创建且依赖已安装，无需重复创建或安装，双击 `启动魔方.cmd` 即可。

也可以在 Anaconda Prompt 或已经初始化 conda 的 CMD 中运行：

```bat
rem 进入项目目录，/d 同时切换盘符。
cd /d "C:\Users\LENOVO\Desktop\python魔方"
rem 激活已有专用环境。
conda activate D:\conda_envs\rubik_visual
rem 使用该环境启动图形界面，-s 忽略用户级 Python 包。
python -s main.py
```

**环境指南：首次创建环境**

仅在环境尚不存在时，进入包含 `environment.yml` 的项目目录，再执行以下命令。其他使用者可把环境路径改为自己的位置。

```bat
rem 用 conda 创建专用环境，并安装 requirements.txt 中的固定版本依赖。
conda env create --prefix D:\conda_envs\rubik_visual --file environment.yml
rem 激活新环境。
conda activate D:\conda_envs\rubik_visual
rem 查看实际使用的解释器，确认它位于刚创建的环境中。
python -s -c "import sys; print(sys.executable)"
rem 检查已安装依赖的版本关系。
python -s -m pip check
rem 启动程序。
python -s main.py
```

`environment.yml` 使用 conda 安装 Python 和 pip，并在同一个环境内安装程序依赖。环境激活时设置 `PYTHONNOUSERSITE=1`，配合 `-s` 防止其他项目的用户级包影响运行。

没有 D 盘时，可以选择自己的完整路径，也可以执行 `conda env create --file environment.yml` 创建名为 `rubik_visual` 的环境，再用 `conda activate rubik_visual` 激活。

**启动脚本怎样选择环境**

`启动魔方.cmd` 的选择顺序为：显式设置的 `RUBIK_PYTHON` → 已激活的 conda 环境 → 默认路径 `D:\conda_envs\rubik_visual\python.exe`。它只使用已有环境，不自动安装依赖。

环境放在其他位置时，可以从激活环境的终端调用启动脚本，也可以在 CMD 中指定解释器：

```bat
rem 指定已有环境的解释器，把示例路径替换为自己的实际路径。
set "RUBIK_PYTHON=E:\my_envs\rubik_visual\python.exe"
rem 启动界面。
call 启动魔方.cmd
```

**界面使用方法**

1. **编辑魔方**：进入编辑模式后选择色块并修改颜色，右键拖动查看背面和底面。点击“完成编辑”检查状态；输入错误时保留编辑模式并提示原因。中心上的黑色小点表示不可编辑。
2. **随机打乱**：重新生成合法状态，同时清除之前的复原步骤，也可用来从错误涂色恢复到合法状态。
3. **自动复原**：根据当前 54 个颜色计算解法并播放。暂停时当前动作先完整结束；继续时沿用同一份动作队列。
4. **单步复原**：点击一次执行一个 90° 动作，按住连续执行。在任意位置松开都停止后续动作。自动模式暂停后也能接着单步操作。

Esc 取消当前色块选择。动画中暂时禁止编辑和打乱，关闭窗口退出程序。

| 自动速度 | 动画时间 | 动作间等待 | 相邻动作开始间隔 |
| --- | --- | --- | --- |
| 1 倍 | 0.30 秒 | 0.70 秒 | 1.00 秒 |
| 5 倍 | 0.06 秒 | 0.14 秒 | 0.20 秒 |
| 10 倍 | 0.03 秒 | 0.07 秒 | 0.10 秒 |

这是播放器的目标时间，显示流畅度受设备帧率影响。切换档位时，正在转动的一步保持原速度，后续自动动作使用新档位。单步点击和长按保持一倍速度。

**复原方法与动作记号**

程序使用初学者层先法：白色底面十字 → 白色底层角块 → 中间层棱块 → 黄色顶面十字 → 顶层棱块归位 → 顶层角块归位 → 顶层角块转向。它展示教学过程，不追求最少步数。

`U、D、F、B、L、R` 分别表示初始参考朝向中的顶、底、前、后、左、右面。正对被转动的面判断顺时针：`R` 为右面顺时针 90°，`R'` 为逆时针 90°，`R2` 为 180°，播放时拆成两步。右键改变观察角度后，动作记号仍使用原来的参考系。

求解依据当前色块状态，不依赖打乱记录。颜色数量正确也不一定合法，例如单独翻转一条棱、单独扭转一个角或只交换两条棱，都不能通过正常转动复原。

**代码结构与阅读顺序**

| 文件 | 作用 |
| --- | --- |
| `main.py` | 程序入口、中文字体和窗口配置 |
| `rubik/model.py` | 魔方颜色状态、编辑和面转动 |
| `rubik/validation.py` | 颜色与物理可复原性检查 |
| `rubik/solver.py` | 层先法适配、阶段说明和动作转换 |
| `rubik/playback.py` | 动作队列、动画计时、暂停和速度控制 |
| `rubik/geometry.py` | 色块坐标和 90° 几何变换 |
| `rubik/view.py` | 三维魔方实体、贴片与转动动画 |
| `rubik/ui.py` | 按钮、鼠标操作和后台求解任务协调 |
| `environment.yml` | conda 环境创建配置 |
| `requirements.txt` | 完整固定版本依赖 |
| `启动魔方.cmd` | Windows 双击启动入口 |

建议依次阅读模型、合法性检查、求解器、播放器，再阅读几何、显示和界面。模块通过颜色字符串与动作列表连接；模型负责状态，求解器产出动作，播放器管理时间，显示层绘制画面，界面协调用户操作。

**常见问题**

- **找不到 Python**：激活正确的 conda 环境，或设置 `RUBIK_PYTHON` 指向已有解释器。
- **找不到 ursina / magiccube**：先查看 `sys.executable` 确认环境，避免把依赖误装进 base。
- **找不到中文字体**：设置 `RUBIK_FONT` 指向自己已有的中文 `.ttf` 字体，再启动程序。
- **无法打开窗口**：检查显卡驱动、OpenGL 支持和当前桌面会话。
- **启动脚本出现半截英文被当成命令**：`.cmd` 必须保持 ASCII 内容和 CRLF 换行。

```bat
rem 指定已有中文字体，把示例路径替换为实际文件路径。
set "RUBIK_FONT=E:\fonts\ChineseFont.ttf"
rem 在已激活的项目环境中启动程序。
python -s main.py
```

**依赖来源**

三维引擎为 [Ursina](https://github.com/pokepetter/ursina)，采用 MIT 许可；魔方模型与层先法为 [magiccube](https://github.com/trincaog/magiccube)，采用 BSD-3-Clause 许可。依赖通过软件包安装获取，本项目没有复制或修改其安装目录中的源码；它们的版权与许可声明仍以原软件包为准。
