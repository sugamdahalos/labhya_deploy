# PowerShell helper to build and optionally push the dev image
param(
    [switch]$Push
)

$tag = 'labhya/ssh-gpu:dev'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$dockerfileDir = Join-Path $root ''

Write-Host "Building $tag from $dockerfileDir"
docker build -t $tag $dockerfileDir

if ($Push) {
    Write-Host "Pushing $tag to registry"
    docker push $tag
}
