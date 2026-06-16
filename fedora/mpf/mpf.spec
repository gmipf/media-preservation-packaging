%global mpfver         3.7.1
%global mpfsnap        20260612220844.b16abc89
%global rolltag        rolling

%global debug_package      %{nil}
%global __strip            /bin/true
%global __os_install_post  %{nil}
%global _build_id_links    none

Name:           mpf
Version:        %{mpfver}~%{mpfsnap}
# Release: 4 — adds first-launch config.json seeding in the /usr/bin
# wrappers. Upstream MPF defaults bake relative paths
# (`Programs/Creator/DiscImageCreator.out` etc.) that match its ZIP
# bundle layout but not a system /usr-tree install. The wrappers now
# write a config.json with `/usr/bin/<tool>` paths on first launch if
# the user has no config yet — once the user touches settings the seed
# becomes a no-op and personal choices are preserved.
# The watcher resets Release to 1 on the next genuine upstream
# rolling-SHA change (= new identity).
Release:        4%{?dist}
Summary:        Media Preservation Frontend suite (mpf-check, mpf-cli, mpf-gui)

License:        MIT
URL:            https://github.com/SabreTools/MPF

Source0:        %{url}/releases/download/%{rolltag}/MPF.Check_net10.0_linux-x64_release.zip
Source1:        %{url}/releases/download/%{rolltag}/MPF.CLI_net10.0_linux-x64_release.zip
Source2:        %{url}/releases/download/%{rolltag}/MPF.Avalonia_net10.0_linux-x64_release.zip

Source3:        mpf-gui.desktop
Source4:        mpf-check.1
Source5:        mpf-cli.1
Source6:        mpf-gui.1

Source10:       mpf-32.png
Source11:       mpf-64.png
Source12:       mpf-128.png
Source13:       mpf-256.png
Source14:       mpf-512.png

ExclusiveArch:  x86_64
BuildRequires:  unzip
AutoReqProv:    no

# Meta-package: pulls in all three subpackages.
Requires:       %{name}-check = %{version}-%{release}
Requires:       %{name}-cli   = %{version}-%{release}
Requires:       %{name}-gui   = %{version}-%{release}

%description
Media Preservation Frontend (MPF) is a suite of tools that drives the
optical-media dumping workflow used by the Redump preservation project.
Each tool wraps a specific role in the workflow:

  * mpf-check  log validator + submission-info writer
  * mpf-cli    headless dump orchestrator
  * mpf-gui    Avalonia desktop frontend

This meta-package installs all three. Install the individual subpackages
if you only need part of the suite.

# ---------------------------------------------------------------- check

%package check
Summary:        Validator that generates Redump !submissionInfo.txt from disc-dump logs
Requires:       libicu
Requires:       krb5-libs
Requires:       libunwind
Requires:       openssl-libs
Requires:       zlib

%description check
MPF.Check reads the log files next to a finished optical-media dump and
writes a !submissionInfo.txt alongside in the Redump submission format.
Supported dump sources include Redumper, Aaru, DiscImageCreator, Cleanrip
and UmdImageCreator.

Optional copy-protection scanning is available via --path/--scan; that
path uses vendor SCSI commands and requires CAP_SYS_RAWIO, which is
preset on the shipped binary so no sudo is needed.

Self-contained .NET 10 binary, repackaged unmodified from the upstream
rolling release.

# ------------------------------------------------------------------ cli

%package cli
Summary:        Headless dump orchestrator (drives redumper, aaru, discimagecreator)
Requires:       libicu
Requires:       krb5-libs
Requires:       libunwind
Requires:       openssl-libs
Requires:       zlib
Recommends:     redumper
Recommends:     aaru
Recommends:     discimagecreator

%description cli
MPF.CLI orchestrates the disc-dumping workflow from a terminal: it drives
the selected backend (redumper, aaru or discimagecreator) through the
dump, post-processes the output and writes the submission info.

CAP_SYS_RAWIO is preset on the shipped binary for vendor-SCSI access.

The bundled Programs/Creator/ folder from the upstream ZIP is dropped at
package build time in favor of the system-installed dumpers; mpf-cli
resolves the backend binary via PATH.

Self-contained .NET 10 binary, repackaged from the upstream rolling
release.

# ------------------------------------------------------------------ gui

