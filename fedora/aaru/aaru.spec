%global aaruver       6.0.0
%global aaruprerel    alpha.19
%global aarutag       v%{aaruver}-%{aaruprerel}
%global aarudir       /opt/Aaru

# Don't strip .NET binaries / generate debug subpackage / produce
# build-id links — the self-contained single-file launcher does not
# carry the standard ELF .note sections those macros expect.
%global __strip /bin/true
%global _build_id_links none
%global debug_package %{nil}

# Self-contained .NET single-file embeds many shared objects whose
# names rpm's automatic dep scanner can't resolve. The pattern matches
# the upstream pkg/rpm/aaru.spec convention.
%global __requires_exclude ^lib.*\.so.*$
%global __provides_exclude ^lib.*\.so.*$

Name:           aaru
Version:        %{aaruver}
# Pre-release sort: leading 0. ensures future stable 6.0.0-1 outranks
# any 0.alpha.NN.M from this line.
Release:        0.%{aaruprerel}.1%{?dist}
Summary:        Data preservation suite for optical, magnetic and solid-state media

License:        GPL-3.0-or-later AND LGPL-2.1-or-later AND MIT
URL:            https://github.com/aaru-dps/Aaru
# The packit create-archive action repacks the maintainer-signed
# source tarball into a properly-named %{name}-%{version}-%{prerel}/
# top-level layout that %setup expects.
Source0:        aaru-%{aaruver}-%{aaruprerel}.tar.gz
Source1:        aaru.1

ExclusiveArch:  x86_64

BuildRequires:  dotnet-sdk-10.0

# Native runtime deps of the self-contained .NET single-file (these
# are what the bundled runtime dynamically links to). Mirrors the
# upstream pkg/rpm/aaru.spec dep set.
Requires:       libicu
Requires:       krb5-libs
Requires:       libunwind
Requires:       openssl-libs
Requires:       zlib

# Desktop integration
Requires:       shared-mime-info
Requires:       desktop-file-utils
Requires(post): shared-mime-info, desktop-file-utils, hicolor-icon-theme

# The same `aaru` binary serves CLI and Avalonia GUI (gui is a
# ProjectReference; launched via `aaru gui`). Headless installs only
# need the CLI side and should not be forced to pull in the X11 / GL
# stack — declared as Recommends so dnf installs them by default but
# `--setopt=install_weak_deps=False` skips them cleanly.
Recommends:     libX11
Recommends:     libICE
Recommends:     libSM
Recommends:     libXext
Recommends:     libXi
Recommends:     libXrandr
Recommends:     libXcursor
Recommends:     mesa-libGL
Recommends:     fontconfig
Recommends:     freetype

%description
Aaru is a data preservation suite for optical, magnetic and solid-state
media. It dumps discs (CD/DVD/HD-DVD/BD/UMD/Floppy/MO) to byte-perfect
images, decodes filesystems, validates checksums and produces metadata
in the CICM format used by preservation projects.

The single `aaru` binary handles both modes:
  * `aaru` ............ command-line entry point (default)
  * `aaru gui` ........ launches the Avalonia desktop UI

cap_sys_rawio is set on the launcher binary so vendor SCSI passthrough
commands work without sudo.

%prep
%setup -q -n %{name}-%{aaruver}-%{aaruprerel}

# Strip the maintainer's Syncthing conflict copies that leaked into
# nupkgs/; they collide with the real package versions on restore.
find nupkgs -name "*sync-conflict*" -delete 2>/dev/null || true

%build
# Self-contained PublishSingleFile build, mirroring upstream's
# pkg/rpm/aaru.spec %build. EnableCompressionInSingleFile shaves the
# single-file binary from ~150 MB to ~80 MB; the runtime trade-off is
# a slightly slower first-launch decompression — acceptable for a CLI
# tool that is not in any hot path.
cd Aaru
dotnet publish -f net10.0 -c Release \
    --self-contained -r linux-x64 \
    -p:PublishSingleFile=true \
    -p:IncludeNativeLibrariesForSelfExtract=true \
    -p:EnableCompressionInSingleFile=true \
    -p:DebugType=none \
    -p:DebugSymbols=false

