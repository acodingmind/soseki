#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import pytest
from unittest.mock import patch, Mock
from wtforms import ValidationError
from flask import current_app

from ssk.forms.contact_form import ContactForm
from ssk.forms.user_edit import EditUserProfileForm
from ssk.forms.validators import (
    password_validator, 
    unique_username_validator, 
    unique_email_validator
)


class TestContactForm:
    """Test suite for ContactForm"""
    
    def test_contact_form_creation(self, app):
        """Test ContactForm can be created successfully"""
        with app.app_context():
            form = ContactForm()
            
            # Verify all fields exist
            assert hasattr(form, 'name')
            assert hasattr(form, 'email')
            assert hasattr(form, 'message')
            assert hasattr(form, 'submit')
            assert hasattr(form, 'source')
            
            # Verify field types
            from wtforms import StringField, TextAreaField, SubmitField, HiddenField
            assert isinstance(form.name, StringField)
            assert isinstance(form.email, StringField)
            assert isinstance(form.message, TextAreaField)
            assert isinstance(form.submit, SubmitField)
            assert isinstance(form.source, HiddenField)
    
    def test_contact_form_valid_data(self, app):
        """Test ContactForm validation with valid data"""
        with app.app_context():
            form_data = {
                'name': 'John Doe',
                'email': 'john@example.com',
                'message': 'This is a test message',
                'source': 'about'
            }
            
            form = ContactForm(data=form_data)
            assert form.validate() is True
            assert len(form.errors) == 0
    
    def test_contact_form_missing_name(self, app):
        """Test ContactForm validation with missing name"""
        with app.app_context():
            form_data = {
                'name': '',
                'email': 'john@example.com',
                'message': 'This is a test message',
                'source': 'about'
            }
            
            form = ContactForm(data=form_data)
            assert form.validate() is False
            assert 'name' in form.errors
            assert 'This field is required.' in form.errors['name']
    
    def test_contact_form_missing_email(self, app):
        """Test ContactForm validation with missing email"""
        with app.app_context():
            form_data = {
                'name': 'John Doe',
                'email': '',
                'message': 'This is a test message',
                'source': 'about'
            }
            
            form = ContactForm(data=form_data)
            assert form.validate() is False
            assert 'email' in form.errors
            assert 'This field is required.' in form.errors['email']
    
    def test_contact_form_invalid_email(self, app):
        """Test ContactForm validation with invalid email format"""
        with app.app_context():
            form_data = {
                'name': 'John Doe',
                'email': 'not-an-email',
                'message': 'This is a test message',
                'source': 'about'
            }
            
            form = ContactForm(data=form_data)
            assert form.validate() is False
            assert 'email' in form.errors
            assert 'Invalid email address.' in form.errors['email']
    
    def test_contact_form_message_optional(self, app):
        """Test ContactForm validation where message is optional"""
        with app.app_context():
            form_data = {
                'name': 'John Doe',
                'email': 'john@example.com',
                'message': '',  # Empty message should be ok
                'source': 'about'
            }
            
            form = ContactForm(data=form_data)
            assert form.validate() is True
    
    def test_contact_form_field_labels(self, app):
        """Test ContactForm field labels are correct"""
        with app.app_context():
            form = ContactForm()
            
            assert form.name.label.text == 'Name'
            assert form.email.label.text == 'Email'
            assert form.message.label.text == 'Additional Information'
            assert form.submit.label.text == 'Please contact me'
            assert form.source.label.text == 'source'


