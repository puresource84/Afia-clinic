# Afia Clinic - GUI Wizard Installer
# Run as Administrator for best results
# Usage: .\install.ps1

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# -- Branding ------------------------------------------------------------------
$BRAND_BLUE   = [System.Drawing.Color]::FromArgb(26, 115, 167)
$BRAND_DARK   = [System.Drawing.Color]::FromArgb(13, 90, 138)
$BRAND_LIGHT  = [System.Drawing.Color]::FromArgb(214, 232, 245)
$WHITE        = [System.Drawing.Color]::White
$GREY_TEXT    = [System.Drawing.Color]::FromArgb(95, 99, 104)
$GREEN        = [System.Drawing.Color]::FromArgb(30, 142, 62)
$SCRIPT_DIR   = Split-Path -Parent $MyInvocation.MyCommand.Path
$MODULES_DIR  = Join-Path $SCRIPT_DIR "modules"
$DOCKER_DIR   = Join-Path $SCRIPT_DIR "docker"

# -- Helpers -------------------------------------------------------------------
function New-Label($text, $x, $y, $w, $h, $size=10, $bold=$false, $color=$null) {
    $l = New-Object System.Windows.Forms.Label
    $l.Text = $text; $l.Left = $x; $l.Top = $y; $l.Width = $w; $l.Height = $h
    $l.Font = New-Object System.Drawing.Font("Segoe UI", $size, $(if($bold){"Bold"}else{"Regular"}))
    $l.ForeColor = if($color){$color}else{[System.Drawing.Color]::FromArgb(32,33,36)}
    $l.BackColor = [System.Drawing.Color]::Transparent
    return $l
}
function New-Btn($text, $x, $y, $w=120, $h=36, $primary=$true) {
    $b = New-Object System.Windows.Forms.Button
    $b.Text = $text; $b.Left = $x; $b.Top = $y; $b.Width = $w; $b.Height = $h
    $b.FlatStyle = "Flat"
    $b.FlatAppearance.BorderSize = 0
    $b.BackColor = if($primary){$BRAND_BLUE}else{[System.Drawing.Color]::FromArgb(232,234,237)}
    $b.ForeColor = if($primary){$WHITE}else{[System.Drawing.Color]::FromArgb(32,33,36)}
    $b.Font = New-Object System.Drawing.Font("Segoe UI", 10, "Regular")
    $b.Cursor = [System.Windows.Forms.Cursors]::Hand
    return $b
}
function New-Panel($x, $y, $w, $h, $color) {
    $p = New-Object System.Windows.Forms.Panel
    $p.Left=$x; $p.Top=$y; $p.Width=$w; $p.Height=$h; $p.BackColor=$color
    return $p
}

# -- Main Form -----------------------------------------------------------------
$form = New-Object System.Windows.Forms.Form
$form.Text = "Afia Clinic - Setup Wizard"
$form.Size = New-Object System.Drawing.Size(620, 480)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.MinimizeBox = $false
$form.BackColor = $WHITE

# Header band
$header = New-Panel 0 0 620 90 $BRAND_BLUE
$form.Controls.Add($header)
$hTitle = New-Label "Afia Clinic" 24 14 400 36 22 $true $WHITE
$hTitle.BackColor = $BRAND_BLUE
$header.Controls.Add($hTitle)
$hSub = New-Label "Dental Practice Management Suite for Odoo 18" 24 50 500 24 10 $false $BRAND_LIGHT
$hSub.BackColor = $BRAND_BLUE
$header.Controls.Add($hSub)

# Step indicator panel
$stepBar = New-Panel 0 90 620 4 $BRAND_LIGHT
$form.Controls.Add($stepBar)
$stepProg = New-Panel 0 90 155 4 $BRAND_BLUE
$form.Controls.Add($stepProg)

# -- Page container ------------------------------------------------------------
$pages = @{}
$currentPage = 0

function Show-Page($name) {
    foreach ($k in $pages.Keys) { $pages[$k].Visible = $false }
    $pages[$name].Visible = $true
}

# ==============================================================================
# PAGE 1 - WELCOME
# ==============================================================================
$p1 = New-Panel 0 100 620 320 $WHITE
$form.Controls.Add($p1)
$pages["welcome"] = $p1

$p1.Controls.Add((New-Label "Welcome to Afia Clinic Setup" 40 20 540 34 16 $true))
$p1.Controls.Add((New-Label "This wizard will install Afia Clinic - 38 dental practice management`nmodules - on your computer in a few simple steps." 40 60 540 50 10))
$p1.Controls.Add((New-Label "What this installer does:" 40 120 540 22 10 $true))

