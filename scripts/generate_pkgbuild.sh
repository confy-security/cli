#!/bin/bash

# Script to generate PKGBUILD with updated information from PyPI
# Usage: ./generate_pkgbuild.sh <pypi_package_name>

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check arguments
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: PyPI package name is required${NC}"
    echo "Usage: $0 <pypi_package_name>"
    exit 1
fi

PYPI_PACKAGE="$1"
PKGBUILD_TEMPLATE="${2:-.PKGBUILD.template}"

# Check if we are in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}Error: Not in a Git repository${NC}"
    exit 1
fi

# Get git version
echo -e "${YELLOW}Obtaining Git repository version...${NC}"
VERSION=$(git describe --tags --always 2>/dev/null | cut -d'-' -f1 | sed 's/^v//')

if [ -z "$VERSION" ]; then
    echo -e "${RED}Error: Could not obtain Git version${NC}"
    exit 1
fi

echo -e "${GREEN}Detected version: $VERSION${NC}"

# Get PyPI information
echo -e "${YELLOW}Obtaining PyPI information for $PYPI_PACKAGE...${NC}"

PYPI_JSON=$(curl -s "https://pypi.org/pypi/$PYPI_PACKAGE/$VERSION/json")

if echo "$PYPI_JSON" | grep -q '"404"'; then
    echo -e "${RED}Error: Package not found on PyPI with version $VERSION${NC}"
    exit 1
fi

# Extract information
PACKAGE_NAME=$(echo "$PYPI_JSON" | jq -r '.info.name // empty')
PACKAGE_URL=$(echo "$PYPI_JSON" | jq -r '.info.project_urls.Homepage // .info.project_urls.Repository // empty')
SOURCE_URL=$(echo "$PYPI_JSON" | jq -r '.urls[] | select(.filename | endswith(".tar.gz")) | .url' | head -1)
SHA256=$(echo "$PYPI_JSON" | jq -r '.urls[] | select(.filename | endswith(".tar.gz")) | .digests.sha256' | head -1)

if [ -z "$SOURCE_URL" ] || [ -z "$SHA256" ]; then
    echo -e "${RED}Error: Could not obtain source URL or SHA256${NC}"
    exit 1
fi

# Extract source folder name
SRC_FOLDER=$(basename "$SOURCE_URL" .tar.gz)

echo -e "${GREEN}Information obtained successfully:${NC}"
echo "  Version: $VERSION"
echo "  Package Name: $PACKAGE_NAME"
echo "  Source URL: $SOURCE_URL"
echo "  SHA256: $SHA256"
echo "  Src Folder: $SRC_FOLDER"

# Generate PKGBUILD
echo -e "${YELLOW}Generating PKGBUILD...${NC}"

cat > PKGBUILD << EOF
# Maintainer: Henrique Sebastião <contato@henriquesebastiao.com>

_pkgname='confy'
pkgname='confy-cli'
_module='confy-cli'
_src_folder='$SRC_FOLDER'
pkgver='$VERSION'
pkgrel=1
pkgdesc="CLI client for the Confy encrypted communication system"
url="$PACKAGE_URL"
depends=(
    'python'
    'python-confy-addons'
    'python-cryptography'
    'python-prompt_toolkit'
    'python-pydantic-settings'
    'python-typer'
    'python-websockets'
)
makedepends=('python-poetry' 'python-installer')
license=('custom:GNU General Public License v3 (GPLv3)')
arch=('any')
source=($SOURCE_URL)
sha256sums=('$SHA256')

provides=(\$_pkgname)
conflicts=(\$_pkgname)

build() {
    cd "\${srcdir}/\${_src_folder}"
    
    poetry build -f wheel --no-interaction --no-ansi --no-cache
}

package() {
    cd "\${srcdir}/\${_src_folder}"

    install -Dm644 -t "\${pkgdir}/usr/share/licenses/\${pkgname}" LICENSE
    install -Dm644 -t "\${pkgdir}/usr/share/doc/\${pkgname}" README.md
    
    python -m installer --destdir="\${pkgdir}" dist/*.whl
}
EOF

echo -e "${GREEN}PKGBUILD gerado com sucesso!${NC}"
echo -e "${YELLOW}Arquivo salvo como: ./PKGBUILD${NC}"