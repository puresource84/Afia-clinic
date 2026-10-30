# Afia Clinic - One-Click Installer
# Run as Administrator
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$BRAND_BLUE  = [System.Drawing.Color]::FromArgb(26,115,167)
$BRAND_DARK  = [System.Drawing.Color]::FromArgb(13,90,138)
$BRAND_LIGHT = [System.Drawing.Color]::FromArgb(214,232,245)
$WHITE       = [System.Drawing.Color]::White
$GREEN       = [System.Drawing.Color]::FromArgb(30,142,62)
$GREY        = [System.Drawing.Color]::FromArgb(95,99,104)
$SCRIPT_DIR  = Split-Path -Parent $MyInvocation.MyCommand.Path
$MODULES_DIR = Join-Path $SCRIPT_DIR "modules"
# Odoo's own packaged Windows installer for the maintained 18.0 branch -
# the same Odoo CE major version (18.0) every Afia Clinic module targets.
# This is the correct, official public source for the stable Odoo 18 CE
# Windows installer (odoo.com's own Download page links here) - not an
# unstable dev-branch nightly. Previously this pointed at a nonexistent
# path (.../18.0/nightly/exe/...) which would have 404'd; fixed 2026-08-07.
$ODOO_NIGHTLY = "https://nightly.odoo.com/18.0/nightly/windows/odoo_setup_18.0.latest.exe"

# Module install layers.
# 2026-08-07: rebuilt against the current afia_dental_core rewrite (35
# modules - dental_report_builder is gone entirely, clinic_core_plus and
# dental_hide_re_tabs are excluded from this package). Odoo's ORM resolves
# the full dependency graph internally on button_immediate_install, so
# this doesn't need to be a precise topological order - it only needs to
# put afia_dental_core first (for clean, readable progress logging) and
# list everything else. If it's out of order Odoo will still install
# correctly; it just won't log in as tidy a sequence.
$LAYERS = @(
    @("afia_dental_core"),
    @("clinic_core","dental_analytics","dental_charting_pro","dental_communication","dental_consent","dental_insurance","dental_lab","dental_patient_flow","dental_patient_portal","dental_portal_booking","dental_sterilization","dental_treatment_plan"),
    @("afia_app_launcher","dental_appointment_times","dental_booking_slots","dental_case_acceptance","dental_clinical_permissions","dental_consumables","dental_imaging","dental_insurance_v2","dental_reminders_telegram"),
    @("custom_dental_menu","dental_soap_notes","dental_telegram_templates"),
    @("dental_perio_charting","dental_portal_v2"),
    @("dental_ux_fixes"),
    @("dental_allergy_guard"),
    @("dental_audit")
)
# v1.1 (single clinic, cash only, Telegram + email reminders) deliberately
# does NOT auto-install: dental_branch, dental_reminders_whatsapp,
# payment_paytabs, payment_zaincash. They stay in modules/ and can be
# installed from Apps once they are production-ready.
# dental_demo_data is intentionally NOT in this list - it seeds fake
# patient data and should only ever be installed on a separate, disposable
# database, never through this production installer. See
# dental_demo_data/README.md for its own install steps.

#  Font helper (safe across all PS versions)
function fnt($size, $bold=$false) {
    try {
        $s = if($bold){[System.Drawing.FontStyle]::Bold}else{[System.Drawing.FontStyle]::Regular}
        return [System.Drawing.Font]::new("Segoe UI", [float]$size, $s)
    } catch { return $null }
}

#  Core helpers
function Find-OdooServer {
    $patterns = @(
        "C:\Program Files\Odoo*\server",
        "C:\Program Files (x86)\Odoo*\server",
        "C:\Odoo*\server",
        "D:\Odoo*\server"
    )
    foreach ($p in $patterns) {
        $hit = Get-Item $p -EA SilentlyContinue | Sort-Object Name -Desc | Select-Object -First 1
        if ($hit) { return $hit.FullName }
    }
    return $null
}

function Find-OdooConf {
    # Independent of a detected $serverPath - used by the "already have
    # Odoo running" path where we may jump straight to database/module
    # setup without going through Find-OdooServer first.
    $candidates = @("C:\ProgramData\Odoo\odoo.conf")
    $candidates += (Get-ChildItem "C:\Program Files\Odoo*\server\odoo.conf" -EA SilentlyContinue | ForEach-Object { $_.FullName })
    $candidates += (Get-ChildItem "C:\Program Files\Odoo*\odoo.conf" -EA SilentlyContinue | ForEach-Object { $_.FullName })
    $candidates += (Get-ChildItem "C:\Program Files (x86)\Odoo*\server\odoo.conf" -EA SilentlyContinue | ForEach-Object { $_.FullName })
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    return $null
}

