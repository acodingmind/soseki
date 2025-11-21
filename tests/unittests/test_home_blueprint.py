#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from unittest.mock import patch, mock_open, Mock
from flask import current_app
from ssk import SSK_ADMIN_GROUP
from ssk.forms.contact_form import ContactForm
import pytest


# Mock the Flask render_template globally to avoid template errors
@pytest.fixture(autouse=True)
def mock_flask_render_template():
    with patch('ssk.render_template') as mock_render:
        mock_render.side_effect = lambda template, *args, **kwargs: f'<html>Mock {template}</html>'
        yield mock_render


def test_closed_route(app, client):
    """Test the /ssk/closed route"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.render_closed', return_value='<html>Closed</html>') as mock_render:
            response = client.get('/ssk/closed')
            
            assert response.status_code == 200
            assert b'Closed' in response.data
            mock_render.assert_called_once()


def test_index_open(app, client):
    """Test the /ssk/ route when website is open"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=False), \
             patch('ssk.blueprints.home.render_template', return_value='<html>Start Page</html>') as mock_render:
            
            response = client.get('/ssk/')
            
            assert response.status_code == 200
            assert b'Start Page' in response.data
            mock_render.assert_called_once_with("local/start.html", admin_group_name=SSK_ADMIN_GROUP)


def test_index_closed(app, client):
    """Test the /ssk/ route when website is closed"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=True), \
             patch('ssk.blueprints.home.WebGate.render_closed', return_value='<html>Closed</html>') as mock_render:
            
            response = client.get('/ssk/')
            
            assert response.status_code == 200
            assert b'Closed' in response.data
            mock_render.assert_called_once()


def test_tasks_open(app, client):
    """Test the /ssk/tasks route when website is open"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=False), \
             patch('ssk.blueprints.home_handler.HomeHandler.tasks', 
                   return_value=('ssk/tasks.html', [{'tid': '123', 'name': 'Test Task'}])) as mock_tasks, \
             patch('ssk.blueprints.home.render_template', return_value='<html>Tasks</html>') as mock_render:
            
            response = client.get('/ssk/tasks')
            
            assert response.status_code == 200
            assert b'Tasks' in response.data
            mock_tasks.assert_called_once()
            mock_render.assert_called_once_with('ssk/tasks.html', 
                                              tasks=[{'tid': '123', 'name': 'Test Task'}], 
                                              admin_group_name=SSK_ADMIN_GROUP)


def test_tasks_closed(app, client):
    """Test the /ssk/tasks route when website is closed"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=True), \
             patch('ssk.blueprints.home.WebGate.render_closed', return_value='<html>Closed</html>') as mock_render:
            
            response = client.get('/ssk/tasks')
            
            assert response.status_code == 200
            assert b'Closed' in response.data
            mock_render.assert_called_once()


def test_blog_open_success(app, client):
    """Test the /ssk/blog/<note> route with valid note when website is open"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=False), \
             patch('ssk.blueprints.home.ContactForm') as mock_form_class, \
             patch('ssk.blueprints.home.render_template', return_value='<html>Blog Post</html>') as mock_render:
            
            mock_form = Mock()
            mock_form_class.return_value = mock_form
            
            response = client.get('/ssk/blog/test-note')
            
            assert response.status_code == 200
            assert b'Blog Post' in response.data
            
            # Verify form was configured correctly
            assert mock_form.source == "note test-note"
            
            mock_render.assert_called_once_with("local/notebook.html",
                                              toshow="local/notes/test-note.html",
                                              form=mock_form,
                                              message=None,
                                              admin_group_name=SSK_ADMIN_GROUP)


def test_blog_open_exception(app, client):
    """Test the /ssk/blog/<note> route when exception occurs"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=False), \
             patch('ssk.blueprints.home.ContactForm', side_effect=Exception("Template error")), \
             patch('ssk.blueprints.home.WebGate.render_notfound', return_value='<html>Not Found</html>') as mock_notfound, \
             patch.object(current_app.logger, 'error') as mock_logger:
            
            response = client.get('/ssk/blog/invalid-note')
            
            assert response.status_code == 200
            assert b'Not Found' in response.data
            mock_notfound.assert_called_once()
            mock_logger.assert_called_once()


def test_blog_closed(app, client):
    """Test the /ssk/blog/<note> route when website is closed"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=True), \
             patch('ssk.blueprints.home.WebGate.render_closed', return_value='<html>Closed</html>') as mock_render:
            
            response = client.get('/ssk/blog/test-note')
            
            assert response.status_code == 200
            assert b'Closed' in response.data
            mock_render.assert_called_once()


