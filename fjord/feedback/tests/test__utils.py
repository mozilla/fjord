from django.test.client import RequestFactory

from nose.tools import ok_

from fjord.base.tests import TestCase, reverse
from fjord.feedback.utils import actual_ip_plus_desc


class Testactual_ip_plus_desc(TestCase):
    def test_valid_key(self):
        """Make sure the key is valid"""

        # create a request with this as the description
        desc = (
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
            u'\u5347\u7ea7\u4e86\u65b0\u7248\u672c\u4e4b\u540e'
        )

        url = reverse('feedback')
        factory = RequestFactory(HTTP_X_CLUSTER_CLIENT_IP='192.168.100.101')
        req = factory.post(url, {
            'description': desc
        })

        key = actual_ip_plus_desc(req)

        # Key can't exceed memcached 250 character max
        length = len(key)
        ok_(length < 250)

        # Key must be a string
        ok_(isinstance(key, str))

        # create a request with this as the description
        second_desc = (
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
            u'\u62e9\u201c\u5728\u65b0\u6807\u7b7e\u9875\u4e2d'
        )
        second_req = factory.post(url, {
            'description': second_desc
        })
        second_key = actual_ip_plus_desc(second_req)

        # Two descriptions with the same ip address should produce
        # different keys.
        assert key != second_key
