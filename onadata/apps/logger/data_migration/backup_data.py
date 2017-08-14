from onadata.apps.logger.models.backup import BackupInstance, BackupXForm


def backup_xform(xform):
    """Create backup of xform version before changing schema."""
    return BackupXForm.objects.create(
        xls=xform.xls,
        json=xform.json,
        xml=xform.xml,
        description=xform.description,
        user=xform.user,
        date_created=xform.date_created,
    )


def backup_survey(survey, backup_xform):
    return BackupInstance.objects.create(
        xml=survey.xml,
        xform=backup_xform,
        user=survey.user,
        date_created=survey.date_created,
    )
