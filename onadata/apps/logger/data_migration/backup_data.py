import json

from onadata.apps.logger.models.backup import BackupInstance, BackupXForm


def create_xform_backup(xform, xform_id=None, changes=None):
    xform_backup = backup_xform(xform, xform_id, changes)

    for survey in xform.instances.iterator():
        backup_survey(survey, xform_backup)

    return xform_backup


def backup_xform(xform, xform_id=None, migration_changes=None):
    """Create backup of xform version before changing schema.

    :param logger.XForm xform: from which the data will be taken
    :param int xform_id: Id of the backed-up form
    :param dict migration_changes: fields changes occured during migration
    """
    xform_id = xform_id or xform.id
    changes = json.dumps(migration_changes) \
        if migration_changes is not None \
        else getattr(
            BackupXForm.objects.latest_backup_with_changes(xform_id=xform_id),
            'migration_changes', {}
        )

    return BackupXForm.objects.create(
        xform_id=xform_id,
        xls=xform.xls,
        xml=xform.xml,
        id_string=xform.id_string,
        description=xform.description,
        user=xform.user,
        date_created=xform.date_created,
        migration_changes=changes,
    )


def backup_survey(survey, xform_backup):
    return BackupInstance.objects.create(
        xml=survey.xml,
        uuid=survey.uuid,
        xform=xform_backup,
        user=survey.user,
        date_created=survey.date_created,
    )
