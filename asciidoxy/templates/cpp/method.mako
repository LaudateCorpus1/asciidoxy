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
<%!
from asciidoxy.templates.cpp.helpers import CppTemplateHelper
%>

= [[${element.id},${element.name}]]
${api_context.insert(element)}

[%autofit]
[source,cpp,subs="-specialchars,macros+"]
----
${CppTemplateHelper(api_context).method_signature(element)}
----
<%include file="/cpp/_function.mako"/>