function Get-OdooConfValue($key, $default) {
    $conf = Find-OdooConf
    if ($conf) {
        $line = Get-Content $conf -EA SilentlyContinue | Where-Object { $_ -match "^\s*$key\s*=" } | Select-Object -First 1
        if ($line) {
            $val = ($line -split '=',2)[1].Trim()
            if ($val) { return $val }
        }
    }
    return $default
}

function Find-Python {
    # The Odoo Windows all-in-one installer bundles its own Python - use
    # that if present so we don't depend on a separate system install.
    $candidates = @()
    $candidates += (Get-ChildItem "C:\Program Files\Odoo*\python\python.exe" -EA SilentlyContinue | ForEach-Object { $_.FullName })
    $candidates += (Get-ChildItem "C:\Program Files (x86)\Odoo*\python\python.exe" -EA SilentlyContinue | ForEach-Object { $_.FullName })
    if ($candidates) { return ($candidates | Select-Object -First 1) }
    $cmd = Get-Command python -EA SilentlyContinue
    if ($cmd) { return $cmd.Source }
    $cmd = Get-Command python3 -EA SilentlyContinue
    if ($cmd) { return $cmd.Source }
    return $null
}

function Ensure-CustomAddons($serverPath) {
    $addons = Join-Path $serverPath "custom_addons"
    if (-not (Test-Path $addons)) {
        New-Item -ItemType Directory -Force -Path $addons | Out-Null
    }
    # Patch odoo.conf so Odoo knows about the folder
    $confCandidates = @(
        "C:\ProgramData\Odoo\odoo.conf",
        (Join-Path (Split-Path $serverPath -Parent) "odoo.conf"),
        (Join-Path $serverPath "odoo.conf")
    )
    foreach ($conf in $confCandidates) {
        if (Test-Path $conf) {
            $txt = Get-Content $conf -Raw
            if ($txt -notmatch [regex]::Escape($addons)) {
                $txt = $txt -replace "(addons_path\s*=\s*[^\r\n]+)", "`$1,$addons"
                Set-Content $conf $txt -Encoding UTF8
            }
            break
        }
    }
    return $addons
}

function Test-Port8069 {
    try { $c=New-Object System.Net.Sockets.TcpClient; $c.Connect("localhost",8069); $c.Close(); return $true } catch { return $false }
}

#  UI
$form = New-Object System.Windows.Forms.Form
$form.Text = "Afia Clinic Setup"
$form.Size = New-Object System.Drawing.Size(560,460)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.BackColor = $WHITE

# Header band
$hdr = New-Object System.Windows.Forms.Panel
$hdr.Size = New-Object System.Drawing.Size(560,90)
$hdr.BackColor = $BRAND_BLUE
$form.Controls.Add($hdr)

$hdrTitle = New-Object System.Windows.Forms.Label
$hdrTitle.Text = "Afia Clinic"
$hdrTitle.ForeColor = $WHITE
$hdrTitle.Left=30; $hdrTitle.Top=18; $hdrTitle.Width=400; $hdrTitle.Height=34
$f = fnt 20 $true; if($f){ $hdrTitle.Font=$f }
$hdr.Controls.Add($hdrTitle)

$hdrSub = New-Object System.Windows.Forms.Label
$hdrSub.Text = "Dental Practice Management Suite"
$hdrSub.ForeColor = [System.Drawing.Color]::FromArgb(180,210,235)
$hdrSub.Left=31; $hdrSub.Top=54; $hdrSub.Width=400; $hdrSub.Height=22
$f = fnt 10; if($f){ $hdrSub.Font=$f }
$hdr.Controls.Add($hdrSub)

#  PAGE 1: WELCOME
$p1 = New-Object System.Windows.Forms.Panel
$p1.SetBounds(0,90,560,310); $p1.BackColor=$WHITE
$form.Controls.Add($p1)

$lbl1 = New-Object System.Windows.Forms.Label
$lbl1.Text = "Welcome"
$lbl1.Left=30; $lbl1.Top=24; $lbl1.Width=500; $lbl1.Height=32
$f = fnt 18 $true; if($f){$lbl1.Font=$f}
$p1.Controls.Add($lbl1)

