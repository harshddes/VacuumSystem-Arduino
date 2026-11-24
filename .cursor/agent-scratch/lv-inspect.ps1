$ErrorActionPreference = 'Stop'
try {
    $lv = New-Object -ComObject 'LabVIEW.Application'
    Write-Output ("COM_OK " + $lv.Name)
} catch {
    Write-Output ("COM_FAIL " + $_.Exception.Message)
}
