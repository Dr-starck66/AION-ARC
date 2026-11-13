# ASTRA OMEGA - Official Kaggle GPU check, idempotent, no paid resources
# Windows PowerShell 5.1+ | reads the existing Kaggle OAuth credentials.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$root = Join-Path $env:LOCALAPPDATA "ASTRA-Kaggle"
$kg = Join-Path $root ".venv\Scripts\kaggle.exe"
$py = Join-Path $root ".venv\Scripts\python.exe"
$oldKernel = "drstarck/astra-arc3-gpu-authorization-20261104"
$newKernel = "drstarck/astra-omega-gpu-check-20261113"
$script:KaggleCode = -1

function Invoke-Kaggle {
    param([string[]]$CliArgs)
    $savedPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $outputText = (& $kg @CliArgs 2>&1 | Out-String)
        $script:KaggleCode = $LASTEXITCODE
        return [string]$outputText
    } finally {
        $ErrorActionPreference = $savedPreference
    }
}

function Get-KernelState {
    param([string]$Kernel)
    $status = Invoke-Kaggle -CliArgs @("kernels", "status", $Kernel)
    if ($script:KaggleCode -ne 0) { return "UNAVAILABLE" }
    if ($status -match "(?i)\b(ERROR|FAILED|CANCELLED|CANCELED)\b") { return "FAILED" }
    if ($status -match "(?i)\b(COMPLETE|SUCCEEDED)\b") { return "COMPLETE" }
    return "RUNNING"
}

function Get-VerifiedReceipt {
    param([string]$Kernel)
    if ((Get-KernelState -Kernel $Kernel) -ne "COMPLETE") { return $false }
    $download = Join-Path $root ("receipt-" + [guid]::NewGuid().ToString("N"))
    New-Item -ItemType Directory -Path $download -Force | Out-Null
    $result = Invoke-Kaggle -CliArgs @("kernels", "output", $Kernel,
        "-p", $download, "-o", "--file-pattern", ".*astra_arc3_gpu_receipt[.]json$")
    if ($script:KaggleCode -ne 0) { return $false }
    $receipts = @(Get-ChildItem -LiteralPath $download -Recurse -File -Filter "astra_arc3_gpu_receipt.json")
    if ($receipts.Count -ne 1) { return $false }
    try {
        $receipt = Get-Content -LiteralPath $receipts[0].FullName -Raw -Encoding UTF8 | ConvertFrom-Json
        $count = [int]$receipt.gpu_count
        if ($receipt.status -ne "PASS" -or $receipt.gpu_available -ne $true -or $count -lt 1) {
            return $false
        }
        if ($receipt.scope -and $receipt.scope -notin @("kaggle_private_gpu_smoke_test_not_aion_solver","astra_gpu_probe_v1")) {
            return $false
        }
        $verified = Join-Path $root "astra_gpu_verified_receipt.json"
        Copy-Item -LiteralPath $receipts[0].FullName -Destination $verified -Force
        Write-Host ""
        Write-Host "ASTRA_KAGGLE_GPU_VERIFIED_PASS" -ForegroundColor Green
        Write-Host ("GPU : " + ($receipt.gpu_names -join ", "))
        Write-Host ("Kernel : " + $Kernel)
        Write-Host ("Preuve : " + $verified)
        Write-Host "Recherche scientifique et score officiel : UNVERIFIED"
        return $true
    } catch {
        return $false
    }
}