$lbl2 = New-Object System.Windows.Forms.Label
$lbl2.Text = "This wizard will:`n`n   1.  Detect Odoo 18 Community Edition, or install it from`n        Odoo's official public build server`n   2.  Copy the Afia Clinic modules`n   3.  Let you create a new database or connect to an existing one`n   4.  Configure Odoo and open your browser"
$lbl2.Left=30; $lbl2.Top=60; $lbl2.Width=490; $lbl2.Height=130
$lbl2.ForeColor=$GREY
$f = fnt 10; if($f){$lbl2.Font=$f}
$p1.Controls.Add($lbl2)

$btnInstall = New-Object System.Windows.Forms.Button
$btnInstall.Text = "Detect / Install Odoo, then Continue"
$btnInstall.SetBounds(230,200,280,40)
$btnInstall.FlatStyle="Flat"; $btnInstall.FlatAppearance.BorderSize=0
$btnInstall.BackColor=$BRAND_BLUE; $btnInstall.ForeColor=$WHITE
$btnInstall.Cursor=[System.Windows.Forms.Cursors]::Hand
$f = fnt 10 $true; if($f){$btnInstall.Font=$f}
$p1.Controls.Add($btnInstall)

$btnSkipToDb = New-Object System.Windows.Forms.Button
$btnSkipToDb.Text = "I already have Odoo running - set up database and modules"
$btnSkipToDb.SetBounds(90,250,420,32)
$btnSkipToDb.FlatStyle="Flat"; $btnSkipToDb.FlatAppearance.BorderSize=1
$btnSkipToDb.FlatAppearance.BorderColor = $BRAND_BLUE
$btnSkipToDb.BackColor=$WHITE; $btnSkipToDb.ForeColor=$BRAND_BLUE
$btnSkipToDb.Cursor=[System.Windows.Forms.Cursors]::Hand
$f = fnt 9; if($f){$btnSkipToDb.Font=$f}
$p1.Controls.Add($btnSkipToDb)

#  PAGE 2: PROGRESS
$p2 = New-Object System.Windows.Forms.Panel
$p2.SetBounds(0,90,560,310); $p2.BackColor=$WHITE; $p2.Visible=$false
$form.Controls.Add($p2)

$lblStatus = New-Object System.Windows.Forms.Label
$lblStatus.Text = "Starting..."
$lblStatus.Left=30; $lblStatus.Top=30; $lblStatus.Width=500; $lblStatus.Height=30
$f = fnt 13 $true; if($f){$lblStatus.Font=$f}
$p2.Controls.Add($lblStatus)

$bar = New-Object System.Windows.Forms.ProgressBar
$bar.SetBounds(30,72,490,20); $bar.Minimum=0; $bar.Maximum=100; $bar.Value=0
$bar.Style="Continuous"
$p2.Controls.Add($bar)

$log = New-Object System.Windows.Forms.TextBox
$log.SetBounds(30,104,490,190)
$log.Multiline=$true; $log.ReadOnly=$true; $log.ScrollBars="Vertical"
$log.BackColor=[System.Drawing.Color]::FromArgb(245,245,245)
$log.BorderStyle="None"
$f = try{[System.Drawing.Font]::new("Consolas",[float]8)}catch{$null}; if($f){$log.Font=$f}
$p2.Controls.Add($log)

#  PAGE 3: DONE (shown after modules finish installing)
$p3 = New-Object System.Windows.Forms.Panel
$p3.SetBounds(0,90,560,310); $p3.BackColor=$WHITE; $p3.Visible=$false
$form.Controls.Add($p3)

$lblDoneIcon = New-Object System.Windows.Forms.Label
$lblDoneIcon.Text = "OK"; $lblDoneIcon.ForeColor=$GREEN
$lblDoneIcon.Left=30; $lblDoneIcon.Top=20; $lblDoneIcon.Width=60; $lblDoneIcon.Height=60
$f = fnt 40 $true; if($f){$lblDoneIcon.Font=$f}
$p3.Controls.Add($lblDoneIcon)

$lblDone = New-Object System.Windows.Forms.Label
$lblDone.Text = "Afia Clinic is ready!"
$lblDone.Left=90; $lblDone.Top=28; $lblDone.Width=420; $lblDone.Height=36
$f = fnt 16 $true; if($f){$lblDone.Font=$f}
$p3.Controls.Add($lblDone)

