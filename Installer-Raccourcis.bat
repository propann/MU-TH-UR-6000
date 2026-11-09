@echo off
rem ============================================================
rem  Cree les raccourcis "Veille Azoth" (Bureau + menu Demarrer)
rem  A relancer si tu deplaces le dossier veille-azoth.
rem
rem  Le raccourci lance pythonw.exe (Python SANS fenetre noire) :
rem  la veille tourne en arriere-plan, on l'arrete avec le bouton
rem  du tableau de bord. Journal : data\veille.log
rem ============================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$dir = (Get-Location).Path;" ^
  "$py = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source;" ^
  "if (-not $py) { $p = (Get-Command python.exe -ErrorAction SilentlyContinue).Source; if ($p) { $py = Join-Path (Split-Path $p) 'pythonw.exe' } };" ^
  "if (-not $py -or -not (Test-Path $py)) { Write-Host 'pythonw.exe introuvable : installe Python depuis python.org'; exit 1 };" ^
  "$ws = New-Object -ComObject WScript.Shell;" ^
  "foreach ($target in @([Environment]::GetFolderPath('Desktop'), (Join-Path ([Environment]::GetFolderPath('Programs')) ''))) {" ^
  "  $lnk = $ws.CreateShortcut((Join-Path $target 'Veille Azoth.lnk'));" ^
  "  $lnk.TargetPath = $py; $lnk.Arguments = '\"' + (Join-Path $dir 'veille.py') + '\"';" ^
  "  $lnk.WorkingDirectory = $dir; $lnk.IconLocation = (Join-Path $dir 'dist\azoth.ico');" ^
  "  $lnk.Description = 'MU-TH-UR // Veille Azoth'; $lnk.Save(); Write-Host ('Raccourci cree : ' + $lnk.FullName) }"
echo.
echo Termine. Double-clique sur "Veille Azoth" sur ton Bureau.
pause
