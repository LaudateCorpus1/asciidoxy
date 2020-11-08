## Copyright (C) 2019-2020, TomTom (http://tomtom.com).
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##   http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.

################################################################################ Helper includes ##
<%!
from asciidoxy.templates.helpers import has
from asciidoxy.templates.swift.helpers import SwiftTemplateHelper
%>
<%
helper = SwiftTemplateHelper(api, element, insert_filter)
%>
######################################################################## Header and introduction ##
= [[${element.id},${element.name}]]${element.name}
${api.inserted(element)}

[source,swift,subs="-specialchars,macros+"]
----
${element.kind} ${element.name}
----
${element.brief}

${element.description}

################################################################################# Overview table ##
[cols='h,5a']
|===

###################################################################################################
% if has(helper.simple_enclosed_types(prot="public")) or has(helper.complex_enclosed_types(prot="public")):
|*Enclosed types*
|
% for enclosed in chain(helper.simple_enclosed_types(prot="public"), helper.complex_enclosed_types(prot="public")):
`xref:${enclosed.id}[${enclosed.name}]`::
${enclosed.brief}
% endfor

% endif
###################################################################################################
% if has(helper.constructors(prot="public")):
|*Constructors*
|
% for constructor in helper.constructors(prot="public"):
`xref:${constructor.id}[${constructor.name}${helper.type_list(constructor.params)}]`::
${constructor.brief}
% endfor

% endif
###################################################################################################
% if has(helper.properties(prot="public")):
|*Properties*
|
% for prop in helper.properties(prot="public"):
`xref:${prop.id}[${prop.name}]`::
${prop.brief}
% endfor

% endif
###################################################################################################
% if has(helper.type_methods(prot="public")):
|*Type methods*
|
% for method in helper.type_methods(prot="public"):
`xref:${method.id}[${method.name}${helper.type_list(method.params)}]`::
${method.brief}
% endfor

% endif
###################################################################################################
% if has(helper.methods(prot="public")):
|*Methods*
|
% for method in helper.methods(prot="public"):
`xref:${method.id}[${method.name}${helper.type_list(method.params)}]`::
${method.brief}
% endfor

% endif
|===

############################################################################ Simple inner types ##
% for enclosed in helper.simple_enclosed_types(prot="public"):
${api.insert_fragment(enclosed, insert_filter)}
% endfor

== Members

################################################################################### Constructors ##
% for constructor in helper.constructors(prot="public"):
[[${constructor.id},${constructor.name}]]
${api.inserted(constructor)}
[source,swift,subs="-specialchars,macros+"]
----
${helper.method_signature(constructor)}
----

${constructor.brief}

${constructor.description}

% if constructor.params or constructor.exceptions or constructor.returns:
[cols='h,5a']
|===
% if constructor.params:
| Parameters
|
% for param in constructor.params:
`${helper.parameter(param)}`::
${param.description}

% endfor
% endif
% if constructor.exceptions:
| Throws
|
% for exception in constructor.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif

'''
% endfor
##################################################################################### Properties ##
% for prop in helper.properties(prot="public"):
[[${prop.id},${prop.name}]]
${api.inserted(prop)}
[source,swift,subs="-specialchars,macros+"]
----
var ${prop.name}: ${helper.print_ref(prop.returns.type)}
----

${prop.brief}

${prop.description}

'''
% endfor
################################################################################### Type methods ##
% for method in helper.type_methods(prot="public"):
[[${method.id},${method.name}]]
${api.inserted(method)}
[source,swift,subs="-specialchars,macros+"]
----
${helper.method_signature(method)}
----

${method.brief}

${method.description}

% if method.params or method.exceptions or method.returns:
[cols='h,5a']
|===
% if method.params:
| Parameters
|
% for param in method.params:
`${helper.parameter(param)}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${helper.print_ref(method.returns.type)}`::
${method.returns.description}

% endif
% if method.exceptions:
| Throws
|
% for exception in method.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif

'''
% endfor
######################################################################################## Methods ##
% for method in helper.methods(prot="public"):
[[${method.id},${method.name}]]
${api.inserted(method)}
[source,swift,subs="-specialchars,macros+"]
----
${helper.method_signature(method)}
----

${method.brief}

${method.description}

% if method.params or method.exceptions or method.returns:
[cols='h,5a']
|===
% if method.params:
| Parameters
|
% for param in method.params:
`${helper.parameter(param)}`::
${param.description}

% endfor
% endif
% if method.returns and method.returns.type.name != "void":
| Returns
|
`${helper.print_ref(method.returns.type)}`::
${method.returns.description}

% endif
% if method.exceptions:
| Throws
|
% for exception in method.exceptions:
`${exception.type.name}`::
${exception.description}

% endfor
%endif
|===
% endif

'''
% endfor

############################################################################# Inner/Nested types ##

% for enclosed in helper.complex_enclosed_types(prot="public"):
${api.insert_fragment(enclosed, insert_filter)}
% endfor
