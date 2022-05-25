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

- To ensure security and stability, many endpoints that were already
  available in KPI, long-unsupported, or underutilized have been removed in
  release
  [2.020.40](https://github.com/kobotoolbox/kobocat/releases/tag/2.020.40).
  These were related to charts and stats, form cloning, form sharing, user
  profiles, organizations / projects / teams, bamboo, and ziggy. For a full
  list, please see [REMOVALS.md](REMOVALS.md). These endpoints were last
  available in the release
  [2.020.39](https://github.com/kobotoolbox/kobocat/releases/tag/2.020.39).
- REST Services - an improved version [has been added to
  KPI](https://github.com/kobotoolbox/kpi/pull/1864). The last KoBoCAT
  release to contain legacy REST services is
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

```sh
$ django-admin.py makemessages -l es -e py,html,email,txt ;
$ for app in {main,viewer} ; do cd kobocat/apps/${app} && django-admin.py makemessages -d djangojs -l es && cd - ; done
```

To update PO files

```sh
$ django-admin.py makemessages -a ;
$ for app in {main,viewer} ; do cd kobocat/apps/${app} && django-admin.py makemessages -d djangojs -a && cd - ; done
```

To compile MO files and update live translations

```sh
$ django-admin.py compilemessages ;
$ for app in {main,viewer} ; do cd kobocat/apps/${app} && django-admin.py compilemessages && cd - ; done
```

## Testing in KoBoCAT

For kobo-install users, enter the folder for kobo-install and run this command

```
./run.py -cf exec kobocat bash
```

For all other users, enter the container using this command

```sh
$ docker exec -it {{kobocat container}} /bin/bash
```

Run pip install the development dependencies

```sh
$ pip install -r requirements/dev.pip
```

Run pytest to run all automated tests

```sh
$ pytest
```

## Github Actions Workflows

The `build.yml` script on the `.github.workflows` directory is responsible to promote changes to the kobocat dev environment. It does that by a series of steps:

- Build a new docker image from the source branch that triggered the workflow
- Push that image to the image repository(ECR)
- Run a helm upgrade command to make kubernetes pull and use the image with the new source code.

This workflow is triggered by pushing a commit to a branch with the prefix `feat/*` or to `develop`.

To create new workflows for different environments or isolated tasks please referr to the github action documentation(https://docs.github.com/en/actions) and add them to the `.github.workflows` directory.

To follow the execution of a workflow please referr to
[![Build Veritree API](https://github.com/tentree-org/veritree-toolbox/actions/workflows/dev.yml/badge.svg)](https://github.com/tentree-org/veritree-toolbox/actions/workflows/dev.yml)
