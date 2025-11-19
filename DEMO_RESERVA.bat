@echo off
chcp 65001 >nul
cls

echo.
echo ╔═══════════════════════════════════════════════════════╗
echo ║     DEMO - SISTEMA DE RESERVAS BARBERÍA             ║
echo ╚═══════════════════════════════════════════════════════╝
echo.

echo [1/3] Verificando servidor...
docker-compose ps | findstr "barber_tcp" >nul
if %errorlevel% neq 0 (
    echo ❌ Servidor no está corriendo. Iniciando...
    docker-compose up -d
    timeout /t 5 /nobreak >nul
) else (
    echo ✅ Servidor corriendo
)

echo.
echo [2/3] Preparando demo...
timeout /t 2 /nobreak >nul

echo.
echo [3/3] Ejecutando script de prueba...
echo ════════════════════════════════════════════════════════
echo.

powershell.exe -ExecutionPolicy Bypass -File "%~dp0prueba_rapida.ps1"

echo.
echo ════════════════════════════════════════════════════════
echo.
echo ✅ Demo completada
echo.
pause