$lblDoneSub = New-Object System.Windows.Forms.Label
$lblDoneSub.Text = "Open your browser and go to:`nhttp://localhost:8069`n`nLog in with the admin login/password you set, then go to`nApps > Update Apps List if 'Afia Dental Clinic' isn't visible yet."
$lblDoneSub.Left=30; $lblDoneSub.Top=90; $lblDoneSub.Width=480; $lblDoneSub.Height=110
$lblDoneSub.ForeColor=$GREY
$f = fnt 10; if($f){$lblDoneSub.Font=$f}
$p3.Controls.Add($lblDoneSub)

$btnOpen = New-Object System.Windows.Forms.Button
$btnOpen.Text = "Open Afia Clinic in Browser"
$btnOpen.SetBounds(160,210,230,44)
$btnOpen.FlatStyle="Flat"; $btnOpen.FlatAppearance.BorderSize=0
$btnOpen.BackColor=$GREEN; $btnOpen.ForeColor=$WHITE
$btnOpen.Cursor=[System.Windows.Forms.Cursors]::Hand
$f = fnt 11 $true; if($f){$btnOpen.Font=$f}
$btnOpen.Add_Click({ Start-Process "http://localhost:8069" })
$p3.Controls.Add($btnOpen)

$lblDoneErr = New-Object System.Windows.Forms.Label
$lblDoneErr.Text = ""
$lblDoneErr.Left=30; $lblDoneErr.Top=262; $lblDoneErr.Width=490; $lblDoneErr.Height=30
$lblDoneErr.ForeColor=[System.Drawing.Color]::Red
$f = fnt 9; if($f){$lblDoneErr.Font=$f}
$p3.Controls.Add($lblDoneErr)

#  PAGE 4: DATABASE & MODULES
$p4 = New-Object System.Windows.Forms.Panel
$p4.SetBounds(0,90,560,310); $p4.BackColor=$WHITE; $p4.Visible=$false
$form.Controls.Add($p4)

$p4.Controls.Add((& { $l=New-Object System.Windows.Forms.Label; $l.Text="Database & Modules"; $l.SetBounds(30,14,500,28); $f=fnt 15 $true; if($f){$l.Font=$f}; $l }))
$p4.Controls.Add((& { $l=New-Object System.Windows.Forms.Label; $l.Text="Create a new Odoo database or connect to one you already have, then install the Afia Clinic modules automatically."; $l.SetBounds(30,44,500,30); $l.ForeColor=$GREY; $f=fnt 9; if($f){$l.Font=$f}; $l }))

$rbCreate = New-Object System.Windows.Forms.RadioButton
$rbCreate.Text = "Create a new database"
$rbCreate.SetBounds(30,78,230,20); $rbCreate.Checked = $true
$f = fnt 9; if($f){$rbCreate.Font=$f}
$p4.Controls.Add($rbCreate)

$rbExisting = New-Object System.Windows.Forms.RadioButton
$rbExisting.Text = "Connect to an existing database"
$rbExisting.SetBounds(270,78,250,20)
$f = fnt 9; if($f){$rbExisting.Font=$f}
$p4.Controls.Add($rbExisting)

$p4.Controls.Add((& { $l=New-Object System.Windows.Forms.Label; $l.Text="Database Name:"; $l.SetBounds(30,102,220,18); $f=fnt 9; if($f){$l.Font=$f}; $l }))
$txtDb = New-Object System.Windows.Forms.TextBox; $txtDb.SetBounds(30,121,220,26); $txtDb.Text="afia_clinic"
$p4.Controls.Add($txtDb)

$p4.Controls.Add((& { $l=New-Object System.Windows.Forms.Label; $l.Text="Admin Login (email):"; $l.SetBounds(270,102,220,18); $f=fnt 9; if($f){$l.Font=$f}; $l }))
$txtAdminLogin = New-Object System.Windows.Forms.TextBox; $txtAdminLogin.SetBounds(270,121,220,26); $txtAdminLogin.Text="admin"
$p4.Controls.Add($txtAdminLogin)

$p4.Controls.Add((& { $l=New-Object System.Windows.Forms.Label; $l.Text="Admin Password:"; $l.SetBounds(30,151,220,18); $f=fnt 9; if($f){$l.Font=$f}; $l }))
$txtPwd = New-Object System.Windows.Forms.TextBox; $txtPwd.SetBounds(30,170,220,26); $txtPwd.PasswordChar='*'
$p4.Controls.Add($txtPwd)