$steps_text = @(
    "1.  Checks if Docker or Odoo 18 CE is installed",
    "2.  Installs the prerequisite if missing",
    "3.  Deploys all 38 Afia Clinic modules automatically",
    "4.  Opens your clinic system in the browser"
)
$ty = 146
foreach ($s in $steps_text) {
    $p1.Controls.Add((New-Label $s 56 $ty 500 20 10 $false $GREY_TEXT))
    $ty += 22
}
$p1.Controls.Add((New-Label "Developed by ITCS (IT Corner Solutions) - itcornersolutions.net" 40 250 540 20 9 $false $GREY_TEXT))

$btnNext1 = New-Btn "Next >" 480 270
$p1.Controls.Add($btnNext1)

# ==============================================================================
# PAGE 2 - CHOOSE METHOD
# ==============================================================================
$p2 = New-Panel 0 100 620 320 $WHITE
$p2.Visible = $false
$form.Controls.Add($p2)
$pages["method"] = $p2

$p2.Controls.Add((New-Label "Choose Installation Method" 40 20 540 34 16 $true))
$p2.Controls.Add((New-Label "Select how you want to run Afia Clinic:" 40 58 540 22 10))

# Docker option
$dockerPanel = New-Panel 36 88 530 82 $BRAND_LIGHT
$dockerPanel.Cursor = [System.Windows.Forms.Cursors]::Hand
$p2.Controls.Add($dockerPanel)

$rbDocker = New-Object System.Windows.Forms.RadioButton
$rbDocker.Left=14; $rbDocker.Top=14; $rbDocker.Width=20; $rbDocker.Height=20
$rbDocker.Checked = $true; $rbDocker.BackColor = $BRAND_LIGHT
$dockerPanel.Controls.Add($rbDocker)
$dockerPanel.Controls.Add((New-Label "Docker  (Recommended)" 40 12 400 22 11 $true))
$dockerPanel.Controls.Add((New-Label "Fully automatic. Installs everything in isolated containers.`nNo manual Odoo setup needed. Works on any Windows 10/11 machine." 40 36 470 38 9 $false $GREY_TEXT))

# Native Odoo option
$odooPanel = New-Panel 36 182 530 82 ([System.Drawing.Color]::FromArgb(248,249,250))
$odooPanel.Cursor = [System.Windows.Forms.Cursors]::Hand
$p2.Controls.Add($odooPanel)

$rbOdoo = New-Object System.Windows.Forms.RadioButton
$rbOdoo.Left=14; $rbOdoo.Top=14; $rbOdoo.Width=20; $rbOdoo.Height=20
$rbOdoo.BackColor = [System.Drawing.Color]::FromArgb(248,249,250)
$odooPanel.Controls.Add($rbOdoo)
$odooPanel.Controls.Add((New-Label "Native Odoo 18 CE" 40 12 400 22 11 $true))
$odooPanel.Controls.Add((New-Label "Installs Odoo 18 Community Edition directly on Windows.`nBetter for clinics that prefer a local installation without Docker." 40 36 470 38 9 $false $GREY_TEXT))

# Radio sync on panel click
$dockerPanel.Add_Click({ $rbDocker.Checked = $true; $rbOdoo.Checked = $false; $dockerPanel.BackColor = $BRAND_LIGHT; $odooPanel.BackColor = [System.Drawing.Color]::FromArgb(248,249,250) })
$odooPanel.Add_Click({ $rbOdoo.Checked = $true; $rbDocker.Checked = $false; $odooPanel.BackColor = $BRAND_LIGHT; $dockerPanel.BackColor = [System.Drawing.Color]::FromArgb(248,249,250) })

$btnBack2 = New-Btn "< Back" 350 270 110 36 $false
$btnNext2 = New-Btn "Install >" 476 270
$p2.Controls.Add($btnBack2)
$p2.Controls.Add($btnNext2)

# ==============================================================================
# PAGE 3 - INSTALLING
# ==============================================================================
$p3 = New-Panel 0 100 620 320 $WHITE
$p3.Visible = $false
$form.Controls.Add($p3)
$pages["installing"] = $p3

$p3.Controls.Add((New-Label "Installing..." 40 20 540 34 16 $true))
$lblStatus = New-Label "Preparing installation..." 40 62 540 22 10 $false $GREY_TEXT
$p3.Controls.Add($lblStatus)

$progress = New-Object System.Windows.Forms.ProgressBar
$progress.Left=40; $progress.Top=94; $progress.Width=530; $progress.Height=22
$progress.Style = "Continuous"; $progress.Minimum=0; $progress.Maximum=100
$p3.Controls.Add($progress)

$lblStep = New-Label "" 40 126 540 20 9 $false $GREY_TEXT
$p3.Controls.Add($lblStep)

