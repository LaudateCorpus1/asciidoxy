# Copyright (C) 2019-2021, TomTom (http://tomtom.com).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parse brief and detailed descriptions from Doxygen XML."""

import xml.etree.ElementTree as ET

from abc import ABC, abstractmethod
from typing import List, Mapping, Optional, Tuple, Type, TypeVar


def parse_description(xml_root: Optional[ET.Element]) -> "ParaContainer":
    """Parse a description from Doxygen XML.

    Expects either `briefdescription` or `detaileddescription`. In case of `detaileddescription` it
    can contain additional sections documenting parameters and return types.

    Args:
        xml_root: Element to start processing from.
    Returns:
        A container with description paragraphs and sections.
    """
    contents = ParaContainer()
    if xml_root is not None:
        for xml_element in xml_root:
            _parse_description(xml_element, contents)
        contents.normalize()
    return contents


def select_descriptions(brief: "ParaContainer", detailed: "ParaContainer") -> Tuple[str, str]:
    """Select the approprate brief and detailed descriptions.

    Sometimes one of the descriptions is missing. This method makes sure there is always at least
    a brief description.

    Args:
        brief: Brief description as found in the XML.
        detailed: Detailed description as found in the XML.

    Returns:
        brief: Brief description to use.
        detailed: Detailed description to use.
    """
    brief_adoc = brief.to_asciidoc()
    if brief_adoc:
        return brief_adoc, detailed.to_asciidoc()

    if detailed.contents:
        brief.contents.append(detailed.contents.pop(0))
    return brief.to_asciidoc(), detailed.to_asciidoc()


class DescriptionElement(ABC):
    """A description in Doxygen XML is made up of several different XML elements. Each element
    requires its own conversion into AsciiDoc format.
    """
    @abstractmethod
    def to_asciidoc(self) -> str:
        """Convert the element, and all contained elements, to AsciiDoc format."""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element) -> "DescriptionElement":
        """Generate a description element from its XML counterpart.

        Information and attributes from XML can be used, but the contained text and the tail text
        are handled separately.
        """
        return cls()

    def update_from_xml(self, xml_element: ET.Element):
        """Update the current element with information from another XML element.

        By default this method does nothing. To be implemented only by subclasses that support or
        require information from some if its children, without adding a new element for the child.
        """

    def add_text(self, text: str) -> None:
        """Add the text inside the XML element.

        By default the text is ignored. To be implemented only by subclasses that use the text.
        """

    def add_tail(self, parent: "NestedDescriptionElement", text: str) -> None:
        """Add the text after the closing tag of the element.

        By default the tail is ignored. To be used by subclasses that support tail text. The parent
        can be used to create additional elements for the tail text after the current element.
        """


class NestedDescriptionElement(DescriptionElement):
    """A description element that contains additional description elements.

    Attributes:
        contents: Additional description elements inside this element.
    """
    contents: List[DescriptionElement]

    def __init__(self, *contents: DescriptionElement):
        self.contents = list(contents)

    def append(self, content: DescriptionElement) -> None:
        if content:
            self.contents.append(content)

    def to_asciidoc(self) -> str:
        return "".join(element.to_asciidoc() for element in self.contents)


class ParaContainer(NestedDescriptionElement):
    """Element that contains a sequence of paragraphes."""
    def append(self, content: DescriptionElement) -> None:
        assert isinstance(content, (Para, ParaContainer))
        super().append(content)

    def to_asciidoc(self) -> str:
        return "\n\n".join(element.to_asciidoc() for element in self.contents
                           if element.to_asciidoc().strip())

    def normalize(self) -> None:
        new_contents: List[DescriptionElement] = []
        while self.contents:
            child = self.contents.pop(0)

            # Normalize ParaContainers and add them if not empty
            if isinstance(child, ParaContainer):
                child.normalize()
                if child.contents:
                    new_contents.append(child)
                continue

            assert isinstance(child, Para)

            # Paras and ParaContainers inside a Para need to be promoted to the current
            # ParaContainer. Split the existing content in separate Paras around other Paras and
            # ParaContainers

            # Para for non-Para content
            # Original para
            new_para = child.clone_without_contents()
            while child.contents and not isinstance(child.contents[0], (Para, ParaContainer)):
                new_para.append(child.contents.pop(0))
            new_contents.append(new_para)

            reassess = []
            while child.contents:
                # Promote Paras and ParaContainers
                while child.contents and isinstance(child.contents[0], (Para, ParaContainer)):
                    reassess.append(child.contents.pop(0))

                # Para for non-Para content
                if isinstance(reassess[-1], Para):
                    new_para = reassess.pop(-1)
                else:
                    new_para = child.clone_without_contents()
                while child.contents and not isinstance(child.contents[0], (Para, ParaContainer)):
                    new_para.append(child.contents.pop(0))
                reassess.append(new_para)
            self.contents = reassess + self.contents

        self.contents = new_contents

    SectionT = TypeVar("SectionT", bound="NamedSection")

    def pop_section(self, section_type: Type[SectionT], name: str) -> Optional[SectionT]:
        for i, child in enumerate(self.contents):
            if isinstance(child, section_type) and child.name == name:
                return self.contents.pop(i)
        return None


