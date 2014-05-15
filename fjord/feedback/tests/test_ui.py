# FIXME: We can uncomment this out when we fix the problems affecting
# LiveServerTestCases.

# from fjord.base.tests import SeleniumTestCase, reverse


# class TestFeedback(SeleniumTestCase):

#     def happy_elem(self):
#         return self.webdriver.find_element_by_css_selector('article#happy')

#     def sad_elem(self):
#         return self.webdriver.find_element_by_css_selector('article#sad')

#     def test_happy_url(self):
#         """
#         If the happy URL is used, the happy survey element is shown.
#         """
#         url = self.live_server_url + reverse('feedback') + '#happy'
#         self.webdriver.get(url)
#         assert self.happy_elem().is_displayed()
#         assert not self.sad_elem().is_displayed()

#     def test_sad_url(self):
#         """
#         If the sad URL is used, the sad survey element is shown.
#         """
#         url = self.live_server_url + reverse('feedback') + '#sad'
#         self.webdriver.get(url)
#         assert self.sad_elem().is_displayed()
#         assert not self.happy_elem().is_displayed()
