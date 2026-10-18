$studyPython = 'python'
if (-not (Test-Path -LiteralPath $studyPython)) {
    $studyPython = (Get-Command python -ErrorAction Stop).Source
}
& $studyPython (Join-Path $PSScriptRoot 'run.py') @args
exit $LASTEXITCODE
