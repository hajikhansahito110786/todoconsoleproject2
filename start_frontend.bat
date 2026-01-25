@echo off
echo Starting Next.js Development Server...
echo.
echo If you encounter permission errors, try running this script as Administrator
echo.
echo Clearing Next.js cache...
if exist .next rmdir /s /q .next
echo.
echo Starting development server...
npm run dev
pause