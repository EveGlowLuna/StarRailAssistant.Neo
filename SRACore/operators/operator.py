import platform
import threading
import time
from pathlib import Path

import pyautogui
import pyscreeze

from SRACore.operators.ioperator import IOperator
from SRACore.operators.model import Box, Region
from SRACore.util.errors import ErrorCode, SRAError, ThreadStoppedError
from SRACore.util.logger import logger

if platform.system() == "Windows":
    import ctypes
    from ctypes.wintypes import POINT, RECT
    import pygetwindow  # type: ignore

if platform.system() == "Linux":
    try:
        from ewmh import EWMH  # type: ignore
        _EWMH_AVAILABLE = True
    except ImportError:
        _EWMH_AVAILABLE = False
        logger.warning("ewmh 未安装，窗口查找功能不可用。请运行: pip install ewmh")

    from PIL import Image as _PILImage

    def _screenshot_linux(region: tuple[int, int, int, int]) -> "_PILImage.Image":
        """
        Linux/Wayland 截图，走 XDG Desktop Portal ScreenCast + GStreamer PipeWire。
        pipeline 在进程内缓存，只有首次或 session 失效后才重建。
        """
        left, top, width, height = region
        from SRACore.util.wayland_screenshot import screenshot_region
        return screenshot_region(left, top, width, height)


