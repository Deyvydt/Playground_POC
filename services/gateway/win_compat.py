"""Arranca LiteLLM corrigiendo os.kill(pid, 0) en Windows.

LiteLLM vigila el proceso del query engine de Prisma con os.kill(pid, 0), que en
Unix solo comprueba si el proceso existe. En Windows la señal 0 es CTRL_C_EVENT:
cada segundo envía un Ctrl+C a toda la consola y apaga el gateway y Postgres a los
pocos segundos de arrancar. Aquí la señal 0 se vuelve una comprobación real.

Uso (lo hace start.py): python win_compat.py --config ... --host ... --port ...
"""
import ctypes
import os
import sys

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
STILL_ACTIVE = 259
_original_kill = os.kill


def _process_alive(pid: int) -> bool:
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(code))) and code.value == STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


def _kill(pid: int, sig: int) -> None:
    if sig == 0:
        if not _process_alive(pid):
            raise ProcessLookupError(pid)
        return
    _original_kill(pid, sig)


if __name__ == "__main__":
    if sys.platform == "win32":
        os.kill = _kill
    from litellm import run_server

    sys.argv[0] = "litellm"
    run_server()
