"""Store the Wordstat API key in the current Windows user's Credential Manager."""
import ctypes
from ctypes import wintypes
from functools import lru_cache
import sys


TARGET = 'AVIOR.Wordstat.YandexApiKey.v1'
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2
ERROR_NOT_FOUND = 1168
MAX_BLOB_SIZE = 2560


class Credential(ctypes.Structure):
    _fields_ = [
        ('Flags', wintypes.DWORD),
        ('Type', wintypes.DWORD),
        ('TargetName', wintypes.LPWSTR),
        ('Comment', wintypes.LPWSTR),
        ('LastWritten', wintypes.FILETIME),
        ('CredentialBlobSize', wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_ubyte)),
        ('Persist', wintypes.DWORD),
        ('AttributeCount', wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', wintypes.LPWSTR),
        ('UserName', wintypes.LPWSTR),
    ]


CredentialPointer = ctypes.POINTER(Credential)


@lru_cache(maxsize=1)
def credential_api():
    if sys.platform != 'win32':
        raise OSError('Диспетчер учётных данных доступен только в Windows.')
    api = ctypes.WinDLL('advapi32', use_last_error=True)
    api.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                              ctypes.POINTER(CredentialPointer)]
    api.CredReadW.restype = wintypes.BOOL
    api.CredWriteW.argtypes = [CredentialPointer, wintypes.DWORD]
    api.CredWriteW.restype = wintypes.BOOL
    api.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    api.CredDeleteW.restype = wintypes.BOOL
    api.CredFree.argtypes = [ctypes.c_void_p]
    api.CredFree.restype = None
    return api


def read_key():
    api = credential_api()
    pointer = CredentialPointer()
    if not api.CredReadW(TARGET, CRED_TYPE_GENERIC, 0, ctypes.byref(pointer)):
        error = ctypes.get_last_error()
        if error == ERROR_NOT_FOUND:
            return None
        raise ctypes.WinError(error)
    credential = pointer.contents
    try:
        return ctypes.string_at(credential.CredentialBlob, credential.CredentialBlobSize).decode('utf-8')
    finally:
        if credential.CredentialBlobSize:
            ctypes.memset(credential.CredentialBlob, 0, credential.CredentialBlobSize)
        api.CredFree(pointer)


def save_key(key):
    encoded = key.encode('utf-8')
    if not 0 < len(encoded) <= MAX_BLOB_SIZE or '\x00' in key:
        raise ValueError('Введите корректный API-ключ.')
    api = credential_api()
    buffer = (ctypes.c_ubyte * len(encoded)).from_buffer_copy(encoded)
    credential = Credential(Type=CRED_TYPE_GENERIC, TargetName=TARGET, UserName='Wordstat API',
                            CredentialBlobSize=len(buffer), CredentialBlob=buffer,
                            Persist=CRED_PERSIST_LOCAL_MACHINE)
    try:
        if not api.CredWriteW(ctypes.byref(credential), 0):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        ctypes.memset(buffer, 0, len(buffer))


def delete_key():
    api = credential_api()
    if not api.CredDeleteW(TARGET, CRED_TYPE_GENERIC, 0):
        error = ctypes.get_last_error()
        if error != ERROR_NOT_FOUND:
            raise ctypes.WinError(error)
