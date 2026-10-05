**Rubik Visual · 三阶魔方可视化复原**

**功能描述**

使用 Python、Ursina 和 magiccube 实现完整三阶魔方的三维显示与层先法复原。默认白底、黄顶、蓝前、绿后、左橙、右红，六个中心色块固定。

| 功能 | 操作与效果 |
| --- | --- |
| 观察魔方 | 按住鼠标右键拖动旋转视角，上下、左右拖动方向均为反转设置 |
| 编辑魔方 | 点击“编辑魔方”，左键选择非中心色块，再在右侧选色；完成编辑时检查颜色与物理可复原性 |
| 随机打乱 | 从复原状态执行 25 个合法随机动作，生成可复原状态并清除旧的解法 |
| 自动复原 | 根据当前颜色计算层先法并播放动画，支持暂停、继续及 1 倍、5 倍、10 倍速度 |
| 单步复原 | 每次点击转动一个面 90°；按住每秒执行一步，松开停止后续动作 |

自动复原默认约每秒一步，5 倍约每秒五步，10 倍约每秒十步，显示流畅度受设备帧率影响。单步和长按始终保持一倍速度。切换速度或暂停时，正在转动的一步会完整结束。

界面显示复原阶段、动作和进度。右键拖动只改变观察角度，不改变魔方状态；动画中暂时禁止编辑和打乱。Esc 取消当前色块选择，关闭窗口退出程序。

**配置环境**

支持 Windows，使用独立 conda 环境与 Python 3.12，需要能够运行 OpenGL 的图形环境。主要依赖为 Ursina 8.3.0、magiccube 1.2.0，全部固定版本保存在 `requirements.txt`，环境创建配置为 `environment.yml`。

默认读取电脑已有的 `C:\Windows\Fonts\simhei.ttf` 中文字体。项目不安装或分发系统字体；如需使用其他已有中文 `.ttf` 字体，可设置 `RUBIK_FONT` 为其完整路径。

在 Anaconda Prompt 或已经初始化 conda 的 CMD 中执行以下命令。示例项目路径为 `C:\Users\LENOVO\Desktop\python魔方`，环境路径为 `D:\conda_envs\rubik_visual`，其他使用者请替换为自己的实际位置。

首次创建环境：

```bat
rem 进入包含 environment.yml 的项目根目录。
cd /d "C:\Users\LENOVO\Desktop\python魔方"
rem 创建专用环境，并在其中安装 requirements.txt 的依赖。
conda env create --prefix D:\conda_envs\rubik_visual --file environment.yml
rem 激活刚创建的环境。
conda activate D:\conda_envs\rubik_visual
rem 启动程序，-s 忽略用户级 Python 包。
python -s main.py
```

已有环境且依赖已安装时，无需重复创建或安装：

```bat
rem 进入项目目录。
cd /d "C:\Users\LENOVO\Desktop\python魔方"
rem 激活已有专用环境。
conda activate D:\conda_envs\rubik_visual
rem 启动图形界面。
python -s main.py
```

也可双击 `启动魔方.cmd`。它依次选择 `RUBIK_PYTHON` 显式指定的解释器、已激活的 conda 环境、默认路径 `D:\conda_envs\rubik_visual\python.exe`，不会自动安装依赖。环境位于其他位置时，可先激活该环境再从终端启动，或设置 `RUBIK_PYTHON` 为已有 `python.exe` 的完整路径。

没有 D 盘时，可以把环境路径改成其他位置，也可以用 `conda env create --file environment.yml` 创建名为 `rubik_visual` 的环境，再执行 `conda activate rubik_visual`。环境激活时设置 `PYTHONNOUSERSITE=1`，隔离用户级 Python 包。

**版权声明**

Copyright (c) 2026 Fanfzy。本项目自身编写的代码与配套说明采用 [MIT 许可证](LICENSE)，允许使用、复制、修改和分发，包括商业使用，需保留版权与许可声明。软件按现状提供，完整条件以 LICENSE 原文为准。

| 第三方组件 | 用途 | 版权声明 | 原始许可 |
| --- | --- | --- | --- |
| [Ursina](https://github.com/pokepetter/ursina) | 三维绘制、界面和鼠标输入 | Copyright (c) 2020 Petter Amland | [MIT](https://github.com/pokepetter/ursina/blob/master/LICENSE) |
| [magiccube](https://github.com/trincaog/magiccube) | 魔方状态模型与初学者层先法 | Copyright (c) 2022 trincaog | [BSD-3-Clause](https://github.com/trincaog/magiccube/blob/main/LICENSE) |

项目 LICENSE 适用于本项目自身内容，第三方组件仍遵循各自的许可。Fanfzy 的项目署名不表示拥有第三方组件或系统字体的版权，也不表示第三方作者为本项目背书。

依赖通过软件包安装获取，本仓库不包含第三方安装包源码或系统字体。其他依赖的版权与许可声明以各自发行包为准；另行打包分发第三方组件时，需保留其许可证要求的声明。