%package gui
Summary:        Avalonia desktop frontend for the MPF disc-dumping workflow
Requires:       libicu
Requires:       krb5-libs
Requires:       libunwind
Requires:       openssl-libs
Requires:       zlib
Requires:       hicolor-icon-theme
Requires:       desktop-file-utils
Recommends:     redumper
Recommends:     aaru
Recommends:     discimagecreator
# Avalonia 11.x ships only the X11 backend; on Wayland sessions the GUI
# runs through Xwayland. Recommends are library-level so the same set
# covers both X11 and XWayland-on-Wayland setups.
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

%description gui
MPF.Avalonia is the desktop GUI of the MPF suite. It drives the disc-
dumping workflow with a graphical interface built on Avalonia (.NET
cross-platform UI toolkit).

CAP_SYS_RAWIO is preset on the shipped binary for vendor-SCSI access.

The bundled Programs/Creator/ folder from the upstream ZIP is dropped at
package build time in favor of the system-installed dumpers, resolved
via PATH.

On Wayland sessions the GUI runs through Xwayland (Avalonia 11.x has no
native Wayland backend yet); on X11 sessions it runs natively.

Self-contained .NET 10 binary, repackaged from the upstream rolling
release.

# =====================================================================

%prep
%setup -q -c -T

unzip -q %{SOURCE0}

mkdir cli
pushd cli
unzip -q %{SOURCE1}
popd

mkdir gui
pushd gui
unzip -q %{SOURCE2}
popd

# Drop the bundled Programs/Creator/ folder (~1.5 MB code + data) from
# CLI and GUI zips. The Fedora package relies on the system-installed
# redumper / aaru / discimagecreator, resolved via PATH instead.
rm -rf cli/Programs gui/Programs

%build
# Self-contained binaries; nothing to compile.

%install
# --- check: real binary + wrapper ---
install -d %{buildroot}%{_libdir}/mpf-check
install -m 0755 MPF.Check %{buildroot}%{_libdir}/mpf-check/MPF.Check

# --- cli: real binary + wrapper ---
install -d %{buildroot}%{_libdir}/mpf-cli
install -m 0755 cli/MPF.CLI %{buildroot}%{_libdir}/mpf-cli/MPF.CLI

# --- gui: upstream zip names the binary "MPF"; we install it as
#         MPF.Avalonia to make the role obvious on disk.
install -d %{buildroot}%{_libdir}/mpf-gui
install -m 0755 gui/MPF %{buildroot}%{_libdir}/mpf-gui/MPF.Avalonia

# --- /usr/bin/ wrappers ---
# The wrappers seed ~/.config/mpf/config.json with system-binary paths
# if (and only if) the file is missing or empty. Upstream MPF defaults
# to relative paths like "Programs/Creator/DiscImageCreator.out" baked
# from the upstream ZIP bundle layout, which doesn't match a /usr-tree
# install. Once the user touches the GUI/CLI settings the file is no
# longer empty, so the seed becomes a no-op and user choices are
# preserved.
install -d %{buildroot}%{_bindir}

cat > %{buildroot}%{_bindir}/mpf-check <<'EOF'
#!/bin/sh
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/mpf"
config="$config_dir/config.json"
if [ ! -s "$config" ]; then
    mkdir -p "$config_dir"
    cat > "$config" <<'JSON'
{
  "AaruPath": "/usr/bin/aaru",
  "DiscImageCreatorPath": "/usr/bin/DiscImageCreator.out",
  "RedumperPath": "/usr/bin/redumper"
}
JSON
fi
exec /usr/lib64/mpf-check/MPF.Check "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/mpf-check

cat > %{buildroot}%{_bindir}/mpf-cli <<'EOF'
#!/bin/sh
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/mpf"
config="$config_dir/config.json"
if [ ! -s "$config" ]; then
    mkdir -p "$config_dir"
    cat > "$config" <<'JSON'
{
  "AaruPath": "/usr/bin/aaru",
  "DiscImageCreatorPath": "/usr/bin/DiscImageCreator.out",
  "RedumperPath": "/usr/bin/redumper"
}
JSON
fi
exec /usr/lib64/mpf-cli/MPF.CLI "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/mpf-cli

cat > %{buildroot}%{_bindir}/mpf-gui <<'EOF'
#!/bin/sh
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/mpf"
config="$config_dir/config.json"
if [ ! -s "$config" ]; then
    mkdir -p "$config_dir"
    cat > "$config" <<'JSON'
{
  "AaruPath": "/usr/bin/aaru",
  "DiscImageCreatorPath": "/usr/bin/DiscImageCreator.out",
  "RedumperPath": "/usr/bin/redumper"
}
JSON
fi
exec /usr/lib64/mpf-gui/MPF.Avalonia "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/mpf-gui