$logBox = New-Object System.Windows.Forms.RichTextBox
$logBox.Left=40; $logBox.Top=154; $logBox.Width=530; $logBox.Height=120
$logBox.ReadOnly=$true; $logBox.BackColor=[System.Drawing.Color]::FromArgb(248,249,250)
$logBox.Font=New-Object System.Drawing.Font("Consolas",8)
$logBox.BorderStyle="FixedSingle"
$p3.Controls.Add($logBox)

function Log($msg) {
    $logBox.AppendText("$msg`n")
    $logBox.ScrollToCaret()
    [System.Windows.Forms.Application]::DoEvents()
}
function Set-Status($msg, $pct) {
    $lblStatus.Text = $msg
    $progress.Value = [Math]::Min($pct, 100)
    [System.Windows.Forms.Application]::DoEvents()
}

# ==============================================================================
# PAGE 4 - COMPLETE
# ==============================================================================
$p4 = New-Panel 0 100 620 320 $WHITE
$p4.Visible = $false
$form.Controls.Add($p4)
$pages["done"] = $p4

$doneIcon = New-Label "OK" 40 20 60 60 32 $true $GREEN
$p4.Controls.Add($doneIcon)
$p4.Controls.Add((New-Label "Installation Complete!" 100 28 440 36 16 $true $GREEN))
$p4.Controls.Add((New-Label "Afia Clinic is ready. Open your browser to get started:" 40 90 540 22 10))

$urlLabel = New-Label "http://localhost:8069" 40 118 400 28 13 $true $BRAND_BLUE
$p4.Controls.Add($urlLabel)

$p4.Controls.Add((New-Label "Next steps:" 40 158 540 22 10 $true))
$p4.Controls.Add((New-Label "1. Create a new database on the login screen" 56 182 500 20 10 $false $GREY_TEXT))
$p4.Controls.Add((New-Label "2. Go to Apps and install 'Dental Hospital'" 56 204 500 20 10 $false $GREY_TEXT))
$p4.Controls.Add((New-Label "3. All 38 Afia Clinic modules will be available" 56 226 500 20 10 $false $GREY_TEXT))

$btnBrowser = New-Btn "Open in Browser" 40 260 160 36
$btnFinish  = New-Btn "Finish" 476 260
$p4.Controls.Add($btnBrowser)
$p4.Controls.Add($btnFinish)

$btnBrowser.Add_Click({ Start-Process "http://localhost:8069" })
$btnFinish.Add_Click({ $form.Close() })

# ==============================================================================
# NAVIGATION
# ==============================================================================
$btnNext1.Add_Click({
    $stepProg.Width = 310
    Show-Page "method"
})

$btnBack2.Add_Click({
    $stepProg.Width = 155
    Show-Page "welcome"
})

$btnNext2.Add_Click({
    $stepProg.Width = 465
    Show-Page "installing"
    $form.Refresh()

    if ($rbDocker.Checked) {
        Install-WithDocker
    } else {
        Install-WithNativeOdoo
    }

    $stepProg.Width = 620
    Show-Page "done"
})

# ==============================================================================
# INSTALL LOGIC - DOCKER
# ==============================================================================
function Install-WithDocker {
    $lblStatus.Text = "Checking Docker..."
    [System.Windows.Forms.Application]::DoEvents()

    $dockerOk = $false
    try {
        $v = & docker --version 2>$null
        if ($LASTEXITCODE -eq 0) { $dockerOk = $true }
    } catch {}

    if (-not $dockerOk) {
        Set-Status "Downloading Docker Desktop..." 10
        Log "Docker not found. Downloading Docker Desktop..."
        Log "This may take a few minutes depending on your connection."

        $dockerInstaller = Join-Path $env:TEMP "DockerDesktopInstaller.exe"
        $url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"

        try {
            $wc = New-Object System.Net.WebClient
            $wc.DownloadFile($url, $dockerInstaller)
            Set-Status "Installing Docker Desktop..." 30
            Log "Download complete. Installing Docker Desktop..."
            Log "A UAC prompt may appear - please accept it."
            Start-Process $dockerInstaller -ArgumentList "install --quiet --accept-license" -Wait
            Log "Docker Desktop installed."
            Log "IMPORTANT: Please restart your computer, then re-run this installer."
            Set-Status "Restart required to complete Docker setup." 40
            [System.Windows.Forms.MessageBox]::Show(
                "Docker Desktop was installed successfully.`n`nPlease RESTART your computer, then run this installer again to complete the Afia Clinic setup.",
                "Restart Required",
                [System.Windows.Forms.MessageBoxButtons]::OK,
                [System.Windows.Forms.MessageBoxIcon]::Information
            )
            $form.Close()
            return
        } catch {
            Log "ERROR: Could not download Docker. Check your internet connection."
            Log "Alternatively, download Docker manually from: https://docker.com/products/docker-desktop"
            Set-Status "Download failed. See log for details." 0
            return
        }
    }

    Log "Docker found: $( & docker --version 2>$null )"
    Set-Status "Starting Afia Clinic containers..." 50
    Log "Running docker compose..."

    try {
        Set-Location $DOCKER_DIR
        $proc = Start-Process "docker" -ArgumentList "compose up -d" -Wait -PassThru -NoNewWindow
        if ($proc.ExitCode -ne 0) { throw "docker compose failed" }
        Set-Status "Waiting for Odoo to start..." 80
        Log "Containers started. Waiting 30 seconds for Odoo to initialize..."
        for ($i = 0; $i -lt 30; $i++) {
            Start-Sleep 1
            $progress.Value = 80 + [int]($i / 30 * 18)
            [System.Windows.Forms.Application]::DoEvents()
        }
        Set-Status "Afia Clinic is ready!" 100
        Log "Done! Afia Clinic is running at http://localhost:8069"
    } catch {
        Log "ERROR: $($_.Exception.Message)"
        Set-Status "Installation failed. See log above." 0
    }
}

