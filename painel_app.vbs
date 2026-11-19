Set WShell = CreateObject("WScript.Shell")
WShell.Run chr(34) & WShell.CurrentDirectory & "\painel_app.bat" & chr(34), 0, False
Set WShell = Nothing