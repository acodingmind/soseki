#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from datetime import datetime, timedelta
from unittest.mock import patch
from ssk.blueprints.admin_handler import AdminHandler
from ssk import SSK_ADMIN_GROUP, AppSettings, get_db
from ssk.models.status import Status
from ssk.models.stats import Stats
from ssk.models.db_stats import DBStats
import unittest.mock as mock


@mock.patch('flask_login.utils._get_user')
def run_system_chart_with_data(current_user):
    """Test system chart with actual status data"""
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(
        is_authenticated=True,
        is_anonymous=False,
        **attrs
    )
    current_user.return_value.is_admin.return_value = True
    
    # Create some test status data
    session = get_db().session
    now = datetime.now()
    for i in range(5):
        status = Status(
            created=now - timedelta(minutes=i*10),
            response_time=100 + i*10,
            mem=500 + i*50,
            users_active=i+1
        )
        session.add(status)
    session.commit()
    
    my_file, my_chart_data = AdminHandler.system_chart()
    
    assert my_file == AdminHandler.PAGE_SYSTEM_CHART
    assert 'labels' in my_chart_data
    assert 'datasets' in my_chart_data
    assert len(my_chart_data['datasets']) == 3
    # Verify datasets have correct labels
    dataset_labels = [ds['label'] for ds in my_chart_data['datasets']]
    assert 'Response Times' in dataset_labels
    assert 'Memory' in dataset_labels
    assert 'Users' in dataset_labels


@mock.patch('flask_login.utils._get_user')
def run_system_chart_closed(current_user):
    """Test system chart when system is closed"""
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(
        is_authenticated=True,
        is_anonymous=False,
        **attrs
    )
    current_user.return_value.is_admin.return_value = True
    
    # Mock LOGIN_OFF setting to True
    with patch.object(AppSettings, 'get_setting', return_value=True):
        my_file, my_chart_data = AdminHandler.system_chart()
        
        assert my_file == AdminHandler.PAGE_CLOSED
        assert my_chart_data == {"labels": [], "datasets": [{}, {}, {}]}


@mock.patch('flask_login.utils._get_user')
def run_system_stats_with_data(current_user):
    """Test system stats with actual data"""
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(
        is_authenticated=True,
        is_anonymous=False,
        **attrs
    )
    current_user.return_value.is_admin.return_value = True
    
    # Create test DB stats
    session = get_db().session
    now = datetime.now()
    db_stat = DBStats(
        created=now,
        table='test_table',
        counter=100
    )
    session.add(db_stat)
    
    # Create test page stats
    page_stat = Stats(
        path='/test',
        day=now.strftime('%Y-%m-%d'),
        hits=50,
        mean_response_time=250.0
    )
    session.add(page_stat)
    session.commit()
    
    my_file, my_stats = AdminHandler.system_stats()
    
    assert my_file == AdminHandler.PAGE_SYSTEM_STATS
    assert len(my_stats.keys()) == 8
    assert 'plot' in my_stats
    assert 'stats' in my_stats
    assert 'perf' in my_stats
    assert 'all_pages' in my_stats
    assert 'all_days' in my_stats
    assert 'db_stats' in my_stats
    assert 'db_tables' in my_stats
    assert 'db_days' in my_stats
    
    # Verify plot structure
    plot = my_stats['plot']
    assert 'labels' in plot
    assert 'datasets' in plot
    assert len(plot['datasets']) == 1
    assert plot['datasets'][0]['label'] == 'Response Time'


@mock.patch('flask_login.utils._get_user')
def run_system_stats_closed(current_user):
    """Test system stats when system is closed"""
    attrs = {
        'id': 1,
        'email': 'admin@soseki.io',
        'name': 'Soseki Admin',
        'roles': [SSK_ADMIN_GROUP]
    }
    current_user.return_value = mock.Mock(
        is_authenticated=True,
        is_anonymous=False,
        **attrs
    )
    current_user.return_value.is_admin.return_value = True
    
    # Mock LOGIN_OFF setting to True
    with patch.object(AppSettings, 'get_setting', return_value=True):
        my_file, my_stats = AdminHandler.system_stats()
        
        assert my_file == AdminHandler.PAGE_CLOSED
        assert my_stats == {"labels": [], "datasets": [{}, {}, {}]}





def test_system_chart_with_data(app):
    """Test system chart generation with actual data"""
    with app.app_context():
        run_system_chart_with_data()


def test_system_chart_closed(app):
    """Test system chart when system is closed"""
    with app.app_context():
        run_system_chart_closed()


def test_system_stats_with_data(app):
    """Test system stats with real data"""
    with app.app_context():
        run_system_stats_with_data()


def test_system_stats_closed(app):
    """Test system stats when system is closed"""
    with app.app_context():
        run_system_stats_closed()


