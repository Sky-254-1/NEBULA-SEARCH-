"""Tests for services.analytics_background — 169 lines, 0% covered."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from datetime import datetime


class TestAnalyticsBackgroundFunctions:
    @patch("app.services.analytics_background.connect", new_callable=AsyncMock)
    async def test_get_db(self, mock_connect):
        from app.services.analytics_background import _get_db
        mock_db = AsyncMock()
        mock_connect.return_value = mock_db
        result = await _get_db()
        assert result is mock_db

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_aggregate_hourly_stats(self, mock_get_db):
        from app.services.analytics_background import aggregate_hourly_stats
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        with patch("app.services.analytics_background.AnalyticsService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.aggregate_hourly = AsyncMock()
            mock_svc_cls.return_value = mock_svc
            await aggregate_hourly_stats()
            mock_svc.aggregate_hourly.assert_awaited_once()
            mock_db.close.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_aggregate_hourly_stats_error(self, mock_get_db):
        from app.services.analytics_background import aggregate_hourly_stats
        mock_get_db.side_effect = Exception("db error")
        await aggregate_hourly_stats()  # should not raise

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_aggregate_daily_stats(self, mock_get_db):
        from app.services.analytics_background import aggregate_daily_stats
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        with patch("app.services.analytics_background.AnalyticsService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.aggregate_daily = AsyncMock()
            mock_svc_cls.return_value = mock_svc
            await aggregate_daily_stats()
            mock_svc.aggregate_daily.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_aggregate_weekly_stats(self, mock_get_db):
        from app.services.analytics_background import aggregate_weekly_stats
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        with patch("app.services.analytics_background.AnalyticsService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.aggregate_weekly = AsyncMock()
            mock_svc_cls.return_value = mock_svc
            await aggregate_weekly_stats()
            mock_svc.aggregate_weekly.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_aggregate_monthly_stats(self, mock_get_db):
        from app.services.analytics_background import aggregate_monthly_stats
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        with patch("app.services.analytics_background.AnalyticsService") as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.aggregate_monthly = AsyncMock()
            mock_svc_cls.return_value = mock_svc
            await aggregate_monthly_stats()
            mock_svc.aggregate_monthly.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_compute_trending_searches_sqlite(self, mock_get_db):
        from app.services.analytics_background import compute_trending_searches
        mock_db = AsyncMock()
        mock_db.fetchall = AsyncMock(return_value=[
            {"query": "python", "count": 10},
            {"query": "javascript", "count": 5},
        ])
        mock_db.execute = AsyncMock()
        mock_get_db.return_value = mock_db

        with patch("app.config.get_settings") as mock_gs:
            mock_settings = MagicMock()
            mock_settings.uses_postgres = False
            mock_gs.return_value = mock_settings
            await compute_trending_searches()
            assert mock_db.execute.await_count == 2
            mock_db.close.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_compute_trending_searches_postgres(self, mock_get_db):
        from app.services.analytics_background import compute_trending_searches
        mock_db = AsyncMock()
        mock_db.fetchall = AsyncMock(return_value=[{"query": "ai", "count": 20}])
        mock_db.execute = AsyncMock()
        mock_get_db.return_value = mock_db

        with patch("app.config.get_settings") as mock_gs:
            mock_settings = MagicMock()
            mock_settings.uses_postgres = True
            mock_gs.return_value = mock_settings
            await compute_trending_searches()
            mock_db.execute.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_compute_trending_error(self, mock_get_db):
        from app.services.analytics_background import compute_trending_searches
        mock_get_db.side_effect = Exception("fail")
        await compute_trending_searches()  # should not raise

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_refresh_analytics_cache_no_redis(self, mock_get_db):
        from app.services.analytics_background import refresh_analytics_cache
        with patch("app.services.cache.cache_service") as mock_cache:
            mock_cache._redis = None
            await refresh_analytics_cache()
            mock_get_db.assert_not_awaited()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_refresh_analytics_cache_with_redis(self, mock_get_db):
        from app.services.analytics_background import refresh_analytics_cache
        mock_db = AsyncMock()
        mock_get_db.return_value = mock_db
        with patch("app.services.cache.cache_service") as mock_cache:
            mock_cache._redis = MagicMock()  # Redis is available
            with patch("app.services.analytics_background.AnalyticsService") as mock_svc_cls:
                mock_svc = MagicMock()
                mock_svc.get_popular = AsyncMock()
                mock_svc.get_dashboard = AsyncMock()
                mock_svc_cls.return_value = mock_svc
                await refresh_analytics_cache()
                mock_svc.get_popular.assert_awaited_once()
                mock_svc.get_dashboard.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_refresh_analytics_cache_error(self, mock_get_db):
        from app.services.analytics_background import refresh_analytics_cache
        with patch("app.services.cache.cache_service") as mock_cache:
            mock_cache._redis = MagicMock()
            mock_get_db.side_effect = Exception("err")
            await refresh_analytics_cache()  # should not raise

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_archive_old_analytics(self, mock_get_db):
        from app.services.analytics_background import archive_old_analytics
        mock_db = AsyncMock()
        mock_db.fetchone = AsyncMock(return_value={"count": 100})
        mock_get_db.return_value = mock_db
        await archive_old_analytics(days=30)
        mock_db.fetchone.assert_awaited_once()
        mock_db.close.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_archive_old_analytics_zero_count(self, mock_get_db):
        from app.services.analytics_background import archive_old_analytics
        mock_db = AsyncMock()
        mock_db.fetchone = AsyncMock(return_value={"count": 0})
        mock_get_db.return_value = mock_db
        await archive_old_analytics()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_archive_old_analytics_error(self, mock_get_db):
        from app.services.analytics_background import archive_old_analytics
        mock_get_db.side_effect = Exception("fail")
        await archive_old_analytics()  # should not raise

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_cleanup_expired_logs(self, mock_get_db):
        from app.services.analytics_background import cleanup_expired_logs
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock()
        mock_db.commit = AsyncMock()
        mock_get_db.return_value = mock_db
        await cleanup_expired_logs(days=60)
        mock_db.execute.assert_awaited_once()
        mock_db.commit.assert_awaited_once()
        mock_db.close.assert_awaited_once()

    @patch("app.services.analytics_background._get_db", new_callable=AsyncMock)
    async def test_cleanup_expired_logs_error(self, mock_get_db):
        from app.services.analytics_background import cleanup_expired_logs
        mock_get_db.side_effect = Exception("fail")
        await cleanup_expired_logs()  # should not raise


class TestAnalyticsBackgroundWorker:
    async def test_start_stop(self):
        from app.services.analytics_background import AnalyticsBackgroundWorker
        worker = AnalyticsBackgroundWorker()
        assert worker._running is False
        assert worker._task is None

        with patch.object(worker, "_run", new_callable=AsyncMock):
            await worker.start()
            assert worker._running is True
            assert worker._task is not None

            # Starting again is no-op
            await worker.start()
            await worker.stop()
            assert worker._running is False

    async def test_stop_without_start(self):
        from app.services.analytics_background import AnalyticsBackgroundWorker
        worker = AnalyticsBackgroundWorker()
        await worker.stop()  # should not raise

    async def test_start_stop_analytics_worker(self):
        from app.services.analytics_background import (
            start_analytics_worker,
            stop_analytics_worker,
            _analytics_worker,
        )
        with patch.object(_analytics_worker, "start", new_callable=AsyncMock) as mock_start:
            await start_analytics_worker()
            mock_start.assert_awaited_once()

        with patch.object(_analytics_worker, "stop", new_callable=AsyncMock) as mock_stop:
            await stop_analytics_worker()
            mock_stop.assert_awaited_once()