$lblMaster = New-Object System.Windows.Forms.Label
$lblMaster.Text = "Master Password (new DB only):"
$lblMaster.SetBounds(270,151,240,18)
$f = fnt 9; if($f){$lblMaster.Font=$f}
$p4.Controls.Add($lblMaster)
$txtMaster = New-Object System.Windows.Forms.TextBox
$txtMaster.SetBounds(270,170,220,26); $txtMaster.PasswordChar='*'
$txtMaster.Text = Get-OdooConfValue "admin_passwd" "admin"
$p4.Controls.Add($txtMaster)

# Toggle which fields are relevant based on create vs. existing
function Update-DbModeUI {
    if ($rbCreate.Checked) {
        $lblMaster.Enabled = $true; $txtMaster.Enabled = $true
        $txtAdminLogin.Text = if ($txtAdminLogin.Text) { $txtAdminLogin.Text } else { "admin" }
    } else {
        $lblMaster.Enabled = $false; $txtMaster.Enabled = $false
    }
}
$rbCreate.Add_CheckedChanged({ Update-DbModeUI })
$rbExisting.Add_CheckedChanged({ Update-DbModeUI })

$bar4 = New-Object System.Windows.Forms.ProgressBar; $bar4.SetBounds(30,202,490,14); $bar4.Minimum=0; $bar4.Maximum=$LAYERS.Count
$p4.Controls.Add($bar4)
$log4 = New-Object System.Windows.Forms.TextBox; $log4.SetBounds(30,220,490,56); $log4.Multiline=$true; $log4.ReadOnly=$true; $log4.ScrollBars="Vertical"; $log4.BackColor=[System.Drawing.Color]::FromArgb(245,245,245); $log4.BorderStyle="None"
$f=try{[System.Drawing.Font]::new("Consolas",[float]8)}catch{$null}; if($f){$log4.Font=$f}
$p4.Controls.Add($log4)

$btnInstallMods = New-Object System.Windows.Forms.Button; $btnInstallMods.Text="Create / Connect & Install Modules"; $btnInstallMods.SetBounds(230,280,300,26)
$btnInstallMods.FlatStyle="Flat"; $btnInstallMods.FlatAppearance.BorderSize=0; $btnInstallMods.BackColor=$BRAND_BLUE; $btnInstallMods.ForeColor=$WHITE; $btnInstallMods.Cursor=[System.Windows.Forms.Cursors]::Hand
$f=fnt 9 $true; if($f){$btnInstallMods.Font=$f}
$p4.Controls.Add($btnInstallMods)

#  Helpers
function Show($page) {
    $p1.Visible=$false; $p2.Visible=$false; $p3.Visible=$false; $p4.Visible=$false
    $page.Visible=$true
    [System.Windows.Forms.Application]::DoEvents()
}

function Log($msg) {
    $log.AppendText("$msg`r`n")
    [System.Windows.Forms.Application]::DoEvents()
}

function Step($msg, $pct) {
    $lblStatus.Text = $msg
    $bar.Value = [Math]::Min($pct, 100)
    Log $msg
    [System.Windows.Forms.Application]::DoEvents()
}

