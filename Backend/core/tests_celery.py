from django.test import TestCase, override_settings

from .tasks import health_check_task


class CeleryInfrastructureTests(TestCase):
    @override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
        CELERY_BROKER_URL="memory://",
        CELERY_RESULT_BACKEND="cache+memory://",
    )
    def test_health_check_task_delay(self):
        result = health_check_task.delay()
        self.assertEqual(result.get(), "celery working")
