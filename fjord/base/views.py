from mobility.decorators import mobile_template
import jingo


@mobile_template('{mobile/}home.html')
def home_view(request, template=None):
    return jingo.render(request, template)
