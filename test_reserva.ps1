# Script para probar el sistema de reservas
# Ejecutar desde: ChatBot-Computacion-II\

param(
    [string]$Usuario = "Cliente1",
    [string]$Horario = ""
)

Write-Host "`n╔═══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     SISTEMA DE RESERVAS - BARBERÍA COMPUTACIÓN II       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Conectar al servidor
$client = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 8765)
$stream = $client.GetStream()
$reader = New-Object System.IO.StreamReader($stream)
$writer = New-Object System.IO.StreamWriter($stream)
$writer.AutoFlush = $true

# Mensaje de bienvenida
Write-Host "► Conectándose al servidor..." -ForegroundColor Green
$welcome = $reader.ReadLine()
Write-Host "  $welcome`n" -ForegroundColor Gray

# Suscribirse
Write-Host "► Suscribiéndose como usuario: $Usuario" -ForegroundColor Green
$writer.WriteLine('{"action":"subscribe","tenant_id":"barberia-01","user":"' + $Usuario + '"}')
Start-Sleep -Milliseconds 300
$response = $reader.ReadLine()
Write-Host "  $response`n" -ForegroundColor Gray

# Listar horarios disponibles
Write-Host "► Obteniendo horarios disponibles..." -ForegroundColor Green
$writer.WriteLine('{"action":"list"}')
Start-Sleep -Milliseconds 500

$slotsJson = $reader.ReadLine()
$slots = ($slotsJson | ConvertFrom-Json).slots

# Limpiar el buffer de cualquier respuesta duplicada
while ($stream.DataAvailable) {
    $reader.ReadLine() | Out-Null
    Start-Sleep -Milliseconds 50
}

Write-Host "`n╔═════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
Write-Host "║           HORARIOS DISPONIBLES - HOY                  ║" -ForegroundColor Yellow
Write-Host "╚═════════════════════════════════════════════════════════╝" -ForegroundColor Yellow

foreach ($slot in $slots) {
    $disponible = if ($slot.available -gt 0) { "✓" } else { "✗" }
    $color = if ($slot.available -gt 0) { "Green" } else { "Red" }
    Write-Host "  $disponible $($slot.display) - Disponibles: $($slot.available)/$($slot.capacity)" -ForegroundColor $color
}

# Seleccionar horario para reservar
if ($Horario -eq "") {
    Write-Host "`n¿Qué horario deseas reservar? (formato: 2025-11-19 14:00)" -ForegroundColor Cyan
    $Horario = Read-Host "Horario"
}

# Hacer la reserva
Write-Host "`n► Realizando reserva para: $Horario" -ForegroundColor Green
$writer.WriteLine('{"action":"book","slot":"' + $Horario + '"}')
Start-Sleep -Milliseconds 800

$bookResponseLine = ""
$attempts = 0
while ($stream.DataAvailable -or $attempts -lt 10) {
    if ($stream.DataAvailable) {
        $bookResponseLine = $reader.ReadLine()
        break
    }
    Start-Sleep -Milliseconds 100
    $attempts++
}

if ($bookResponseLine -eq "") {
    Write-Host "`n✗ No se recibió respuesta del servidor (pero la reserva puede haberse creado)`n" -ForegroundColor Yellow
    $client.Close()
    return
}

$bookResponse = $bookResponseLine | ConvertFrom-Json

if ($bookResponse.event -eq "book.ok") {
    Write-Host "`n╔═════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║              ✓ RESERVA CONFIRMADA                      ║" -ForegroundColor Green
    Write-Host "╚═════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host "  Usuario:     $Usuario" -ForegroundColor White
    Write-Host "  Fecha/Hora:  $($bookResponse.display)" -ForegroundColor White
    Write-Host "  Código:      $($bookResponse.code)" -ForegroundColor Cyan
    Write-Host "  Cupos:       $($bookResponse.occupied) ocupado(s), $($bookResponse.available) disponible(s)`n" -ForegroundColor White
} else {
    Write-Host "`n✗ Error en la reserva: $($bookResponse.message)`n" -ForegroundColor Red
}

$client.Close()
Write-Host "► Conexión cerrada`n" -ForegroundColor Gray