class TestEditUserProfileForm:
    """Test suite for EditUserProfileForm"""
    
    def test_edit_user_form_creation(self, app):
        """Test EditUserProfileForm can be created successfully"""
        with app.app_context():
            form = EditUserProfileForm()
            
            # Verify all fields exist
            assert hasattr(form, 'id')
            assert hasattr(form, 'username')
            assert hasattr(form, 'first_name')
            assert hasattr(form, 'last_name')
            assert hasattr(form, 'email')
            assert hasattr(form, 'active')
            assert hasattr(form, 'new_password')
            assert hasattr(form, 'retype_password')
            assert hasattr(form, 'submit')
            
            # Verify field types
            from wtforms import (StringField, HiddenField, BooleanField, 
                               PasswordField, SubmitField)
            assert isinstance(form.id, HiddenField)
            assert isinstance(form.username, StringField)
            assert isinstance(form.first_name, StringField)
            assert isinstance(form.last_name, StringField)
            assert isinstance(form.email, StringField)
            assert isinstance(form.active, BooleanField)
            assert isinstance(form.new_password, PasswordField)
            assert isinstance(form.retype_password, PasswordField)
            assert isinstance(form.submit, SubmitField)
    
    def test_edit_user_form_valid_data(self, app):
        """Test EditUserProfileForm validation with valid data"""
        with app.app_context():
            # Mock the validators to avoid database dependencies
            with patch('ssk.forms.user_edit.unique_username_validator'), \
                 patch('ssk.forms.user_edit.unique_email_validator'), \
                 patch('ssk.forms.user_edit.password_validator'):
                
                form_data = {
                    'id': '1',
                    'username': 'testuser',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john@example.com',
                    'active': True,
                    'new_password': '',  # Empty password should be ok
                    'retype_password': ''
                }
                
                form = EditUserProfileForm(data=form_data)
                assert form.validate() is True
    
    def test_edit_user_form_missing_required_fields(self, app):
        """Test EditUserProfileForm validation with missing required fields"""
        with app.app_context():
            with patch('ssk.forms.user_edit.unique_username_validator'), \
                 patch('ssk.forms.user_edit.unique_email_validator'), \
                 patch('ssk.forms.user_edit.password_validator'):
                
                form_data = {
                    'id': '1',
                    'username': '',  # Required
                    'first_name': '',  # Required
                    'last_name': '',  # Required
                    'email': '',  # Required
                    'active': False,
                    'new_password': '',
                    'retype_password': ''
                }
                
                form = EditUserProfileForm(data=form_data)
                assert form.validate() is False
                assert 'username' in form.errors
                assert 'first_name' in form.errors
                assert 'last_name' in form.errors
                assert 'email' in form.errors
    
    def test_edit_user_form_invalid_email(self, app):
        """Test EditUserProfileForm validation with invalid email"""
        with app.app_context():
            with patch('ssk.forms.user_edit.unique_username_validator'), \
                 patch('ssk.forms.user_edit.unique_email_validator'), \
                 patch('ssk.forms.user_edit.password_validator'):
                
                form_data = {
                    'id': '1',
                    'username': 'testuser',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'not-a-valid-email',
                    'active': True,
                    'new_password': '',
                    'retype_password': ''
                }
                
                form = EditUserProfileForm(data=form_data)
                assert form.validate() is False
                assert 'email' in form.errors
    
    def test_edit_user_form_password_mismatch(self, app):
        """Test EditUserProfileForm validation with password mismatch"""
        with app.app_context():
            with patch('ssk.forms.user_edit.unique_username_validator'), \
                 patch('ssk.forms.user_edit.unique_email_validator'), \
                 patch('ssk.forms.user_edit.password_validator'):
                
                form_data = {
                    'id': '1',
                    'username': 'testuser',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'john@example.com',
                    'active': True,
                    'new_password': 'password123',
                    'retype_password': 'different_password'
                }
                
                form = EditUserProfileForm(data=form_data)
                assert form.validate() is False
                assert 'retype_password' in form.errors
                assert 'New Password and Retype Password did not match' in form.errors['retype_password']
    
    def test_edit_user_form_field_labels(self, app):
        """Test EditUserProfileForm field labels are correct"""
        with app.app_context():
            form = EditUserProfileForm()
            
            assert form.id.label.text == 'id'
            assert form.username.label.text == 'Username'
            assert form.first_name.label.text == 'First name'
            assert form.last_name.label.text == 'Last name'
            assert form.email.label.text == 'Email'
            assert form.active.label.text == 'Active'
            assert form.new_password.label.text == 'New Password'
            assert form.retype_password.label.text == 'Retype New Password'
            assert form.submit.label.text == 'Save'


