# Script de verificación rápida del servidor TCP
# Ejecutar: .\verificar_servidor.ps1

Write-Host "🔍 Verificando servidor TCP..." -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Docker
Write-Host "1. Verificando Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Docker está instalado: $dockerVersion" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Docker no está disponible" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "   ❌ Docker no está disponible" -ForegroundColor Red
    exit 1
}

# Verificar que Docker está corriendo
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Docker Desktop está corriendo" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Docker Desktop NO está corriendo!" -ForegroundColor Red
        Write-Host "   Por favor, inicia Docker Desktop" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "   ❌ Docker Desktop NO está corriendo!" -ForegroundColor Red
    Write-Host "   Por favor, inicia Docker Desktop" -ForegroundColor Yellow
    exit 1
}

# 2. Verificar puertos
Write-Host ""
Write-Host "2. Verificando puertos..." -ForegroundColor Yellow
$port8765 = netstat -ano | findstr :8765
if ($port8765) {
    Write-Host "   ⚠️  Puerto 8765 está en uso (puede ser el servidor)" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ Puerto 8765 está libre" -ForegroundColor Green
}

# 3. Verificar contenedores
Write-Host ""
Write-Host "3. Verificando contenedores..." -ForegroundColor Yellow
try {
    $containers = docker-compose ps 2>&1
    if ($containers -match "barber_tcp.*Up") {
        Write-Host "   ✅ Servidor TCP está corriendo" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Servidor TCP no está corriendo" -ForegroundColor Yellow
        Write-Host "   Ejecuta: docker-compose up" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ⚠️  No se pudo verificar contenedores" -ForegroundColor Yellow
}

# 4. Verificar conexión
Write-Host ""
Write-Host "4. Verificando conexión TCP..." -ForegroundColor Yellow
try {
    $connection = Test-NetConnection -ComputerName localhost -Port 8765 -WarningAction SilentlyContinue -InformationLevel Quiet
    if ($connection) {
        Write-Host "   ✅ Servidor responde en puerto 8765" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Servidor NO responde en puerto 8765" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ No se pudo verificar conexión" -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ Verificación completa!" -ForegroundColor Green
Write-Host ""
Write-Host "Para probar la conexión ejecuta:" -ForegroundColor Cyan
Write-Host "   python test_conexion.py" -ForegroundColor White

