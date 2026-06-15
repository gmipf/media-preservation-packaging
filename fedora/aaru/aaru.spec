%global debug_package %{nil}
%global __strip /bin/true
%global __os_install_post %{nil}
%global _build_id_links none

# Upstream prerelease naming: v6.0.0-alpha.19. Map to Fedora-conformant
# Version+Release with a leading 0. so a future v6.0.0 stable will sort
# higher (1.fc43 > 0.alpha.19.1.fc43).
%global aaruver       6.0.0
%global aaruprerel    alpha.19
%global aarutag       v%{aaruver}-%{aaruprerel}

Name:           aaru
Version:        %{aaruver}
Release:        0.%{aaruprerel}.1%{?dist}
Summary:        Data preservation suite for optical, magnetic and solid-state media

License:        GPL-3.0-or-later AND LGPL-2.1-or-later AND MIT
URL:            https://github.com/aaru-dps/Aaru
# Maintainer-curated source tarball (signed). The auto-generated GitHub
# archive at /archive/refs/tags/ is missing vendored content and won't
# build; this tarball is the only working source distribution.
Source0:        %{url}/releases/download/%{aarutag}/aaru-src-%{aaruver}-%{aaruprerel}.tar.xz
Source1:        aaru.desktop
Source2:        aaru.1

ExclusiveArch:  x86_64

BuildRequires:  dotnet-sdk-10.0

# Hard runtime: framework-dependent build needs system .NET 10 runtime.
Requires:       dotnet-runtime-10.0

# The same `aaru` binary handles both the CLI and the Avalonia GUI
# (Aaru.Gui is a ProjectReference, linked in at compile-time; launched
# via `aaru gui`). To keep headless installs lean, the X11 / GL /
# fontconfig stack is pulled in via Recommends — `aaru dump ...` works
# fine without these, only `aaru gui` requires them.
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

# AutoReq scans the launcher binary and embedded native libs and either
# fails or fabricates noise — disable across the board.
AutoReqProv:    no

%description
Aaru is a data preservation suite for optical, magnetic and solid-state
media. It dumps discs (CD/DVD/HD-DVD/BD/UMD/Floppy/MO) to byte-perfect
images, decodes filesystems, validates checksums and produces metadata
in the CICM format used by preservation projects.

This binary handles both the CLI and the Avalonia-based GUI:
  * `aaru` — CLI entry point (default)
  * `aaru gui` — launches the GUI; needs an X11 / Wayland desktop

cap_sys_rawio is set on the launcher binary so vendor SCSI passthrough
commands work without sudo.

%prep
# Source tarball is rootless (entries start at ./Aaru/, ./Aaru.Gui/, ...)
%setup -q -c -n %{name}-%{aaruver}-%{aaruprerel}

# Remove the maintainer's Syncthing conflict copies that leaked into
# the source tarball under nupkgs/. These would compete with the real
# package versions during restore.
find nupkgs -name "*sync-conflict*" -delete 2>/dev/null || true

%build
# Framework-dependent publish so the binary uses the system
# dotnet-runtime-10.0 instead of bundling its own copy of the runtime
# (saves ~50 MB and lets multiple .NET apps share the runtime).
dotnet publish Aaru/Aaru.csproj \
    -c Release \
    -r linux-x64 \
    --self-contained false \
    -p:UseAppHost=true \
    -p:DebugType=none \
    -p:DebugSymbols=false

%install
install -d %{buildroot}%{_libdir}/aaru
cp -a Aaru/bin/Release/net10.0/linux-x64/publish/. \
       %{buildroot}%{_libdir}/aaru/

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/aaru <<'EOF'
#!/bin/sh
exec %{_libdir}/aaru/aaru "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/aaru

install -Dm 0644 %{SOURCE1} %{buildroot}%{_datadir}/applications/aaru.desktop
install -Dm 0644 %{SOURCE2} %{buildroot}%{_mandir}/man1/aaru.1

%files
%license LICENSE
%license LICENSE.LGPL
%license LICENSE.MIT
%doc README.md
%doc Changelog.md
%doc CONTRIBUTING.md
%{_bindir}/aaru
%dir %{_libdir}/aaru
%caps(cap_sys_rawio=ep) %attr(0755,root,root) %{_libdir}/aaru/aaru
%{_libdir}/aaru/*.dll
%{_libdir}/aaru/*.json
%{_libdir}/aaru/*.pdb
%{_libdir}/aaru/*.so
%{_libdir}/aaru/runtimes/
%{_datadir}/applications/aaru.desktop
%{_mandir}/man1/aaru.1*

%changelog
* Mon Jun 15 2026 gmipf <gmipf64@gmail.com> - 6.0.0-0.alpha.19.1
- Initial COPR build of Aaru v6.0.0-alpha.19
- Source build from maintainer-signed aaru-src tarball (only viable
  source: auto-generated archive lacks vendored deps)
- Framework-dependent .NET 10 publish — relies on dotnet-runtime-10.0
  so the binary stays around 30-40 MB instead of ~95 MB self-contained
- Single binary handles CLI and Avalonia GUI (`aaru gui` subcommand);
  X11/GL/fontconfig stack listed as Recommends so headless installs
  stay lean while desktop installs get the full GUI experience
- cap_sys_rawio=ep on the launcher binary; the /usr/bin/ wrapper
  delegates to /usr/lib64/aaru/aaru where the caps actually sit
- Manpage handwritten (upstream provides none); pinned to v6 syntax
- .desktop entry shipped with `Exec=aaru gui`
