# Maintainer: Henrique Sebastião <contato@henriquesebastiao.com>

_pkgname='confy'
pkgname='confy-cli'
_module='confy-cli'
_src_folder='confy_cli-0.2.0'
pkgver='0.2.0'
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
source=(https://files.pythonhosted.org/packages/7b/45/a18279358f7527d85f1a382d36f5f9acfc0073f38e602cb1e515486dd4ff/confy_cli-0.2.0.tar.gz)
sha256sums=('61f3829a745a55c7ce09526e0df3f1ed779a804b7c8c3cf44b9c788a08c0b67a')

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
