<%inherit file="base.mako"/>

<%block name="head_title"></%block>
<%block name="page_header">${_("All Service Providers")}</%block>

% for sp in sp_list:
    <div>
        <a href="${ sp_link_base }/${ sp[1] }">${ sp[0] }</a>
    </div>
% endfor
