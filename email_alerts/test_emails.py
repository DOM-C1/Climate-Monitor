
import pytest
from datetime import datetime


from email_alert_setup import emails_to_dict, remove_unnecessary_weather_data, sort_warnings_to_email
from create_email_messages import get_alert_msg, get_alert_visual, create_html_table_weather, create_html_air_quality, create_html_flood_alerts


def test_emails_to_dict():
    """test that the emails are made into a dictionary"""
    test_data = ['email@1.com', 'email@2.com']
    output = emails_to_dict(test_data)
    assert isinstance(output, dict)
    assert output == {'email@1.com': [], 'email@2.com': []}


def test_remove_unnecessary_weather_data():

    test_data = ['weather_alert', 1, 'Alert', 'belfast',
                 'antrim', 'Wind', datetime.strptime('12:00:00', '%H:%M:%S'),
                 "Windy", datetime.strptime('12:00:00', '%H:%M:%S'),
                 12, 12, 15, 15, 0, 0, 1000, 0, 0, 'email']

    output = ['weather_alert', 1, 'Alert', 'belfast',
              'antrim', 'Wind', datetime.strptime('12:00:00', '%H:%M:%S'),
              "Windy", datetime.strptime('12:00:00', '%H:%M:%S'), 15, 15, '&#x1F32C;']

    assert remove_unnecessary_weather_data(test_data) == output


def test_sort_warnings_to_email():

    test_data1 = [['weather_alert', 1, 'Alert', 'belfast',
                  'antrim', 'Wind', datetime.strptime('12:00:00', '%H:%M:%S'),
                   "Windy", datetime.strptime('12:00:00', '%H:%M:%S'),
                   12, 12, 15, 15, 0, 0, 1000, 0, 0, 'email@1.com']]

    test_data2 = ['email@1.com']

    expected_output = {'email@1.com': [['weather_alert', 1, 'Alert', 'belfast',
                                        'antrim', 'Wind', datetime.strptime(
                                            '12:00:00', '%H:%M:%S'),
                                        "Windy", datetime.strptime('12:00:00', '%H:%M:%S'), 15, 15, '&#x1F32C;']]}

    output = sort_warnings_to_email(test_data2, test_data1)
    assert isinstance(output, dict)
    assert isinstance(output.get('email@1.com'), list)
    assert output == expected_output


@pytest.mark.parametrize("test_input1,test_input2,expected", [("Alert", 'Wind', 'Alert! Elevated Wind'),
                                                              ("Warning", 'Rain',
                                                               'Warning! High Rain'),
                                                              ("Severe Warning", 'Snowfall', 'Severe Warning! Extreme Snowfall')])
def test_get_alert_msg(test_input1, test_input2, expected):

    assert get_alert_msg(test_input1, test_input2) == expected


def test_alert_visual():

    assert get_alert_visual('Warning') == '#FF8300'


def test_create_table_weather():

    test_data = [['weather_alert', 1, 'Alert', 'belfast',
                  'antrim', 'Wind', datetime.strptime(
                      '12:00:00', '%H:%M:%S'),
                  "Windy", datetime.strptime('12:00:00', '%H:%M:%S'), 15, 15, '&#x1F32C;']]

    output = create_html_table_weather(test_data, 'weather_alert')

    assert '#f3d300' in output
    assert 'belfast' in output
    assert '<table ' in output
    assert '<tr>' in output
    assert '<td' in output
    assert '</table>' in output
    assert 'Alert! Elevated Wind' in output


def test_create_html_air_quality():

    test_data = [['air_quality', 1, 'Alert', 'belfast', 'antrim', 111]]

    output = create_html_air_quality(test_data, 'air_quality')

    assert "Elevated Pollution Levels" in output
    assert ">!</span> Alert!" in output


def test_create_html_flood_alerts():

    test_data = [['flood_warnings', 1, 'Alert', 'belfast', 'antrim',
                  datetime.strptime('12:00:00', '%H:%M:%S')]]

    output = create_html_flood_alerts(test_data, 'flood_warnings')

    assert "Alert! Elevated Risk of Flooding" in output
    assert ">!</span> Alert!" in output
    assert 'belfast - 12:00:00' in output
