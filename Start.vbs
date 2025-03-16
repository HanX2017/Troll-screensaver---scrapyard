Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c timeout /t 20 && python main.py", 0, False