class TestValidators:
    """Test suite for form validators"""
    
    def test_password_validator_empty_password(self, app):
        """Test password_validator with empty password (should pass)"""
        with app.app_context():
            form = Mock()
            field = Mock()
            field.data = ""
            
            # Should return True for empty password (no exception raised)
            result = password_validator(form, field)
            assert result is True
    
    def test_password_validator_with_password(self, app):
        """Test password_validator with actual password"""
        with app.app_context():
            # Mock current_app.user_manager.password_validator
            mock_user_manager = Mock()
            current_app.user_manager = mock_user_manager
            
            form = Mock()
            field = Mock()
            field.data = "testpassword123"
            
            # Should call user_manager.password_validator
            password_validator(form, field)
            mock_user_manager.password_validator.assert_called_once_with(form, field)
    
    def test_unique_username_validator_same_username(self, app):
        """Test unique_username_validator when user keeps same username"""
        with app.app_context():
            # Mock User model and form
            with patch('ssk.models.user.User') as MockUser:
                mock_user = Mock()
                mock_user.username = 'existing_user'
                MockUser.get_by_id.return_value = mock_user
                
                form = Mock()
                form.id.data = '123'
                field = Mock()
                field.data = 'existing_user'  # Same as current username
                
                # Should not raise ValidationError
                unique_username_validator(form, field)
                MockUser.get_by_id.assert_called_once_with('123')
    
    def test_unique_username_validator_new_available_username(self, app):
        """Test unique_username_validator with new available username"""
        with app.app_context():
            with patch('ssk.models.user.User') as MockUser:
                # Mock current user
                mock_current_user = Mock()
                mock_current_user.username = 'old_username'
                MockUser.get_by_id.return_value = mock_current_user
                
                # Mock that new username doesn't exist
                MockUser.get_by_name.return_value = None
                
                form = Mock()
                form.id.data = '123'
                field = Mock()
                field.data = 'new_username'
                
                # Should not raise ValidationError
                unique_username_validator(form, field)
                MockUser.get_by_name.assert_called_once_with('new_username')
    
    def test_unique_username_validator_username_taken(self, app):
        """Test unique_username_validator with taken username"""
        with app.app_context():
            with patch('ssk.models.user.User') as MockUser:
                # Mock current user
                mock_current_user = Mock()
                mock_current_user.username = 'old_username'
                MockUser.get_by_id.return_value = mock_current_user
                
                # Mock that new username already exists
                mock_existing_user = Mock()
                MockUser.get_by_name.return_value = mock_existing_user
                
                form = Mock()
                form.id.data = '123'
                field = Mock()
                field.data = 'taken_username'
                
                # Should raise ValidationError
                with pytest.raises(ValidationError) as exc_info:
                    unique_username_validator(form, field)
                
                assert 'This Username is already in use. Please try another one.' in str(exc_info.value)
    
    def test_unique_email_validator_same_email(self, app):
        """Test unique_email_validator when user keeps same email"""
        with app.app_context():
            with patch('ssk.models.user.User') as MockUser:
                mock_user = Mock()
                mock_user.email = 'user@example.com'
                MockUser.get_by_id.return_value = mock_user
                
                form = Mock()
                form.id.data = '123'
                field = Mock()
                field.data = 'user@example.com'  # Same as current email
                
                # Should not raise ValidationError
                unique_email_validator(form, field)
                MockUser.get_by_id.assert_called_once_with('123')
    
    def test_unique_email_validator_new_available_email(self, app):
        """Test unique_email_validator with new available email"""
        with app.app_context():
            with patch('ssk.models.user.User') as MockUser:
                # Mock current user
                mock_current_user = Mock()
                mock_current_user.email = 'old@example.com'
                MockUser.get_by_id.return_value = mock_current_user
                
                # Mock that new email doesn't exist
                MockUser.get_by_email.return_value = None
                
                form = Mock()
                form.id.data = '123'
                field = Mock()
                field.data = 'new@example.com'
                
                # Should not raise ValidationError
                unique_email_validator(form, field)
                MockUser.get_by_email.assert_called_once_with('new@example.com')
    
    def test_unique_email_validator_email_taken(self, app):
        """Test unique_email_validator with taken email"""
        with app.app_context():
            with patch('ssk.models.user.User') as MockUser:
                # Mock current user
                mock_current_user = Mock()
                mock_current_user.email = 'old@example.com'
                MockUser.get_by_id.return_value = mock_current_user
                
                # Mock that new email already exists
                mock_existing_user = Mock()
                MockUser.get_by_email.return_value = mock_existing_user
                
                form = Mock()
                form.id.data = '123'
                field = Mock()
                field.data = 'taken@example.com'
                
                # Should raise ValidationError
                with pytest.raises(ValidationError) as exc_info:
                    unique_email_validator(form, field)
                
                assert 'This Email is already in use. Please try another one.' in str(exc_info.value)
    
    def test_validators_edge_cases(self, app):
        """Test validators with edge cases"""
        with app.app_context():
            # Test with None values
            with patch('ssk.models.user.User') as MockUser:
                mock_user = Mock()
                mock_user.username = None
                mock_user.email = None
                MockUser.get_by_id.return_value = mock_user
                
                form = Mock()
                form.id.data = '123'
                
                # Test username validator with None current username
                field = Mock()
                field.data = 'new_username'
                MockUser.get_by_name.return_value = None
                
                unique_username_validator(form, field)
                
                # Test email validator with None current email
                field.data = 'new@example.com'
                MockUser.get_by_email.return_value = None
                
                unique_email_validator(form, field)
    
    def test_validators_with_special_characters(self, app):
        """Test validators handle special characters properly"""
        with app.app_context():
            with patch('ssk.models.user.User') as MockUser:
                mock_user = Mock()
                mock_user.username = 'test_user'
                mock_user.email = 'test@example.com'
                MockUser.get_by_id.return_value = mock_user
                MockUser.get_by_name.return_value = None
                MockUser.get_by_email.return_value = None
                
                form = Mock()
                form.id.data = '123'
                
                # Test username with special characters
                field = Mock()
                field.data = 'user-with_special.chars'
                unique_username_validator(form, field)
                
                # Test email with special characters  
                field.data = 'user+tag@sub.domain.com'
                unique_email_validator(form, field)


