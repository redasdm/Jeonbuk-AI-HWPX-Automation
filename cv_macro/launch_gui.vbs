' launch_gui.vbs - 콘솔 창 없이 GUI 앱만 실행
Set WshShell = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = scriptDir
WshShell.Run scriptDir & "\.venv\Scripts\pythonw.exe gui_app.py", 0, False
