; The desktop app's Windows installer. Build it with installer_run.py, which supplies every
; define checked below from organization.json and the backend's version.

Unicode true
ManifestDPIAware true
SetCompressor /SOLID lzma

!macro RequireDefine NAME
  !ifndef ${NAME}
    !error "${NAME} is not defined. Build with: python apps/desktop/installer_run.py"
  !endif
!macroend
!insertmacro RequireDefine APP_NAME
!insertmacro RequireDefine DISPLAY_NAME
!insertmacro RequireDefine DESCRIPTION
!insertmacro RequireDefine URL
!insertmacro RequireDefine VERSION
!insertmacro RequireDefine NUMERIC_VERSION
!insertmacro RequireDefine SOURCE_DIR
!insertmacro RequireDefine LICENSE_FILE
!insertmacro RequireDefine OUT_FILE

!define UNINSTALL_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
!define WEBVIEW2_CLIENT "Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
!define WEBVIEW2_DOWNLOAD "https://developer.microsoft.com/microsoft-edge/webview2/consumer/"

Name "${DISPLAY_NAME}"
OutFile "${OUT_FILE}"
BrandingText "${DISPLAY_NAME} ${VERSION}"

VIProductVersion "${NUMERIC_VERSION}"
VIAddVersionKey "ProductName" "${DISPLAY_NAME}"
VIAddVersionKey "ProductVersion" "${VERSION}"
VIAddVersionKey "FileVersion" "${VERSION}"
VIAddVersionKey "CompanyName" "${DISPLAY_NAME}"
VIAddVersionKey "FileDescription" "${DISPLAY_NAME} Setup"
VIAddVersionKey "Comments" "${DESCRIPTION}"
VIAddVersionKey "LegalCopyright" "See the license agreement"

; Install scope: "just me" or "all users", also /CurrentUser or /AllUsers on the command line.
!define MULTIUSER_EXECUTIONLEVEL Highest
!define MULTIUSER_MUI
!define MULTIUSER_INSTALLMODE_COMMANDLINE
!define MULTIUSER_USE_PROGRAMFILES64
!define MULTIUSER_INSTALLMODE_INSTDIR "${APP_NAME}"
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_KEY "${UNINSTALL_KEY}"
!define MULTIUSER_INSTALLMODE_DEFAULT_REGISTRY_VALUENAME "InstallLocation"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_KEY "${UNINSTALL_KEY}"
!define MULTIUSER_INSTALLMODE_INSTDIR_REGISTRY_VALUENAME "InstallLocation"

!include MultiUser.nsh
!include MUI2.nsh
!include LogicLib.nsh
!include x64.nsh
!include FileFunc.nsh

!define MUI_ABORTWARNING
!define MUI_LICENSEPAGE_RADIOBUTTONS
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Launch ${DISPLAY_NAME}"
!define MUI_FINISHPAGE_RUN_FUNCTION LaunchApp

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "${LICENSE_FILE}"
!insertmacro MULTIUSER_PAGE_INSTALLMODE
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

Function .onInit
  ${IfNot} ${RunningX64}
    MessageBox MB_ICONSTOP "${DISPLAY_NAME} requires 64-bit Windows." /SD IDOK
    Abort
  ${EndIf}
  SetRegView 64
  !insertmacro MULTIUSER_INIT
  Call CheckWebView2
FunctionEnd

Function un.onInit
  SetRegView 64
  !insertmacro MULTIUSER_UNINIT
FunctionEnd

; Microsoft's documented check: a "pv" value above 0.0.0.0 in either location means installed.
Function CheckWebView2
  ReadRegStr $0 HKLM "SOFTWARE\WOW6432Node\${WEBVIEW2_CLIENT}" "pv"
  ${If} $0 == ""
  ${OrIf} $0 == "0.0.0.0"
    ReadRegStr $0 HKCU "Software\${WEBVIEW2_CLIENT}" "pv"
  ${EndIf}
  ${If} $0 == ""
  ${OrIf} $0 == "0.0.0.0"
    MessageBox MB_ICONSTOP "${DISPLAY_NAME} needs the Microsoft Edge WebView2 Runtime, which is not installed.$\r$\n$\r$\nInstall it from ${WEBVIEW2_DOWNLOAD} and then run this setup again." /SD IDOK
    Abort
  ${EndIf}
FunctionEnd

Function RemovePreviousInstall
  ReadRegStr $0 SHCTX "${UNINSTALL_KEY}" "InstallLocation"
  ${If} $0 != ""
  ${AndIf} ${FileExists} "$0\Uninstall.exe"
    DetailPrint "Removing the previous version from $0"
    ; _?= runs the old uninstaller in place so ExecWait actually waits for it.
    ExecWait '"$0\Uninstall.exe" /S /$MultiUser.InstallMode _?=$0'
    Delete "$0\Uninstall.exe"
    RMDir "$0"
  ${EndIf}
FunctionEnd

; Launching through explorer.exe starts the app as the signed-in user, not with this
; installer's administrator rights.
Function LaunchApp
  Exec '"$WINDIR\explorer.exe" "$INSTDIR\${APP_NAME}.exe"'
FunctionEnd

Section "-${DISPLAY_NAME}"
  Call RemovePreviousInstall

  SetOutPath "$INSTDIR"
  File /r "${SOURCE_DIR}\*.*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  CreateShortcut "$SMPROGRAMS\${DISPLAY_NAME}.lnk" "$INSTDIR\${APP_NAME}.exe"

  WriteRegStr SHCTX "${UNINSTALL_KEY}" "DisplayName" "${DISPLAY_NAME}"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "DisplayVersion" "${VERSION}"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "Publisher" "${DISPLAY_NAME}"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "URLInfoAbout" "${URL}"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "DisplayIcon" "$INSTDIR\${APP_NAME}.exe"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "UninstallString" '"$INSTDIR\Uninstall.exe" /$MultiUser.InstallMode'
  WriteRegStr SHCTX "${UNINSTALL_KEY}" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /$MultiUser.InstallMode /S'
  WriteRegDWORD SHCTX "${UNINSTALL_KEY}" "NoModify" 1
  WriteRegDWORD SHCTX "${UNINSTALL_KEY}" "NoRepair" 1
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  WriteRegDWORD SHCTX "${UNINSTALL_KEY}" "EstimatedSize" $0
SectionEnd

Section /o "Desktop shortcut"
  CreateShortcut "$DESKTOP\${DISPLAY_NAME}.lnk" "$INSTDIR\${APP_NAME}.exe"
SectionEnd

; Removes only what the installer put there -- the PyInstaller bundle's exe and _internal/
; -- so choosing a shared folder like Program Files itself cannot wipe unrelated files.
Section "Uninstall"
  Delete "$INSTDIR\${APP_NAME}.exe"
  RMDir /r "$INSTDIR\_internal"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"

  Delete "$SMPROGRAMS\${DISPLAY_NAME}.lnk"
  Delete "$DESKTOP\${DISPLAY_NAME}.lnk"
  DeleteRegKey SHCTX "${UNINSTALL_KEY}"
SectionEnd