**第三方来源与许可声明**

本项目自写代码的许可证为根目录 [LICENSE](LICENSE)。以下组件保留各自的版权与许可条件；项目许可证不会改变依赖许可证。

| 组件 | 验收版本 | 来源 | 声明文件 |
| --- | --- | --- | --- |
| Ursina | 8.3.0 | https://github.com/pokepetter/ursina | [MIT 原文](third_party_licenses/ursina-MIT.txt) |
| magiccube | 1.2.0 | https://github.com/trincaog/magiccube | [BSD-3-Clause 原文](third_party_licenses/magiccube-BSD-3-Clause.txt) |

`rubik/solver.py` 对固定版本 magiccube 的阶段接口进行适配，`rubik/model.py` 对其面顺序进行转换。项目未把安装包源码复制为自己的模块，也没有修改环境中的第三方源码。

完整依赖包括 Panda3D、NumPy、Pillow 等，版本清单见 [requirements-lock.txt](requirements-lock.txt)。它们通过正常的软件包安装获取，版权与许可证以各发行包携带的声明为准。本文件列出了本项目直接选用的两个主要组件，不宣称是所有间接依赖许可证的完整副本。

项目运行时读取使用者已有的中文字体；仓库不包含 Windows 字体文件。展示图片由本项目图形测试生成。