#  Odoo detect/install + module copy (Page 1 -> Page 2 -> Page 4)
$btnInstall.Add_Click({
    Show $p2

    # 1. Check for Odoo
    Step "Checking for Odoo 18 CE..." 5
    $serverPath = Find-OdooServer

    if ($serverPath) {
        Log "  Found: $serverPath"
    } else {
        Step "Downloading Odoo 18 CE (~320 MB) from Odoo's public build server..." 10
        Log "  Odoo not found. Downloading the official Odoo 18.0 Community Edition"
        Log "  Windows installer from nightly.odoo.com (Odoo's own public build"
        Log "  server for the maintained 18.0 branch - the same CE version this"
        Log "  package targets)."
        Log "  This may take 5-15 minutes depending on your connection."
        Log "  Please wait - do not close this window."

        $exe = Join-Path $env:TEMP "odoo_18_setup.exe"
        $ok  = $false

        # Try BITS first (handles large files + resumes)
        try {
            Import-Module BitsTransfer -EA Stop
            Start-BitsTransfer -Source $ODOO_NIGHTLY -Destination $exe -Description "Downloading Odoo 18 CE" -DisplayName "Afia Clinic Setup"
            if ((Get-Item $exe -EA SilentlyContinue).Length -gt 10MB) { $ok = $true }
        } catch {}

        # Fallback: WebClient with progress polling
        if (-not $ok) {
            try {
                $wc = New-Object System.Net.WebClient
                $wc.Headers.Add("User-Agent","Mozilla/5.0")
                $wc.DownloadFile($ODOO_NIGHTLY, $exe)
                if ((Get-Item $exe -EA SilentlyContinue).Length -gt 10MB) { $ok = $true }
            } catch { Log "  Download error: $($_.Exception.Message)" }
        }

        if (-not $ok) {
            Step "Download failed." 0
            Log ""
            Log "  Could not download Odoo automatically."
            Log "  Please download and install Odoo 18 CE manually:"
            Log "  https://www.odoo.com/page/download"
            Log "  Then re-run this installer."
            Show $p3
            $lblDone.Text = "Manual step required"
            $lblDoneErr.Text = "Install Odoo 18 CE then re-run this installer."
            $btnOpen.Visible = $false
            return
        }

        Step "Installing Odoo 18 CE (silent)..." 35
        Log "  Running Odoo installer silently - this takes 3-8 minutes..."
        try {
            Start-Process $exe -ArgumentList "/S" -Wait
        } catch {
            Log "  Warning: $($_.Exception.Message)"
        }

        Start-Sleep 5
        $serverPath = Find-OdooServer

        if (-not $serverPath) {
            Step "Odoo installation not detected." 0
            Log ""
            Log "  Silent install may have failed. Trying interactive install..."
            Start-Process $exe -Wait
            Start-Sleep 5
            $serverPath = Find-OdooServer
        }

        if (-not $serverPath) {
            Step "Could not detect Odoo after install." 0
            Log "  Could not find Odoo in Program Files after installation."
            Log "  Please install Odoo 18 CE manually, then re-run this installer."
            Show $p3
            $lblDone.Text = "Manual step required"
            $lblDoneErr.Text = "Install Odoo 18 CE then re-run this installer."
            $btnOpen.Visible = $false
            return
        }
        Log "  Odoo installed at: $serverPath"
    }

    # 2. Ensure custom_addons exists and is in odoo.conf
    Step "Configuring Odoo addons path..." 55
    $customAddons = Ensure-CustomAddons $serverPath
    Log "  Addons folder: $customAddons"

    # 3. Copy modules
    Step "Copying Afia Clinic modules..." 62
    $count = 0
    $allModuleDirs = Get-ChildItem -Path $MODULES_DIR -Directory
    $totalModules = [Math]::Max($allModuleDirs.Count, 1)
    $allModuleDirs | ForEach-Object {
        $dest = Join-Path $customAddons $_.Name
        Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
        $count++
        $bar.Value = 62 + [int]($count/$totalModules*25)
        [System.Windows.Forms.Application]::DoEvents()
    }
    Log "  Copied $count modules."

    # 4. Restart Odoo service (handle Paused state) so it picks up the new addons path
    Step "Restarting Odoo service..." 88
    $svc = Get-Service -Name "*odoo*" -EA SilentlyContinue | Select-Object -First 1
    if ($svc) {
        Log "  Service found: $($svc.Name) [$($svc.Status)]"
        try {
            if ($svc.Status -eq "Paused") {
                Log "  Service is paused - stopping first..."
                $svc.Stop()
                $svc.WaitForStatus("Stopped", (New-TimeSpan -Seconds 15))
            } elseif ($svc.Status -eq "Running") {
                $svc.Stop()
                $svc.WaitForStatus("Stopped", (New-TimeSpan -Seconds 15))
            }
            Start-Sleep 2
            $svc.Refresh()
            $svc.Start()
            $svc.WaitForStatus("Running", (New-TimeSpan -Seconds 20))
            Log "  Service started successfully."
        } catch {
            Log "  Service start error: $($_.Exception.Message)"
            Log "  Check log: C:\ProgramData\Odoo\logs\odoo-server.log"
        }
    } else {
        Log "  Odoo service not found - attempting to start via odoo-bin..."
        $odoobin = Join-Path $serverPath "odoo-bin"
        if (Test-Path $odoobin) {
            Start-Process $odoobin -ArgumentList "--config=C:\ProgramData\Odoo\odoo.conf" -WindowStyle Hidden
        }
    }

    # 5. Wait for port 8069
    Step "Waiting for Odoo to respond..." 92
    $ready = $false
    for ($i=0; $i -lt 60; $i++) {
        Start-Sleep 1
        $bar.Value = [Math]::Min(92 + $i/10, 99)
        [System.Windows.Forms.Application]::DoEvents()
        if (Test-Port8069) { $ready=$true; break }
    }
    $bar.Value = 100

    if (-not $ready) {
        Log "  Odoo hasn't responded on port 8069 yet - it may still be starting."
        Log "  Waiting a bit longer before moving on..."
        Start-Sleep 10
    }

    # Straight into database & module setup - no separate confirmation
    # screen needed here, since the real "done" moment is after modules
    # install (Page 3).
    Show $p4
})