class Operator(IOperator):
    def __init__(self, stop_event: threading.Event | None = None):
        super().__init__(stop_event)
        self.window_title = "崩坏：星穹铁道"
        self.top = 0
        self.left = 0
        self.width = 0
        self.height = 0
        self._win = None
        self._hwnd: int | None = None

    def is_window_active(self) -> bool:
        if platform.system() == "Windows":
            try:
                win = pygetwindow.getWindowsWithTitle(self.window_title)[0]  # type: ignore
                return win.isActive
            except (IndexError, Exception):
                return False
        elif platform.system() == "Linux":
            if not _EWMH_AVAILABLE:
                return False
            try:
                ewmh = EWMH()
                active_window = ewmh.getActiveWindow()
                if not active_window:
                    return False
                for window in ewmh.getClientList():
                    try:
                        name = ewmh.getWmName(window)
                        if name and self.window_title in (name if isinstance(name, str) else name.decode("utf-8", errors="replace")):
                            return window.id == active_window.id
                    except Exception:
                        continue
            except Exception as e:
                logger.trace(f"is_window_active 失败: {e}")
            return False
        return False

    def get_win_region(self, active_window: bool = True) -> Region:
        if platform.system() == "Windows":
            return self._get_win_region_windows(active_window)
        elif platform.system() == "Linux":
            return self._get_win_region_linux(active_window)
        raise SRAError(ErrorCode.WINDOW_NOT_FOUND, f"不支持的平台: {platform.system()}")

    def _get_win_region_windows(self, active_window: bool) -> Region:
        hwnd = self._get_hwnd()
        if hwnd is None:
            raise SRAError(ErrorCode.WINDOW_NOT_FOUND, f"未找到窗口: {self.window_title}")
        if active_window and self._win is not None and not self._win.isActive:  # type: ignore
            self._win.activate()
        region = self._get_client_region(hwnd)
        if region is None:
            raise SRAError(
                ErrorCode.WINDOW_REGION_INVALID,
                f"无法获取窗口客户区区域 '{self.window_title}'", "窗口可能被最小化")
        return region

    def _get_hwnd(self) -> int | None:
        if self._hwnd is not None and ctypes.windll.user32.IsWindow(self._hwnd):  # type: ignore  # NOQA
            return self._hwnd
        self._win = None
        self._hwnd = None
        try:
            windows = pygetwindow.getWindowsWithTitle(self.window_title)  # type: ignore
            for w in windows:
                if w.title == self.window_title:
                    self._win = w
                    self._hwnd = w._hWnd  # type: ignore  # NOQA
                    break
        except Exception as e:
            logger.trace(f"WindowNotFound: {self.window_title} -> {e}")
        return self._hwnd

    def _get_client_region(self, hwnd: int) -> Region | None:
        client_rect = RECT()  # type: ignore
        ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(client_rect))  # type: ignore  # NOQA
        left_top = POINT(client_rect.left, client_rect.top)  # type: ignore
        ctypes.windll.user32.ClientToScreen(hwnd, ctypes.byref(left_top))  # type: ignore  # NOQA
        width = client_rect.right - client_rect.left
        height = client_rect.bottom - client_rect.top
        if width <= 0 or height <= 0:
            return None
        self.left = left_top.x
        self.top = left_top.y
        self.width = width
        self.height = height
        return Region(self.left, self.top, self.width, self.height)

    def _get_win_region_linux(self, active_window: bool = True) -> Region:
        if not _EWMH_AVAILABLE:
            raise SRAError(ErrorCode.WINDOW_NOT_FOUND, "ewmh 未安装，无法查找窗口")
        ewmh = EWMH()
        for window in ewmh.getClientList():
            try:
                name = ewmh.getWmName(window)
                if not name:
                    continue
                name_str = name if isinstance(name, str) else name.decode("utf-8", errors="replace")
                if self.window_title not in name_str:
                    continue
                logger.debug(f"找到窗口 id: {window.id:x}")
                if active_window:
                    try:
                        ewmh.setActiveWindow(window)
                        ewmh.display.flush()
                        # 只等待窗口切换，不阻塞截图流程
                        time.sleep(0.1)
                    except Exception as e:
                        logger.trace(f"激活窗口失败: {e}")
                geom = window.get_geometry()
                translate = window.translate_coords(ewmh.root, 0, 0)
                abs_x = translate._data["x"]
                abs_y = translate._data["y"]
                width = geom.width
                height = geom.height
                if width <= 0 or height <= 0:
                    raise SRAError(
                        ErrorCode.WINDOW_REGION_INVALID,
                        f"无法获取窗口区域 '{self.window_title}'", "窗口可能被最小化")
                self.left = abs_x
                self.top = abs_y
                self.width = width
                self.height = height
                return Region(self.left, self.top, self.width, self.height)
            except SRAError:
                raise
            except Exception as e:
                logger.trace(f"遍历窗口失败: {e}")
                continue
        raise SRAError(ErrorCode.WINDOW_NOT_FOUND, f"未找到窗口: {self.window_title}")

    def screenshot_in_region(self, region: Region | None = None):
        if region is None:
            region = self.get_win_region(active_window=True)
        if region is None or region.width <= 0 or region.height <= 0:
            return pyscreeze.screenshot()
        if platform.system() == "Linux":
            return _screenshot_linux(region.tuple)
        return pyscreeze.screenshot(region=region.tuple)

    def screenshot_in_tuple(self, from_x: float, from_y: float, to_x: float, to_y: float):
        region = self.get_win_region()
        sub = region.sub_region(from_x, from_y, to_x, to_y)
        if platform.system() == "Linux":
            return _screenshot_linux(sub.tuple)
        return pyscreeze.screenshot(region=sub.tuple)

    def locate_in_region(self,
                         img_path: str,
                         region: Region | None = None,
                         confidence: float | None = None,
                         trace: bool = True) -> Box | None:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("图像识别中断", "线程已停止")
        match_confidence = confidence if confidence is not None else self.confidence
        try:
            if region is None:
                region = self.get_win_region()
                time.sleep(0.5)
            if not Path(img_path).exists():
                raise FileNotFoundError("无法找到或读取文件 " + img_path)
            box = pyscreeze.locate(img_path, self.screenshot(region), confidence=match_confidence)
            if box is None:
                return None
            return Box(box.left, box.top, box.width, box.height, source=img_path)
        except Exception as e:
            if trace:
                logger.trace(f"ImageNotFound: {img_path} -> {e}")
            return None

    def locate_in_tuple(self, templates: str, from_x: float, from_y: float, to_x: float, to_y: float,
                        confidence: float | None = None, trace: bool = True, **_) -> Box | None:
        try:
            region = self.get_win_region()
        except Exception as e:
            logger.trace(f"ImageNotFound: {templates} -> {e}")
            return None
        return self.locate_in_region(templates, region.sub_region(from_x, from_y, to_x, to_y), confidence, trace)

    def locate_any_in_region(self, templates: list[str], region: Region | None = None, confidence: float | None = None,
                             trace: bool = True) -> tuple[int, Box | None]:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("图像识别中断", "线程已停止")
        match_confidence = self.confidence if confidence is None else confidence
        try:
            screenshot = self.screenshot(region=region)
        except Exception as e:
            logger.debug(f"Error taking screenshot: {e}")
            return -1, None
        if screenshot is None:
            logger.debug("screenshot returned None")
            return -1, None
        for img_path in templates:
            logger.trace(f"locate_any: 检查 {img_path}")
            if not Path(img_path).exists():
                logger.debug(f"locate_any: 文件不存在 {img_path}")
                raise FileNotFoundError("无法找到或读取文件 " + img_path)
            try:
                box = pyscreeze.locate(img_path, screenshot, confidence=match_confidence)
            except (pyscreeze.ImageNotFoundException, ValueError) as e:
                if trace:
                    logger.trace(f"ImageNotFound: {img_path} -> {e}")
                continue
            except Exception as e:
                logger.debug(f"locate 异常: {img_path} -> {type(e).__name__}: {e}")
                continue
            if box is not None:
                logger.trace(f"locate_any: 找到 {img_path}")
                return templates.index(img_path), Box(box.left, box.top, box.width, box.height, source=img_path)
        logger.trace(f"locate_any: 全部未找到，返回 -1")
        return -1, None

    def locate_any_in_tuple(self, templates: list[str], from_x: float, from_y: float, to_x: float, to_y: float,
                            confidence: float | None = None, trace: bool = False) -> tuple[int, Box | None]:
        try:
            region = self.get_win_region()
        except Exception as e:
            logger.trace(f"UnexceptedInterrupt: {templates} -> {e}")
            return -1, None
        return self.locate_any_in_region(templates, region.sub_region(from_x, from_y, to_x, to_y), confidence, trace)

    def locate_all_in_region(self, template: str, region: Region | None = None, confidence: float | None = None,
                             trace: bool = True) -> list[Box] | None:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("图像识别中断", "线程已停止")
        match_confidence = self.confidence if confidence is None else confidence
        try:
            if region is None:
                region = self.get_win_region()
                time.sleep(0.5)
            if not Path(template).exists():
                raise FileNotFoundError("无法找到或读取文件 " + template)
            boxes = pyscreeze.locateAll(template, self.screenshot(region), confidence=match_confidence)
            result = []
            for box in boxes:
                result.append(Box(box.left, box.top, box.width, box.height, source=template))  # type: ignore
            return result  # type: ignore
        except Exception as e:
            if trace:
                logger.trace(f"ImageNotFound: {template} -> {e}")
            return None

    def locate_all_in_tuple(self, template: str, from_x: float, from_y: float, to_x: float, to_y: float,
                            confidence: float | None = None, trace: bool = True) -> list[Box] | None:
        try:
            region = self.get_win_region()
        except Exception as e:
            logger.trace(f"ImageNotFound: {template} -> {e}")
            return None
        return self.locate_all_in_region(template, region.sub_region(from_x, from_y, to_x, to_y), confidence, trace)

    def click_point(self, x: int | float, y: int | float, x_offset: int | float = 0, y_offset: int | float = 0,
                    after_sleep: float = 0, tag: str = "") -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("点击中断", "线程已停止")
        if isinstance(x_offset, float) and isinstance(y_offset, float):
            x_offset = int(self.width * x_offset)
            y_offset = int(self.height * y_offset)
        if isinstance(x, int) and isinstance(y, int):
            pyautogui.click(x + self.left + x_offset, y + self.top + y_offset)
            self.sleep(after_sleep)
            return True
        elif isinstance(x, float) and isinstance(y, float):
            x = int(self.left + self.width * x + x_offset)
            y = int(self.top + self.height * y + y_offset)
            logger.debug(f"Click point: ({x}, {y}), tag: {tag}")
            pyautogui.click(x, y)
            self.sleep(after_sleep)
            return True
        else:
            raise ValueError(
                f"Invalid arguments: expected 'int, int' or 'float, float', got '{type(x).__name__}, {type(y).__name__}'")

    def press_key(self, key: str, presses: int = 1, interval: float = 0, wait: float = 0, trace: bool = True) -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("按键中断", "线程已停止")
        try:
            time.sleep(wait)
            if trace:
                logger.debug(f"Press key: {key}")
            pyautogui.press(key, presses=presses, interval=interval)
            return True
        except Exception as e:
            if trace:
                logger.debug(f"Failed to press key: {e}")
            return False

    def hold_key(self, key: str, duration: float = 0) -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("按键中断", "线程已停止")
        try:
            logger.debug(f"Hold key {key}")
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            return True
        except Exception as e:
            logger.debug(f"Failed to hold key: {e}")
            return False

    def paste(self) -> None:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("粘贴中断", "线程已停止")
        pyautogui.keyDown("ctrl")
        pyautogui.keyDown("v")
        pyautogui.keyUp("v")
        pyautogui.keyUp("ctrl")

    def move_rel(self, x_offset: int, y_offset: int) -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("鼠标移动中断", "线程已停止")
        try:
            pyautogui.moveRel(x_offset, y_offset)
            return True
        except Exception as e:
            logger.debug(f"Error moving cursor: {e}")
            return False

    def move_to(self, x: int | float, y: int | float, duration: float = 0.0, trace: bool = True) -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("鼠标移动中断", "线程已停止")
        try:
            if trace:
                logger.debug(f"Move cursor to ({x}, {y}), duration: {duration}s")
            if isinstance(x, int) and isinstance(y, int):
                pyautogui.moveTo(x + self.left, y + self.top, duration=duration)
            elif isinstance(x, float) and isinstance(y, float):
                x = int(self.left + self.width * x)
                y = int(self.top + self.height * y)
                pyautogui.moveTo(x, y, duration=duration)
            else:
                raise ValueError(
                    f"Invalid arguments: expected 'int, int' or 'float, float', got '{type(x).__name__}, {type(y).__name__}'")
            return True
        except Exception as e:
            logger.debug(f"Error moving cursor: {e}")
            return False

    def mouse_down(self, x: int | float, y: int | float, trace: bool = True) -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("点击中断", "线程已停止")
        try:
            if trace:
                logger.debug(f"Mouse down: ({x}, {y})")
            if isinstance(x, int) and isinstance(y, int):
                pyautogui.mouseDown(x + self.left, y + self.top)
            elif isinstance(x, float) and isinstance(y, float):
                x = int(self.left + self.width * x)
                y = int(self.top + self.height * y)
                pyautogui.mouseDown(x, y)
            else:
                raise ValueError(
                    f"Invalid arguments: expected 'int, int' or 'float, float', got '{type(x).__name__}, {type(y).__name__}'")
            return True
        except Exception as e:
            logger.debug(f"Error pressing mouse button: {e}")
            return False

    def mouse_up(self, x: int | float | None = None, y: int | float | None = None, trace: bool = True) -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("点击中断", "线程已停止")
        try:
            if trace:
                logger.debug("Mouse up")
            pyautogui.mouseUp()
            return True
        except Exception as e:
            logger.debug(f"Error releasing mouse button: {e}")
            return False

    def scroll(self, distance: int) -> bool:
        if self.stop_event is not None and self.stop_event.is_set():
            raise ThreadStoppedError("Error scrolling", "线程已停止")
        try:
            pyautogui.scroll(distance)
            return True
        except Exception as e:
            logger.debug(f"Error scrolling: {e}")
            return False
