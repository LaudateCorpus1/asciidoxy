# Copyright (C) 2019-2020, TomTom (http://tomtom.com).
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
"""Filters for selecting which parts of elements are generated."""

import re

from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional, Pattern, Sequence, Union

from ..model import EnumValue, InnerTypeReference, Member, ThrowsClause


class FilterAction(Enum):
    """Action to take based on the filter."""
    INCLUDE = 1
    """Include the item."""

    EXCLUDE = 2
    """Exclude the item."""

    NEUTRAL = 3
    """Do not change whether the item is included or excluded."""


class StringFilter(ABC):
    """Filter string values."""
    @abstractmethod
    def __call__(self, value: str) -> FilterAction:
        return FilterAction.NEUTRAL


class AllStringFilter(StringFilter):
    """Include all values."""
    def __call__(self, value: str) -> FilterAction:
        return FilterAction.INCLUDE


class NoneStringFilter(StringFilter):
    """Exclude all values."""
    def __call__(self, value: str) -> FilterAction:
        return FilterAction.EXCLUDE


class IncludeStringFilter(StringFilter):
    """Include values that match a regular expression."""
    include_pattern: Pattern

    def __init__(self, include_pattern: str):
        self.include_pattern = re.compile(include_pattern)

    def __call__(self, value: str) -> FilterAction:
        if self.include_pattern.match(value) is not None:
            return FilterAction.INCLUDE
        else:
            return FilterAction.NEUTRAL


class ExcludeStringFilter(StringFilter):
    """Exclude all values that match a regular expression."""
    exclude_pattern: Pattern

    def __init__(self, exclude_pattern: str):
        self.exclude_pattern = re.compile(exclude_pattern)

    def __call__(self, value: str) -> FilterAction:
        if self.exclude_pattern.match(value) is not None:
            return FilterAction.EXCLUDE
        else:
            return FilterAction.NEUTRAL


class ChainedStringFilter(StringFilter):
    """Ordered chain of string filters.

    The last non-neutral filter action determines the outcome of this filter.
    """
    filters: Sequence[StringFilter]

    def __init__(self, *filters: StringFilter):
        self.filters = filters

    def __call__(self, value: str) -> FilterAction:
        combined_action = FilterAction.NEUTRAL
        for f in self.filters:
            action = f(value)
            if action is not FilterAction.NEUTRAL:
                combined_action = action
        return combined_action


class MemberFilter:
    """Filter for selecting members (of a compound) to insert.

    Attributes:
        name_filter: Filter for the name of the members to include.
        kind_filter: Filter for the kind of the members to include.
        prot_filter: Filter for the protection level of the members to include.
    """
    name_filter: StringFilter
    kind_filter: StringFilter
    prot_filter: StringFilter

    # TODO static_filter: BoolFilter

    def __init__(self,
                 name_filter: Optional[StringFilter] = None,
                 kind_filter: Optional[StringFilter] = None,
                 prot_filter: Optional[StringFilter] = None):
        self.name_filter = name_filter or AllStringFilter()
        self.kind_filter = kind_filter or AllStringFilter()
        self.prot_filter = prot_filter or AllStringFilter()

    def __call__(self, member: Member) -> bool:
        """Apply the filter to a member.

        Returns:
            True if the member should be included.
        """
        if self.name_filter(member.name) is FilterAction.EXCLUDE:
            return False
        if self.kind_filter(member.kind) is FilterAction.EXCLUDE:
            return False
        if self.prot_filter(member.prot) is FilterAction.EXCLUDE:
            return False
        return True


class InnerClassFilter:
    """Filter for selecting inner classes (of a compound) to insert.

    Ignores class references that have not been resolved.

    Attributes:
        name_filter: Filter for the name of the members to include.
        kind_filter: Filter for the kind of the members to include.
    """
    name_filter: StringFilter
    kind_filter: StringFilter

    def __init__(self,
                 name_filter: Optional[StringFilter] = None,
                 kind_filter: Optional[StringFilter] = None):
        self.name_filter = name_filter or AllStringFilter()
        self.kind_filter = kind_filter or AllStringFilter()

    def __call__(self, ref: InnerTypeReference) -> bool:
        """Apply the filter to an inner class.

        Returns:
            True if the inner class should be included.
        """
        if ref.referred_object is None:
            return False
        if self.name_filter(ref.referred_object.name) is FilterAction.EXCLUDE:
            return False
        if self.kind_filter(ref.referred_object.kind) is FilterAction.EXCLUDE:
            return False
        return True


class EnumValueFilter:
    """Filter for selecting enum values (of a compound or member) to insert.

    Attributes:
        name_filter: Filter for the name of the enum values to include.
    """
    name_filter: StringFilter

    def __init__(self, name_filter: StringFilter):
        self.name_filter = name_filter

    def __call__(self, enum_value: EnumValue) -> bool:
        """Apply the filter to an enum value.

        Returns:
            True if the enum value should be included.
        """
        if self.name_filter(enum_value.name) is FilterAction.EXCLUDE:
            return False
        return True


class ExceptionFilter:
    """Filter for selecting exceptions (of a member) to insert.

    Attributes:
        name_filter: Filter for the name of the exceptions to include.
    """
    name_filter: StringFilter

    def __init__(self, name_filter: StringFilter):
        self.name_filter = name_filter

    def __call__(self, throws_clause: ThrowsClause) -> bool:
        """Apply the filter to an exception in a throws clause.

        Returns:
            True if the enum value should be included.
        """
        if self.name_filter(throws_clause.type.name) is FilterAction.EXCLUDE:
            return False
        return True


def filter_from_strings(filter_strings: Union[str, Sequence[str]]) -> StringFilter:
    """Create a string filter from a sequence of input strings.

    Each string in the sequence can have the following format:
    - `ALL`: Accept all strings.
    - `NONE`: Accept no strings.
    - `<regex>` or `+<regex>`: Include strings matching the regex.
    - `-<regex>`: Exclude strings matching the regex.

    If the first string is an include regex, an implicit NONE is inserted before. If the first
    string is an exclude regex, an implicit ALL is inserted before.

    Args:
        filter_strings: List of filter strings to build the filter from.

    Returns:
        A string filter matching the input specification.
    """
    if isinstance(filter_strings, str):
        filter_strings = [filter_strings]

    filters: List[StringFilter] = []

    for filter_string in filter_strings:
        if filter_string == "ALL":
            filters.append(AllStringFilter())
        elif filter_string == "NONE":
            filters.append(NoneStringFilter())
        elif filter_string.startswith("-"):
            filters.append(ExcludeStringFilter(filter_string[1:]))
        elif filter_string.startswith("+"):
            filters.append(IncludeStringFilter(filter_string[1:]))
        else:
            filters.append(IncludeStringFilter(filter_string))

    if len(filters) > 0:
        if isinstance(filters[0], ExcludeStringFilter):
            filters.insert(0, AllStringFilter())
        elif isinstance(filters[0], IncludeStringFilter):
            filters.insert(0, NoneStringFilter())

    if len(filters) == 0:
        return AllStringFilter()
    elif len(filters) == 1:
        return filters[0]
    else:
        return ChainedStringFilter(*filters)
