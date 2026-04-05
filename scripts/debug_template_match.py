"""
模板匹配颜色差异分析工具。
运行后有5秒时间切换到游戏窗口，然后自动截图并分析模板匹配情况。
用法: python scripts/debug_template_match.py resources/img/tp/"calyx(crimson) (16).png"
"""
import sys
import os
import time
import cv2
import numpy as np
from PIL import Image

# 把项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/debug_template_match.py <模板图路径>")
        sys.exit(1)

    tmpl_path = sys.argv[1]

    print("正在建立 ScreenCast session（如有授权弹窗请先点击允许）...")
    from SRACore.util.wayland_screenshot import screenshot_region
    # 先截一帧触发 session 建立和 keepalive 启动
    screenshot_region(0, 0, 1, 1)

    print("\n10秒后截图，请切换到游戏窗口...")
    for i in range(10, 0, -1):
        print(f"  {i}...")
        time.sleep(1)

    screen = screenshot_region(0, 0, 1920, 1080)
    screen_arr = np.array(screen)
    screen_bgr = screen_arr[:, :, ::-1].copy()

    tmpl = cv2.imread(tmpl_path, cv2.IMREAD_COLOR)
    if tmpl is None:
        print(f"无法读取模板图: {tmpl_path}")
        sys.exit(1)

    result = cv2.matchTemplate(screen_bgr, tmpl, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    print(f"\n最高 confidence: {max_val:.4f}  位置: {max_loc}")

    h, w = tmpl.shape[:2]
    x, y = max_loc
    region_bgr = screen_bgr[y:y+h, x:x+w]

    print(f"模板图 mean BGR:      {tmpl.mean(axis=(0,1)).round(1)}")
    print(f"截图对应区域 mean BGR: {region_bgr.mean(axis=(0,1)).round(1)}")

    # 计算亮度比例
    tmpl_brightness = tmpl.mean()
    region_brightness = region_bgr.mean()
    ratio = region_brightness / tmpl_brightness if tmpl_brightness > 0 else 1.0
    print(f"\n亮度比例 (截图/模板): {ratio:.3f}")

    # 保存对比图
    screen.save("/tmp/debug_screen.png")
    Image.fromarray(region_bgr[:, :, ::-1]).save("/tmp/debug_match_region.png")
    Image.fromarray(tmpl[:, :, ::-1]).save("/tmp/debug_template.png")
    print("\n已保存:")
    print("  /tmp/debug_screen.png       - 全屏截图")
    print("  /tmp/debug_match_region.png - 截图中匹配到的区域")
    print("  /tmp/debug_template.png     - 模板图")

if __name__ == "__main__":
    main()
