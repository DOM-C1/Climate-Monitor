import pytest
from unittest.mock import Mock, patch
from psycopg2 import OperationalError
from pandas import DataFrame
import asyncio

import report


@pytest.fixture
def mock_env():
    """Fixture to mock environment variables."""
    with patch.dict(report.ENV, {
        'AWS_KEY': 'fake_key',
        'AWS_SKEY': 'fake_secret',
        'DB_USER': 'user',
        'DB_PASSWORD': 'password',
        'DB_HOST': 'localhost',
        'DB_PORT': '5432',
        'DB_NAME': 'forecast_db'
    }):
        yield


@pytest.fixture
def mock_db_connection():
    """Fixture to mock database connection."""
    with patch('daily_report.connect') as mock_connect:
        yield mock_connect


@pytest.mark.asyncio
async def test_send_email_success(mock_aioboto3_session):
    """Test sending an email successfully."""
    mock_aioboto3_session.send_email.return_value = asyncio.Future()
    mock_aioboto3_session.send_email.return_value.set_result(
        {'MessageId': '12345'})
    await report.send_email(mock_aioboto3_session, "<p>Hello, World!</p>", "user@example.com")
    mock_aioboto3_session.send_email.assert_called_once()


def test_get_db_connection_success(mock_env, mock_db_connection):
    """Test successful database connection."""
    report.get_db_connection(daily_report.ENV)
    mock_db_connection.assert_called_once_with(
        user='user',
        password='password',
        host='localhost',
        port='5432',
        database='forecast_db'
    )


def test_get_db_connection_failure(mock_env):
    """Test failure in database connection."""
    with patch('daily_report.connect', side_effect=OperationalError):
        with pytest.raises(OperationalError):
            report.get_db_connection(report.ENV)


def test_execute_query():
    """Test execute query function."""
    conn = Mock()
    cur = conn.cursor.return_value.__enter__.return_value
    cur.fetchall.return_value = [('data',)]
    cur.description = [('column',)]
    result = report.execute_query(conn, "SELECT * FROM table")
    assert type(result) is DataFrame
    assert 'column' in result.columns
    assert result.at[0, 'column'] == 'data'


@pytest.mark.asyncio
async def test_main(mock_env, mock_db_connection, mock_aioboto3_session):
    """Test the main function with mocked dependencies."""
    with patch('daily_report.prepare_data_frame', return_value=DataFrame({'email': ['user@example.com']})):
        with patch('daily_report.format_forecast_report', side_effect=lambda df, email: asyncio.Future()):
            await report.main()
            assert mock_aioboto3_session.send_email.called
