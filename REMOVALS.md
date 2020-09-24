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
