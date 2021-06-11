# KoBoCAT endpoint removals as of release 2.021.22

The last release to contain any of the endpoints listed below was [2.021.21](https://github.com/kobotoolbox/kpi/releases/tag/2.021.21).

## Submission Data Access and Management

URL Pattern | View Class or Function | Description | Available in KPI
-- | -- | -- | --
`/<username>/exports/<id_string>.csv` | `onadata.apps.export.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/exports/<id_string>.html` | `onadata.apps.export.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/exports/<id_string>.xlsx` | `onadata.apps.export.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/exports/<id_string>/` | `onadata.apps.export.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/forms/<id_string>/add-submission-with` | `onadata.apps.viewer.views.add_submission_with` | Unknown (no hits in access log, undocumented, no UI, no significant development since 2013) | No
`/<username>/forms/<id_string>/data.sav.zip` | `onadata.apps.viewer.views.data_export` | SPSS SAV data export (dropped from UI in 2015) | No
`/<username>/forms/<id_string>/delete_data` | `onadata.apps.main.views.delete_data` | Delete an individual submission | Yes
`/<username>/forms/<id_string>/edit-data/<data_id>` | `onadata.apps.logger.views.edit_data` | Edit a submission in Enketo | Yes
`/<username>/forms/<id_string>/enter-data` | `onadata.apps.logger.views.enter_data` | Add a submission with Enketo | Yes
`/<username>/forms/<id_string>/instance` | `onadata.apps.viewer.views.instance` | View a single instance | Yes
`/<username>/forms/<id_string>/map` | `onadata.apps.viewer.views.map_view` | View submissions on a map | Yes
`/<username>/forms/<id_string>/map_embed` | `onadata.apps.viewer.views.map_embed_view` | View submissions on a map | Yes
`/<username>/forms/<id_string>/view-data` | `onadata.apps.viewer.views.data_view` | View submissions in a table | Yes
`/<username>/reports/<id_string>/digest.html` | `onadata.apps.survey_report.views._wrapper` | “Analyze data” (outdated version of KPI’s “Reports”) | Yes
`/<username>/reports/<id_string>/digest/` | `onadata.apps.survey_report.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/reports/<id_string>/export.csv` | `onadata.apps.survey_report.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/reports/<id_string>/export.html` | `onadata.apps.survey_report.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/reports/<id_string>/export.xlsx` | `onadata.apps.survey_report.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/reports/<id_string>/export/` | `onadata.apps.survey_report.views._wrapper` | Old version of formpack (not legacy) exports | Yes
`/<username>/reports/<id_string>/submission/<submission>.html` | `onadata.apps.survey_report.views._wrapper` | Old version of formpack (not legacy) exports | Yes

## Project Management

URL Pattern | View Class or Function | Description | Available in KPI
-- | -- | -- | --
`/<username>/<id_string>/toggle_downloadable/` | `onadata.apps.logger.views.toggle_downloadable` | Switch data collection on and off for a project | Yes, as “archive”
`/<username>/cloneform` | `onadata.apps.main.views.clone_xlsform` | Unused and undocumented form cloning feature | Yes
`/<username>/delete/<id_string>/` | `onadata.apps.logger.views.delete_xform` | Delete an entire project | Yes
`/<username>/forms/<id_string>/delete-doc/<data_id>` | `onadata.apps.main.views.delete_metadata` | Delete background documents | No
`/<username>/forms/<id_string>/perms` | `onadata.apps.main.views.set_perm` | Set project permissions | Yes
`/<username>/forms/<id_string>/preview` | `onadata.apps.main.views.enketo_preview` | Preview a form in Enketo | Yes
`/<username>/forms/<id_string>/public_api` | `onadata.apps.main.views.public_api` | Basic form metadata: title, owner’s username, date created/modified, id_string, uuid, sharing status, archival status | Yes, but only if public access to the project is explicitly granted
`/<username>/forms/<id_string>/qrcode` | `onadata.apps.main.views.qrcode` | QR code (as a HTML page) containing Enketo data-entry URL | No
`/<username>/forms/<id_string>/update` | `onadata.apps.main.views.update_xform` | Overwrite a project with new XLSForm | Yes
`/api/v1/forms/<pk>/enketo` | `onadata.apps.api.viewsets.xform_viewset.XFormViewSet` | Retrieve Enketo data entry URL | Yes

## Already Unused or Non-functional

URL Pattern | View Class or Function | Description | Available in KPI
-- | -- | -- | --
`/<username>/activity` | `onadata.apps.main.views.activity` | Audit log entries (non-functional) | No
`/<username>/activity/api` | `onadata.apps.main.views.activity_api` | Audit log entries (non-functional) | No
`/<username>/forms/<id_string>/gdocs` | `onadata.apps.viewer.views.google_xls_export` | Google Docs export (non-functional) | No
`/<username>/forms/<id_string>/sms_multiple_submissions` | `onadata.apps.sms_support.views.import_multiple_submissions_for_form` | Data collection via SMS (non-functional) | No
`/<username>/forms/<id_string>/sms_submission` | `onadata.apps.sms_support.views.import_submission_for_form` | Data collection via SMS (non-functional) | No
`/<username>/forms/<id_string>/sms_submission/<service>/` | `onadata.apps.sms_support.providers.import_submission_for_form` | Data collection via SMS (non-functional) | No
`/<username>/forms/<id_string>/thank_you_submission` | `onadata.apps.viewer.views.thank_you_submission` | Data collection via SMS (non-functional) | No
`/<username>/sms_multiple_submissions` | `onadata.apps.sms_support.views.import_multiple_submissions` | Data collection via SMS (non-functional) | No
`/<username>/sms_submission` | `onadata.apps.sms_support.views.import_submission` | Data collection via SMS (non-functional) | No
`/<username>/sms_submission/<service>/` | `onadata.apps.sms_support.providers.import_submission` | Data collection via SMS (non-functional) | No
`/about-us/` | `onadata.apps.main.views.about_us` | Unused informational page | Yes (on kobotoolbox.org)
`/accounts/activate/<activation_key>/` | `registration.backends.default.views.ActivationView` | Unused user management | Yes (always was)
`/accounts/activate/complete/` | `django.views.generic.base.TemplateView` | Unused user management | Yes (always was)
`/accounts/password/change/` | `django.contrib.auth.views.password_change` | Unused user management | Yes (always was)
`/accounts/password/change/done/` | `django.contrib.auth.views.password_change_done` | Unused user management | Yes (always was)
`/accounts/password/reset/` | `django.contrib.auth.views.password_reset` | Unused user management | Yes (always was)
`/accounts/password/reset/complete/` | `django.contrib.auth.views.password_reset_complete` | Unused user management | Yes (always was)
`/accounts/password/reset/confirm/<uidb64>/<token>/` | `django.contrib.auth.views.password_reset_confirm` | Unused user management | Yes (always was)
`/accounts/password/reset/done/` | `django.contrib.auth.views.password_reset_done` | Unused user management | Yes (always was)
`/accounts/register/` | `onadata.apps.main.registration_views.FHRegistrationView` | Unused user management | Yes (always was)
`/accounts/register/complete/` | `django.views.generic.base.TemplateView` | Unused user management | Yes (always was)
`/activity/fields` | `onadata.apps.main.views.activity_fields` | Schema for audit log | No
`/api/v1/profiles/<user>/change_password` | `onadata.apps.api.viewsets.user_profile_viewset.UserProfileViewSet` | Unused user management | Yes (always was)
`/api/v1/profiles/<user>/change_password.<format>/` | `onadata.apps.api.viewsets.user_profile_viewset.UserProfileViewSet` | Unused user management | Yes (always was)
`/faq/` | `onadata.apps.main.views.faq` | Unused informational page | Yes (on kobotoolbox.org)
`/gauthtest/` | `onadata.apps.main.google_export.google_oauth2_request` | Google authentication (non-functional) | No
`/getting_started/` | `onadata.apps.main.views.getting_started` | Unused informational page | Yes (on kobotoolbox.org)
`/gwelcome/` | `onadata.apps.main.google_export.google_auth_return` | Google authentication (non-functional) | No
`/people/` | `onadata.apps.main.views.members_list` | Unused informational page | Yes (on kobotoolbox.org)
`/privacy/` | `onadata.apps.main.views.privacy` | Unused informational page | Yes
`/resources/` | `onadata.apps.main.views.resources` | Unused informational page | Yes (on kobotoolbox.org)
`/support/` | `onadata.apps.main.views.support` | Unused informational page | Yes (on kobotoolbox.org)
`/syntax/` | `onadata.apps.main.views.syntax` | Unused informational page | Yes (on kobotoolbox.org)
`/tos/` | `onadata.apps.main.views.tos` | Unused informational page | Yes
`/tutorial/` | `onadata.apps.main.views.tutorial` | Unused informational page | Yes (on kobotoolbox.org)
`/typeahead_usernames` | `onadata.apps.main.views.username_list` | Username autocompletion for legacy permissions UI (not API endpoint for external use) | No (removed for privacy)
`/xls2xform/` | `onadata.apps.main.views.xls2xform` | Unused informational page | Yes (on kobotoolbox.org)


# KoBoCAT endpoint removals as of release [2.020.40](https://github.com/kobotoolbox/kobocat/releases/tag/2.020.40)

The last release to contain any of the endpoints listed below was https://github.com/kobotoolbox/kobocat/releases/tag/2.020.39.

## Already available in KPI

### Charts and Stats

URL Pattern | View Class or Function | View Name
-- | -- | --
`/<username>/forms/<id_string>/stats` | `onadata.apps.viewer.views.charts` | `form-stats`
`/<username>/forms/<id_string>/tables` | `onadata.apps.viewer.views.stats_tables` |  
`/api/v1/charts` | `onadata.apps.api.viewsets.charts_viewset.ChartsViewSet` | `chart-list`
`/api/v1/charts.<format>/` | `onadata.apps.api.viewsets.charts_viewset.ChartsViewSet` | `chart-list`
`/api/v1/charts/<pk>` | `onadata.apps.api.viewsets.charts_viewset.ChartsViewSet` | `chart-detail`
`/api/v1/charts/<pk>.<format>/` | `onadata.apps.api.viewsets.charts_viewset.ChartsViewSet` | `chart-detail`
`/api/v1/stats` | `onadata.apps.api.viewsets.stats_viewset.StatsViewSet` | `stats-list`
`/api/v1/stats.<format>/` | `onadata.apps.api.viewsets.stats_viewset.StatsViewSet` | `stats-list`
`/api/v1/stats/<pk>` | `onadata.apps.api.viewsets.stats_viewset.StatsViewSet` | `stats-detail`
`/api/v1/stats/<pk>.<format>/` | `onadata.apps.api.viewsets.stats_viewset.StatsViewSet` | `stats-detail`
`/api/v1/stats/submissions` | `onadata.apps.api.viewsets.submissionstats_viewset.SubmissionStatsViewSet` | `submissionstats-list`
`/api/v1/stats/submissions.<format>/` | `onadata.apps.api.viewsets.submissionstats_viewset.SubmissionStatsViewSet` | `submissionstats-list`
`/api/v1/stats/submissions/<pk>` | `onadata.apps.api.viewsets.submissionstats_viewset.SubmissionStatsViewSet` | `submissionstats-detail`
`/api/v1/stats/submissions/<pk>.<format>/` | `onadata.apps.api.viewsets.submissionstats_viewset.SubmissionStatsViewSet` | `submissionstats-detail`
`/stats/` | `onadata.apps.stats.views.stats` | `form-stats`
`/stats/submissions/` | `onadata.apps.stats.views.submissions` |

### Form Cloning

URL Pattern | View Class or Function | View Name
-- | -- | --
`/api/v1/forms/<pk>/clone` | `onadata.apps.api.viewsets.xform_viewset.XFormViewSet` | `xform-clone`
`/api/v1/forms/<pk>/clone.<format>/` | `onadata.apps.api.viewsets.xform_viewset.XFormViewSet` | `xform-clone`

### Form Sharing

URL Pattern | View Class or Function | View Name
-- | -- | --
`/api/v1/forms/<pk>/share` | `onadata.apps.api.viewsets.xform_viewset.XFormViewSet` | `xform-share`
`/api/v1/forms/<pk>/share.<format>/` | `onadata.apps.api.viewsets.xform_viewset.XFormViewSet` | `xform-share`

### User Profiles

URL Pattern | View Class or Function | View Name
-- | -- | --
`/api/v1/profiles` | `onadata.apps.api.viewsets.user_profile_viewset.UserProfileViewSet` | `userprofile-list`
`/api/v1/profiles.<format>/` | `onadata.apps.api.viewsets.user_profile_viewset.UserProfileViewSet` | `userprofile-list`
`/api/v1/profiles/<user>` | `onadata.apps.api.viewsets.user_profile_viewset.UserProfileViewSet` | `userprofile-detail`
`/api/v1/profiles/<user>.<format>/` | `onadata.apps.api.viewsets.user_profile_viewset.UserProfileViewSet` | `userprofile-detail`
`/api/v1/profiles/<user>/change_password` | `onadata.apps.api.viewsets.user_profile_viewset.UserProfileViewSet` | `userprofile-change-password`
`/api/v1/profiles/<user>/change_password.<format>/` | `onadata.apps.api.viewsets.user_profile_viewset.UserProfileViewSet` | `userprofile-change-password`
`/api/v1/user/reset` | `onadata.apps.api.viewsets.connect_viewset.ConnectViewSet` | `userprofile-reset`
`/api/v1/user/reset.<format>/` | `onadata.apps.api.viewsets.connect_viewset.ConnectViewSet` | `userprofile-reset`
`/api/v1/users` | `onadata.apps.api.viewsets.user_viewset.UserViewSet` | `user-list`
`/api/v1/users.<format>/` | `onadata.apps.api.viewsets.user_viewset.UserViewSet` | `user-list`
`/api/v1/users/<username>` | `onadata.apps.api.viewsets.user_viewset.UserViewSet` | `user-detail`
`/api/v1/users/<username>.<format>/` | `onadata.apps.api.viewsets.user_viewset.UserViewSet` | `user-detail`

## Discontinued

These endpoints existed but were neither maintained nor tested, and their features were never available in the UI. They might be added to KPI at an indeterminate future time given interest and funding.

### Organizations, Projects, and Teams

URL Pattern | View Class or Function | View Name
-- | -- | --
`/api/v1/orgs` | `onadata.apps.api.viewsets.organization_profile_viewset.OrganizationProfileViewSet` | `organizationprofile-list`
`/api/v1/orgs.<format>/` | `onadata.apps.api.viewsets.organization_profile_viewset.OrganizationProfileViewSet` | `organizationprofile-list`
`/api/v1/orgs/<user>` | `onadata.apps.api.viewsets.organization_profile_viewset.OrganizationProfileViewSet` | `organizationprofile-detail`
`/api/v1/orgs/<user>.<format>/` | `onadata.apps.api.viewsets.organization_profile_viewset.OrganizationProfileViewSet` | `organizationprofile-detail`
`/api/v1/orgs/<user>/members` | `onadata.apps.api.viewsets.organization_profile_viewset.OrganizationProfileViewSet` | `organizationprofile-members`
`/api/v1/orgs/<user>/members.<format>/` | `onadata.apps.api.viewsets.organization_profile_viewset.OrganizationProfileViewSet` | `organizationprofile-members`
`/api/v1/projects` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-list`
`/api/v1/projects.<format>/` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-list`
`/api/v1/projects/<pk>` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-detail`
`/api/v1/projects/<pk>.<format>/` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-detail`
`/api/v1/projects/<pk>/forms` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-forms`
`/api/v1/projects/<pk>/forms.<format>/` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-forms`
`/api/v1/projects/<pk>/labels` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-labels`
`/api/v1/projects/<pk>/labels.<format>/` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-labels`
`/api/v1/projects/<pk>/share` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-share`
`/api/v1/projects/<pk>/share.<format>/` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-share`
`/api/v1/projects/<pk>/star` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-star`
`/api/v1/projects/<pk>/star.<format>/` | `onadata.apps.api.viewsets.project_viewset.ProjectViewSet` | `project-star`
`/api/v1/teams` | `onadata.apps.api.viewsets.team_viewset.TeamViewSet` | `team-list`
`/api/v1/teams.<format>/` | `onadata.apps.api.viewsets.team_viewset.TeamViewSet` | `team-list`
`/api/v1/teams/<pk>` | `onadata.apps.api.viewsets.team_viewset.TeamViewSet` | `team-detail`
`/api/v1/teams/<pk>.<format>/` | `onadata.apps.api.viewsets.team_viewset.TeamViewSet` | `team-detail`
`/api/v1/teams/<pk>/members` | `onadata.apps.api.viewsets.team_viewset.TeamViewSet` | `team-members`
`/api/v1/teams/<pk>/members.<format>/` | `onadata.apps.api.viewsets.team_viewset.TeamViewSet` | `team-members`

### User Profiles

URL Pattern | View Class or Function | View Name
-- | -- | --
`/api/v1/user/<user>/starred` | `onadata.apps.api.viewsets.connect_viewset.ConnectViewSet` | `userprofile-starred`
`/api/v1/user/<user>/starred.<format>/` | `onadata.apps.api.viewsets.connect_viewset.ConnectViewSet` | `userprofile-starred`

## Discontinued permanently

### Bamboo and Ziggy

URL Pattern | View Class or Function | View Name
-- | -- | --
`/<username>/forms/<id_string>/bamboo` | `onadata.apps.main.views.link_to_bamboo` |
`/<username>/form-submissions` | `onadata.apps.logger.views.ziggy_submissions` |
