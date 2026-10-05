**Fanfzy 的首次上传与后续发布指南**

拟用仓库名为 `rubik-visual`，公开地址为 `https://github.com/Fanfzy/rubik-visual`。该地址只有在仓库创建后才可访问；本指南不表示已经完成上传。

**第一步：确认本地验收结果**

确认完整测试通过，打开 README 检查说明与截图。环境仍保存在 `D:\conda_envs\rubik_visual`，不会上传虚拟环境。

```bat
rem 切换到作者的项目目录，/d 同时切换盘符。
cd /d "C:\Users\LENOVO\Desktop\python魔方"
rem 使用项目专用解释器检查文档和源码格式。
D:\conda_envs\rubik_visual\python.exe -s tools\check_project.py
rem 查看 Git 工作区是否还有未提交改动。
git status
```

本地整理阶段会准备 `main` 分支与首个提交。若你在另一份全新的下载目录操作，先根据 Git 提示初始化仓库并配置提交身份；不要把教程的占位姓名或邮箱直接当成自己的身份。

**第二步：在网页新建空仓库**

登录 Fanfzy 账号，打开 [创建仓库页面](https://github.com/new)。选择：

- Owner：`Fanfzy`。
- Repository name：`rubik-visual`。
- Description：`Python 三阶魔方可视化与层先法复原，支持编辑、单步动画和速度选择，含逐行中文注释。`
- Visibility：`Public`。
- 不在网页勾选初始化 README、.gitignore 或 License；这些文件已在本地准备。

点击 Create repository。创建后检查地址确实是自己的账号与预期仓库名。GitHub 官方建议导入已有本地仓库时不要预先添加这些文件，以免引入合并冲突：[创建仓库说明](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)。

**第三步：连接远程仓库并上传**

本地 Git 保存历史；GitHub 是存放该历史的远程位置。`origin` 是远程位置的常用昵称，`main` 是当前主分支名。

```bat
rem 先查看现有远程配置，避免重复添加。
git remote -v
rem 仅在没有 origin 时执行，连接刚创建的空仓库。
git remote add origin https://github.com/Fanfzy/rubik-visual.git
rem 核对地址，确认上传目标正确。
git remote -v
rem 首次推送并建立 main 与远程分支的对应关系。
git push -u origin main
```

若已存在 origin，先核对其地址；不要反复执行 add，也不要用强制推送解决不明原因的冲突。HTTPS 登录由 Git 凭据管理器或浏览器完成。若 Git 提示认证问题，按实际提示处理；GitHub 账号密码不能直接当作 HTTPS Git 的密码：[认证说明](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github)。

**第四步：检查别人看到的页面**

打开仓库主页，确认 README 图片、内部文档链接、MIT 标识和署名正确；确认看不到环境目录、测试临时文件和字节码。

打开 Actions，等待 Core tests 的实际结果。它使用 Windows 与 Python 3.12，检查固定依赖、项目格式、核心求解和启动脚本；不会代替本地 OpenGL 图形验收。

在仓库 About 的设置中填写简介，建议 Topics 为 `python`、`rubiks-cube`、`ursina`、`3d`、`beginner-friendly`、`layer-by-layer`。这些标签帮助别人理解用途，不影响程序运行。

**第五步：发布第一个版本**

首次上传与验收通过后，在 Releases 选择创建新版本，标签建议 `v0.1.0`、目标分支 `main`，名称建议“三阶魔方可视化 · 首个教学版本”。版本说明列出功能、安装方式、已验收环境和已知限制。

初期分发源码即可，使用者按 README 创建 conda 环境；没有制作可执行安装包时，不要把源码 ZIP 描述成“免安装版”。发布时也不要上传整个 conda 环境。

**以后如何更新**

```bat
rem 查看修改内容。
git diff
rem 修改涉及图形时完成完整验收。
D:\conda_envs\rubik_visual\python.exe -s run_tests.py
rem 将经过检查的源码与说明纳入下一次提交。
git add .
rem 查看实际将提交哪些文件。
git diff --cached --stat
rem 用一句具体说明记录这次改动。
git commit -m "Improve cube editing feedback"
rem 上传新提交到已经关联的远程分支。
git push
```

每个提交尽量围绕一个具体问题。版本标签表示可复现的发布状态，不必每次小修改都发布新版本。

**许可证为什么使用 MIT**

你可以自行写授权说明，并非必须采用 MIT。但“允许修改”没有说明复制、发布修改版、商业使用和保留声明等条件。MIT 是简短的标准授权文本，其他使用者容易识别。

本项目署名为 `Copyright (c) 2026 Fanfzy`，无需为许可证登记或申请。许可证允许使用、修改和分发，包括商业使用，要求保留版权和许可声明，并载明按现状提供软件的条件。以根目录 [LICENSE](../LICENSE) 原文为准：[MIT 说明](https://choosealicense.com/licenses/mit/)。