# "I already have Odoo running" shortcut - skip detection/download/copy
# entirely and go straight to database & module setup. Use this when Odoo
# is already installed and running (as a service, or manually started) and
# the Afia Clinic modules are already on its addons_path - or when you'd
# rather copy the modules yourself and just need the DB/install step.
$btnSkipToDb.Add_Click({
    $conf = Find-OdooConf
    if ($conf) {
        $txtMaster.Text = Get-OdooConfValue "admin_passwd" "admin"
    }
    if (-not (Test-Port8069)) {
        $result = [System.Windows.Forms.MessageBox]::Show(
            "Odoo doesn't appear to be responding on http://localhost:8069 yet.`n`nContinue anyway? (It may just need a moment to finish starting.)",
            "Afia Clinic Setup", "YesNo", "Warning")
        if ($result -eq "No") { return }
    }
    Show $p4
})

# Footer
$footer = New-Object System.Windows.Forms.Panel
$footer.SetBounds(0,400,560,60); $footer.BackColor=[System.Drawing.Color]::FromArgb(245,245,245)
$form.Controls.Add($footer)
$fLbl = New-Object System.Windows.Forms.Label
$fLbl.Text = "Afia Clinic v2.0  |  ITCS  |  Powered by Odoo 18 CE"
$fLbl.Left=20; $fLbl.Top=20; $fLbl.Width=520; $fLbl.Height=20
$fLbl.ForeColor=$GREY; $fLbl.TextAlign="MiddleCenter"
$f = fnt 8; if($f){$fLbl.Font=$f}
$footer.Controls.Add($fLbl)

#  Database creation + module install (Page 4)
Update-DbModeUI

