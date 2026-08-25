"""Tests for the dca_service package top-level module."""

from dca_service import hello


def test_hello_returns_expected_greeting():
    assert hello() == "Hello from dca-service!"


def test_hello_returns_string_type():
    result = hello()
    assert isinstance(result, str)


def test_hello_is_deterministic_across_calls():
    assert hello() == hello()