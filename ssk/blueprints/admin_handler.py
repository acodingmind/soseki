#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from datetime import datetime, timedelta

from statistics import mean

from ssk import AppSettings, get_db
from ssk.utils import now


class AdminHandler(object):
    PAGE_CLOSED = "ssk/closed.html"
    PAGE_SYSTEM_CHART = "ssk/system_chart.html"
    PAGE_SYSTEM_STATS = "ssk/system_stats.html"

    @staticmethod
    def system_chart():
        my_to_plot = {"labels": [], "datasets": [{}, {}, {}]}

        if AppSettings().get_setting("LOGIN_OFF"):
            return AdminHandler.PAGE_CLOSED, my_to_plot

        from ..models.status import Status
        my_now = datetime.now()
        my_threshold = my_now - timedelta(minutes=360)
        my_session = get_db().session
        my_records = my_session.query(Status).filter(Status.created > my_threshold).order_by(Status.id.asc()).all()

        my_times = [my_tmp_item.created for my_tmp_item in my_records]
        my_res_time = [my_tmp_item.response_time for my_tmp_item in my_records]
        my_mem = [my_tmp_item.mem for my_tmp_item in my_records]
        my_users_active = [my_tmp_item.users_active for my_tmp_item in my_records]

        my_res_time_ds = {"label": "Response Times",
                          "data": my_res_time,
                          "fill": False,
                          "borderColor": 'rgba(100, 153, 255 , 0.6)',
                          }

        my_mem_ds = {"label": "Memory",
                     "data": my_mem,
                     "fill": False,
                     "borderColor": 'rgba(204, 153, 255 , 0.6)',
                     }

        my_users_ds = {"label": "Users",
                       "data": my_users_active,
                       "fill": False,
                       "borderColor": 'rgb(201, 204, 63, 0.6)',
                       }

        my_to_plot = {"labels": my_times, "datasets": [my_res_time_ds, my_mem_ds, my_users_ds]}

        return AdminHandler.PAGE_SYSTEM_CHART, my_to_plot

    @staticmethod
    def system_stats():
        my_to_plot = {"labels": [], "datasets": [{}, {}, {}]}

        if AppSettings().get_setting("LOGIN_OFF"):
            return AdminHandler.PAGE_CLOSED, my_to_plot

        my_now = now()

        my_from = my_now - timedelta(days=21)
        from ssk.models.db_stats import DBStats
        my_recent_db_stats = DBStats.get_since(my_from)

        my_db_stats = {}
        my_all_db_tables = []
        for my_tmp_db_stat in my_recent_db_stats:
            my_day = my_tmp_db_stat.created.strftime("%Y-%m-%d")

            if my_day not in my_db_stats.keys():
                my_db_stats[my_day] = {}

            my_db_stats[my_day][my_tmp_db_stat.table] = my_tmp_db_stat.counter

            if my_tmp_db_stat.table not in my_all_db_tables:
                my_all_db_tables.append(my_tmp_db_stat.table)

        my_all_db_days = list(my_db_stats.keys())

        # page stats
        from ssk.models.stats import Stats
        my_page_stats = Stats.get_all()

        my_daily_stats = {}
        my_daily_perf = {}
        my_all_pages = []
        my_all_days = []

        my_per_day = {}

        for my_tmp_stat in my_page_stats:
            if my_tmp_stat.path not in my_all_pages:
                my_all_pages.append(my_tmp_stat.path)

            if my_tmp_stat.day not in my_per_day.keys():
                my_per_day[my_tmp_stat.day] = []

            my_per_day[my_tmp_stat.day].append(my_tmp_stat.mean_response_time)

            if my_tmp_stat.day not in my_all_days:
                my_all_days.append(my_tmp_stat.day)

            if my_tmp_stat.day not in my_daily_stats.keys():
                my_daily_stats[my_tmp_stat.day] = {}
                my_daily_perf[my_tmp_stat.day] = {}

            my_daily_stats[my_tmp_stat.day][my_tmp_stat.path] = my_tmp_stat.hits
            my_daily_perf[my_tmp_stat.day][my_tmp_stat.path] = round(my_tmp_stat.mean_response_time)

            if len(my_all_days) > 21:
                break

        my_days = list(my_per_day.keys())
        my_days.reverse()
        my_labels = my_days

        my_mean_rt = []

        for my_tmp_item in my_days:
            my_all_rts = my_per_day[my_tmp_item]
            if len(my_all_rts) > 0:
                my_mean_rt.append(mean(my_all_rts))
            else:
                my_mean_rt.append(0)

        my_res_time_ds = {"label": "Response Time",
                          "data": my_mean_rt,
                          "borderColor": 'rgba(100, 153, 255 , 0.6)',
                          }

        my_to_plot = {"labels": my_labels, "datasets": [my_res_time_ds]}

        my_all_days.reverse()

        my_ret_val = {"plot": my_to_plot,
                      "stats": my_daily_stats,
                      "perf": my_daily_perf,
                      "all_pages": my_all_pages,
                      "all_days": my_all_days,
                      "db_stats": my_db_stats,
                      "db_tables": my_all_db_tables,
                      "db_days": my_all_db_days}

        return AdminHandler.PAGE_SYSTEM_STATS, my_ret_val