class Para(NestedDescriptionElement):
    """A single paragraph of text."""
    def to_asciidoc(self) -> str:
        return super().to_asciidoc().strip()

    def clone_without_contents(self):
        return self.__class__()

    def add_text(self, text: str) -> None:
        self.append(PlainText(text))


class PlainText(DescriptionElement):
    """Plain text.

    Formatting may be applied by parent elements.

    Attributes:
        text: The plain text.
    """
    text: str

    def __init__(self, text: str):
        self.text = text

    def to_asciidoc(self) -> str:
        return self.text.strip("\r\n")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {repr(self.text)}"

    def add_text(self, text: str) -> None:
        self.text += text


class NamedSection(ParaContainer):
    """Special paragraph indicating a section that can be retrieved by name.

    Attributes:
        name: Name of the section.
    """
    name: str

    def __init__(self, name: str = "", *contents: DescriptionElement):
        super().__init__(*contents)
        self.name = name


class Section(NamedSection):
    """Special paragraph indicating a text section that is either an admonition or has a caption."""
    ADMONITION_MAP = {
        "ATTENTION": "CAUTION",
        "NOTE": "NOTE",
        "REMARK": "NOTE",
        "WARNING": "WARNING",
    }

    def __init__(self, name: str = "", *contents: DescriptionElement):
        super().__init__(name, *contents)

    def to_asciidoc(self) -> str:
        admonition = self.ADMONITION_MAP.get(self.name.upper())
        if admonition is None:
            return f".{self.name.capitalize()}\n[NOTE]\n====\n{super().to_asciidoc()}\n===="
        else:
            return f"[{admonition}]\n====\n{super().to_asciidoc()}\n===="

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"

    @classmethod
    def from_xml(cls, xml_element: ET.Element):
        return cls(name=xml_element.get("kind", ""))

    def update_from_xml(self, xml_element: ET.Element):
        if xml_element.tag == "xreftitle":
            assert xml_element.text
            self.name = xml_element.text

    def add_tail(self, parent: NestedDescriptionElement, text: str):
        parent.append(Para(PlainText(text.lstrip())))


class Style(NestedDescriptionElement):
    """Apply a text style to contained elements.

    Attributes:
        kind: The kind of style to apply.
    """
    STYLE_MAP = {
        "emphasis": "__",
        "bold": "**",
        "computeroutput": "``",
        "verbatim": "``",
    }

    kind: str

    def __init__(self, kind: str, *contents: DescriptionElement):
        super().__init__(*contents)
        self.kind = kind

    def to_asciidoc(self) -> str:
        asciidoc_style = self.STYLE_MAP.get(self.kind, "")
        return f"{asciidoc_style}{super().to_asciidoc()}{asciidoc_style}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.kind}"

    @classmethod
    def from_xml(cls, xml_element) -> "Style":
        return cls(kind=xml_element.tag)

    def add_text(self, text: str) -> None:
        self.append(PlainText(text))

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(PlainText(text))


class ItemizedList(ParaContainer):
    """Paragraph that contains a bullet list."""
    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(Para(PlainText(text.lstrip())))


class ListItem(ParaContainer):
    """A single item in a bullet list.

    The item itself can contain multiple paragraphs.
    """
    def to_asciidoc(self) -> str:
        return f"* {super().to_asciidoc()}"

    def add_text(self, text: str) -> None:
        self.append(PlainText(text))


class CodeBlock(NestedDescriptionElement):
    """A block of code."""
    def to_asciidoc(self) -> str:
        code = "\n".join(element.to_asciidoc() for element in self.contents)
        # TODO: set language
        return f"[source]\n----\n{code}\n----"


class CodeLine(NestedDescriptionElement):
    """A single line in a block of code."""


