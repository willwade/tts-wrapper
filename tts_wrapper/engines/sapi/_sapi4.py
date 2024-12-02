import os
import winreg

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE", 0, winreg.KEY_WRITE):
            return True
    except PermissionError:
        return False
    
def find_sapi4_dll_path() -> str:
    """
    Locates and returns the path to the SAPI 4 DLL (speech.dll).
    Returns:
        str: Full path to the SAPI 4 DLL.
    """
    sapi4_path = os.path.join(os.getenv("WINDIR"), "Speech", "speech.dll")
    if not os.path.exists(sapi4_path):
        raise FileNotFoundError("SAPI 4 speech.dll not found in C:\\Windows\\Speech.")
    return sapi4_path

def find_sapi4_clsid() -> str:
    """
    Locates and returns the CLSID for SAPI 4 by searching the registry.
    Returns:
        str: The CLSID of the SAPI 4 COM object.
    """
    try:
        # Registry path for SAPI 4 (may vary based on installation)
        clsid_key_path = r"SOFTWARE\Classes\SAPI4\CLSID"
        
        # Open the registry key
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_READ) as key:
            clsid, _ = winreg.QueryValueEx(key, None)  # Default value contains the CLSID
            return clsid
    except FileNotFoundError:
        raise Exception("SAPI 4 CLSID not found in the registry. Ensure SAPI 4 is installed.")

def get_appid_for_clsid(clsid):
    try:
        registry_path = f"CLSID\\{clsid}\\AppID"
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, registry_path) as key:
            appid, _ = winreg.QueryValueEx(key, None)  # Default value of the key
            return appid
    except FileNotFoundError:
        return None

def configure_sapi4_surrogacy(clsid: str, appid: str, dll_path: str) -> None:
    """
    Configures COM surrogacy for SAPI 4 if not already set up.
    
    Args:
        clsid (str): The CLSID of the SAPI 4 COM object.
        appid (str): The AppID for the COM object.
        dll_path (str): Full path to the speech.dll.
    """
    try:
        # Check if CLSID is registered
        clsid_key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_READ):
            print(f"CLSID {clsid} is registered.")
    except FileNotFoundError:
        raise Exception(f"CLSID {clsid} is not registered. Ensure SAPI 4 is installed.")

    try:
        # Check or set AppID
        appid_key_path = f"SOFTWARE\\Classes\\AppID\\{appid}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, appid_key_path, 0, winreg.KEY_READ):
            print(f"AppID {appid} is already configured.")
    except FileNotFoundError:
        # Create AppID key and set DllSurrogate
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, appid_key_path) as appid_key:
            winreg.SetValueEx(appid_key, "DllSurrogate", 0, winreg.REG_SZ, "")
            print(f"AppID {appid} configured with DllSurrogate.")

    # Link CLSID to AppID
    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_SET_VALUE) as clsid_key:
        winreg.SetValueEx(clsid_key, "AppID", 0, winreg.REG_SZ, appid)
        print(f"CLSID {clsid} linked to AppID {appid}.")

    # Register speech.dll as the COM server
    if not os.path.exists(dll_path):
        raise FileNotFoundError(f"speech.dll not found at {dll_path}.")
    try:
        os.system(f'regsvr32 /s "{dll_path}"')
        print(f"{dll_path} registered successfully.")
    except Exception as e:
        raise Exception(f"Failed to register {dll_path}: {e}")

    print("SAPI 4 surrogacy setup completed.")

def check_sapi4_installation():
    try:
        # Check if speech.dll exists
        sapi4_dll_path = os.path.join(os.getenv("WINDIR"), "Speech", "speech.dll")
        if not os.path.exists(sapi4_dll_path):
            return "SAPI4 DLL not found."

        # Check if CLSID is registered
        clsid_key_path = r"SOFTWARE\Classes\CLSID\{A910187F-0C7A-45AC-92CC-59EDAFB77B53}"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_READ):
            return "SAPI4 CLSID is registered."
    except FileNotFoundError:
        return "SAPI4 CLSID is not registered. Please register speech.dll."
    except Exception as e:
        return f"Error checking SAPI4 installation: {e}"


import os
import uuid
import winreg


def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE", 0, winreg.KEY_WRITE):
            return True
    except PermissionError:
        return False


