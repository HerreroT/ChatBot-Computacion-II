# PRUEBA RÁPIDA - Sistema de Reservas
# Ejecutar: .\prueba_rapida.ps1

Write-Host "`n🚀 INICIANDO DEMO RÁPIDA...`n" -ForegroundColor Cyan

$client = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 8765)
$stream = $client.GetStream()
$reader = New-Object System.IO.StreamReader($stream)
$writer = New-Object System.IO.StreamWriter($stream)
$writer.AutoFlush = $true

# Bienvenida
$reader.ReadLine() | Out-Null

# Suscribirse
$writer.WriteLine('{"action":"subscribe","tenant_id":"barberia-01","user":"DemoUser"}')
Start-Sleep -Milliseconds 200
$reader.ReadLine() | Out-Null

# Listar horarios
Write-Host "📅 HORARIOS DISPONIBLES:" -ForegroundColor Yellow
$writer.WriteLine('{"action":"list"}')
Start-Sleep -Milliseconds 300

$slotsJson = $reader.ReadLine()
$slots = ($slotsJson | ConvertFrom-Json).slots

# Limpiar el buffer de respuestas duplicadas
while ($stream.DataAvailable) {
    $reader.ReadLine() | Out-Null
    Start-Sleep -Milliseconds 50
}

foreach ($slot in $slots | Select-Object -First 5) {
    Write-Host "   $($slot.display) - Cupos: $($slot.available)" -ForegroundColor Green
}

# Hacer reserva automática con el primer horario disponible
$primerHorario = $slots[0].slot
Write-Host "`n✅ RESERVANDO: $($slots[0].display)" -ForegroundColor Cyan

$writer.WriteLine('{"action":"book","slot":"' + $primerHorario + '"}')
Start-Sleep -Milliseconds 500

$bookResponseLine = $reader.ReadLine()
if ($bookResponseLine) {
    try {
        $bookResponse = $bookResponseLine | ConvertFrom-Json
        
        if ($bookResponse.event -eq "book.ok") {
            Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
            Write-Host "✓ RESERVA CONFIRMADA" -ForegroundColor Green
            Write-Host "   Código: $($bookResponse.code)" -ForegroundColor White
            Write-Host "   Horario: $($bookResponse.display)" -ForegroundColor White
            Write-Host "   Cupos restantes: $($bookResponse.available)" -ForegroundColor White
            Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Green
        } else {
            Write-Host "`n✗ ERROR: $($bookResponse.message)`n" -ForegroundColor Red
        }
    } catch {
        Write-Host "`n✗ ERROR procesando respuesta: $bookResponseLine`n" -ForegroundColor Red
    }
} else {
    Write-Host "`n✗ No se recibió respuesta del servidor`n" -ForegroundColor Red
}

$client.Close()