# --- desktop entry (gui only) ---
install -d %{buildroot}%{_datadir}/applications
install -m 0644 %{SOURCE3} %{buildroot}%{_datadir}/applications/mpf-gui.desktop

# --- hicolor icons (gui only) ---
for sz in 32 64 128 256 512; do
  install -d %{buildroot}%{_datadir}/icons/hicolor/${sz}x${sz}/apps
done
install -m 0644 %{SOURCE10} %{buildroot}%{_datadir}/icons/hicolor/32x32/apps/mpf.png
install -m 0644 %{SOURCE11} %{buildroot}%{_datadir}/icons/hicolor/64x64/apps/mpf.png
install -m 0644 %{SOURCE12} %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/mpf.png
install -m 0644 %{SOURCE13} %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/mpf.png
install -m 0644 %{SOURCE14} %{buildroot}%{_datadir}/icons/hicolor/512x512/apps/mpf.png

# --- manpages ---
install -d %{buildroot}%{_mandir}/man1
install -m 0644 %{SOURCE4} %{buildroot}%{_mandir}/man1/mpf-check.1
install -m 0644 %{SOURCE5} %{buildroot}%{_mandir}/man1/mpf-cli.1
install -m 0644 %{SOURCE6} %{buildroot}%{_mandir}/man1/mpf-gui.1

# =====================================================================

%files
# meta-package: no files, only Requires above

%files check
%{_bindir}/mpf-check
%caps(cap_sys_rawio=ep) %attr(0755,root,root) %{_libdir}/mpf-check/MPF.Check
%dir %{_libdir}/mpf-check
%{_mandir}/man1/mpf-check.1*

%files cli
%{_bindir}/mpf-cli
%caps(cap_sys_rawio=ep) %attr(0755,root,root) %{_libdir}/mpf-cli/MPF.CLI
%dir %{_libdir}/mpf-cli
%{_mandir}/man1/mpf-cli.1*

%files gui
%{_bindir}/mpf-gui
%caps(cap_sys_rawio=ep) %attr(0755,root,root) %{_libdir}/mpf-gui/MPF.Avalonia
%dir %{_libdir}/mpf-gui
%{_mandir}/man1/mpf-gui.1*
%{_datadir}/applications/mpf-gui.desktop
%{_datadir}/icons/hicolor/32x32/apps/mpf.png
%{_datadir}/icons/hicolor/64x64/apps/mpf.png
%{_datadir}/icons/hicolor/128x128/apps/mpf.png
%{_datadir}/icons/hicolor/256x256/apps/mpf.png
%{_datadir}/icons/hicolor/512x512/apps/mpf.png

%changelog
* Mon Jun 15 2026 gmipf <gmipf64@gmail.com> - 3.7.1~20260612220844.b16abc89-2
- Phase 5: refactor single-binary mpf-check.spec into a multi-subpackage
  mpf.spec that builds mpf-check, mpf-cli and mpf-gui from one SRPM. The
  main `mpf` package is a meta-package pulling in all three.
- Add mpf-gui.desktop and hicolor icons (32 / 64 / 128 / 256 / 512,
  extracted from upstream MPF.UI/Images/Icon.ico).
- Add handwritten manpages for mpf-check, mpf-cli and mpf-gui.
- Drop bundled Programs/Creator/ from cli/gui zips; the Fedora package
  uses the system-installed redumper / aaru / discimagecreator via PATH.
- Recommends X11/XWayland runtime libs on mpf-gui (Avalonia 11.x has no
  native Wayland backend yet).
- Release bumped to 2 because the previously published mpf-check
  3.7.1~20260612220844.b16abc89-1 occupied -1; this refactor reuses the
  same snapshot identity. Watcher resets to -1 on the next SHA change.

* Mon Jun 15 2026 gmipf <gmipf64@gmail.com> - 3.7.1~20260612220844.b16abc89-1
- Migrate to tilde-style versioning (Version: 3.7.1~<UTC-TS>.<short-SHA>,
  Release: 1) to match the convention used on aaru: rolling snapshot
  identifier sits in Version after `~`, packaging iteration is the
  trailing -N of NEVRA.

* Sun Jun 14 2026 gmipf - 3.7.1-1
- Initial mpf-check standalone package, repackaging upstream rolling
  release.
