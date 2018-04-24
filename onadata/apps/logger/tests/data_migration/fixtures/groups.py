GROUPS_FIELDS_AFTER = [
    'start', 'end', 'math_degree', 'current_date', 'group_transformations',
    'bijective', 'isomorphism', 'automorphism', 'endomorphism', 'homeomorphism',
    'continuous',
]

form_xml_groups_before = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>Test groups</h:title>
    <model>
      <instance>
        <data id="groups">
          <start/>
          <end/>
          <homomorphism/>
          <isooomorphism/>
          <meta>
            <instanceID/>
          </meta>
        </data>
      </instance>
      <bind jr:preload="timestamp" jr:preloadParams="start" nodeset="/data/start" type="dateTime"/>
      <bind jr:preload="timestamp" jr:preloadParams="end" nodeset="/data/end" type="dateTime"/>
      <bind nodeset="/data/homomorphism" required="false()" type="string"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/data/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/data/homomorphism">
      <label>homomorphism</label>
    </input>
  </h:body>
</h:html>
"""

form_xml_groups_after = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>Test groups</h:title>
    <model>
      <instance>
        <data id="groups2">
          <start/>
          <end/>
          <group_transformations>
            <isomorphism/>
            <homomorphism/>
          </group_transformations>
          <meta>
            <instanceID/>
          </meta>
        </data>
      </instance>
      <bind jr:preload="timestamp" jr:preloadParams="start" nodeset="/data/start" type="dateTime"/>
      <bind jr:preload="timestamp" jr:preloadParams="end" nodeset="/data/end" type="dateTime"/>
      <bind nodeset="/data/group_transformations/homomorphism" required="false()" type="string"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/data/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <group ref="/data/group_transformations">
      <label>Group</label>
      <input ref="/data/group_transformations/homomorphism">
        <label>homomorphism</label>
      </input>
    </group>
  </h:body>
</h:html>
"""

survey_xml_groups_before = """
<TestGroup xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" id="TestGroup" version="vaEytJG3RWgRJMAuCnKWtC">
  <formhub>
    <uuid>30760c2faa6c498a83f0c6a7ff761f83</uuid>
  </formhub>
  
  <start>2017-11-10T17:57:48.000+01:00</start>
  <end>2017-11-10T18:00:02.000+01:00</end>
  
  <homomorphism>identity</homomorphism>
  
  <__version__>vaEytJG3RWgRJMAuCnKWtC</__version__>
  <meta>
    <instanceID>uuid:ec5f2a1c-1cbd-49ac-8ab7-8be1ba33c14f</instanceID>
  </meta>
</TestGroup>
"""

survey_xml_groups_after = """
<groups2 xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" id="groups2" version="vaEytJG3RWgRJMAuCnKWtC">
  <formhub>
    <uuid>30760c2faa6c498a83f0c6a7ff761f83</uuid>
  </formhub>
  
  <start>2017-11-10T17:57:48.000+01:00</start>
  <end>2017-11-10T18:00:02.000+01:00</end>
  
  <__version__>vaEytJG3RWgRJMAuCnKWtC</__version__>
  <meta>
    <instanceID>uuid:ec5f2a1c-1cbd-49ac-8ab7-8be1ba33c14f</instanceID>
  </meta>

  <group_transformations>
    <isomorphism/>
    <homomorphism>identity</homomorphism>
  </group_transformations>
  
</groups2>
"""

form_xml_groups_before__second = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>Test groups</h:title>
    <model>
      <instance>
        <data id="AlgebraicTypes">
          <start/>
          <end/>
          <isomorphism/>
          <current_date/>
          <endomorphism/>
          <math_degree/>
          <automorphism/>
          <meta>
            <instanceID/>
          </meta>
        </data>
      </instance>
      <bind jr:preload="timestamp" jr:preloadParams="start" nodeset="/data/start" type="dateTime"/>
      <bind jr:preload="timestamp" jr:preloadParams="end" nodeset="/data/end" type="dateTime"/>
      <bind nodeset="/data/isomorphism" required="false()" type="string"/>
      <bind nodeset="/data/current_date" required="false()" type="string"/>
      <bind nodeset="/data/endomorphism" required="false()" type="string"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/data/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <input ref="/data/isomorphism">
      <label>isomorphism</label>
    </input>
    <input ref="/data/current_date">
      <label>endomorphism</label>
    </input>
    <input ref="/data/endomorphism">
      <label>endomorphism</label>
    </input>
    <input ref="/data/math_degree">
      <label>endomorphism</label>
    </input>
    <input ref="/data/automorphism">
      <label>automorphism</label>
    </input>
  </h:body>
