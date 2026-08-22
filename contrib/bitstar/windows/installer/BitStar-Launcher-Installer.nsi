Unicode true
RequestExecutionLevel user
SetCompressor /SOLID lzma
SetDateSave off

!ifndef PACKAGE_DIR
  !error "PACKAGE_DIR must point to an extracted BitStar Windows package"
!endif

!ifndef OUT_FILE
  !define OUT_FILE "BitStar_Core_Setup.exe"
!endif

!ifndef VERSION
  !define VERSION "dev"
!endif

!ifndef VI_VERSION
  !define VI_VERSION "0.0.0.0"
!endif

!define APP_NAME "BitStar Core"
!define COMPANY "BitStar project"
!define URL "https://bitstarcoin.org"
!define REGKEY "Software\BitStar Core"
!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\BitStar Core"

Name "${APP_NAME}"
OutFile "${OUT_FILE}"
InstallDir "$LOCALAPPDATA\Programs\BitStar Core"
InstallDirRegKey HKCU "${REGKEY}" "InstallDir"
BrandingText " "
ShowInstDetails show
ShowUninstDetails show

VIProductVersion "${VI_VERSION}"
VIAddVersionKey ProductName "${APP_NAME}"
VIAddVersionKey ProductVersion "${VERSION}"
VIAddVersionKey CompanyName "${COMPANY}"
VIAddVersionKey CompanyWebsite "${URL}"
VIAddVersionKey FileVersion "${VERSION}"
VIAddVersionKey FileDescription "Installer for ${APP_NAME}"
VIAddVersionKey LegalCopyright "Copyright (C) 2026 BitStar project"

!include MUI2.nsh
!include x64.nsh

!define MUI_ABORTWARNING
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_UNFINISHPAGE_NOAUTOCLOSE

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_LANGUAGE English

Section "BitStar Core" SEC_MAIN
    SetShellVarContext current
    SetOutPath "$INSTDIR"
    SetOverwrite on
    File /r "${PACKAGE_DIR}\*.*"

    WriteUninstaller "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "${REGKEY}" "InstallDir" "$INSTDIR"

    CreateDirectory "$SMPROGRAMS\BitStar Core"
    CreateShortcut "$SMPROGRAMS\BitStar Core\BitStar Launcher.lnk" "$INSTDIR\BitStar-Launcher.bat"
    CreateShortcut "$SMPROGRAMS\BitStar Core\Show BitStar Wallet Address.lnk" "$INSTDIR\Show-BitStar-Wallet-Address.bat" "" "$INSTDIR\bitstar.exe"
    IfFileExists "$INSTDIR\bitstar-qt.exe" 0 +2
      CreateShortcut "$SMPROGRAMS\BitStar Core\BitStar GUI.lnk" "$INSTDIR\bitstar.exe" "gui" "$INSTDIR\bitstar.exe"
    CreateShortcut "$SMPROGRAMS\BitStar Core\BitStar Console.lnk" "$INSTDIR\Open-BitStar-Console.bat"
    CreateShortcut "$SMPROGRAMS\BitStar Core\Uninstall BitStar Core.lnk" "$INSTDIR\Uninstall.exe"

    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "Publisher" "${COMPANY}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "URLInfoAbout" "${URL}"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\bitstar.exe"
    WriteRegStr HKCU "${UNINSTALL_KEY}" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoModify" 1
    WriteRegDWORD HKCU "${UNINSTALL_KEY}" "NoRepair" 1
SectionEnd

Section "Uninstall"
    SetShellVarContext current
    Delete "$SMPROGRAMS\BitStar Core\BitStar Launcher.lnk"
    Delete "$SMPROGRAMS\BitStar Core\Show BitStar Wallet Address.lnk"
    Delete "$SMPROGRAMS\BitStar Core\BitStar GUI.lnk"
    Delete "$SMPROGRAMS\BitStar Core\BitStar Console.lnk"
    Delete "$SMPROGRAMS\BitStar Core\Uninstall BitStar Core.lnk"
    RMDir "$SMPROGRAMS\BitStar Core"

    DeleteRegKey HKCU "${UNINSTALL_KEY}"
    DeleteRegKey HKCU "${REGKEY}"

    RMDir /r "$INSTDIR"
SectionEnd

Function .onInit
    ${IfNot} ${RunningX64}
      MessageBox MB_OK|MB_ICONSTOP "BitStar Core requires 64-bit Windows."
      Abort
    ${EndIf}
FunctionEnd
