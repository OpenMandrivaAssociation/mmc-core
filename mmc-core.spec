%define _requires_exceptions pear(graph\\|pear(includes\\|pear(modules\\|pear(license.php)
%define _enable_debug_packages %{nil}
%define debug_package          %{nil}

%if %mdkversion < 200610
%define py_puresitedir %{_prefix}/lib/python%{pyver}/site-packages/
%endif
%define ver 6790

Summary:	Mandriva Management Console Agent
Name:		mmc-core
Version:	3.0.0
Release:	%mkrel 0.0.2
License:	GPL
Group:		System/Servers
URL:		http://mds.mandriva.org/
Source0:	%{name}-%{version}-%{ver}.tar.gz
Source1:	mmc-agent.init
Patch0:		mmc-core-3.0.0-mdv_conf.diff
BuildRequires:	python-devel
BuildRequires:	openldap-devel
BuildArch: 	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%description
XMLRPC server of the MMC API.

%package -n	mmc-agent
Summary:	Mandriva Management Console Agent
Group:		System/Servers
Requires:	pycrypto
Requires:	python-mmc-base >= %{version}
Requires:	python-OpenSSL
Requires(post): rpm-helper
Requires(preun): rpm-helper

%description -n	mmc-agent
XMLRPC server of the MMC API.

%package -n	python-mmc-base
Summary:	Mandriva Management Console base plugin
Group:		System/Servers
Requires:	python-ldap
Requires:       cdrkit-genisoimage
Requires:       python-mmc-core >= %{version}
# python-twisted-* deps is to be investigated
#Requires:	python-twisted
#Requires:	python-twisted-conch
#Requires:	python-twisted-core
#Requires:	python-twisted-lore
#Requires:	python-twisted-mail
#Requires:	python-twisted-names
#Requires:	python-twisted-runner
#Requires:	python-twisted-web
#Requires:	python-twisted-words

%description -n	python-mmc-base
Contains the base infrastructure for all MMC plugins:
 * support classes
 * base LDAP management classes

%package -n	python-mmc-core
Summary:	Core shared dependency for MMC API
Group:		System/Servers
Suggests:	python-sqlalchemy < 0.5
Suggests:	python-mysql
Requires:	python-twisted-web
Conflicts:	python-mmc-base < 2.3.3

%description -n	python-mmc-core
Contains base functions used by MMC.

%package -n	python-mmc-ppolicy
Summary:	Mandriva Management Console password policy plugin
Group:		System/Servers
Requires:	python-mmc-base >= %{version}

%description -n	python-mmc-ppolicy
Contains password policy plugin to enforce minimum password security in MMC.

%package -n	mmc-web-base
Summary:	MMC web interface to interact with a MMC agent
Group:		System/Servers
Requires:	apache-mod_php
Requires:	php-xmlrpc
Requires:	php-iconv
Requires:	php-gd
%if %mdkversion < 201010
Requires(post):   rpm-helper
Requires(postun):   rpm-helper
%endif

%description -n	mmc-web-base
Mandriva Management Console web interface designed by Mandriva.

%package -n	mmc-web-ppolicy
Summary:	Password policy module for Mandriva MMC
Group:		System/Servers
Requires:	python-mmc-base >= %{version}

%description -n	mmc-web-ppolicy
Module to enforce minimum password security in MMC.


%prep

%setup -q -n %{name}-%{version}

for i in `find . -type d -name .svn`; do
    if [ -e "$i" ]; then rm -rf $i; fi >&/dev/null
done
%patch0 -p1

cp %{SOURCE1} mmc-agent.init

# mdv default fixes
#for i in `find -type f`; do
#    perl -pi -e "s|ou=Groups\b|ou=Group|g;s|ou=Users\b|ou=People|g;s|ou=Computers\b|ou=Hosts|g" $i
#done

%build

# this is packaged separately in the mmc-check-password package
pushd agent/openldap-check-password
    make CFLAGS="%{optflags} -fPIC"
popd

%install
rm -rf %{buildroot}

%makeinstall_std -C agent PREFIX=%{_prefix} LIBDIR=%{_prefix}/lib/mmc
%makeinstall_std -C web PREFIX=%{_prefix} LIBDIR=%{_prefix}/lib/mmc

pushd agent
    rm -rf %{buildroot}%{_prefix}/lib*/python*
    python setup.py install --root=%{buildroot} --install-purelib=%{py_puresitedir}
popd

pushd web
    make apache_conf
popd

install -d %{buildroot}%{_initrddir}
install -d %{buildroot}%{_sysconfdir}/logrotate.d
install -d %{buildroot}/var/log/mmc

install -m0755 mmc-agent.init %{buildroot}%{_initrddir}/mmc-agent

# install log rotation stuff
cat > %{buildroot}%{_sysconfdir}/logrotate.d/mmc-agent << EOF
/var/log/mmc/mmc-agent.log /var/log/dhcp-ldap-startup.log /var/log/mmc/mmc-fileprefix.log {
    create 644 root root
    monthly
    compress
    missingok
    postrotate
	%{_initrddir}/mmc-agent condrestart >/dev/null 2>&1 || :
    endscript
}
EOF

# put the openldap schemas in place
install -d %{buildroot}%{_datadir}/openldap/schema
install -m0644 agent/contrib/ldap/mmc.schema %{buildroot}%{_datadir}/openldap/schema/

install -d %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d

cat > %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d/mmc-web-base.conf << EOF
Alias /mmc %{_datadir}/mmc

<Directory "%{_datadir}/mmc">
    AllowOverride None
    Order allow,deny
    allow from all
    php_flag short_open_tag on
    php_flag magic_quotes_gpc on
</Directory>
EOF

# cleanup
rm -f %{buildroot}%{_sysconfdir}/openldap/mmc-check-password.conf

# nuke the license.php file on Enterprise products
if [ "%{product_type}" == Enterprise ]; then
    rm -f %{buildroot}%{_datadir}/mmc/license.php
fi

%post -n mmc-agent
%_post_service mmc-agent

%preun -n mmc-agent
%_preun_service mmc-agent

%post -n mmc-web-base
%if %mdkversion < 201010
%_post_webapp
%endif

%postun -n mmc-web-base
%if %mdkversion < 201010
%_postun_webapp
%endif

%clean
rm -rf %{buildroot}

%files -n mmc-agent
%defattr(-,root,root,0755)
%attr(0755,root,root) %{_initrddir}/mmc-agent
%attr(0755,root,root) %dir %{_sysconfdir}/mmc/agent
%attr(0755,root,root) %dir %{_sysconfdir}/mmc/agent/keys
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/agent/config.ini
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/agent/keys/cacert.pem
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/agent/keys/localcert.pem
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/mmc-agent
%attr(0755,root,root) %{_sbindir}/mmc-agent
%{py_puresitedir}/mmc/agent.py*
%if %mdkversion >= 200700
%{py_puresitedir}/*.egg-info
%endif
%attr(0755,root,root) %dir /var/log/mmc

%files -n python-mmc-base
%defattr(-,root,root,0755)
%doc agent/contrib
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/plugins/base.ini
%{_sbindir}/mds-report
%{_prefix}/lib/mmc/backup-tools/cdlist
%{_prefix}/lib/mmc/backup-tools/backup.sh
%{py_puresitedir}/mmc/plugins/__init__.py*
%{py_puresitedir}/mmc/plugins/base
%{_datadir}/openldap/schema/mmc.schema

%files -n python-mmc-core
%defattr(-,root,root,0755)
%{_bindir}/mmc-helper
%{_bindir}/mmc-password-helper
%{py_puresitedir}/mmc/core
%{py_puresitedir}/mmc/support
%{py_puresitedir}/mmc/client.py*
%{py_puresitedir}/mmc/__init__.py*

%files -n python-mmc-ppolicy
%defattr(-,root,root,0755)
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/plugins/ppolicy.ini
%{py_puresitedir}/mmc/plugins/ppolicy

%files -n mmc-web-base
%defattr(-,root,root,0755)
%config(noreplace) %{_sysconfdir}/httpd/conf/webapps.d/mmc-web-base.conf
%attr(0640,root,apache) %config(noreplace) %{_sysconfdir}/mmc/mmc.ini
%{_datadir}/mmc/graph
%{_datadir}/mmc/img
%{_datadir}/mmc/includes
%{_datadir}/mmc/*.php
%{_datadir}/mmc/jsframework
%{_datadir}/mmc/logout
%{_datadir}/mmc/modules/base

%files -n mmc-web-ppolicy
%defattr(-,root,root,0755)
%{_datadir}/mmc/modules/ppolicy

