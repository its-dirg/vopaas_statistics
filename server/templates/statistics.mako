<%inherit file="base.mako"/>

<%block name="head_title">${ sp }}</%block>
<%block name="page_header">${_("Statistics for ")}${ sp }</%block>

<table class="table table-bordered table-striped">
    <thead>
        <tr>
            <th>#</th>
            <th>${_("Identity Provider")}</th>
            <th>${_("Frequency")}</th>
        </tr>
    </thead>
    <tbody>
    % for index, idp_info in enumerate(stat):
        <tr>
            <th scope="row">${ index + 1 }</th>
            <td>${ idp_info[0] }</td>
            <td>${ idp_info[1] }</td>
        </tr>
    % endfor
    </tbody>
</table>
