# The preview channel's release image: one build's release files, made by release.sh, kept in the
# private armada-release-preview package beside that build's server and web images. It has no
# shell and is never run; machines read /release out of it with docker create and docker cp.
#
#   docker build -f infra/deploy/release.Dockerfile -t <name> <release.sh output directory>
FROM scratch
COPY . /release/
