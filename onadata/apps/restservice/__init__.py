SERVICE_F2DHIS2 = (u"f2dhis2", u"f2dhis2")
SERVICE_BAMBOO = (u"bamboo", u"bamboo")  # Deprecated TODO to remove
SERVICE_GENERIC_XML = (u"generic_xml", u"XML POST")
SERVICE_GENERIC_JSON = (u"generic_json", u"JSON POST")
SERVICE_KPI_HOOK = (u"kpi_hook", u"KPI Hook POST")

SERVICE_CHOICES = (
    SERVICE_F2DHIS2,
    SERVICE_BAMBOO,
    SERVICE_GENERIC_XML,
    SERVICE_GENERIC_JSON,
    SERVICE_KPI_HOOK
)


default_app_config = "onadata.apps.restservice.app.RestServiceConfig"