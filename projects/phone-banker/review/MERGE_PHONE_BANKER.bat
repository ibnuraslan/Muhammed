@echo off
setlocal enabledelayedexpansion
rem Rebuilds phone_banker_film\ from the 6 parts (Windows 10/11 built-in tar reads .zip files).
cd /d "%~dp0"
set /a have=0
for %%f in (phone_banker_part*of06.zip) do set /a have+=1
if not "!have!"=="6" (
  echo Found !have! of 6 parts. Put all phone_banker_partXXof06.zip files next to this script, then run it again.
  pause & exit /b 1
)
for %%f in (phone_banker_part*of06.zip) do (
  echo Extracting %%f ...
  tar -xf "%%f"
  if errorlevel 1 ( echo FAILED on %%f - download that part again. & pause & exit /b 1 )
)
set /a n=0
for /r "phone_banker_film" %%f in (*) do set /a n+=1
echo Files in phone_banker_film: !n! (expected 382)
if "!n!"=="382" (
  echo OK - open phone_banker_film\out\blend\film\phone_banker_film.blend
) else (
  echo MISMATCH - a part is incomplete; download it again and re-run this script.
)
pause
