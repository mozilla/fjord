from django.shortcuts import render
from django.test.client import RequestFactory


def render_email(template, context):
    """Renders a template for email."""
    req = RequestFactory()
    req.META = {}
    resp = render(req, template, context)
    return resp.content
