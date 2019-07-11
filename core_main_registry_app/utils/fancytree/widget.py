"""
FancyTree widget.
Based on xrmx work: https://github.com/xrmx/django-fancytree.
Modified for the registry project.
"""
from itertools import chain

from django import forms
from django.conf import settings
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.forms.widgets import Widget
from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_text
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from mptt.templatetags.mptt_tags import cache_tree_children

try:
    import simplejson as json
except ImportError:
    import json


def get_doc(node, values, count_mode):
    """ Represent a node.

    Args:
        node:
        values:
        count_mode:  Add an html element to display counts next to each node (True/False).

    Returns:

    """
    if hasattr(node, "get_doc"):
        return node.get_doc(values)
    if hasattr(node, "name"):
        name = node.name
    else:
        name = str(node)

    #  Add an html element to display counts next to each node.
    if count_mode:
        count_html = "<em class='occurrences' id='{0}'></em>".format(node.pk)
        doc = {"title": "{0} {1}".format(name, count_html), "key": node.pk}
    else:
        doc = {"title": name, "key": node.pk}

    if str(node.pk) in values:
        doc['selected'] = True
        doc['expand'] = True
    return doc


def recursive_node_to_dict(node, values, count_mode):
    result = get_doc(node, values, count_mode)
    children = [recursive_node_to_dict(c, values, count_mode) for c in node.get_children()]
    if children:
        expand = [c for c in children if c.get('selected', False)]
        if expand:
            result["expand"] = True
        result["folder"] = True
        result['children'] = children
    return result


def get_tree(nodes, values, count_mode):
    root_nodes = cache_tree_children(nodes)
    return [recursive_node_to_dict(n, values, count_mode) for n in root_nodes]


