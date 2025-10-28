# Maintainer: Henrique Sebastião <contato@henriquesebastiao.com>

_pkgname='confy'
pkgname='confy-cli'
_module='confy-cli'
_src_folder='confy_cli-0.1.10'
pkgver='0.1.10'
pkgrel=1
pkgdesc="CLI client for the Confy encrypted communication system"
url=""
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
source=(https://files.pythonhosted.org/packages/47/ef/136323e423a5520fe8cf98794ff45d591da1b511a6b6c4f63309d42bcd36/confy_cli-0.1.10.tar.gz)
sha256sums=('a281665012132a342e38dc86b00b94263a92b590147e238ad51494436dc50c88')

provides=($_pkgname)
conflicts=($_pkgname)

build() {
    cd "${srcdir}/${_src_folder}"
    
    poetry build -f wheel --no-interaction --no-ansi --no-cache
}

package() {
    cd "${srcdir}/${_src_folder}"

    install -Dm644 -t "${pkgdir}/usr/share/licenses/${pkgname}" LICENSE
    install -Dm644 -t "${pkgdir}/usr/share/doc/${pkgname}" README.md
    
    python -m installer --destdir="${pkgdir}" dist/*.whl
}
