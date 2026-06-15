%global debug_package %{nil}
%global __strip /bin/true
%global __os_install_post %{nil}
%global _build_id_links none

Name:           mpf-check
Version:        3.7.1
# Release format: <upstream-rolling-snapshot>.<our-iteration>%{?dist}
# Snapshot = <UTC-timestamp-compact>.<short-SHA>, written by the
# watch-mpf-rolling.yml workflow whenever the upstream rolling tag
# moves. Trailing .1 is our packaging-iteration counter (bump if we
# change the spec without an upstream change).
Release:        20260612220844.b16abc89.1%{?dist}
Summary:        Validator that generates Redump !submissionInfo.txt from disc-dump logs

License:        MIT
URL:            https://github.com/SabreTools/MPF
Source0:        https://github.com/SabreTools/MPF/releases/download/rolling/MPF.Check_net10.0_linux-x64_release.zip

ExclusiveArch:  x86_64
BuildRequires:  unzip
Requires:       glibc

AutoReqProv:    no

%description
MPF.Check reads the log files next to a finished optical-media dump
and writes a !submissionInfo.txt alongside in the Redump submission
format. Supported dump sources include Redumper, Aaru, DiscImageCreator,
Cleanrip and UmdImageCreator.

Optional copy protection scanning is available when given a physical
drive path via --path/--scan; this path uses vendor SCSI commands and
requires CAP_SYS_RAWIO (already set on the shipped binary).

Self-contained .NET 10 binary, repackaged unmodified from the upstream
rolling release.

%prep
%setup -q -c -T
unzip -q %{SOURCE0}

%build
# self-contained binary, nothing to build

%install
install -d %{buildroot}%{_libdir}/mpf-check
install -m 0755 MPF.Check %{buildroot}%{_libdir}/mpf-check/MPF.Check

install -d %{buildroot}%{_bindir}
cat > %{buildroot}%{_bindir}/mpf-check <<'EOF'
#!/bin/sh
exec %{_libdir}/mpf-check/MPF.Check "$@"
EOF
chmod 0755 %{buildroot}%{_bindir}/mpf-check

%files
%{_bindir}/mpf-check
%caps(cap_sys_rawio=ep) %attr(0755,root,root) %{_libdir}/mpf-check/MPF.Check
%dir %{_libdir}/mpf-check

%changelog
* Sun Jun 14 2026 gmipf - 3.7.1-1
- Initial package, repackaging upstream rolling release
