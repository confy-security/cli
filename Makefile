build:
	makepkg --syncdeps;

install:
	sudo pacman -U --noconfirm *.zst;

uninstall:
	sudo pacman -Rns --noconfirm confy-cli;

clean:
	rm -rf src pkg cli;
	rm -f *.zst *.tar.gz;

srcinfo:
	makepkg --printsrcinfo > .SRCINFO;

.PHONY: pkgbuild clean build install uninstall srcinfo