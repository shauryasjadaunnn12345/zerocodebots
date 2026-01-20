from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Project, Feedback, BotResponse


class FeedbackAndResponseTests(TestCase):
	def setUp(self):
		self.client = Client()
		self.user = User.objects.create_user(username='tester', password='pass')
		self.project = Project.objects.create(user=self.user, name='T1')

	def test_submit_feedback_creates_feedback(self):
		url = reverse('submit_feedback', args=[self.project.id])
		resp = self.client.post(url, {
			'rating': '4',
			'comment': 'Helpful',
			'question': 'What is X?',
			'response': 'X is Y',
		})
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('ok'))
		self.assertTrue(Feedback.objects.filter(project=self.project, rating=4).exists())

	def test_botresponse_model_saved(self):
		BotResponse.objects.create(project=self.project, question='Q', response='A', confidence=0.75)
		self.assertEqual(BotResponse.objects.filter(project=self.project).count(), 1)

	def test_feedback_links_to_botresponse(self):
		br = BotResponse.objects.create(project=self.project, question='Q1', response='A1', confidence=0.5)
		url = reverse('submit_feedback', args=[self.project.id])
		resp = self.client.post(url, {'rating': '2', 'comment': 'bad', 'question': 'Q1', 'response': 'A1', 'bot_response_id': str(br.id)})
		self.assertEqual(resp.status_code, 200)
		fb = Feedback.objects.filter(project=self.project).first()
		self.assertIsNotNone(fb)
		self.assertIsNotNone(fb.bot_response)
		self.assertEqual(fb.bot_response.id, br.id)

	def test_thumbs_down_creates_feedback(self):
		br = BotResponse.objects.create(project=self.project, question='Q2', response='A2', confidence=0.8)
		url = reverse('submit_feedback', args=[self.project.id])
		resp = self.client.post(url, {'selected_option': 'thumbs_down', 'question': 'Q2', 'response': 'A2', 'bot_response_id': str(br.id)})
		self.assertEqual(resp.status_code, 200)
		fb = Feedback.objects.filter(project=self.project, selected_option='thumbs_down').first()
		self.assertIsNotNone(fb)
		self.assertEqual(fb.bot_response.id, br.id)

	def test_project_analytics_view(self):
		self.client.login(username='tester', password='pass')
		url = reverse('project_analytics', args=[self.project.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertIn('event_counts', data)

	def test_export_analytics_view(self):
		self.client.login(username='tester', password='pass')
		url = reverse('export_analytics', args=[self.project.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		self.assertEqual(resp['Content-Type'], 'text/csv')

	def test_project_analytics_dashboard_view(self):
		self.client.login(username='tester', password='pass')
		url = reverse('project_analytics_dashboard', args=[self.project.id])
		resp = self.client.get(url)
		self.assertEqual(resp.status_code, 200)
		# page should contain project name
		self.assertIn(self.project.name, resp.content.decode())