def test_blog_posts_open(app, client):
    """Test the /ssk/blog_posts route when website is open"""
    with app.app_context():
        mock_csv_data = "id,note,title,subtitle,created,labels\n1,note1,Title 1,Subtitle 1,2024-01-01,tag1\n2,note2,Title 2,Subtitle 2,2024-01-02,tag2"
        
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=False), \
             patch('builtins.open', mock_open(read_data=mock_csv_data)), \
             patch('ssk.blueprints.home.render_template', return_value='<html>All Posts</html>') as mock_render:
            
            current_app.jinja_loader = Mock()
            current_app.jinja_loader.searchpath = ['/fake/template/path']
            
            response = client.get('/ssk/blog_posts')
            
            assert response.status_code == 200
            assert b'All Posts' in response.data
            
            # Verify multiple posts were parsed correctly
            call_args = mock_render.call_args
            posts = call_args[1]['posts']
            assert len(posts) == 2
            assert posts[0]['note'] == 'note1'
            assert posts[1]['note'] == 'note2'


def test_blog_posts_closed(app, client):
    """Test the /ssk/blog_posts route when website is closed"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=True), \
             patch('ssk.blueprints.home.WebGate.render_closed', return_value='<html>Closed</html>') as mock_render:
            
            response = client.get('/ssk/blog_posts')
            
            assert response.status_code == 200
            assert b'Closed' in response.data
            mock_render.assert_called_once()


def test_tasks_action_post(app, client):
    """Test the /ssk/tasks_action POST route"""
    with app.app_context():
        with patch('ssk.blueprints.home_handler.HomeHandler.tasks_action', 
                   return_value=('ssk/tasks.html', [{'tid': '456', 'name': 'Updated Task'}])) as mock_tasks_action, \
             patch('ssk.blueprints.home.render_template', return_value='<html>Updated Tasks</html>') as mock_render:
            
            response = client.post('/ssk/tasks_action', data={'action': 'stop', 'task_id': '123'})
            
            assert response.status_code == 200
            assert b'Updated Tasks' in response.data
            
            # Verify the handler was called with the request
            mock_tasks_action.assert_called_once()
            mock_render.assert_called_once_with("ssk/tasks.html", 
                                              tasks=[{'tid': '456', 'name': 'Updated Task'}], 
                                              admin_group_name=SSK_ADMIN_GROUP)


def test_task_log_download_exists(app, client):
    """Test the /ssk/task_log_download/<tid> route when log file exists"""
    with app.app_context():
        with patch('ssk.blueprints.home.get_logic') as mock_get_logic, \
             patch('os.path.exists', return_value=True), \
             patch('ssk.blueprints.home.send_file') as mock_send_file:
            
            mock_job_mgr = Mock()
            mock_job_mgr.get_logfile.return_value = '/path/to/logfile.txt'
            mock_get_logic.return_value.get_job_mgr.return_value = mock_job_mgr
            
            from flask import Response
            mock_response = Response(b'log content', status=200)
            mock_send_file.return_value = mock_response
            
            response = client.get('/ssk/task_log_download/task123')
            
            assert response.status_code == 200
            mock_job_mgr.get_logfile.assert_called_once_with('task123')
            mock_send_file.assert_called_once_with('/path/to/logfile.txt', as_attachment=True)


def test_task_log_download_not_exists(app, client):
    """Test the /ssk/task_log_download/<tid> route when log file doesn't exist"""
    with app.app_context():
        with patch('ssk.blueprints.home.get_logic') as mock_get_logic, \
             patch('os.path.exists', return_value=False):
            
            mock_job_mgr = Mock()
            mock_job_mgr.get_logfile.return_value = '/path/to/nonexistent.txt'
            mock_get_logic.return_value.get_job_mgr.return_value = mock_job_mgr
            
            response = client.get('/ssk/task_log_download/task123')
            
            # Should return 500 error because function returns None (this is a bug in the original code)
            assert response.status_code == 500


