# Maintainer: Henrique Sebastião <contato@henriquesebastiao.com>

_pkgname='confy'
pkgname='confy-cli'
_module='confy-cli'
_src_folder='confy_cli-'
pkgver='0.1.4'
pkgrel=1
pkgdesc="CLI client for the Confy encrypted communication system"
url="https://github.com/confy-security/cli"
depends=('python')
makedepends=('python-poetry' 'python-installer' 'git')
license=('custom:GNU General Public License v3 (GPLv3)')
arch=('any')
source=(git+$url)
sha256sums=(SKIP)

provides=($_pkgname)
conflicts=($_pkgname)

build() {
    cd "${srcdir}/cli"
    poetry build -f wheel --no-interaction --no-ansi --no-cache
}

package() {
    cd "${srcdir}/cli"

    install -Dm644 -t "${pkgdir}/usr/share/licenses/${pkgname}" LICENSE
    install -Dm644 -t "${pkgdir}/usr/share/doc/${pkgname}" README.md CHANGELOG
    install -Dm755 -t "${pkgdir}/usr/bin" "$(poetry env info -p)/bin/${_pkgname}"

    poetry add installer
    poetry run python -m installer --destdir="dist" dist/*.whl
}
