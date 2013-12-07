#%#define _use_internal_dependency_generator	0
%define __noautoreq 'pear\\(graph|pear\\(includes|pear\\(modules'
%define _disable_ld_no_undefined 1

Summary:	Mandriva Management Console
Name:		mmc-core
Version:	3.0.3.2
Release:	4
License:	GPLv2
Group:		System/Servers
Url:		http://mds.mandriva.org/
Source0:	http://mds.mandriva.org/pub/mmc-core/sources/%{version}/%{name}-%{version}.tar.gz
BuildRequires:	python-devel
BuildRequires:	gettext
BuildRequires:	gettext-devel
BuildRequires:	openldap-devel
BuildRequires:	wrap-devel

%description
Mandriva Management Console agent & web interface with
base and password policies modules.

%package -n mmc-agent
Summary:	Mandriva Management Console agent
Group:		System/Servers
Requires:	python-base
Requires:	python-mmc-base
Requires:	pyOpenSSL
Requires:	logrotate

%description -n mmc-agent
XMLRPC server of the Mandriva Management Console API.
This is the underlying service used by the MMC web interface.

%package -n python-mmc-core
Summary:	Mandriva Management Console core
Group:		System/Servers
Requires:	python-base
Requires:	python-twisted-web
Suggests:	python-sqlalchemy > 0.4
Suggests:	python-mysql

%description -n python-mmc-core
Contains the mmc core python classes used by all other
modules.

%package -n	python-mmc-base
Summary:	Mandriva Management Console base plugin
Group:		System/Servers
Requires:	python-base
Requires:	python-ldap
Requires:	python-mmc-plugins-tools
Requires:	python-mmc-core

%description -n	python-mmc-base
Contains the base infrastructure for all MMC plugins:
 * support classes
 * base LDAP management classes

%package -n python-mmc-ppolicy
Summary:	Mandriva Management Console password policy plugin
Group:		System/Servers
Requires:	python-base
Requires:	python-mmc-core
Suggests:	mmc-check-password
%if %mdkversion >= 201200 && %{_use_internal_dependency_generator}
# add buggy self dependencies
Provides:	pear(ppolicy-xmlrpc.php)
Provides:	pear(ppolicy.inc.php)
%endif

%description -n python-mmc-ppolicy
Contains the password policy python classes to handle
password policies in LDAP.

%package -n	mmc-web-ppolicy
Summary:	Password policies plugin
Group:		System/Servers
Requires:	mmc-web-base

%description -n mmc-web-ppolicy
Contains the password policy web interface

%package -n 	mmc-web-base
Summary:	MMC web interface to interact with a MMC agent
Group:		System/Servers
Requires:	apache >= 2.0.52
Requires:	apache-mod_php
Requires:	php-xmlrpc
Requires:	php-iconv
%if %mdkversion >= 201200 && %{_use_internal_dependency_generator}
# add buggy self dependencies
Provides:	pear(ErrorHandling.php)
Provides:	pear(FormGenerator.php)
Provides:	pear(ModulesGenerator.php)
Provides:	pear(PageGenerator.php)
Provides:	pear(acl.inc.php)
Provides:	pear(config.inc.php)
Provides:	pear(edit.php)
Provides:	pear(i18n.inc.php)
Provides:	pear(license.php)
Provides:	pear(localSidebar.php)
Provides:	pear(logging-xmlrpc.inc.php)
Provides:	pear(main_content.php)
Provides:	pear(session.inc.php)
Provides:	pear(xmlrpc.inc.php)
%endif

%description -n mmc-web-base
Mandriva Management Console web interface designed by Linbox.

%package -n	python-mmc-plugins-tools
Summary:	Required tools for some MMC plugins
Group:		System/Servers
Requires:	cdrkit-genisoimage

%description -n	python-mmc-plugins-tools
Contains common tools needed by some plugins of mmc-agent package.

%package -n	mmc-check-password
Summary:	OpenLDAP password checker module for MMC
Group:		System/Servers

%description -n mmc-check-password
OpenLDAP module to validate users passwords against LDAP's password policies.

%prep
%setup -q -n %{name}-%{version}

%build
sed -e 's|-Werror||g' -i configure
%configure2_5x						\
	--with-initdir=%{_initrddir}			\
	--disable-python-check				\
	--enable-check-password				\
	--with-ldap-confdir=%{_sysconfdir}/openldap	\
	--with-ldap-libdir=%{_libdir}/openldap
make

%install
%makeinstall_std
# logrotate configuration
install -d %{buildroot}%{_sysconfdir}/logrotate.d
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
# install log directory
install -d %{buildroot}/var/log/mmc
# patch privkey.pem
mv %{buildroot}%{_sysconfdir}/mmc/agent/keys/localcert.pem %{buildroot}%{_sysconfdir}/mmc/agent/keys/privkey.pem
sed -i 's!localcert.pem!privkey.pem!g' %{buildroot}%{_sysconfdir}/mmc/agent/config.ini
# install apache configuration
install -d %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d/
cp %{buildroot}%{_sysconfdir}/mmc/apache/mmc.conf %{buildroot}%{_sysconfdir}/httpd/conf/webapps.d/mmc.conf
# Cleanup
rm -f `find %{buildroot} -name *.pyo`
%find_lang base
%find_lang ppolicy

