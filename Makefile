changelog:
	github_changelog_generator -u confy-security -p cli -o CHANGELOG --no-verbose;

build:
	makepkg --syncdeps;

install:
	sudo pacman -U --noconfirm *.zst;

uninstall:
	sudo pacman -Rns --noconfirm confy-cli;

clean:
	rm -rf src pkg cli;
	rm -f *.zst;

srcinfo:
	makepkg --printsrcinfo > .SRCINFO;

pkgbuild:
	./scripts/generate_pkgbuild.sh confy-cli;
	makepkg --printsrcinfo > .SRCINFO;

.PHONY: changelog pkgbuild clean build install uninstall srcinfo