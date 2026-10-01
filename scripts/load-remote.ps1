# HTTP load against the public school API. No k6/kubectl needed.
# Lab 3:  powershell -ExecutionPolicy Bypass -File .\load-remote.ps1 -Lab 3
# Lab 4:  powershell -ExecutionPolicy Bypass -File .\load-remote.ps1 -Lab 4
param(
    [ValidateSet('3', '4')]
    [string]$Lab = '4',
    [string]$Url,
    [int]$Workers = 80,
    [int]$Seconds = 240
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::DefaultConnectionLimit = [Math]::Max(256, $Workers * 2)
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
[Net.ServicePointManager]::Expect100Continue = $false

if (-not $Url) {
    $Url = @{
        '3' = 'http://89.169.152.212/api/events'
        '4' = 'http://84.252.131.166/api/events'
    }[$Lab]
}

$ok = [long]0
$fail = [long]0
$lock = New-Object object
$stopAt = [DateTime]::UtcNow.AddSeconds($Seconds)
$handler = {
    param($Target, $Until, $CounterLock)
    $script:localOk = 0
    $script:localFail = 0
    while ([DateTime]::UtcNow -lt $Until) {
        try {
            $req = [Net.WebRequest]::Create($Target)
            $req.Method = 'GET'
            $req.Timeout = 8000
            $req.KeepAlive = $true
            $req.Proxy = $null
            $resp = $req.GetResponse()
            $resp.Close()
            $script:localOk++
        }
        catch {
            $script:localFail++
        }
    }
    return @{ Ok = $script:localOk; Fail = $script:localFail }
}

$pool = [RunspaceFactory]::CreateRunspacePool(1, $Workers)
$pool.Open()
$jobs = @()
Write-Host "Load $Url  workers=$Workers  duration=${Seconds}s"
Write-Host "Watch HPA: kubectl -n school get hpa,pods -w"
Write-Host "Ctrl+C stops this laptop; cluster HPA will scale down after ~1 min."

try {
    1..$Workers | ForEach-Object {
        $ps = [PowerShell]::Create()
        $ps.RunspacePool = $pool
        [void]$ps.AddScript($handler).AddArgument($Url).AddArgument($stopAt).AddArgument($lock)
        $jobs += @{ Shell = $ps; Handle = $ps.BeginInvoke() }
    }

    $started = Get-Date
    while ($jobs | Where-Object { -not $_.Handle.IsCompleted }) {
        Start-Sleep -Seconds 5
        $elapsed = [int]((Get-Date) - $started).TotalSeconds
        Write-Host ("  running {0}/{1}s ..." -f $elapsed, $Seconds)
    }

    foreach ($job in $jobs) {
        $result = $job.Shell.EndInvoke($job.Handle)
        $ok += [long]$result.Ok
        $fail += [long]$result.Fail
        $job.Shell.Dispose()
    }
}
finally {
    $pool.Close()
    $pool.Dispose()
}

Write-Host ("Done. ok={0} fail={1}" -f $ok, $fail)