# ==============================================================================
# INSTALL LOGIC - NATIVE ODOO
# ==============================================================================
function Install-WithNativeOdoo {
    Set-Status "Checking for Odoo 18 CE..." 5
    Log "Checking for existing Odoo installation..."

    $customAddons = $null
    $odooService  = Get-Service -Name "*odoo*" -ErrorAction SilentlyContinue | Select-Object -First 1
    $searchPaths  = @("C:\Program Files\Odoo 18*\server\custom_addons","C:\Program Files (x86)\Odoo 18*\server\custom_addons")
    foreach ($pattern in $searchPaths) {
        $found = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) { $customAddons = $found.FullName; break }
    }

    if (-not $customAddons) {
        Set-Status "Downloading Odoo 18 CE..." 10
        Log "Odoo 18 CE not found. Downloading installer..."
        Log "File size ~350 MB. This may take several minutes."

        $odooInstaller = Join-Path $env:TEMP "odoo_18_setup.exe"
        $url = "https://download.odoocdn.com/download/win/community?release=18.0"

        try {
            $wc = New-Object System.Net.WebClient
            $wc.DownloadFile($url, $odooInstaller)
            Set-Status "Installing Odoo 18 CE..." 40
            Log "Download complete. Launching Odoo installer..."
            Log "Follow the Odoo setup wizard. Use default settings."
            Log "When it finishes, this installer will continue automatically."
            Start-Process $odooInstaller -Wait
            Log "Odoo setup finished. Scanning for installation..."

            # Re-scan after install
            foreach ($pattern in $searchPaths) {
                $found = Get-Item $pattern -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($found) { $customAddons = $found.FullName; break }
            }
            $odooService = Get-Service -Name "*odoo*" -ErrorAction SilentlyContinue | Select-Object -First 1

            if (-not $customAddons) {
                Log "ERROR: Could not find custom_addons after install. Please re-run this installer."
                Set-Status "Could not locate Odoo folder. Re-run installer." 0
                return
            }
        } catch {
            Log "ERROR: $($_.Exception.Message)"
            Set-Status "Download failed. Check internet and try again." 0
            return
        }
    }

    Log "Odoo found at: $customAddons"
    Set-Status "Copying Afia Clinic modules..." 60
    Log "Copying 38 modules to custom_addons..."

    $count = 0
    Get-ChildItem -Path $MODULES_DIR -Directory | ForEach-Object {
        $dest = Join-Path $customAddons $_.Name
        Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
        $count++
        $progress.Value = 60 + [int]($count / 38 * 25)
        $lblStep.Text = "Copying: $($_.Name)"
        [System.Windows.Forms.Application]::DoEvents()
    }
    $lblStep.Text = ""
    Log "Copied $count modules."

    if ($odooService) {
        Set-Status "Restarting Odoo service..." 88
        Log "Restarting Odoo service: $($odooService.Name)"
        try {
            Restart-Service -Name $odooService.Name -Force
            Log "Service restarted. Waiting 20 seconds..."
            for ($i = 0; $i -lt 20; $i++) {
                Start-Sleep 1
                $progress.Value = 88 + [int]($i / 20 * 10)
                [System.Windows.Forms.Application]::DoEvents()
            }
        } catch {
            Log "Note: Could not restart service automatically. Please restart Odoo manually."
        }
    } else {
        Log "Note: Odoo service not detected. Start Odoo manually if it is not running."
    }

    Set-Status "Afia Clinic is ready!" 100
    Log "Done! Open http://localhost:8069"
    Log "Go to Apps > Update Apps List, then install 'Dental Hospital'."
}

# -- Launch --------------------------------------------------------------------
Show-Page "welcome"
$form.Add_Shown({ $form.Activate() })
[System.Windows.Forms.Application]::Run($form)
