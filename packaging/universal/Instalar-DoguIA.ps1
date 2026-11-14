# Entrada Windows. PowerShell do sistema, sem Python nem downloads adicionais.
param([switch]$Verificar, [switch]$SemAbrir)
$ErrorActionPreference = 'Stop'
try {
    $arquitetura = $env:PROCESSOR_ARCHITEW6432
    if (-not $arquitetura) { $arquitetura = $env:PROCESSOR_ARCHITECTURE }
    if ($arquitetura -ne 'AMD64') { throw 'Este pacote Windows requer um sistema x64. Consulte LEIA-ME.html.' }
    $manifesto = Join-Path $PSScriptRoot 'pacotes.tsv'
    if (-not (Test-Path -LiteralPath $manifesto)) { throw 'Extraia o ZIP inteiro antes de instalar (pacotes.tsv ausente).' }
    $linhas = @(Get-Content -LiteralPath $manifesto | Where-Object { $_.StartsWith("windows-x64`t") })
    if ($linhas.Count -ne 1) { throw 'O pacote Windows não foi encontrado no manifesto.' }
    $campos = $linhas[0].Split("`t")
    if ($campos.Count -ne 3 -or $campos[1] -notmatch '^[a-zA-Z0-9._-]+$' -or $campos[2] -notmatch '^[a-f0-9]{64}$') { throw 'Manifesto inválido.' }
    $arquivo = Join-Path (Join-Path $PSScriptRoot 'pacotes') $campos[1]
    Write-Host 'DoguIA Companion — conferindo o instalador Windows…'
    if ((Get-FileHash -LiteralPath $arquivo -Algorithm SHA256).Hash.ToLowerInvariant() -ne $campos[2]) { throw 'Pacote incompleto ou alterado. Baixe e extraia novamente. Nada foi instalado.' }
    if ($Verificar) { Write-Host 'Pacote íntegro e compatível.'; exit 0 }
    if ($SemAbrir) {
        $processo = Start-Process -FilePath $arquivo -ArgumentList '/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART' -Wait -PassThru
    } else {
        $processo = Start-Process -FilePath $arquivo -Wait -PassThru
    }
    if ($processo.ExitCode -ne 0) { throw "Instalação cancelada ou interrompida (código $($processo.ExitCode))." }
    Write-Host 'DoguIA instalado. Abra Configurar DoguIA Usage no menu Iniciar.'
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
