Name:           q3alert
Version:        0.3.1
Release:        1%{?dist}
Summary:        Q3 server monitoring applet

License:        GPLv3
URL:            http://github.com/bboozzoo/q3alert
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python, desktop-file-utils
Requires:       pygtk2, pygobject2, notify-python

%description
Applet to monitor a Q3 server and notify user about games in progress

%prep
%setup -q


%build


%install
rm -rf %{buildroot}
%{__python} setup.py install --root %{buildroot}
rm -rf %{buildroot}%{python_sitelib}
desktop-file-install \
  --add-category="Game" \
  --delete-original \
  --dir=%{buildroot}%{_datadir}/applications \
  %{buildroot}%{_datadir}/applications/%{name}.desktop

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root,-)
%{_bindir}/%{name}
%{_datadir}/applications/%{name}.desktop
%{_datadir}/%{name}
%{_datadir}/pixmaps/%{name}

%changelog
