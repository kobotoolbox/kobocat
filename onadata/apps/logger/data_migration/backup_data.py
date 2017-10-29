from onadata.apps.logger.models import BackupInstance, BackupXForm, VersionTree
from .decisioner import MigrationDecisioner


def create_xform_backup(xform_data, xform=None, changes=None):
    xform = xform or xform_data
    xform_backup = backup_xform(xform_data, xform, changes)

    for survey in xform.instances.iterator():
        backup_survey(survey, xform_backup)

    return xform_backup


def backup_xform(xform_data, xform=None, migration_changes=None, bind=False):
    """Create backup of xform version before changing schema.

    :param logger.XForm xform_data: from which the data will be taken
    :param logger.XForm xform: The actual backed-up xform. Usually the same as above
    :param int xform_id: id of the backed-up form
    :param dict migration_changes: fields changes occured during migration
    :param bool bind: if true, bind updated xform to version tree
    """
    xform = xform or xform_data
    changes = migration_changes or MigrationDecisioner.construct_changes()

    backup = BackupXForm.objects.create(
        xform_id=xform.id,
        xls=xform_data.xls,
        xml=xform_data.xml,
        id_string=xform_data.id_string,
        description=xform_data.description,
        user=xform_data.user,
        date_created=xform_data.date_created,
        migration_changes=changes,
    )
    if bind:
        bind_backup_to_version_tree(xform, backup)
    return backup


def bind_backup_to_version_tree(xform, backup):
    vt = VersionTree.objects.create(version=backup)
    if xform.version_tree is not None:
        vt.parent = xform.version_tree
        vt.save()
    xform.version_tree = vt
    xform.save()


def backup_survey(survey, xform_backup):
    return BackupInstance.objects.create(
        xml=survey.xml,
        uuid=survey.uuid,
        xform=xform_backup,
        user=survey.user,
        date_created=survey.date_created,
    )
