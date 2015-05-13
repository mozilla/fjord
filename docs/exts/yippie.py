from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util.compat import make_admonition
from sphinx.locale import _


def setup(app):
    app.add_node(
        yippie_node,
        html=(visit_yippie_node, depart_yippie_node),
        latext=(visit_yippie_node, depart_yippie_node),
        text=(visit_yippie_node, depart_yippie_node)
    )
    app.add_directive('yippie', YippieDirective)


class yippie_node(nodes.Admonition, nodes.Element):
    pass

def visit_yippie_node(self, node):
    self.visit_admonition(node)

def depart_yippie_node(self, node):
    self.depart_admonition(node)


class YippieDirective(Directive):
    has_content = True

    def run(self):
        env = self.state.document.settings.env

        targetid = 'yippie-%d' % env.new_serialno('yippie')
        targetnode = nodes.target('', '', ids=[targetid])

        ad = make_admonition(yippie_node, self.name, [_('Yippie')], self.options,
                             self.content, self.lineno, self.content_offset,
                             self.block_text, self.state, self.state_machine)

        return [targetnode] + ad