%post -n mmc-agent
if [ $1 = 1 ]; then
    /sbin/chkconfig --add mmc-agent >/dev/null 2>&1 || :
fi
# comment on le fait juste pour un package ?
if [ -f /var/lock/subsys/httpd ]; then
    %{_initrddir}/httpd restart >/dev/null || :
fi

%preun -n mmc-agent
if [ $1 = 0 ]; then
   /sbin/chkconfig --del mmc-agent >/dev/null 2>&1 || :
   [ -f /var/lock/subsys/mmc-agent ] && %{_initrddir}/mmc-agent stop >/dev/null 2>&1 || :
fi
exit 0

%postun -n mmc-agent
if [ "$1" -ge 1 ]; then
    %{_initrddir}/mmc-agent condrestart >/dev/null 2>&1 || :
fi
# comment on le fait juste pour un package ?
if [ "$1" = "0" ]; then
    if [ -f /var/lock/subsys/httpd ]; then
        %{_initrddir}/httpd restart >/dev/null || :
    fi
fi

%files -n mmc-agent
%doc COPYING ChangeLog
%attr(0755,root,root) %{_initrddir}/mmc-agent
%attr(0755,root,root) %dir %{_sysconfdir}/mmc
%attr(0755,root,root) %dir %{_sysconfdir}/mmc/agent
%attr(0755,root,root) %dir %{_sysconfdir}/mmc/agent/keys
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/agent/config.ini
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/agent/keys/cacert.pem
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/agent/keys/privkey.pem
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/logrotate.d/mmc-agent
%attr(0755,root,root) %{_sbindir}/mmc-agent
%attr(0755,root,root) %{_sbindir}/mmc-add-schema
%attr(0755,root,root) %{_bindir}/mmc-helper
%attr(0755,root,root) %dir /var/log/mmc
%{py_puresitedir}/mmc/agent.py*

%files -n python-mmc-core
%{py_puresitedir}/mmc/core

%files -n python-mmc-base
%{_datadir}/doc/python-mmc-base
%docdir %{_datadir}/doc/python-mmc-base
%attr(0755,root,root) %dir %{_sysconfdir}/mmc/plugins
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/plugins/base.ini
%attr(0755,root,root) %{_sbindir}/mds-report
%dir %{py_puresitedir}/mmc
%{py_puresitedir}/mmc/support
%{py_puresitedir}/mmc/__init__.py*
%{py_puresitedir}/mmc/site.py*
%{py_puresitedir}/mmc/ssl.py*
%{py_puresitedir}/mmc/client
%dir %{py_puresitedir}/mmc/plugins
%{py_puresitedir}/mmc/plugins/__init__.py*
%{py_puresitedir}/mmc/plugins/base

%files -n python-mmc-ppolicy
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/plugins/ppolicy.ini
%{py_puresitedir}/mmc/plugins/ppolicy

%files -n mmc-web-ppolicy -f ppolicy.lang
%dir %{_datadir}/mmc/modules/ppolicy
%dir %{_datadir}/mmc/modules/ppolicy/locale
%{_datadir}/mmc/modules/ppolicy/*.php
%{_datadir}/mmc/modules/ppolicy/default
%{_datadir}/mmc/modules/ppolicy/includes

%files -n mmc-web-base -f base.lang
%attr(0755,root,root) %dir %{_sysconfdir}/mmc/apache
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/mmc/apache/mmc.conf
%attr(0755,root,root) %dir %{_sysconfdir}/httpd/conf/webapps.d/
%attr(0640,root,root) %config(noreplace) %{_sysconfdir}/httpd/conf/webapps.d/mmc.conf
%attr(0640,root,apache) %config(noreplace) %{_sysconfdir}/mmc/mmc.ini
%dir %{_datadir}/mmc
%{_datadir}/mmc/*.php
%{_datadir}/mmc/graph
%{_datadir}/mmc/img
%{_datadir}/mmc/includes
%{_datadir}/mmc/jsframework
%{_datadir}/mmc/logout
%dir %{_datadir}/mmc/modules
%dir %{_datadir}/mmc/modules/base
%dir %{_datadir}/mmc/modules/base/locale
%{_datadir}/mmc/modules/base/*.php
%{_datadir}/mmc/modules/base/audit
%{_datadir}/mmc/modules/base/computers
%{_datadir}/mmc/modules/base/graph
%{_datadir}/mmc/modules/base/groups
%{_datadir}/mmc/modules/base/includes
%{_datadir}/mmc/modules/base/logview
%{_datadir}/mmc/modules/base/status
%{_datadir}/mmc/modules/base/users
%{_datadir}/mmc/modules/base/views

%files -n python-mmc-plugins-tools
%dir %{_libdir}/mmc
%dir %{_libdir}/mmc/backup-tools
%{_libdir}/mmc/backup-tools/cdlist
%{_libdir}/mmc/backup-tools/backup.sh

%files -n mmc-check-password
%attr(0644,root,root) %config(noreplace) %{_sysconfdir}/openldap/mmc-check-password.conf
%attr(0755,root,root) %{_libdir}/openldap/mmc-check-password.*
%attr(0755,root,root) %{_bindir}/mmc-password-helper

