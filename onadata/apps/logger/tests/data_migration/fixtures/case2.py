"""
Second test case of example xml files to parse and compare with each other.

Differences between form_xml_case_1 and form_xml_case_1_after:
- Rename 'name' to 'your_name'
- Add 'mood' field

XML of Surevey instance (answer to xform)

"""
DEFAULT_MOOD = 'good'

FIELDS_2 = [
    'name', 'age', 'picture', 'has_children', 'gps', 'web_browsers'
]

form_xml_case_2 = '''<?xml version="1.0" encoding="utf-8"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>tutorial</h:title>
    <model>
      <instance>
        <tutorial id="tutorial">
          <formhub>
            <uuid/>
          </formhub>
          <name/>
          <age/>
          <picture/>
          <has_children/>
          <gps/>
          <web_browsers/>
          <meta>
            <instanceID/>
          </meta>
        </tutorial>
      </instance>
      <bind nodeset="/tutorial/name" type="string"/>
      <bind nodeset="/tutorial/age" type="int"/>
      <bind nodeset="/tutorial/picture" type="binary"/>
      <bind nodeset="/tutorial/has_children" type="select1"/>
      <bind nodeset="/tutorial/gps" type="geopoint"/>
      <bind nodeset="/tutorial/web_browsers" type="select"/>
      <bind calculate="concat(\'uuid:\', uuid())" nodeset="/tutorial/meta/instanceID" readonly="true()" type="string"/>
      <bind calculate="\'a842eee12a774ff5b688c7b77c5ba467\'" nodeset="/tutorial/formhub/uuid" type="string"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/tutorial/name">
      <label>1. What is your name?</label>
    </input>
    <input ref="/tutorial/age">
      <label>2. How old are you?</label>
    </input>
    <upload mediatype="image/*" ref="/tutorial/picture">
      <label>3. May I take your picture?</label>
    </upload>
    <select1 ref="/tutorial/has_children">
      <label>4. Do you have any children?</label>
      <item>
        <label>no</label>
        <value>0</value>
      </item>
      <item>
        <label>yes</label>
        <value>1</value>
      </item>
    </select1>
    <input ref="/tutorial/gps">
      <label>5. Record your GPS coordinates.</label>
      <hint>GPS coordinates can only be collected when outside.</hint>
    </input>
    <select ref="/tutorial/web_browsers">
      <label>6. What web browsers do you use?</label>
      <item>
        <label>Mozilla Firefox</label>
        <value>firefox</value>
      </item>
      <item>
        <label>Google Chrome</label>
        <value>chrome</value>
      </item>
      <item>
        <label>Internet Explorer</label>
        <value>ie</value>
      </item>
      <item>
        <label>Safari</label>
        <value>safari</value>
      </item>
    </select>
  </h:body>
</h:html>
'''

form_xml_case_2_after = '''<?xml version="1.0" encoding="utf-8"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>tutorial2</h:title>
    <model>
      <instance>
        <tutorial2 id="tutorial2">
          <formhub>
            <uuid/>
          </formhub>
          <your_name/>
          <age/>
          <picture/>
          <has_children/>
          <gps/>
          <web_browsers/>
          <mood/>
          <meta>
            <instanceID/>
          </meta>
        </tutorial2>
      </instance>
      <bind nodeset="/tutorial2/your_name" type="string"/>
      <bind nodeset="/tutorial2/age" type="int"/>
      <bind nodeset="/tutorial2/picture" type="binary"/>
      <bind nodeset="/tutorial2/has_children" type="select1"/>
      <bind nodeset="/tutorial2/gps" type="geopoint"/>
      <bind nodeset="/tutorial2/web_browsers" type="select"/>
      <bind nodeset="/tutorial2/mood" type="string"/>
      <bind calculate="concat(\'uuid:\', uuid())" nodeset="/tutorial2/meta/instanceID" readonly="true()" type="string"/>
      <bind calculate="\'a842eee12a774ff5b688c7b77c5ba467\'" nodeset="/tutorial2/formhub/uuid" type="string"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/tutorial2/your_name">
      <label>1. What is your name?</label>
    </input>
    <input ref="/tutorial2/age">
      <label>2. How old are you?</label>
    </input>
    <upload mediatype="image/*" ref="/tutorial2/picture">
      <label>3. May I take your picture?</label>
    </upload>
    <select1 ref="/tutorial2/has_children">
      <label>4. Do you have any children?</label>
      <item>
        <label>no</label>
        <value>0</value>
      </item>
      <item>
        <label>yes</label>
        <value>1</value>
      </item>
    </select1>
    <input ref="/tutorial2/gps">
      <label>5. Record your GPS coordinates.</label>
      <hint>GPS coordinates can only be collected when outside.</hint>
    </input>
    <select ref="/tutorial2/web_browsers">
      <label>6. What web browsers do you use?</label>
      <item>
        <label>Mozilla Firefox</label>
        <value>firefox</value>
      </item>
      <item>
        <label>Google Chrome</label>
        <value>chrome</value>
      </item>
      <item>
        <label>Internet Explorer</label>
        <value>ie</value>
      </item>
      <item>
        <label>Safari</label>
        <value>safari</value>
      </item>
    </select>
    <input ref="/tutorial2/mood">
      <label>7. How are you today?</label>
    </input>
  </h:body>
</h:html>
'''

survey_xml_2 = '''<tutorial2 xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" id="tutorial2">
  <formhub>
    <uuid>a842eee12a774ff5b688c7b77c5ba467</uuid>
  </formhub>
  <name>Alfred Tarski</name>
  <age>20</age>
  <picture/>
  <has_children>0</has_children>
  <gps>0.000001 0.000001 0 0</gps>
  <web_browsers>chrome</web_browsers>
  <meta>
    <instanceID>uuid:fc9eebf7-49f2-4857-b51f-bf0e385a53f5</instanceID>
  </meta>
</tutorial2>
'''

survey_2_after_migration = '''<tutorial2 xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" id="tutorial2">
  <formhub>
    <uuid>a842eee12a774ff5b688c7b77c5ba467</uuid>
  </formhub>
  <your_name>Alfred Tarski</your_name>
  <age>20</age>
  <picture/>
  <has_children>0</has_children>
  <gps>0.000001 0.000001 0 0</gps>
  <web_browsers>chrome</web_browsers>
  <meta>
    <instanceID>uuid:fc9eebf7-49f2-4857-b51f-bf0e385a53f5</instanceID>
  </meta>
  <mood>good</mood>
</tutorial2>
'''
