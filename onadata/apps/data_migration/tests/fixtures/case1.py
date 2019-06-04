"""
Example xml files to parse and compare with each other.

Differences between form_xml_case_1 and form_xml_case_1_after:
- Modify title
- Age is decimal type
- Location not required
- Added new option to select in gender
- Removed date field
- Rename 'name' to 'last_name'
- Add 'last_name' field
- Add 'birthday' field

XML of Surevey instance (answer to xform)
"""

FIELDS = [
    'name', 'gender', 'photo', 'date', 'location',
    'age', 'thanks', 'start_time', 'end_time', 'today',
]

form_xml_case_1 = '''<?xml version="1.0" encoding="utf-8"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms/" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>Survey</h:title>
    <model>
      <instance>
        <Survey id="Survey">
          <formhub>
            <uuid/>
          </formhub>
          <name/>
          <gender/>
          <photo/>
          <age/>
          <date/>
          <location/>
          <meta>
            <instanceID/>
          </meta>
        </Survey>
      </instance>
      <bind nodeset="/Survey/name" required="true()" type="string"/>
      <bind nodeset="/Survey/age" required="true()" type="int"/>
      <bind nodeset="/Survey/gender" required="true()" type="select1"/>
      <bind nodeset="/Survey/photo" type="binary"/>
      <bind nodeset="/Survey/date" required="true()" type="date"/>
      <bind nodeset="/Survey/location" required="true()" type="geopoint"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/Survey/name">
      <label>What is your name?\u2019</label>
    </input>
    <input ref="/Survey/age">
      <label>How old are you?\u2018</label>
    </input>
    <select1 ref="/Survey/gender">
      <label>Gender</label>
      <item>
        <label>Male</label>
        <value>male</value>
      </item>
      <item>
        <label>Female</label>
        <value>female</value>
      </item>
    </select1>
    <upload mediatype="image/*" ref="/Survey/photo">
      <label>Portrait</label>
    </upload>
    <input ref="/Survey/date">
      <label>Date</label>
    </input>
    <input ref="/Survey/location">
      <label>Where are you?</label>
      <hint>You need to be outside for your GPS to work.</hint>
    </input>
  </h:body>
</h:html>
'''

form_xml_case_1_after = '''<?xml version="1.0" encoding="utf-8"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms/" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>Survey2</h:title>
    <model>
      <instance>
        <Survey2 id="Survey2">
          <formhub>
            <uuid/>
          </formhub>
          <first_name/>
          <last_name/>
          <birthday/>
          <gender/>
          <photo/>
          <age/>
          <location/>
          <meta>
            <instanceID/>
          </meta>
        </Survey2>
      </instance>
      <bind nodeset="/Survey2/first_name" required="true()" type="string"/>
      <bind nodeset="/Survey2/last_name" required="true()" type="string"/>
      <bind nodeset="/Survey2/birthday" required="true()" type="date"/>
      <bind nodeset="/Survey2/age" required="true()" type="decimal"/>
      <bind nodeset="/Survey2/gender" required="true()" type="select1"/>
      <bind nodeset="/Survey2/location" required="false()" type="geopoint"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/Survey2/name">
      <label>What is your name?\u2019</label>
    </input>
    <input ref="/Survey2/age">
      <label>How old are you?\u2018</label>
    </input>
    <select1 ref="/Survey2/gender">
      <label>Gender</label>
      <item>
        <label>Male</label>
        <value>male</value>
      </item>
      <item>
        <label>Female</label>
        <value>female</value>
      </item>
      <item>
        <label>Unknown</label>
        <value>unknown</value>
      </item>
    </select1>
    <upload mediatype="image/*" ref="/Survey2/photo">
      <label>Portrait</label>
    </upload>
    <input ref="/Survey2/location">
      <label>Where are you?</label>
      <hint>You need to be outside for your GPS to work.</hint>
    </input>
  </h:body>
</h:html>
'''

survey_template = '''<Survey xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms/" id="Survey">
  <formhub>
    <uuid>{}</uuid>
  </formhub>
  <name>{}</name>
  <gender>male</gender>
  <photo/>
  <date>{}</date>
  <location>-1 1.1 1 2</location>
  <age>{}</age>
  <thanks/>
  <start_time>2016-01-01T18:32:20.000+03:00</start_time>
  <end_time>2016-01-01T18:33:03.000+03:00</end_time>
  <today>2016-01-01</today>
  <imei>example.com:d123das</imei>
  <meta>
    <instanceID>uuid:{}</instanceID>
  </meta>
</Survey>
'''

survey_after_migration_template = '''<Survey2 xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms/" id="Survey2">
  <formhub>
    <uuid>{}</uuid>
  </formhub>
  <first_name>{}</first_name>
  <gender>male</gender>
  <photo/>
  <date>{}</date>
  <location>-1 1.1 1 2</location>
  <age>{}</age>
  <thanks/>
  <start_time>2016-01-01T18:32:20.000+03:00</start_time>
  <end_time>2016-01-01T18:33:03.000+03:00</end_time>
  <today>2016-01-01</today>
  <imei>example.com:d123das</imei>
  <meta>
    <instanceID>uuid:{}</instanceID>
  </meta>
  <last_name>Fowler</last_name>
  <birthday/>
</Survey2>
'''


_first_survey_data = (
    '123abc', 'Alonzo Church', '2000-01-01', '50', 'das-d123-dsa-dsa-dsa'
)
_second_survey_data = (
    '456asd', 'Richard Feynman', '1988-02-15', '70', 'qwe-ert-yui-opa-sdf'
)

survey_xml = survey_template.format(*_first_survey_data)
survey_xml_second = survey_template.format(*_second_survey_data)

survey_after_migration = survey_after_migration_template.format(*_first_survey_data)
survey_after_migration_second = survey_after_migration_template.format(*_second_survey_data)

append_extra_data = lambda survey, data: survey.replace('</Survey>', data + '</Survey>')
