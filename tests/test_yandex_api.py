import requests
from requests import exceptions
import pytest

from .. import yandex_api_connector as yac
from ..config import YANDEX_TOKEN, api_url, issue_filter


headers = {'Authorization': f'OAuth {YANDEX_TOKEN}'}

list_of_issue = [{
    'summary': 'str',
    'status': {
        'code': 'str',
        'display': 'str'
    },
    'sla': [{
        'failAt': '2017-06-11T05:16:01.339+0030',
        'warnAt': '2017-06-11T05:16:01.339+0030'
    },
        {
        'failAt': '2017-06-11T05:16:01.339+0030',
        'warnAt': '2017-06-11T05:16:01.339+0030'
        }],
}]

list_of_corrupted_issue = [{
    'summary': 'str',
    'status': {
        'code': 'str',
        'display': 'str'
    },
    'sla': [{
        'failAt': 'str',
        'warnAt': 'str'
    },
        {
        'failAt': 'str',
        'warnAt': 'str'
        }],
}]

list_of_invalid_key_issue = [{
    'name': 'str',
    'open': {
        'code': 'str',
        'display': 'str'
    },
    'sla': [{
        'burnedAt': 'str',
        'flameAt': 'str'
    },
        {
        'failAt': 'str',
        'warnAt': 'str'
        }],
}]


def test_token_check_status_code_equels_200():
    response = requests.get(api_url+'myself', headers=headers)
    assert response.status_code == 200


def test_get_heders_func():
    func_header = yac.get_headers(YANDEX_TOKEN)
    response = requests.get(api_url + 'myself', headers=func_header)
    assert response.status_code == 200


def test_get_heders_with_wrong_token():
    func_header = yac.get_headers('kawabanga')
    assert func_header is None


def test_get_issues_func():
    response = yac.get_user_issues(headers)
    assert type(response) == list

    for issue in response:
        assert issue['summary']
        assert issue['status']
        assert issue['status']['display']
        assert issue['sla']
        assert issue['sla'][-1]['failAt']
        assert issue['sla'][-1]['warnAt']


def test_valid_dict_value():
    response = yac.get_user_issues(headers)

    for issue in response:
        assert type(issue['summary']) == str
        assert type(issue['status']) == dict
        assert type(issue['status']['display']) == str
        assert type(issue['sla']) == list
        assert type(issue['sla'][-1]['failAt']) == str
        assert type(issue['sla'][-1]['warnAt']) == str


@pytest.mark.xfail(raises=AttributeError)
def test_get_issues_whith_attribute_error():
    response = yac.get_user_issues('kawabanga')
    assert response is None


@pytest.mark.xfail(raises=exceptions.InvalidHeader)
def test_get_issues_whith_requests_error():
    response = yac.get_user_issues({'kawabanga': 12})
    assert response is None


def test_get_issues_whith_invalid_token_in_headers():
    response = yac.get_user_issues({'kawabanga': '12'})
    assert response is None


def test_valid_list_issue_value():
    issue_list = yac.get_list_issues(list_of_issue)
    assert type(issue_list) == list


@pytest.mark.xfail(raises=ValueError)
def test_get_list_issues_with_corrupted_values():
    issue_list = yac.get_list_issues(list_of_corrupted_issue)


@pytest.mark.xfail(raises=KeyError)
def test_get_list_issues_with_invalid_key():
    issue_list = yac.get_list_issues(list_of_invalid_key_issue)


def test_get_list_issues_whith_empty_input():
    issue_list = yac.get_list_issues([])
    assert type(issue_list) == list


@pytest.mark.xfail(raises=KeyError)
def test_filter_issues_whith_invalid_key():
    filter_list = yac.filter_issues_by_time(list_of_invalid_key_issue)
    assert type(filter_list) == list

def test_filter_issues():
    filter_list = yac.filter_issues_by_time(list_of_issue)
    assert type(filter_list) == list


def test_get_issues():
    issues = yac.get_issues(YANDEX_TOKEN)
    assert type(issues) == list


def test_get_issues_whith_invalid_token():
    issues = yac.get_issues('kawabanga')
    assert issues is None


def test_get_latest_issues():
    issues = yac.get_latest_issues(YANDEX_TOKEN)
    assert type(issues) == list


def test_get_latest_issues_whith_invalid_token():
    issues = yac.get_latest_issues('kawabanga')
    assert issues is None