def test_task_log_download_no_logfile(app, client):
    """Test the /ssk/task_log_download/<tid> route when no logfile is returned"""
    with app.app_context():
        with patch('ssk.blueprints.home.get_logic') as mock_get_logic:
            
            mock_job_mgr = Mock()
            mock_job_mgr.get_logfile.return_value = None
            mock_get_logic.return_value.get_job_mgr.return_value = mock_job_mgr
            
            response = client.get('/ssk/task_log_download/task123')
            
            # Should return 500 error because function returns None (this is a bug in the original code)
            assert response.status_code == 500


def test_progress_stream(app, client):
    """Test the /ssk/progress/<thread_id> route for server-sent events"""
    with app.app_context():
        with patch('ssk.blueprints.home.get_logic') as mock_get_logic:
            
            mock_job_mgr = Mock()
            mock_job_mgr.get_progress.return_value = 75
            mock_get_logic.return_value.get_job_mgr.return_value = mock_job_mgr
            
            response = client.get('/ssk/progress/thread123')
            
            assert response.status_code == 200
            assert response.mimetype == 'text/event-stream'
            assert b'data:75' in response.data
            mock_job_mgr.get_progress.assert_called_once_with('thread123')


def test_about_open(app, client):
    """Test the /ssk/about route when website is open"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=False), \
             patch('ssk.blueprints.home.ContactForm') as mock_form_class, \
             patch('ssk.blueprints.home.render_template', return_value='<html>About Page</html>') as mock_render:
            
            mock_form = Mock()
            mock_form_class.return_value = mock_form
            
            response = client.get('/ssk/about')
            
            assert response.status_code == 200
            assert b'About Page' in response.data
            
            # Verify form was configured correctly
            assert mock_form.source == "about"
            
            mock_render.assert_called_once_with("ssk/about.html", 
                                              form=mock_form, 
                                              message=None, 
                                              admin_group_name=SSK_ADMIN_GROUP)


def test_about_closed(app, client):
    """Test the /ssk/about route when website is closed"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=True), \
             patch('ssk.blueprints.home.WebGate.render_closed', return_value='<html>Closed</html>') as mock_render:
            
            response = client.get('/ssk/about')
            
            assert response.status_code == 200
            assert b'Closed' in response.data
            mock_render.assert_called_once()


def test_post_contact_open(app, client):
    """Test the /ssk/post_contact POST route when website is open"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=False), \
             patch('ssk.blueprints.home_handler.HomeHandler.post_contact', 
                   return_value=('ssk/about.html', ContactForm(), 'Thank you for your message')) as mock_post_contact, \
             patch('ssk.blueprints.home.render_template', return_value='<html>Contact Response</html>') as mock_render:
            
            response = client.post('/ssk/post_contact', data={
                'name': 'John Doe',
                'email': 'john@example.com',
                'message': 'Test message',
                'source': 'about'
            })
            
            assert response.status_code == 200
            assert b'Contact Response' in response.data
            
            mock_post_contact.assert_called_once()
            mock_render.assert_called_once()
            
            # Verify render_template call arguments
            call_args = mock_render.call_args
            assert call_args[0][0] == 'ssk/about.html'
            assert call_args[1]['message'] == 'Thank you for your message'
            assert call_args[1]['admin_group_name'] == SSK_ADMIN_GROUP


def test_post_contact_closed(app, client):
    """Test the /ssk/post_contact POST route when website is closed"""
    with app.app_context():
        with patch('ssk.blueprints.home.WebGate.is_closed', return_value=True), \
             patch('ssk.blueprints.home.WebGate.render_closed', return_value='<html>Closed</html>') as mock_render:
            
            response = client.post('/ssk/post_contact', data={
                'name': 'John Doe',
                'email': 'john@example.com',
                'message': 'Test message'
            })
            
            assert response.status_code == 200
            assert b'Closed' in response.data
            mock_render.assert_called_once()




