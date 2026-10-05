# ---------- 普通桌面窗口启动验收 ----------
from pathlib import Path  # 保存普通窗口渲染的截图。
from main import create_app  # 必须使用和用户启动相同的窗口入口。
from ursina import mouse  # 通过真实桌面指针接口测试事件分发。
app, ui = create_app('onscreen')  # 创建正常桌面窗口，不使用离屏替代。
try:  # 测试失败时也要释放窗口和线程。
    for _ in range(4):  # 运行真实的引擎帧循环以完成窗口初始化。
        app.taskMgr.step()  # 更新原生窗口、鼠标和界面。
    assert hasattr(app.win, 'get_pointer')  # 普通窗口必须提供真正的鼠标指针接口。
    output = Path('test_outputs')  # 截图保存到已有验收目录。
    output.mkdir(exist_ok=True)  # 保证独立运行也有输出位置。
    app.win.saveScreenshot(str(output / 'app_desktop_window.png'))  # 保存正常桌面窗口的实际渲染。
    mouse.hovered_entity = ui.buttons[0]  # 将合成测试点击的命中目标设为编辑按钮。
    app.input('mouse1')  # 事件路径读取真实桌面指针，不替代任何鼠标属性。
    app.input_up('mouse1')  # 模拟一次完整按钮点击。
    assert ui.editing  # 按钮必须通过引擎事件进入编辑模式。
    app.input('mouse3')  # 通过真实指针接口进入右键拖动。
    assert ui.dragging  # 检查观察拖动标志。
    app.input_up('mouse3')  # 释放右键结束拖动。
    assert not ui.dragging  # 释放事件必须清除观察拖动。
    result = 'DESKTOP_WINDOW_OK: 普通窗口、真实指针接口和按钮事件通过。\n'  # 保存清晰的验收结论。
    (output / 'desktop_window_report.txt').write_text(result, encoding='utf-8')  # 保存独立的正常窗口验收报告。
    print('DESKTOP_WINDOW_OK')  # 输出可识别的成功标志。
finally:  # 避免自动测试结束后留下多余窗口。
    ui.close()  # 清理求解线程。
    app.destroy()  # 关闭验收窗口。
