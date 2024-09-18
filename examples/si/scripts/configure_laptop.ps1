$username = ""
$password = ""

########################
########################
## ZEROTIER
########################
########################
$source = 'https://download.zerotier.com/dist/ZeroTier%20One.msi'
$destination = $PSScriptRoot+"\Zerotier.msi"
$binary = 'C:\Program Files (x86)\ZeroTier\One\zerotier-cli.bat'

Invoke-WebRequest -Uri $source -OutFile $destination
Start-Process $destination -ArgumentList "/quiet /passive" -Wait

Write-Host $binary

Start-Process -FilePath $binary -ArgumentList 'join c6714bd6db5847b2' -Wait -NoNewWindow

########################
########################
## Configure Ansible
########################
########################
#####
### Allow ping
#####
netsh advfirewall firewall add rule name="ICMP Allow incoming V4 echo request" protocol=icmpv4:8,any dir=in action=allow

#####
### Upgrading PowerShell and .NET Framework
#####
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$url = "https://raw.githubusercontent.com/jborean93/ansible-windows/master/scripts/Upgrade-PowerShell.ps1"
$file = "$env:temp\Upgrade-PowerShell.ps1"
# $username = ""
# $password = ""

(New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
Set-ExecutionPolicy -ExecutionPolicy Unrestricted -Force

&$file -Version 5.1 -Username $username -Password $password -Verbose

#####
### Good security practice, set the execution policy back to the default.
#####
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Force

#####
### Remove the auto logon
#####
$reg_winlogon_path = "HKLM:\Software\Microsoft\Windows NT\CurrentVersion\Winlogon"
Set-ItemProperty -Path $reg_winlogon_path -Name AutoAdminLogon -Value 0
Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultUserName -ErrorAction SilentlyContinue
Remove-ItemProperty -Path $reg_winlogon_path -Name DefaultPassword -ErrorAction SilentlyContinue

#####
### WinRM Memory Hotfix
#####
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$url = "https://raw.githubusercontent.com/jborean93/ansible-windows/master/scripts/Install-WMF3Hotfix.ps1"
$file = "$env:temp\Install-WMF3Hotfix.ps1"

(New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
powershell.exe -ExecutionPolicy ByPass -File $file -Verbose

#####
### Setup WinRM Listener
#####
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$url = "https://raw.githubusercontent.com/ansible/ansible/devel/examples/scripts/ConfigureRemotingForAnsible.ps1"
$file = "$env:temp\ConfigureRemotingForAnsible.ps1"

(New-Object -TypeName System.Net.WebClient).DownloadFile($url, $file)
powershell.exe -ExecutionPolicy ByPass -File $file

winrm get winrm/config/Service
winrm get winrm/config/Winrs
winrm enumerate winrm/config/Listener