</h:html>
"""

form_xml_groups_after__second = """<?xml version="1.0"?>
<h:html xmlns="http://www.w3.org/2002/xforms" xmlns:ev="http://www.w3.org/2001/xml-events" xmlns:h="http://www.w3.org/1999/xhtml" xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
  <h:head>
    <h:title>Test groups</h:title>
    <model>
      <instance>
        <data id="AlgebraicTypes2">
          <start/>
          <end/>
          <group_transformations>
            <bijective>
                <continuous>
                    <homeomorphism/>
                </continuous>
                <isomorphism/>
                <automorphism/>
            </bijective>
            <endomorphism/>
          </group_transformations>
          <math_degree/>
          <current_date/>
          <meta>
            <instanceID/>
          </meta>
        </data>
      </instance>
      <bind jr:preload="timestamp" jr:preloadParams="start" nodeset="/data/start" type="dateTime"/>
      <bind jr:preload="timestamp" jr:preloadParams="end" nodeset="/data/end" type="dateTime"/>
      <bind nodeset="/data/group_transformations/homomorphism" required="false()" type="string"/>
      <bind nodeset="/data/group_transformations/isomorphism" required="false()" type="string"/>
      <bind nodeset="/data/group_transformations/endomorphism" required="false()" type="string"/>
      <bind nodeset="/data/math_degree" required="false()" type="string"/>
      <bind nodeset="/data/current_date" required="false()" type="dateTime"/>
      <bind calculate="concat('uuid:', uuid())" nodeset="/data/meta/instanceID" readonly="true()" type="string"/>
    </model>
  </h:head>
  <h:body>
    <group ref="/data/group_transformations">
      <label>Group</label>
      <input ref="/data/group_transformations/isomorphism">
        <label>isomorphism</label>
      </input>
      <input ref="/data/group_transformations/endomorphism">
        <label>endomorphism</label>
      </input>
      <input ref="/data/group_transformations/automorphism">
        <label>automorphism</label>
      </input>
    </group>
  </h:body>
</h:html>
"""

survey_xml_groups_before__second = """
<TestGroup xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" id="TestGroup" version="vkvxz56QzsTUnnJvSQDj4R">
  <formhub>
    <uuid>30760c2faa6c498a83f0c6a7ff761f83</uuid>
  </formhub>
  <start>2017-11-10T17:57:48.000+01:00</start>
  <end>2017-11-10T18:00:02.000+01:00</end>
  
  <isomorphism>canonical</isomorphism>
  <math_degree>Ph.D</math_degree>
  <endomorphism>f: G -> G</endomorphism>
  <current_date>3.11.1971</current_date>
  <automorphism>id</automorphism>
   
  <__version__>vaEytJG3RWgRJMAuCnKWtC</__version__>
  <meta>
    <instanceID>uuid:ec5f2a1c-1cbd-49ac-8ab7-8be1ba33c14f</instanceID>
  </meta>
</TestGroup>
"""

survey_xml_groups_after__second = """
<AlgebraicTypes2 xmlns:jr="http://openrosa.org/javarosa" xmlns:orx="http://openrosa.org/xforms" id="AlgebraicTypes2" version="vkvxz56QzsTUnnJvSQDj4R">
  <formhub>
    <uuid>30760c2faa6c498a83f0c6a7ff761f83</uuid>
  </formhub>
  <start>2017-11-10T17:57:48.000+01:00</start>
  <end>2017-11-10T18:00:02.000+01:00</end>
  
  <math_degree>Ph.D</math_degree>
  <current_date>3.11.1971</current_date>

  <__version__>vaEytJG3RWgRJMAuCnKWtC</__version__>
  <meta>
    <instanceID>uuid:ec5f2a1c-1cbd-49ac-8ab7-8be1ba33c14f</instanceID>
  </meta>

  <group_transformations>
    <bijective>
        <continuous>
            <homeomorphism/>
        </continuous>
        <isomorphism>canonical</isomorphism>
        <automorphism>id</automorphism>
    </bijective>
    <endomorphism>f: G -&gt; G</endomorphism>
  </group_transformations>
 
</AlgebraicTypes2>
"""
