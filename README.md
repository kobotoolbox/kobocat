# KoBoCAT

## Important notice when upgrading from any release older than [`2.020.18`](https://github.com/kobotoolbox/kobocat/releases/tag/2.020.18)

Up to and including release [`2.020.18`](https://github.com/kobotoolbox/kobocat/releases/tag/2.020.18), this project (KoBoCAT) and [KPI](https://github.com/kobotoolbox/kpi) both shared a common Postgres database. They now each have their own. **If you are upgrading an existing single-database installation, you must follow [these instructions](https://community.kobotoolbox.org/t/upgrading-to-separate-databases-for-kpi-and-kobocat/7202)** to migrate the KPI tables to a new database and adjust your configuration appropriately.

If you do not want to upgrade at this time, please use the [`shared-database-obsolete`](https://github.com/kobotoolbox/kobocat/tree/shared-database-obsolete) branch instead.

## Deprecation Notices

Much of the user-facing features of this application are being migrated
to <https://github.com/kobotoolbox/kpi>. KoBoCAT's data-access API and
OpenRosa functions will remain intact, and any plans to the contrary
will be announced well in advance. For more details and discussion,
please refer to
<https://community.kobotoolbox.org/t/contemplating-the-future-of-kobocat/2743>.

As features are migrated, we will list them here along with the last
release where each was present:

  - REST Services - an improved version [has been added to
    KPI](https://github.com/kobotoolbox/kpi/pull/1864). Last KoBoCAT
    release
    [2.019.39](https://github.com/kobotoolbox/kobocat/releases/tag/2.019.39).

## About

kobocat is the data collection platform used in KoBoToolbox. It is based
on the excellent [onadata](http://github.com/onaio/onadata) platform
developed by Ona LLC, which in itself is a redevelopment of the
[formhub](http://github.com/SEL-Columbia/formhub) platform developed by
the Sustainable Engineering Lab at Columbia University.

Please refer to
[kobo-install](https://github.com/kobotoolbox/kobo-install) for
instructions on how to install KoBoToolbox.

## Code Structure

  - **logger** - This app serves XForms to and receives submissions from
    ODK Collect and Enketo.
  - **viewer** - This app provides a csv and xls export of the data
    stored in logger. This app uses a data dictionary as produced by
    pyxform. It also provides a map and single survey view.
  - **main** - This app is the glue that brings logger and viewer
    together.

## Localization

To generate a locale from scratch (ex. Spanish)

``` sh
$ django-admin.py makemessages -l es -e py,html,email,txt ;
$ for app in {main,viewer} ; do cd kobocat/apps/${app} && django-admin.py makemessages -d djangojs -l es && cd - ; done
```

To update PO files

``` sh
$ django-admin.py makemessages -a ;
$ for app in {main,viewer} ; do cd kobocat/apps/${app} && django-admin.py makemessages -d djangojs -a && cd - ; done
```

To compile MO files and update live translations

``` sh
$ django-admin.py compilemessages ;
$ for app in {main,viewer} ; do cd kobocat/apps/${app} && django-admin.py compilemessages && cd - ; done
```
