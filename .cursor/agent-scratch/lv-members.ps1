$ErrorActionPreference = 'Stop'
$lv = New-Object -ComObject 'LabVIEW.Application'
Write-Output '--- TYPE ---'
$lv.GetType().FullName
Write-Output '--- MEMBERS ---'
$lv | Get-Member | ForEach-Object { $_.MemberType.ToString() + ' ' + $_.Name }
