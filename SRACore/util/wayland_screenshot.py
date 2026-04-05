"""
Wayland 截图工具，通过 XDG Desktop Portal ScreenCast + GStreamer PipeWire 实现。

首次调用会弹出系统授权窗口，授权后保存 restore token，后续启动免授权。
Session 和 GStreamer pipeline 在进程内缓存，避免重复建立连接。

依赖（系统包）：
  sudo pacman -S gstreamer gst-plugins-good gst-plugin-pipewire python-gobject python-dbus
"""

import os
import random
import string
import threading
from typing import Optional

from PIL import Image
from loguru import logger

TOKEN_FILE = os.path.expanduser("~/.config/sra_screencast_token")

_lock = threading.Lock()
_node_id: Optional[int] = None
_session_handle: Optional[str] = None
_session_bus = None

# 复用的 GStreamer pipeline
_pipeline = None
_gst_sink = None
_gst_initialized = False
_keepalive_thread: Optional[threading.Thread] = None
_keepalive_stop = threading.Event()
_mainloop: Optional[object] = None
_mainloop_thread: Optional[threading.Thread] = None


def _ensure_mainloop():
    """确保 GLib mainloop 在后台运行，GStreamer 信号需要它。"""
    global _mainloop, _mainloop_thread
    if _mainloop_thread is not None and _mainloop_thread.is_alive():
        return
    import gi
    gi.require_version("GLib", "2.0")
    from gi.repository import GLib
    _mainloop = GLib.MainLoop()

    def run():
        _mainloop.run()

    _mainloop_thread = threading.Thread(target=run, daemon=True, name="glib-mainloop")
    _mainloop_thread.start()


def _keepalive_loop(sink):
    """定期拉帧丢弃，防止 pipeline 因缓冲满而停止推帧。"""
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst
    while not _keepalive_stop.is_set():
        try:
            sink.emit("try-pull-sample", int(0.1 * Gst.SECOND))
        except Exception:
            pass
        _keepalive_stop.wait(0.05)


def _random_token(n: int = 16) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


def _load_restore_token() -> str:
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE) as f:
                return f.read().strip()
    except Exception:
        pass
    return ""


def _save_restore_token(token: str) -> None:
    try:
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
    except Exception:
        pass


def _build_session() -> tuple[int, str, object]:
    import dbus
    import dbus.mainloop.glib
    from gi.repository import GLib

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    portal = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop")
    screencast = dbus.Interface(portal, "org.freedesktop.portal.ScreenCast")
    sender = bus.get_unique_name().lstrip(":").replace(".", "_")

    result: dict = {}
    loop = GLib.MainLoop()

    def on_response(response, results, sm=None):
        result["response"] = int(response)
        result["results"] = dict(results)
        if sm:
            sm.remove()
        loop.quit()

    # CreateSession
    req_token = _random_token()
    session_token = _random_token()
    sm1 = bus.add_signal_receiver(
        lambda r, res: on_response(r, res, sm1),
        signal_name="Response",
        dbus_interface="org.freedesktop.portal.Request",
        path=f"/org/freedesktop/portal/desktop/request/{sender}/{req_token}",
    )
    screencast.CreateSession(
        dbus.Dictionary({
            "handle_token": dbus.String(req_token),
            "session_handle_token": dbus.String(session_token),
        }, signature="sv")
    )
    loop.run()
    if result.get("response", 1) != 0:
        raise RuntimeError("ScreenCast CreateSession 失败")
    session_handle = str(result["results"]["session_handle"])

    # SelectSources
    restore_token = _load_restore_token()
    req_token2 = _random_token()
    result.clear()
    sm2 = bus.add_signal_receiver(
        lambda r, res: on_response(r, res, sm2),
        signal_name="Response",
        dbus_interface="org.freedesktop.portal.Request",
        path=f"/org/freedesktop/portal/desktop/request/{sender}/{req_token2}",
    )
    select_opts: dict = {
        "handle_token": dbus.String(req_token2),
        "types": dbus.UInt32(1),
        "multiple": dbus.Boolean(False),
        "cursor_mode": dbus.UInt32(1),
        "persist_mode": dbus.UInt32(2),
    }
    if restore_token:
        select_opts["restore_token"] = dbus.String(restore_token)
    screencast.SelectSources(session_handle, dbus.Dictionary(select_opts, signature="sv"))
    loop.run()
    if result.get("response", 1) != 0:
        raise RuntimeError("ScreenCast SelectSources 失败（用户取消授权？）")

    # Start
    req_token3 = _random_token()
    result.clear()
    sm3 = bus.add_signal_receiver(
        lambda r, res: on_response(r, res, sm3),
        signal_name="Response",
        dbus_interface="org.freedesktop.portal.Request",
        path=f"/org/freedesktop/portal/desktop/request/{sender}/{req_token3}",
    )
    screencast.Start(session_handle, "", dbus.Dictionary({"handle_token": dbus.String(req_token3)}, signature="sv"))
    loop.run()
    if result.get("response", 1) != 0:
        raise RuntimeError("ScreenCast Start 失败")

    streams = result["results"].get("streams", [])
    if not streams:
        raise RuntimeError("ScreenCast 没有返回 stream")
    node_id = int(streams[0][0])

    new_token = str(result["results"].get("restore_token", ""))
    if new_token:
        _save_restore_token(new_token)

    return node_id, session_handle, bus


