import os
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from datetime import datetime
from todo.models import Task


# Create your tests here.
class SampleTestCase(TestCase):
    def test_sample1(self):
        self.assertEqual(1 + 2, 3)


class TaskModelTestCase(TestCase):
    def test_create_task1(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title='task1', due_at=due)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task1')
        self.assertFalse(task.completed)
        self.assertFalse(task.favorite)
        self.assertEqual(task.due_at, due)

    def test_create_task_with_favorite(self):
        task = Task(title='task-fav', favorite=True)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task-fav')
        self.assertTrue(task.favorite)

    def test_creat_task2(self):
        task = Task(title='task2')
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task2')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, None)

    def test_create_task_with_photo(self):
        image = SimpleUploadedFile(
            'test.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;',
            content_type='image/gif',
        )
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        task = Task(title='task-photo', due_at=due, photo=image)
        task.save()

        task = Task.objects.get(pk=task.pk)
        self.assertEqual(task.title, 'task-photo')
        self.assertFalse(task.completed)
        self.assertEqual(task.due_at, due)
        self.assertTrue(task.photo.name.startswith('task_photos/'))

    def test_is_overdue_future(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 6, 30, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))

    def test_is_overdue_past(self):
        due = timezone.make_aware(datetime(2024, 6, 30, 23, 59, 59))
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertTrue(task.is_overdue(current))

    def test_is_overdue_none(self):
        due = None
        current = timezone.make_aware(datetime(2024, 7, 1, 0, 0, 0))
        task = Task(title='task1', due_at=due)
        task.save()

        self.assertFalse(task.is_overdue(current))


class TodoViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._media_root = tempfile.mkdtemp()
        cls._override_settings = override_settings(MEDIA_ROOT=cls._media_root)
        cls._override_settings.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override_settings.disable()
        shutil.rmtree(cls._media_root, ignore_errors=True)
        super().tearDownClass()

    def test_index_get(self):
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 0)

    def test_index_post(self):
        client = Client()
        data = {
            'title': 'Test Task',
            'due_at': '2024-06-30 23:59:59',
            'detail': 'Task detail content',
        }
        response = client.post('/', data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 1)
        self.assertEqual(response.context['tasks'][0].detail, 'Task detail content')

    def test_index_form_has_detail_textbox(self):
        client = Client()
        response = client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="detail"')
        self.assertContains(response, 'id="detailInput"')

    def test_index_post_with_photo(self):
        client = Client()
        image = SimpleUploadedFile(
            'test.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;',
            content_type='image/gif',
        )
        response = client.post('/', {
            'title': 'Test Task',
            'due_at': '2024-06-30 23:59:59',
            'photo': image,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 1)
        task = Task.objects.get(pk=response.context['tasks'][0].pk)
        self.assertTrue(task.photo.name.startswith('task_photos/'))

    def test_index_post_with_favorite(self):
        client = Client()
        response = client.post('/', {
            'title': 'Favorite Task',
            'due_at': '2024-06-30 23:59:59',
            'favorite': 'on',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(len(response.context['tasks']), 1)
        task = Task.objects.get(pk=response.context['tasks'][0].pk)
        self.assertTrue(task.favorite)

    def test_index_get_order_post(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get('/?order=post')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task2)
        self.assertEqual(response.context['tasks'][1], task1)

    def test_index_get_order_due(self):
        task1 = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task1.save()
        task2 = Task(title='task2', due_at=timezone.make_aware(datetime(2024, 8, 1)))
        task2.save()
        client = Client()
        response = client.get('/?order=due')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(response.context['tasks'][0], task1)
        self.assertEqual(response.context['tasks'][1], task2)

    def test_index_get_favorite_only(self):
        favorite_task = Task(title='fav task', favorite=True)
        favorite_task.save()
        normal_task = Task(title='normal task', favorite=False)
        normal_task.save()

        client = Client()
        response = client.get('/?order=favorite')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/index.html')
        self.assertEqual(list(response.context['tasks']), [favorite_task])

    def test_edit_post_update_favorite(self):
        task = Task(title='task1', favorite=False)
        task.save()
        client = Client()
        response = client.post('/{}/edit/'.format(task.pk), {
            'title': 'task1',
            'favorite': 'on',
        })

        self.assertEqual(response.status_code, 302)
        task_refresh = Task.objects.get(pk=task.pk)
        self.assertTrue(task_refresh.favorite)

    def test_detail_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/detail.html')
        self.assertEqual(response.context['task'], task)

    def test_detail_displays_photo(self):
        image = SimpleUploadedFile(
            'test.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;',
            content_type='image/gif',
        )
        task = Task(title='task1', photo=image)
        task.save()
        client = Client()
        response = client.get('/{}/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<img')
        self.assertContains(response, task.photo.url)

    def test_detail_displays_favorite(self):
        task = Task(title='fav detail', favorite=True)
        task.save()
        client = Client()
        response = client.get('/{}/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Status: Favorite')

    def test_detail_get_fail(self):
        client = Client()
        response = client.get('/1/')

        self.assertEqual(response.status_code, 404)

    def test_edit_get_success(self):
        task = Task(title='task1', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/edit/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.templates[0].name, 'todo/edit.html')
        self.assertEqual(response.context['task'], task)

    def test_edit_form_has_detail_textbox(self):
        task = Task(title='task1', detail='Existing detail', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        response = client.get('/{}/edit/'.format(task.pk))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="detail"')
        self.assertContains(response, 'id="detailInput"')
        self.assertContains(response, 'Existing detail')

    def test_edit_get_fail(self):
        client = Client()
        response = client.get('/1/edit/')

        self.assertEqual(response.status_code, 404)

    def test_edit_post_update(self):
        task = Task(title='old title', due_at=timezone.make_aware(datetime(2024, 7, 1)))
        task.save()
        client = Client()
        data = {
            'title': 'new title',
            'due_at': '2024-07-02 12:00:00',
            'completed': 'on',
            'detail': 'updated detail',
        }
        response = client.post('/{}/edit/'.format(task.pk), data)

        # should redirect to detail
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response['Location'].endswith('/{}/'.format(task.pk)))

        task_refresh = Task.objects.get(pk=task.pk)
        self.assertEqual(task_refresh.title, 'new title')
        self.assertTrue(task_refresh.completed)
        self.assertEqual(task_refresh.detail, 'updated detail')
        # due_at should be set (aware) to the provided datetime
        self.assertIsNotNone(task_refresh.due_at)

    def test_edit_post_update_photo(self):
        task = Task(title='old title')
        task.save()
        client = Client()
        image = SimpleUploadedFile(
            'update.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;',
            content_type='image/gif',
        )
        response = client.post('/{}/edit/'.format(task.pk), {
            'title': 'new title',
            'due_at': '2024-07-02 12:00:00',
            'completed': 'on',
            'photo': image,
            'favorite': 'on',
        })

        self.assertEqual(response.status_code, 302)
        task_refresh = Task.objects.get(pk=task.pk)
        self.assertEqual(task_refresh.title, 'new title')
        self.assertTrue(task_refresh.completed)
        self.assertTrue(task_refresh.favorite)
        self.assertTrue(task_refresh.photo.name.startswith('task_photos/'))

    def test_edit_post_overwrite_photo_deletes_old_file(self):
        original_image = SimpleUploadedFile(
            'original.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;',
            content_type='image/gif',
        )
        task = Task(title='old title', photo=original_image)
        task.save()
        old_path = task.photo.path
        self.assertTrue(os.path.exists(old_path))

        client = Client()
        new_image = SimpleUploadedFile(
            'updated.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;',
            content_type='image/gif',
        )
        response = client.post('/{}/edit/'.format(task.pk), {
            'title': 'new title',
            'due_at': '2024-07-02 12:00:00',
            'completed': 'on',
            'photo': new_image,
        })

        self.assertEqual(response.status_code, 302)
        task_refresh = Task.objects.get(pk=task.pk)
        self.assertNotEqual(task_refresh.photo.path, old_path)
        self.assertTrue(os.path.exists(task_refresh.photo.path))
        self.assertFalse(os.path.exists(old_path))

    def test_delete_task_deletes_photo_file(self):
        image = SimpleUploadedFile(
            'delete.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xFF\xFF\xFF!\xF9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;',
            content_type='image/gif',
        )
        task = Task(title='task1', photo=image)
        task.save()
        path = task.photo.path
        self.assertTrue(os.path.exists(path))

        client = Client()
        response = client.get('/{}/delete'.format(task.pk))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
        self.assertFalse(os.path.exists(path))

    def test_delete_success(self):
        task = Task(title='task1')
        task.save()
        client = Client()
        response = client.get('/{}/delete'.format(task.pk))

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())

    def test_delete_fail(self):
        client = Client()
        response = client.get('/1/delete')

        self.assertEqual(response.status_code, 404)
