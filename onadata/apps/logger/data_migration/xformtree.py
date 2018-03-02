from .tree import Tree
from .xmltree import XMLTree
from .common import concat_map


class XFormTree(XMLTree):
    """
    Parse XML string into tree and operate on nodes.

    Specifications of format:
    xls forms: http://xlsform.org/
    w3c xforms: https://www.w3.org/MarkUp/Forms/#waXForms
    """
    def find_element_in_tree(self, searched_tag):
        query = "//*[local-name()='%s']" % self.clean_tag(searched_tag)
        try:
            return self.root.xpath(query)[0]
        except IndexError:
            return None

    def set_tag(self, tag_name, value):
        el = self.find_element_in_tree(tag_name)
        cleaned_tag = self.field_tag(el)
        el.tag = el.tag.replace(cleaned_tag, value)
        return el

    def get_head_content(self):
        """XML Heads content."""
        return self.root[0][1]

    def get_head_instance(self):
        head = self.get_head_content()
        return head[0][0]

    def get_body_content(self):
        """XML body content."""
        return self.root[1].getchildren()

    def get_title(self):
        title = self.root[0][0]
        return title.text

    def get_fields(self):
        """Parse and return list of all fields in form."""
        instance = self.get_head_instance()
        return self.retrieve_leaf_elems_tags(instance)

    def get_groups(self):
        instance = self.get_head_instance()
        return concat_map(self.retrieve_groups, instance)

    def get_structured_fields(self):
        """Return fields structured into groups.

        Format: [field_1, field_2, {'group_name': [field_3, field_4]}, field_5]
        """
        instance = self.get_head_instance()
        return filter(lambda e: e is not None,
                      map(self.retrieve_fields, instance))

    def get_structured_fields_as_tree(self):
        return Tree.construct_tree(self.get_structured_fields())

    @classmethod
    def retrieve_fields(cls, element):
        if cls.is_group(element) and cls.is_relevant(element.tag):
            return {
                cls.field_tag(element):
                    filter(lambda e: e is not None,
                           map(cls.retrieve_fields, element))
            }
        return cls.field_tag(element) if cls.is_relevant(element.tag) else None

    def get_binds(self):
        head = self.get_head_content()
        # Omit <instance> with fields
        binds = head.getchildren()[1:]
        return binds

    def get_fields_types(self):
        """
        Iterate xml <binds> and fetch 'type' attribute.
        Returns dictionary: {'field_name': 'changed_type', ...}
        """
        binds = self.get_binds()
        return {
            self.get_cleaned_nodeset(bind): bind.attrib.get('type', '')
            for bind in binds
        }

    def get_fields_obligation(self):
        """
        Iterate xml <binds> and fetch 'required' attribute.
        Returns dictionary: {'field_name': 'changed_type', ...}
        """
        binds = self.get_binds()
        return {
            self.get_cleaned_nodeset(bind): self.get_obligation(bind)
            for bind in binds
        }

    def get_obligation(self, bind):
        try:
            requirement = bind.attrib['required'].replace('()', '')
        except KeyError:
            return False
        else:
            return requirement == 'true'

    def get_cleaned_nodeset(self, bind):
        """
        Extract field from bind nodeset.
        Example input:  {'nodeset': '/Survey/name',}
        output: 'name'
        """
        nodeset = bind.attrib['nodeset']
        return nodeset[nodeset.find('/', 2)+1:]

    def get_inputs_as_dict(self):
        """
        Get all inputs from body as dictionary
        Output: {'input_name': <XML Elements children of input>, ...}
        """
        body = self.get_body_content()
        return {
            self.get_input_name(input): input.getchildren()
            for input in body
        }

    def get_input_name(self, input):
        ref = input.attrib['ref']
        return ref[ref.find('/', 2)+1:]

    def get_id_string(self):
        return self.get_head_instance().attrib['id']

    def get_head_binds(self):
        return filter(
            lambda node: self.field_tag(node) == 'bind',
            self.get_head_content().getchildren()
        )

    def set_id_string(self, new_id_string):
        old_id_string = self.get_id_string()
        self.rename_head_tag(new_id_string)
        self._replace_in_nodeset_paths(old_id_string, new_id_string)
        self._replace_in_body_refs(old_id_string, new_id_string)

    def rename_head_tag(self, name):
        instance = self.get_head_instance()
        instance.attrib['id'] = name
        self.set_tag(instance.tag, name)

    def _replace_in_nodeset_paths(self, old_val, new_val):
        bind_nodesets = self.get_head_binds()
        for el in bind_nodesets:
            el.attrib['nodeset'] = el.attrib['nodeset'] \
                .replace(old_val, new_val)

    def _replace_in_body_refs(self, old_val, new_val):
        body_els_with_refs = filter(lambda el: el.attrib.get('ref'),
                                    self.get_body_content())
        for el in body_els_with_refs:
            el.attrib['ref'] = el.attrib['ref'].replace(old_val, new_val)

    def added_fields(self, other_tree):
        """Return new fields in actual tree compared to other_tree."""
        return [
            field for field in self.get_fields()
            if field not in other_tree.get_fields()
        ]

    def get_select_values(self, select):
        return [item[1].text for item in select.getchildren()[1:]]

    def get_select_options(self):
        inputs = self.get_inputs_as_dict()
        return {
            input_name: self.get_select_values(items[0].getparent())
            for input_name, items in inputs.items()
            if len(items) > 1 and self.field_tag(items[1]) == 'item'
        }

    def _added_to_list(self, basic, extended):
        """Returns items added to :basic: list"""
        return [item for item in extended if item not in basic]

    def added_select_options(self, other_tree):
        """Return new options in actual tree compared to other_tree."""
        actual_options = self.get_select_options()
        other_options = other_tree.get_select_options()
        return {
            name: self._added_to_list(other_options[name], values)
            for name, values in actual_options.items()
            if name in other_options and
            self._added_to_list(other_options[name], values)
        }