class FancyTreeWidget(Widget):
    def __init__(self, attrs=None, choices=(), queryset=None, select_mode=3, count_mode=False):
        """

        Args:
            attrs:
            choices:
            queryset:
            select_mode:
            count_mode: Add an html element to display counts next to each node (True/False).
        """
        super(FancyTreeWidget, self).__init__(attrs)
        self.queryset = queryset
        self.select_mode = select_mode
        self.choices = list(choices)
        self.count_mode = count_mode

    def value_from_datadict(self, data, files, name):
        if isinstance(data, (MultiValueDict)):
            return data.getlist(name)
        return data.get(name, None)

    def render(self, name, value, attrs=None, choices=()):
        if value is None:
            value = []
        if not isinstance(value, (list, tuple)):
            value = [value]
        has_id = attrs and 'id' in attrs
        final_attrs = self.build_attrs(attrs)
        if has_id:
            output = [u'<div id="%s" name="%s"></div>' % (attrs['id'], self.choices.field.label)]
            id_attr = u' id="%s_checkboxes"' % (attrs['id'])
        else:
            output = [u'<div name="%s"></div>' % self.choices.field.label]
            id_attr = u''
        output.append(u'<ul style="display: none;" class="fancytree_checkboxes"%s>' % id_attr)
        str_values = set([force_text(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            if has_id:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], option_value))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            cb = forms.CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_text(option_value)
            rendered_cb = cb.render(name, option_value)
            option_label = conditional_escape(force_text(option_label))
            output.append(
                u'<li><label%s>%s %s</label></li>' % (label_for, rendered_cb, option_label)
            )
        output.append(u'</ul>')
        output.append(u'<script type="text/javascript">')
        js_data_var = 'fancytree_data_%s' % (attrs['id'].replace('-', '_'))
        if has_id:
            output.append(u'var %s = %s;' % (
                js_data_var,
                json.dumps(get_tree(self.queryset, str_values, self.count_mode))
            ))
            output.append(
                """
                var defer_initFancyTree = function() {
                    $.when(
                        cachedScript( "%(fancytree)s" ),
                        $.Deferred(function( deferred ){
                            $( deferred.resolve );
                        })
                    ).done(function(){
                        $.when(
                            cachedScript( "%(fancytree_wide)s" ),
                            cachedScript( "%(fancytree_customtag)s" ),
                            cachedScript( "%(fancytree_dnd)s" ),
                            cachedScript( "%(fancytree_glyph)s" ),
                            $.Deferred(function( deferred ){
                                $( deferred.resolve );
                            })
                        ).done(function(){
                            $("#%(id)s").fancytree({
                                extensions: ["glyph", "wide", "customTag"],
                                checkbox: true,
                                icon: false,
                                selectMode: %(select_mode)d,
                                source: %(js_var)s,
                                debugLevel: %(debug)d,
                                glyph: {
                                    map: {
                                      doc: "glyphicon glyphicon-file",
                                      docOpen: "glyphicon glyphicon-file",
                                      checkbox: "glyphicon glyphicon-unchecked",
                                      checkboxSelected: "glyphicon glyphicon-check",
                                      checkboxUnknown: "glyphicon glyphicon-share",
                                      dragHelper: "glyphicon glyphicon-play",
                                      dropMarker: "glyphicon glyphicon-arrow-right",
                                      error: "glyphicon glyphicon-warning-sign",
                                      expanderClosed: "glyphicon glyphicon-menu-right",
                                      expanderLazy: "glyphicon glyphicon-menu-right",
                                      expanderOpen: "glyphicon glyphicon-menu-down",
                                      folder: "glyphicon glyphicon-folder-close",
                                      folderOpen: "glyphicon glyphicon-folder-open",
                                      loading: "glyphicon glyphicon-refresh glyphicon-spin"
                                    }
                                },
                                wide: {
                                    iconWidth: "1em",
                                    iconSpacing: "0.5em",
                                    levelOfs: "1.5em"
                                },
                                customTag : {
                                    tag: "div"
                                },
                                _classNames: {
                                    active: "no-css",
                                    focused: "no-css"
                                },
                                select: function(event, data) {
                                    $('#%(id)s_checkboxes').find('input[type=checkbox]').prop('checked', false);
                                    var selNodes = data.tree.getSelectedNodes();
                                    var selKeys = $.map(selNodes, function(node){
                                           $('#%(id)s_' + (node.key)).prop('checked', true);
                                           return node.key;
                                    });
                                    // trigger the event fancy_tree_select
                                    $(document).trigger("fancy_tree_select_event", data);
                                },
                                click: function(event, data) {
                                    var node = data.node;
                                    if (event.targetType == "fancytreeclick")
                                        node.toggleSelected();
                                },
                                keydown: function(event, data) {
                                    var node = data.node;
                                    if (event.which == 32) {
                                        node.toggleSelected();
                                        return false;
                                    }
                                },
                                init: function(event, data) {
                                    // Render all nodes even if collapsed
                                    data.tree.getRootNode().render(force=true, deep=true);
                                    // set a timeout to let the tree finish its rendering
                                    setTimeout(function(){
                                        // trigger the event fancy_tree_ready
                                        $(document).trigger("fancy_tree_ready_event", data);
                                    }, 200);
                                },
                            });
                        });
                    });
                };
                onjQueryReady(defer_initFancyTree);

                """ % {
                    'id': attrs['id'],
                    'js_var': js_data_var,
                    'debug': settings.DEBUG and 1 or 0,
                    'select_mode': self.select_mode,
                    'fancytree': static("core_main_registry_app/libs/fancytree/jquery.fancytree.js"),
                    'fancytree_glyph': static("core_main_registry_app/libs/fancytree/jquery.fancytree.glyph.js"),
                    'fancytree_wide': static("core_main_registry_app/libs/fancytree/jquery.fancytree.wide.js"),
                    'fancytree_customtag': static("core_main_registry_app/libs/fancytree/jquery.fancytree.customtag.js"),
                    'fancytree_dnd': static("core_main_registry_app/libs/fancytree/jquery.fancytree.dnd.js"),
                }
            );
        output.append(u'</script>')
        return mark_safe(u'\n'.join(output))

    class Media(object):

        js = (
            'core_explore_common_app/common/js/tools.js',
        )

        css = {
            'all': ('core_main_registry_app/libs/fancytree/skin-bootstrap/ui.fancytree.css',
                    'core_main_registry_app/user/css/fancytree/fancytree.custom.css',
                    )
        }
