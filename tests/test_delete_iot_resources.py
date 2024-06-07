"""Test the delete_iot_resources script."""

import sys

import boto3
import pytest
from botocore.stub import Stubber

from resourcemanagement import delete_iot_resources


@pytest.fixture
def delete_iot_resources_stub(monkeypatch):
    """Example fixture for mocking aws iot client."""
    iot = boto3.client("iot", "eu-west-2")
    iot_stubber = Stubber(iot)

    iot_stubber.add_response(
        method="list_things_in_thing_group",
        service_response={
            "things": [
                "string",
            ],
        },
    )
    iot_stubber.add_response(
        method="list_thing_principals",
        service_response={
            "principals": [
                "string",
            ],
            "nextToken": "string",
        },
    )
    iot_stubber.add_response(
        method="detach_thing_principal",
        service_response={},
    )
    iot_stubber.add_response(
        method="delete_thing",
        service_response={},
    )
    iot_stubber.add_response(
        method="delete_thing_group",
        service_response={},
    )
    iot_stubber.activate()
    monkeypatch.setattr(boto3, "client", lambda *_: iot)


@pytest.mark.usefixtures("delete_iot_resources_stub")
def test_delete_iot_resources(monkeypatch):
    """Test the script that deletes resources on the IoT Core service."""
    # When
    monkeypatch.setattr(
        sys,
        "argv",
        [
            sys.argv[0],
            "eu-west-2",
            "my-group-name",
        ],
    )

    # Then
    delete_iot_resources.main()


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