# 最新帧缓存，由 GStreamer 回调线程写入，截图时直接读取
_latest_frame: Optional[Image.Image] = None
_frame_lock = threading.Lock()
_frame_seq = 0  # 帧序号，每来一帧递增


def _build_pipeline(node_id: int):
    """建立并启动 GStreamer pipeline，用 emit-signals 回调持续缓存最新帧。"""
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import Gst

    global _gst_initialized
    if not _gst_initialized:
        Gst.init(None)
        _gst_initialized = True

    _ensure_mainloop()

    pipeline_str = (
        f"pipewiresrc path={node_id} ! "
        "videoconvert ! "
        "video/x-raw,format=RGB ! "
        "appsink name=sink emit-signals=true max-buffers=1 drop=true sync=false"
    )
    pipeline = Gst.parse_launch(pipeline_str)
    sink = pipeline.get_by_name("sink")

    def on_new_sample(appsink):
        global _latest_frame, _frame_seq
        sample = appsink.emit("pull-sample")
        if sample:
            buf = sample.get_buffer()
            caps = sample.get_caps()
            s = caps.get_structure(0)
            w = s.get_value("width")
            h = s.get_value("height")
            ok, mapinfo = buf.map(Gst.MapFlags.READ)
            if ok:
                try:
                    data = bytes(mapinfo.data)
                    img = Image.frombytes("RGB", (w, h), data)
                    with _frame_lock:
                        _latest_frame = img
                        _frame_seq += 1
                finally:
                    buf.unmap(mapinfo)
        return Gst.FlowReturn.OK

    sink.connect("new-sample", on_new_sample)
    pipeline.set_state(Gst.State.PLAYING)
    pipeline.get_state(timeout=3 * Gst.SECOND)
    # 等第一帧到位
    import time as _time
    deadline = _time.time() + 5.0
    while _time.time() < deadline:
        with _frame_lock:
            if _latest_frame is not None:
                break
        _time.sleep(0.05)
    return pipeline, sink


def _pull_frame(sink=None, timeout_s: float = 3.0) -> Image.Image:
    """等待并返回一帧比调用时更新的帧，确保拿到的是最新画面。"""
    import time as _time
    with _frame_lock:
        current_seq = _frame_seq
    deadline = _time.time() + timeout_s
    while _time.time() < deadline:
        with _frame_lock:
            if _frame_seq > current_seq and _latest_frame is not None:
                return _latest_frame.copy()
        _time.sleep(0.02)
    raise RuntimeError("GStreamer 截帧超时")
    return Image.frombytes("RGB", (w, h), data)


def _get_pipeline():
    """获取缓存的 pipeline，不存在则新建 session + pipeline。"""
    global _node_id, _session_handle, _session_bus, _pipeline, _gst_sink
    with _lock:
        if _pipeline is not None:
            return _pipeline, _gst_sink
        logger.debug("建立 ScreenCast session...")
        _node_id, _session_handle, _session_bus = _build_session()
        logger.debug(f"ScreenCast session 建立成功，PipeWire node id: {_node_id}")
        _pipeline, _gst_sink = _build_pipeline(_node_id)
        return _pipeline, _gst_sink


def _invalidate() -> None:
    global _node_id, _session_handle, _session_bus, _pipeline, _gst_sink, _latest_frame
    with _lock:
        if _pipeline is not None:
            try:
                import gi
                gi.require_version("Gst", "1.0")
                from gi.repository import Gst
                _pipeline.set_state(Gst.State.NULL)
            except Exception:
                pass
            _pipeline = None
            _gst_sink = None
        with _frame_lock:
            _latest_frame = None
            _frame_seq = 0
        if _session_handle and _session_bus:
            try:
                import dbus
                session = _session_bus.get_object("org.freedesktop.portal.Desktop", _session_handle)
                dbus.Interface(session, "org.freedesktop.portal.Session").Close()
            except Exception:
                pass
        _node_id = None
        _session_handle = None
        _session_bus = None


def screenshot_region(x: int, y: int, width: int, height: int) -> Image.Image:
    """
    截取屏幕指定区域，返回 PIL Image。
    截图前将鼠标移到屏幕右下角避免遮挡，截完移回原位。
    pipeline 在进程内缓存，只有首次或 session 失效后才重建。
    """
    import pyautogui
    pyautogui.FAILSAFE = False

    # 移到右上角：不触发 Dash To Dock，也不在游戏区域内
    screen_w, _ = pyautogui.size()
    orig_pos = pyautogui.position()
    pyautogui.moveTo(screen_w - 1, 0, duration=0)

    try:
        try:
            _, sink = _get_pipeline()
            frame = _pull_frame(sink)
            result = frame.crop((x, y, x + width, y + height))
            logger.trace(f"截图成功: ({x},{y},{width},{height}) -> {result.size}")
            return result
        except Exception as e:
            logger.debug(f"截图失败，重建 session: {e}")
            _invalidate()
            _, sink = _get_pipeline()
            frame = _pull_frame(sink)
            result = frame.crop((x, y, x + width, y + height))
            logger.trace(f"截图成功(重建后): ({x},{y},{width},{height}) -> {result.size}")
            return result
    finally:
        pyautogui.moveTo(orig_pos.x, orig_pos.y, duration=0)
