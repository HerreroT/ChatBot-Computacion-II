# Script de pruebas para Windows PowerShell

$baseUrl = "http://localhost:8000"

Write-Host "🧪 Ejecutando pruebas del sistema de reservas..." -ForegroundColor Cyan
Write-Host ""

Write-Host "1️⃣  Health check..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/health" -Method GET
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Body: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "2️⃣  Crear reserva válida..." -ForegroundColor Yellow
$body1 = @{
    message_id = "pwsh-001"
    from = "+5492611111111"
    body = "corte 15/12 16:00"
    tenant_id = "barberia-01"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/webhook/whatsapp" -Method POST -Body $body1 -ContentType "application/json"
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Body: $($response.Content)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
    if ($_.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        Write-Host "   Response: $($reader.ReadToEnd())" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "3️⃣  Verificar idempotencia (misma reserva)..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/webhook/whatsapp" -Method POST -Body $body1 -ContentType "application/json"
    Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host "   Body: $($response.Content)" -ForegroundColor Gray
    if ($response.Content -match "pwsh-001") {
        Write-Host "   ✅ Idempotencia funcionando" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "4️⃣  Probar fecha pasada (debe fallar)..." -ForegroundColor Yellow
$body2 = @{
    message_id = "pwsh-past"
    from = "+5492611111111"
    body = "corte 01/01 10:00"
    tenant_id = "barberia-01"
} | ConvertTo-Json

try {
    $response = Invoke-WebRequest -Uri "$baseUrl/webhook/whatsapp" -Method POST -Body $body2 -ContentType "application/json"
    Write-Host "   ⚠️  Debería haber fallado pero no falló" -ForegroundColor Red
} catch {
    if ($_.Exception.Response.StatusCode -eq 422) {
        Write-Host "   Status: 422 (esperado)" -ForegroundColor Green
        Write-Host "   ✅ Fecha pasada rechazada correctamente" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Error inesperado: $_" -ForegroundColor Red
    }
}
Write-Host ""

Write-Host "5️⃣  Ver métricas..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "$baseUrl/metrics" -Method GET
    $metrics = $response.Content
    $matches = [regex]::Matches($metrics, "reservations_.*?total\s+(\d+)")
    if ($matches.Count -gt 0) {
        foreach ($match in $matches) {
            Write-Host "   $($match.Value)" -ForegroundColor Gray
        }
    } else {
        Write-Host "   (aún no hay métricas)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}
Write-Host ""

Write-Host "✅ Pruebas completadas!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Para más opciones, abre: http://localhost:8000/docs" -ForegroundColor Cyan








