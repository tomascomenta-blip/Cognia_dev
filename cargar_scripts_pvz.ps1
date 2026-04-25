$proyectoPath = "D:\Descargas\Segurity copy\Assets\PVZFUSIONMOD"
$base = "http://localhost:8001/api/memoria/aprender"

# Carpetas a ignorar (generadas por Unity, no son tuyas)
$ignorar = @("Library", "Temp", "Logs", "obj", "Build", "Builds", ".git", "Packages")

$archivos = Get-ChildItem -Path $proyectoPath -Recurse -Filter "*.cs" | Where-Object {
    $ruta = $_.FullName
    $ignorar | ForEach-Object { if ($ruta -like "*\$_\*") { return } }
    $ignorar -notcontains $_.Directory.Name -and
    ($ignorar | Where-Object { $ruta -like "*\$_\*" }).Count -eq 0
}

$total = $archivos.Count
$i = 0
$ok = 0
$saltados = 0
$errores = 0

Write-Host "`n== Cargando $total scripts a Cognia Dev ==" -ForegroundColor Cyan
Write-Host "Ruta: $proyectoPath`n"

foreach ($archivo in $archivos) {
    $i++
    $nombre = $archivo.Name
    $contenido = [System.IO.File]::ReadAllText($archivo.FullName, [System.Text.Encoding]::UTF8)

    # Sin limite de tamaño - leemos todo
    # Solo saltamos archivos vacios
    if ($contenido.Trim().Length -eq 0) {
        Write-Host "  [$i/$total] SALTEADO (vacio): $nombre" -ForegroundColor DarkGray
        $saltados++
        continue
    }

    # Para archivos muy grandes (+100kb) mandamos solo las primeras 1500 lineas
    $contenidoFinal = $contenido
    if ($contenido.Length -gt 100000) {
        $lineas = $contenido -split "`n"
        $contenidoFinal = ($lineas | Select-Object -First 1500) -join "`n"
        Write-Host "  [$i/$total] GRANDE (truncado a 1500 lineas): $nombre" -ForegroundColor Yellow
    }

    try {
        $body = [ordered]@{ nombre=$nombre; contenido=$contenidoFinal; resumen="" }
        $json = $body | ConvertTo-Json -Depth 2 -Compress
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($json)
        Invoke-RestMethod -Uri $base -Method POST -ContentType "application/json; charset=utf-8" -Body $bytes | Out-Null
        Write-Host "  [$i/$total] OK: $nombre" -ForegroundColor Green
        $ok++
    } catch {
        Write-Host "  [$i/$total] ERROR: $nombre - $_" -ForegroundColor Red
        $errores++
    }
}

Write-Host "`n== Resultado ==" -ForegroundColor Cyan
Write-Host "  Cargados: $ok" -ForegroundColor Green
Write-Host "  Saltados: $saltados" -ForegroundColor DarkGray
Write-Host "  Errores:  $errores" -ForegroundColor Red

# Verificar contexto final
try {
    $ctx = Invoke-RestMethod -Uri "http://localhost:8001/api/memoria/contexto" -Method GET
    Write-Host "`n  Contexto activo: $($ctx.contexto.Length) caracteres" -ForegroundColor Cyan
} catch {}