class TestFormIntegration:
    """Integration tests for forms working together"""
    
    def test_contact_form_with_flask_wtf_features(self, app):
        """Test ContactForm integration with Flask-WTF features"""
        with app.app_context():
            # Test with CSRF protection (should work in app context)
            app.config['WTF_CSRF_ENABLED'] = True
            app.config['SECRET_KEY'] = 'test-secret-key-for-csrf'
            with app.test_request_context('/', method='POST'):
                form = ContactForm()
                # Form should have CSRF token field when CSRF is enabled
                assert hasattr(form, 'csrf_token')
    
    def test_edit_user_form_with_all_validators(self, app):
        """Test EditUserProfileForm with all validators working together"""
        with app.app_context():
            with patch('ssk.models.user.User') as MockUser, \
                 patch.object(current_app, 'user_manager') as mock_user_manager:
                
                # Setup mocks for successful validation
                mock_user = Mock()
                mock_user.username = 'olduser'
                mock_user.email = 'old@example.com'
                MockUser.get_by_id.return_value = mock_user
                MockUser.get_by_name.return_value = None
                MockUser.get_by_email.return_value = None
                
                form_data = {
                    'id': '1',
                    'username': 'newuser',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'email': 'new@example.com',
                    'active': True,
                    'new_password': 'newpass123',
                    'retype_password': 'newpass123'
                }
                
                form = EditUserProfileForm(data=form_data)
                assert form.validate() is True
                
                # Verify all validators were called
                MockUser.get_by_name.assert_called_once_with('newuser')
                MockUser.get_by_email.assert_called_once_with('new@example.com')
                mock_user_manager.password_validator.assert_called_once()
    
    def test_form_field_access_patterns(self, app):
        """Test common patterns of accessing form fields"""
        with app.app_context():
            # Test ContactForm field access
            contact_form = ContactForm()
            
            # Test accessing field data
            assert contact_form.name.data is None
            assert contact_form.email.data is None
            
            # Test setting field data
            contact_form.name.data = "Test User"
            contact_form.email.data = "test@example.com"
            
            assert contact_form.name.data == "Test User"
            assert contact_form.email.data == "test@example.com"
            
            # Test EditUserProfileForm field access
            edit_form = EditUserProfileForm()
            
            # Test boolean field
            assert contact_form.submit.data is False
            edit_form.active.data = True
            assert edit_form.active.data is True
