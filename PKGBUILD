# Maintainer: Henrique Sebastião <contato@henriquesebastiao.com>

_pkgname='confy'
pkgname='confy-cli'
_module='confy-cli'
_src_folder='confy_cli-0.1.4'
pkgver='0.1.4'
pkgrel=2
pkgdesc="CLI client for the Confy encrypted communication system"
url="https://github.com/confy-security/cli"
depends=('python' 'python-cryptography' 'python-typer' 'python-confy-addons')
makedepends=('python-poetry' 'python-installer')
license=('custom:GNU General Public License v3 (GPLv3)')
arch=('any')
source=(https://files.pythonhosted.org/packages/6b/91/254cae2eba178f6af5b38e5b5d3e7e65ab0d05ceb2c78d8117c3270b1005/confy_cli-0.1.4.tar.gz)
sha256sums=('0cc5049c1cc4f832a8ee08ed80f841b6eee17b8b78337ee43a3457ee0a015663')

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
