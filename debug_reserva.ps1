# Script de depuración - muestra todo lo que recibe del servidor
param(
    [string]$Horario = "2025-11-20 14:00"
)

Write-Host "Conectando..." -ForegroundColor Cyan

$client = New-Object System.Net.Sockets.TcpClient("127.0.0.1", 8765)
$stream = $client.GetStream()
$reader = New-Object System.IO.StreamReader($stream)
$writer = New-Object System.IO.StreamWriter($stream)
$writer.AutoFlush = $true

# Recibir welcome
Write-Host "`n1. WELCOME:" -ForegroundColor Yellow
$line = $reader.ReadLine()
Write-Host $line -ForegroundColor Gray

# Suscribir
Write-Host "`n2. ENVIANDO SUBSCRIBE..." -ForegroundColor Yellow
$writer.WriteLine('{"action":"subscribe","tenant_id":"barberia-01","user":"Debug"}')
Start-Sleep -Milliseconds 300
$line = $reader.ReadLine()
Write-Host "RESPUESTA:" -ForegroundColor Green
Write-Host $line -ForegroundColor Gray

# Pedir slots
Write-Host "`n3. ENVIANDO LIST..." -ForegroundColor Yellow
$writer.WriteLine('{"action":"list"}')
Start-Sleep -Milliseconds 500

# Leer respuesta de slots (puede haber 1 o 2 líneas)
$line = $reader.ReadLine()
Write-Host "RESPUESTA SLOTS:" -ForegroundColor Green
Write-Host $line -ForegroundColor Gray

# Reservar
Write-Host "`n4. ENVIANDO BOOK para: $Horario" -ForegroundColor Yellow
$writer.WriteLine("{`"action`":`"book`",`"slot`":`"$Horario`"}")
Start-Sleep -Milliseconds 1000

# Leer todas las respuestas disponibles
Write-Host "RESPUESTA BOOK:" -ForegroundColor Green
$timeout = 0
while ($timeout -lt 20) {
    if ($stream.DataAvailable) {
        $line = $reader.ReadLine()
        Write-Host $line -ForegroundColor Cyan
    } else {
        Start-Sleep -Milliseconds 100
        $timeout++
    }
}

$client.Close()
Write-Host "`nConexión cerrada" -ForegroundColor Gray

