from django.test import TestCase

# Create your tests here.
from celery.exceptions import Retry
from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase, override_settings
from django.urls import reverse
from polls.tasks import task_add_subscribe
from polls.factories import UserFactory

class UserSubscribeTestCase(TransactionTestCase):
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    @patch('polls.views.requests.post')
    def test_subscribe_post_succeed(self, mock_requests_post):
            response = self.client.post(
            reverse('user_subscribe'),
            {
                'username': 'test',
                'email': 'test@email.com',
            }
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(username='test').exists(), True)
        mock_requests_post.assert_called_with(
            'https://httpbin.org/delay/5',
            data={'email': 'test@email.com'}
        )
     
class UserSubscribeViewTestCase(TestCase):
    """
    This class only tests the Django view
    """
    @patch('polls.views.task_add_subscribe.delay')
    def test_subscribe_post_succeed(self, mock_task_add_subscribe_delay):
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            response = self.client.post(
                reverse('user_subscribe'),
                {
                    'username': 'test',
                    'email': 'test@email.com',
                }
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.filter(username='test').exists(), True)
        self.assertEqual(len(callbacks), 1)
        
        user = User.objects.filter(username='test').first()
        mock_task_add_subscribe_delay.assert_called_with(
            user.pk
        )
        
    @patch('polls.tasks.task_add_subscribe.retry')
    @patch('polls.views.requests.post')
    def test_exception(self, mock_requests_post, mock_task_add_subscribe_retry):
        mock_task_add_subscribe_retry.side_effect = Retry()
        mock_requests_post.side_effect = Exception()

        instance = UserFactory.create()

        with self.assertRaises(Retry):
            task_add_subscribe(instance.pk)