%install
# Real binary in /opt/Aaru (per upstream packaging), /usr/bin symlink
# for PATH. file capabilities live on the real binary; the kernel
# follows symlinks when exec'ing so the symlink invocation inherits
# them automatically.
install -D -m 0755 Aaru/bin/Release/net10.0/linux-x64/publish/aaru \
    %{buildroot}%{aarudir}/aaru
install -D -m 0644 README.md      %{buildroot}%{aarudir}/README.md
install -D -m 0644 Changelog.md   %{buildroot}%{aarudir}/Changelog.md
install -D -m 0644 CONTRIBUTING.md %{buildroot}%{aarudir}/CONTRIBUTING.md
install -D -m 0644 LICENSE        %{buildroot}%{aarudir}/LICENSE
install -D -m 0644 LICENSE.MIT    %{buildroot}%{aarudir}/LICENSE.MIT
install -D -m 0644 LICENSE.LGPL   %{buildroot}%{aarudir}/LICENSE.LGPL

# MIME type (.aif / .aaruformat / .dicf / .dicformat / .aaruf)
install -D -m 0644 Aaru/aaruformat.xml \
    %{buildroot}%{_datadir}/mime/packages/aaruformat.xml

# Desktop entry
install -D -m 0644 Aaru/aaru.desktop \
    %{buildroot}%{_datadir}/applications/aaru.desktop

# Icons (five sizes shipped upstream)
install -D -m 0644 icons/32x32/aaru.png    %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/aaru.png
install -D -m 0644 icons/64x64/aaru.png    %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/aaru.png
install -D -m 0644 icons/128x128/aaru.png  %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/aaru.png
install -D -m 0644 icons/256x256/aaru.png  %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/aaru.png
install -D -m 0644 icons/512x512/aaru.png  %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/aaru.png

# Manpage (handwritten — upstream provides none)
install -D -m 0644 %{SOURCE1} %{buildroot}%{_mandir}/man1/aaru.1

# PATH entry
install -d %{buildroot}%{_bindir}
ln -sf %{aarudir}/aaru %{buildroot}%{_bindir}/aaru

%post
touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
update-mime-database %{_datadir}/mime &>/dev/null || :
update-desktop-database &>/dev/null || :

%postun
if [ $1 -eq 0 ] ; then
    touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi
update-mime-database %{_datadir}/mime &>/dev/null || :
update-desktop-database &>/dev/null || :

%posttrans
gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :

%files
%caps(cap_sys_rawio=ep) %attr(0755,root,root) %{aarudir}/aaru
%{aarudir}/README.md
%{aarudir}/Changelog.md
%{aarudir}/CONTRIBUTING.md
%license %{aarudir}/LICENSE
%license %{aarudir}/LICENSE.MIT
%license %{aarudir}/LICENSE.LGPL
%{_bindir}/aaru
%{_datadir}/mime/packages/aaruformat.xml
%{_datadir}/applications/aaru.desktop
%{_datadir}/icons/hicolor/32x32/apps/aaru.png
%{_datadir}/icons/hicolor/64x64/apps/aaru.png
%{_datadir}/icons/hicolor/128x128/apps/aaru.png
%{_datadir}/icons/hicolor/256x256/apps/aaru.png
%{_datadir}/icons/hicolor/512x512/apps/aaru.png
%{_mandir}/man1/aaru.1*

%changelog
* Mon Jun 15 2026 gmipf <gmipf64@gmail.com> - 6.0.0-0.alpha.19.2
- Rewrite based on upstream pkg/rpm/aaru.spec template
- Switch to self-contained PublishSingleFile build (matches upstream),
  drops the framework-dependent / dotnet-runtime-10.0 Requires path
- Install layout moves to /opt/Aaru with /usr/bin/aaru symlink (caps
  on real binary, kernel follows symlink for cap inheritance)
- Ship the upstream desktop entry, MIME type (.aif / .dicformat /
  .aaruformat / .aaruf), and five icon sizes
- Add %post / %postun / %posttrans MIME + icon + desktop cache hooks
- Keep handwritten aaru(1) manpage (upstream provides none)
- X11/GL/fontconfig stack remains in Recommends so headless installs
  stay lean while desktop installs get the full GUI experience

* Mon Jun 15 2026 gmipf <gmipf64@gmail.com> - 6.0.0-0.alpha.19.1
- Initial COPR build attempt (failed in %prep due to rootless tarball
  conflict with Fedora rpm 4.20's _builddir cleanup)
