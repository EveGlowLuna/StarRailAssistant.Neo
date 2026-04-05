"""
跨平台加密工具。

使用 cryptography 库的 Fernet 对称加密，密钥由机器唯一标识派生，
绑定到当前机器（类似 Windows DPAPI 的效果），全平台通用。

依赖: pip install cryptography
"""

import base64
import hashlib
import platform


def _get_machine_id() -> bytes:
    """获取机器唯一标识，用于派生加密密钥。"""
    machine_id = ""

    if platform.system() == "Linux":
        # /etc/machine-id 是 systemd 标准，几乎所有发行版都有
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            try:
                with open(path) as f:
                    machine_id = f.read().strip()
                if machine_id:
                    break
            except OSError:
                continue

    elif platform.system() == "Windows":
        try:
            import winreg  # type: ignore
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography"
            )
            machine_id, _ = winreg.QueryValueEx(key, "MachineGuid")
            winreg.CloseKey(key)
        except Exception:
            pass

    elif platform.system() == "Darwin":
        try:
            import subprocess
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if "IOPlatformUUID" in line:
                    machine_id = line.split('"')[-2]
                    break
        except Exception:
            pass

    if not machine_id:
        # 最后回退：用主机名，不理想但总比崩溃好
        import socket
        machine_id = socket.gethostname()

    return machine_id.encode("utf-8")


def _derive_key() -> bytes:
    """从机器 ID 派生 32 字节 Fernet 密钥（URL-safe base64 编码）。"""
    raw = hashlib.sha256(_get_machine_id()).digest()
    return base64.urlsafe_b64encode(raw)


def encrypt(plaintext: str) -> str:
    """加密字符串，返回 base64 编码的密文。"""
    from cryptography.fernet import Fernet  # type: ignore
    f = Fernet(_derive_key())
    return f.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt(ciphertext: str) -> str:
    """解密字符串，失败时返回空字符串。"""
    if not ciphertext:
        return ""
    try:
        from cryptography.fernet import Fernet, InvalidToken  # type: ignore
        f = Fernet(_derive_key())
        return f.decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""


def win_decryptor(entropy: str | None = None) -> str:
    """
    兼容旧接口。原来在 Windows 上用 DPAPI 解密，现在统一走 Fernet。

    注意：旧版 Windows DPAPI 加密的数据无法在此解密（协议不同）。
    如果用户从旧版迁移，需要重新输入并保存一次密码。
    """
    return decrypt(entropy or "")