class Diagram(Para):
    """Textual description of a diagram that can be used to generate a picture.

    Attributes:
        generator: The generator required to create the diagram.
    """
    generator: str

    def __init__(self, generator: str, *contents: DescriptionElement):
        super().__init__(*contents)
        self.generator = generator

    def to_asciidoc(self) -> str:
        # Not using Para.to_asciidoc() due to extra stripping that needs to be avoided here
        return f"[{self.generator}]\n....\n{NestedDescriptionElement.to_asciidoc(self)}\n...."

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.generator}"

    def clone_without_contents(self) -> "Diagram":
        return self.__class__(self.generator)

    @classmethod
    def from_xml(cls, xml_element) -> "Diagram":
        return cls(xml_element.tag)

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(Para(PlainText(text.lstrip())))


class ParameterList(NamedSection):
    """Special section containing a list of parameter descriptions."""
    def __init__(self, name: str, *contents: NestedDescriptionElement):
        super().__init__(name, *contents)

    def to_asciidoc(self) -> str:
        return ""

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name}"

    @classmethod
    def from_xml(cls, xml_element) -> "ParameterList":
        return cls(xml_element.get("kind"))


class ParameterDescription(ParaContainer):
    """Description of a single parameter.

    Attributes:
        name: Name of the parameter.
        direction: If supported, whether this is an in-parameter, out-parameter, or both.
    """
    name: Optional[str]
    direction: Optional[str]

    def __init__(self, *contents: DescriptionElement):
        super().__init__(*contents)
        self.name = None
        self.direction = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.name or ''} [{self.direction or ''}]"

    def update_from_xml(self, xml_element: ET.Element) -> None:
        if xml_element.tag == "parametername":
            self.name = xml_element.text
            self.direction = xml_element.get("direction")


class Ref(NestedDescriptionElement):
    """Reference to an API element. This appears as a hyperlink.

    Attributes:
        refid: Unique identifier of the API element.
        kindref: The kind of API element referred to.
    """
    refid: str
    kindref: str

    def __init__(self, refid: str, kindref: str, *contents: DescriptionElement):
        super().__init__(*contents)
        self.refid = refid
        self.kindref = kindref

    def to_asciidoc(self) -> str:
        # TODO: fix id
        return f"<<{self.refid},{super().to_asciidoc()}>>"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.kindref}[{self.refid}]"

    @classmethod
    def from_xml(cls, xml_element) -> "Ref":
        return cls(xml_element.get("refid"), xml_element.get("kindref"))

    def add_text(self, text: str) -> None:
        self.append(PlainText(text))

    def add_tail(self, parent: NestedDescriptionElement, text: str) -> None:
        parent.append(PlainText(text))


def _parse_description(xml_element: ET.Element, parent: NestedDescriptionElement):
    element = None

    # Map of element tags for which a new element is to be constructed and added the the parent.
    NEW_ELEMENT: Mapping[str, Type[DescriptionElement]] = {
        "codeline": CodeLine,
        "itemizedlist": ItemizedList,
        "listitem": ListItem,
        "para": Para,
        "parameteritem": ParameterDescription,
        "programlisting": CodeBlock,
        "simplesect": Section,
        "xrefsect": Section,
        "emphasis": Style,
        "bold": Style,
        "computeroutput": Style,
        "highlight": Style,
        "parameterlist": ParameterList,
        "ref": Ref,
        "plantuml": Diagram,
        "dot": Diagram,
        "verbatim": Style,
    }

    # Map of element tags that update the parent element.
    UPDATE_PARENT = {
        "xreftitle": Section,
        "parametername": ParameterDescription,
    }

    # Map of element tags for which the children update its parent.
    USE_PARENT = {
        "xrefdescription": Section,
        "parameternamelist": ParameterDescription,
        "parameterdescription": ParameterDescription,
    }

    if xml_element.tag in NEW_ELEMENT:
        element = NEW_ELEMENT[xml_element.tag].from_xml(xml_element)

    elif xml_element.tag in UPDATE_PARENT:
        assert isinstance(parent, UPDATE_PARENT[xml_element.tag])
        parent.update_from_xml(xml_element)
        element = parent

    elif xml_element.tag in USE_PARENT:
        assert isinstance(parent, USE_PARENT[xml_element.tag])
        element = parent

    elif xml_element.tag == "sp":
        element = PlainText(f" {xml_element.tail or ''}")

    else:
        print(f"Unhandled tag: {xml_element.tag}")

    if element is None:
        return
    if element is not parent:
        parent.append(element)

    if xml_element.text:
        element.add_text(xml_element.text)

    if xml_element.tail:
        element.add_tail(parent, xml_element.tail)

    for child in xml_element:
        assert isinstance(element, NestedDescriptionElement)
        _parse_description(child, element)