import os
import winreg
import uuid
import ctypes
from ctypes.wintypes import BOOL, HWND, LPWSTR, UINT

# Constants for privilege escalation
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008

class LUID(ctypes.Structure):
    _fields_ = [("LowPart", ctypes.c_ulong), ("HighPart", ctypes.c_long)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [("PrivilegeCount", ctypes.c_ulong),
                ("Privileges", LUID * 1)]

def enable_privilege(privilege: str):
    """
    Enables a system privilege for the current process (e.g., SeTakeOwnershipPrivilege).
    """
    hToken = ctypes.c_void_p()
    ctypes.windll.advapi32.OpenProcessToken(
        ctypes.windll.kernel32.GetCurrentProcess(),
        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
        ctypes.byref(hToken)
    )
    
    luid = LUID()
    ctypes.windll.advapi32.LookupPrivilegeValueW(None, privilege, ctypes.byref(luid))
    
    tp = TOKEN_PRIVILEGES(1, (luid,))
    tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED
    
    ctypes.windll.advapi32.AdjustTokenPrivileges(hToken, False, ctypes.byref(tp), 0, None, None)
    ctypes.windll.kernel32.CloseHandle(hToken)

def take_ownership_and_set_permissions(key_path: str):
    """
    Takes ownership of a registry key and grants full permissions.
    """
    key = None  # Ensure 'key' is always defined
    try:
        enable_privilege("SeTakeOwnershipPrivilege")
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, "TestPermission", 0, winreg.REG_SZ, "Check")
        print(f"Permissions modified for {key_path}.")
        winreg.DeleteValue(key, "TestPermission")  # Clean up
    except PermissionError:
        print(f"Could not modify permissions for {key_path}. Ensure you have administrative privileges.")
    except Exception as e:
        print(f"Unexpected error while modifying permissions for {key_path}: {e}")
    finally:
        if key:
            key.Close()

def assign_appid_to_clsid(clsid, appid):
    """
    Assigns AppID to CLSID and sets permissions.
    """
    clsid_key_path = f"SOFTWARE\\Classes\\CLSID\\{clsid}"
    appid_key_path = f"SOFTWARE\\Classes\\AppID\\{appid}"

    try:
        # Modify permissions if needed
        take_ownership_and_set_permissions(clsid_key_path)

        # Link CLSID to AppID
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, clsid_key_path, 0, winreg.KEY_SET_VALUE) as clsid_key:
            winreg.SetValueEx(clsid_key, "AppID", 0, winreg.REG_SZ, appid)
        print(f"Linked CLSID {clsid} to AppID {appid}.")

        # Create the AppID key and set DllSurrogate
        with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, appid_key_path) as appid_key:
            winreg.SetValueEx(appid_key, "DllSurrogate", 0, winreg.REG_SZ, "")
        print(f"AppID {appid} created with DllSurrogate enabled.")
    except PermissionError as e:
        print(f"Registry write access denied: {e}.")
        print("Falling back to creating a .reg file for manual application.")
        create_reg_file(clsid, appid)
    except Exception as e:
        print(f"Unexpected error: {e}")

def create_reg_file(clsid: str, appid: str):
    """
    Generate a .reg file to configure SAPI 4 CLSID and AppID registry entries.
    """
    reg_content = (
        "Windows Registry Editor Version 5.00\r\n\r\n"
        f"[HKEY_LOCAL_MACHINE\\SOFTWARE\\Classes\\CLSID\\{clsid}]\r\n"
        f"\"AppID\"=\"{appid}\"\r\n\r\n"
        f"[HKEY_LOCAL_MACHINE\\SOFTWARE\\Classes\\AppID\\{appid}]\r\n"
        "\"DllSurrogate\"=\"\"\r\n"
    )
    reg_file_path = os.path.join(os.getcwd(), "sapi4_setup.reg")
    with open(reg_file_path, "w", encoding="utf-8") as reg_file:
        reg_file.write(reg_content)
    print(f".reg file created at: {reg_file_path}")
    print("Double-click the .reg file to apply the settings to the registry.")

if __name__ == "__main__":
    clsid = "{A910187F-0C7A-45AC-92CC-59EDAFB77B53}"
    appid = f"{{{str(uuid.uuid4()).upper()}}}"

    try:
        assign_appid_to_clsid(clsid, appid)
    except Exception as e:
        print(f"Error occurred: {e}")