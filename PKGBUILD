# Maintainer: Antigravity <antigravity@example.com>
pkgname=ffuf-gui
pkgver=0.1.1
pkgrel=1
pkgdesc="A modern web GUI wrapper for ffuf"
arch=('any')
url="https://github.com/example/ffuf-gui"
license=('MIT')
depends=('python' 'python-flask' 'ffuf')
makedepends=('python-build' 'python-installer' 'python-wheel' 'python-setuptools')
source=("${pkgname}-${pkgver}.tar.gz::https://github.com/example/ffuf-gui/archive/v${pkgver}.tar.gz")
sha256sums=('0ECF174C0FD851DE9E6C82CC3AE02BDAAADA1D371B987087574D3806C728C28B')

build() {
    cd "$pkgname-$pkgver"
    python -m build --wheel --no-isolation
}

package() {
    cd "$pkgname-$pkgver"
    python -m installer --destdir="$pkgdir" dist/*.whl
    
    # Install license
    install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