$btnInstallMods.Add_Click({
    $btnInstallMods.Enabled = $false
    $db          = $txtDb.Text.Trim()
    $adminLogin  = $txtAdminLogin.Text.Trim()
    $adminPwd    = $txtPwd.Text.Trim()
    $masterPwd   = $txtMaster.Text.Trim()
    $mode        = if ($rbCreate.Checked) { "create" } else { "existing" }
    $log4.Clear()
    $bar4.Value = 0

    if (-not $db) {
        $log4.AppendText("ERROR: Enter a database name.`r`n")
        $btnInstallMods.Enabled = $true
        return
    }
    if (-not $adminLogin) {
        $log4.AppendText("ERROR: Enter an admin login.`r`n")
        $btnInstallMods.Enabled = $true
        return
    }
    if ($mode -eq "existing" -and -not $adminPwd) {
        $log4.AppendText("ERROR: Enter the existing database's admin password.`r`n")
        $btnInstallMods.Enabled = $true
        return
    }
    if ($mode -eq "create") {
        if (-not $masterPwd) {
            $log4.AppendText("ERROR: Enter the Odoo master password (this is the`r`n  'admin_passwd' set in odoo.conf during Odoo's own install,`r`n  not a clinic user's password).`r`n")
            $btnInstallMods.Enabled = $true
            return
        }
        if (-not $adminPwd) {
            # Used as the new database's own admin user password
            $adminPwd = $masterPwd
            $log4.AppendText("No admin password entered for the new database - using the`r`n  master password for the admin account too. You can change this`r`n  later from Settings > Users.`r`n")
        }
    }

    $python = Find-Python
    if (-not $python) {
        $log4.AppendText("ERROR: Could not find Python (checked the bundled Odoo`r`n  python folder and your system PATH). Python ships with the`r`n  Odoo Windows installer - if Odoo installed correctly, restart`r`n  this wizard and try again.`r`n")
        $btnInstallMods.Enabled = $true
        return
    }

    # Write Python installer script to temp file
    $pyScript = Join-Path $env:TEMP "afia_install_modules.py"
    $layersPy = ($LAYERS | ForEach-Object { "    ['" + ($_ -join "','") + "']" }) -join ",`n"
    @"
import xmlrpc.client, sys, os
url = 'http://localhost:8069'
mode        = sys.argv[1]
db          = sys.argv[2]
admin_login = sys.argv[3]
# Passwords come via environment variables, never argv: command lines are
# visible to every local user in Task Manager / process listings.
admin_pwd   = os.environ.get('AFIA_ADMIN_PWD', '')
master_pwd  = os.environ.get('AFIA_MASTER_PWD', '')
try:
    if mode == 'create':
        print('CREATING:Creating database (this installs Odoo base modules first, can take 1-2 minutes)', flush=True)
        db_service = xmlrpc.client.ServerProxy(url + '/xmlrpc/2/db')
        db_service.create_database(master_pwd, db, False, 'en_US', admin_pwd, admin_login)
        print('CREATED', flush=True)

    common = xmlrpc.client.ServerProxy(url + '/xmlrpc/2/common')
    uid = common.authenticate(db, admin_login, admin_pwd, {})
    if not uid:
        print('ERROR:Login failed - check database name, admin login and password')
        sys.exit(1)
    models = xmlrpc.client.ServerProxy(url + '/xmlrpc/2/object')
    layers = [
$layersPy
    ]
    for i, layer in enumerate(layers):
        print(f'LAYER:{i+1}:{",".join(layer)}', flush=True)
        ids = models.execute_kw(db, uid, admin_pwd, 'ir.module.module', 'search', [[['name','in',layer],['state','=','uninstalled']]])
        if ids:
            models.execute_kw(db, uid, admin_pwd, 'ir.module.module', 'button_immediate_install', [ids])
        print(f'OK:{i+1}', flush=True)
    print('ALLDONE', flush=True)
except Exception as e:
    print(f'ERROR:{e}', flush=True)
    sys.exit(1)
"@ | Set-Content $pyScript -Encoding ASCII

    $outFile = Join-Path $env:TEMP "afia_mod_out.txt"
    $errFile = Join-Path $env:TEMP "afia_mod_err.txt"
    Remove-Item $outFile,$errFile -EA SilentlyContinue

    # Child process inherits these; cleared again as soon as it has started.
    $env:AFIA_ADMIN_PWD = $adminPwd
    $env:AFIA_MASTER_PWD = $masterPwd
    $proc = Start-Process -FilePath $python -ArgumentList "`"$pyScript`" `"$mode`" `"$db`" `"$adminLogin`"" -NoNewWindow -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
    Remove-Item Env:AFIA_ADMIN_PWD, Env:AFIA_MASTER_PWD -EA SilentlyContinue

    $lastLine = 0
    $sawAllDone = $false
    while (-not $proc.HasExited) {
        Start-Sleep -Milliseconds 800
        $lines = Get-Content $outFile -EA SilentlyContinue
        if ($lines -and $lines.Count -gt $lastLine) {
            for ($i=$lastLine; $i -lt $lines.Count; $i++) {
                $line = $lines[$i]
                if ($line -match '^CREATING:(.+)$') {
                    $log4.AppendText("$($Matches[1])`r`n")
                } elseif ($line -eq 'CREATED') {
                    $log4.AppendText("Database created.`r`n")
                } elseif ($line -match '^LAYER:(\d+):(.+)$') {
                    $layerNum = [int]$Matches[1]
                    $bar4.Value = $layerNum - 1
                    $log4.AppendText("Installing layer $layerNum/$($LAYERS.Count): $($Matches[2])`r`n")
                } elseif ($line -match '^OK:(\d+)$') {
                    $bar4.Value = [int]$Matches[1]
                    $log4.AppendText("  Layer $($Matches[1]) done.`r`n")
                } elseif ($line -eq 'ALLDONE') {
                    $bar4.Value = $LAYERS.Count
                    $log4.AppendText("`r`nAll modules installed!`r`n")
                    $sawAllDone = $true
                } elseif ($line -match '^ERROR:(.+)$') {
                    $log4.AppendText("ERROR: $($Matches[1])`r`n")
                }
            }
            $lastLine = $lines.Count
        }
        [System.Windows.Forms.Application]::DoEvents()
    }
    $lines = Get-Content $outFile -EA SilentlyContinue
    for ($i=$lastLine; $i -lt $lines.Count; $i++) { $log4.AppendText($lines[$i] + "`r`n") }
    $btnInstallMods.Enabled = $true

    if ($sawAllDone) {
        Show $p3
        $lblDone.Text = "Afia Clinic is ready!"
        $lblDoneErr.Text = ""
        $btnOpen.Visible = $true
        Start-Process "http://localhost:8069/odoo?db=$db"
    }
})

$form.ShowDialog() | Out-Null