try {
    Write-Host "ASTRA OMEGA - Verification GPU Kaggle gratuite" -ForegroundColor Cyan
    if (!(Test-Path -LiteralPath $kg) -or !(Test-Path -LiteralPath $py)) {
        throw "Kaggle CLI introuvable dans l'installation ASTRA existante."
    }

    $version = Invoke-Kaggle -CliArgs @("--version")
    if ($script:KaggleCode -ne 0) { throw "L'outil Kaggle ne fonctionne pas : $version" }
    Write-Host ($version.Trim())

    $owner = Invoke-Kaggle -CliArgs @("kernels","status","drstarck/notebook2700e63354")
    if ($script:KaggleCode -ne 0 -or $owner -notmatch "COMPLETE|RUNNING|QUEUED|PENDING|SUCCEEDED") {
        throw "L'authentification Kaggle drstarck n'est pas valide sous Windows. Relancer : kaggle auth login"
    }
    Write-Host "ASTRA_KAGGLE_AUTH_PASS (drstarck)" -ForegroundColor Green

    Write-Host "Recherche de la preuve GPU existante..."
    if (Get-VerifiedReceipt -Kernel $oldKernel) { exit 0 }
    if (Get-VerifiedReceipt -Kernel $newKernel) { exit 0 }

    $status = Get-KernelState -Kernel $newKernel
    if ($status -ne "RUNNING") {
        $folder = Join-Path $root "gpu-test"
        New-Item -ItemType Directory -Force -Path $folder | Out-Null
        $pythonSource = @'
import json
from pathlib import Path
from datetime import datetime, timezone
import torch

if not torch.cuda.is_available():
    raise RuntimeError("KAGGLE_GPU_UNAVAILABLE")
a = torch.randn(128, 128, device="cuda")
b = a @ a
torch.cuda.synchronize()
receipt = {
    "status": "PASS",
    "scope": "astra_gpu_probe_v1",
    "gpu_available": True,
    "gpu_count": torch.cuda.device_count(),
    "gpu_names": [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())],
    "pytorch_version": torch.__version__,
    "cuda_version": torch.version.cuda,
    "calculation": float(b.sum().item()),
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "scientific_results": "UNVERIFIED",
    "official_competition_score": "UNVERIFIED",
}
Path("/kaggle/working/astra_arc3_gpu_receipt.json").write_text(
    json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
)
print("ASTRA_KAGGLE_GPU_SMOKE_PASS", json.dumps(receipt))
'@
        $metadata = @{
            id = $newKernel
            title = "astra-omega-gpu-check-20261113"
            code_file = "probe.py"
            language = "python"
            kernel_type = "script"
            is_private = $true
            enable_gpu = $true
            enable_internet = $false
            machine_shape = "NvidiaTeslaT4"
            dataset_sources = @()
            competition_sources = @()
            kernel_sources = @()
            model_sources = @()
        }
        $utf8 = New-Object System.Text.UTF8Encoding($false)
        [System.IO.File]::WriteAllText((Join-Path $folder "probe.py"), $pythonSource, $utf8)
        [System.IO.File]::WriteAllText((Join-Path $folder "kernel-metadata.json"),
            ($metadata | ConvertTo-Json -Depth 6), $utf8)
        Write-Host "Envoi d'un test prive sur le quota GPU gratuit Kaggle..."
        $push = Invoke-Kaggle -CliArgs @("kernels","push","-p",$folder,"--accelerator","NvidiaTeslaT4","--timeout","600")
        if ($script:KaggleCode -ne 0) { throw "Kaggle a refuse le lancement : $push" }
        Write-Host "ASTRA_KAGGLE_GPU_PUSH_ACCEPTED_NOT_YET_GPU_PASS"
    } else {
        Write-Host "Test Kaggle deja en cours : pas de nouvel envoi."
    }

    $complete = $false
    for ($i=0; $i -lt 30; $i++) {
        $state = Get-KernelState -Kernel $newKernel
        Write-Host ("Verification Kaggle " + ($i+1) + "/30 : " + $state)
        if ($state -eq "COMPLETE") { $complete = $true; break }
        if ($state -eq "FAILED") { throw "Kaggle indique un echec du notebook GPU." }
        Start-Sleep -Seconds 15
    }
    if (!$complete) { throw "GPU non termine ou statut inaccessible. Le test distant peut encore etre en cours." }
    if (!(Get-VerifiedReceipt -Kernel $newKernel)) {
        throw "Notebook termine mais preuve GPU non valide ou non telechargeable."
    }
} catch {
    Write-Host ("ASTRA_PARTIAL : " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "Aucune preuve de calcul scientifique officiel n'est declaree."
    exit 1
}
