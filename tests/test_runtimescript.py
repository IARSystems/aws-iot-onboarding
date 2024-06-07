"""Test the runtimescript."""

from contextlib import nullcontext as assert_not_raises
from io import BytesIO
from unittest.mock import MagicMock

import boto3
import pytest
from botocore.response import StreamingBody
from botocore.stub import Stubber
from jwcrypto import jws

from runtimescript import runtimescript


@pytest.fixture
def aws_stub(monkeypatch):
    """Example fixture for mocking aws iot and s3 clients."""
    iot = boto3.client("iot", "eu-west-2")
    iot_stubber = Stubber(iot)
    iot_stubber.add_response(
        method="describe_thing_group",
        service_response={
            "thingGroupName": "thing-group-name",
            "thingGroupArn": "thing-group-arn",
            "thingGroupId": "thing-group-id",
        },
    )
    iot_stubber.add_response(
        method="create_thing",
        service_response={
            "thingName": "thing-name",
            "thingArn": "thing-arn",
            "thingId": "thing-id",
        },
    )
    iot_stubber.add_response(
        method="add_thing_to_thing_group",
        service_response={},
    )
    iot_stubber.add_response(
        method="register_certificate_without_ca",
        service_response={
            "certificateId": "64-character-certificate-id-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "certificateArn": "certificate-arn",
        },
    )
    iot_stubber.add_response(
        method="attach_thing_principal",
        service_response={},
    )
    iot_stubber.add_response(
        method="list_things_in_thing_group",
        service_response={
            "things": [
                "string",
            ],
            "nextToken": "string",
        },
    )
    iot_stubber.activate()

    response_body_bytes = (
        "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpPU0UiLCJpYXQiOjE3MTUzNDcwMTAsImtpZCI6Ik9FTV"
        "9QUl9TaWduaW5nIiwiZ2lkIjoiMDMwMDAwMDBERUIwOURFQjA5REVCMDlERUIwOTAwMDAiLCJz"
        "cW4iOiIxIiwicGlkIjoiNTMxNUI2QTNDNzMxRDFCQjYxMkU0MEI5MUZBN0QwQzciLCJkZXYiOn"
        "siZGV2aWNlSUQiOiIxODAwM0IwMDEwNTEzODM0MzIzMjM1MzYiLCJkZXZpY2VDZXJ0IjoiTUlJ"
        "Q1pqQ0NBZ3FnQXdJQkFnSUthd2tBQUdZK0hqOEFBekFNQmdncWhrak9QUVFEQWdVQU1JR2FNUX"
        "N3Q1FZRFZRUUdFd0pIUWpFWE1CVUdBMVVFQ0F3T1EyRnRZbkpwWkdkbGMyaHBjbVV4RlRBVEJn"
        "TlZCQWNNREZCbGRHVnlZbTl5YjNWbmFERWdNQjRHQTFVRUNnd1hTR1ZoWkd4bGVWUmxZMmh1Yj"
        "J4dloybGxjeUJNZEdReEZqQVVCZ05WQkFzTURUUXpOVFEyTlRBd01EQXdNREl4SVRBZkJnTlZC"
        "QU1NR0RFNE1EQXpRakF3TVRBMU1UTTRNelF6TWpNeU16VXpOakFnRncweU5EQTFNVEF4TXpFMk"
        "5EZGFHQTh5TURVeE1Ea3lOakV6TVRZME4xb3dnWm94Q3pBSkJnTlZCQVlUQWtkQ01SY3dGUVlE"
        "VlFRSURBNURZVzFpY21sa1oyVnphR2x5WlRFVk1CTUdBMVVFQnd3TVVHVjBaWEppYjNKdmRXZG"
        "9NU0F3SGdZRFZRUUtEQmRJWldGa2JHVjVWR1ZqYUc1dmJHOW5hV1Z6SUV4MFpERVdNQlFHQTFV"
        "RUN3d05ORE0xTkRZMU1EQXdNREF3TWpFaE1COEdBMVVFQXd3WU1UZ3dNRE5DTURBeE1EVXhNem"
        "d6TkRNeU16SXpOVE0yTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFa095TWlu"
        "UWRCTXkxR1NxNk43MnR3YjZ6Z0tDd2J5OWdIeWloZmdraHBucGxwcUNPNnNkNE9Fc0ljTWdNZG"
        "RTeUVwaVRRcm8wb3NRVW1OTDBBZ2dpeTZNeU1EQXdEQVlEVlIwVEFRSC9CQUl3QURBTEJnTlZI"
        "UThFQkFNQ0E4Z3dFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUhBd0l3REFZSUtvWkl6ajBFQXdJRk"
        "FBTklBREJGQWlCNXJMOEd2VjFNcEJ5eVFGVUhVQ1QrNzZibzQ5QzJEdXZLQkVqL3EzdVkzQUlo"
        "QU1ZSWVFNzhjaEFGNmtwTkZRNzRhZ0t0dFBReU1EQUdSMUlOeGt0VExlazkiLCJjZXJ0UHViS2"
        "V5IjoiOTBFQzhDOEE3NDFEMDRDQ0I1MTkyQUJBMzdCREFEQzFCRUIzODBBMEIwNkYyRjYwMUYy"
        "OEExN0UwOTIxQTY3QTY1QTZBMDhFRUFDNzc4Mzg0QjA4NzBDODBDNzVENEIyMTI5ODkzNDJCQT"
        "M0QTJDNDE0OThEMkY0MDIwODIyQ0IiLCJwcm9kdWN0aW9uUmVzdWx0IjoicGFzcyJ9fQ..FKaQ"
        "ydCfpz0Ya86MUWqAEB_hRcH4IwStZvPMgUj8XwaJCo3tquRpBQA6Udzy3hWXf6qB-XVVbJ5-u-"
        "KmkZzpMw".encode()
    )

    s3 = boto3.client("s3")
    s3_stubber = Stubber(s3)
    s3_stubber.add_response(
        method="get_object",
        service_response={
            "Body": StreamingBody(BytesIO(response_body_bytes), len(response_body_bytes)),
            "ContentType": "application/json",
            "ContentLength": len(response_body_bytes),
            "ETag": '"etag"',
        },
    )
    s3_stubber.activate()

    monkeypatch.setattr(boto3, "client", MagicMock(side_effect=[s3, iot, iot, s3]))


@pytest.fixture
def ignore_post_init(monkeypatch):
    """Ignore the __post_init__ method of the ProductionRecord class which
    validates the signature, but it reads the example data from the file, so
    unless this the unit being tested, it should be ignored.
    """
    monkeypatch.setattr(runtimescript.ProductionRecord, "__post_init__", lambda x: None)


def test_signature_is_valid(monkeypatch):
    """Test that signature_is_valid does not raise an exception when
    called with mock arguments.
    """
    payload = (
        "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpPU0UiLCJpYXQiOjE3MTUzNDcwMTAsImtpZCI6Ik9FTV"
        "9QUl9TaWduaW5nIiwiZ2lkIjoiMDMwMDAwMDBERUIwOURFQjA5REVCMDlERUIwOTAwMDAiLCJz"
        "cW4iOiIxIiwicGlkIjoiNTMxNUI2QTNDNzMxRDFCQjYxMkU0MEI5MUZBN0QwQzciLCJkZXYiOn"
        "siZGV2aWNlSUQiOiIxODAwM0IwMDEwNTEzODM0MzIzMjM1MzYiLCJkZXZpY2VDZXJ0IjoiTUlJ"
        "Q1pqQ0NBZ3FnQXdJQkFnSUthd2tBQUdZK0hqOEFBekFNQmdncWhrak9QUVFEQWdVQU1JR2FNUX"
        "N3Q1FZRFZRUUdFd0pIUWpFWE1CVUdBMVVFQ0F3T1EyRnRZbkpwWkdkbGMyaHBjbVV4RlRBVEJn"
        "TlZCQWNNREZCbGRHVnlZbTl5YjNWbmFERWdNQjRHQTFVRUNnd1hTR1ZoWkd4bGVWUmxZMmh1Yj"
        "J4dloybGxjeUJNZEdReEZqQVVCZ05WQkFzTURUUXpOVFEyTlRBd01EQXdNREl4SVRBZkJnTlZC"
        "QU1NR0RFNE1EQXpRakF3TVRBMU1UTTRNelF6TWpNeU16VXpOakFnRncweU5EQTFNVEF4TXpFMk"
        "5EZGFHQTh5TURVeE1Ea3lOakV6TVRZME4xb3dnWm94Q3pBSkJnTlZCQVlUQWtkQ01SY3dGUVlE"
        "VlFRSURBNURZVzFpY21sa1oyVnphR2x5WlRFVk1CTUdBMVVFQnd3TVVHVjBaWEppYjNKdmRXZG"
        "9NU0F3SGdZRFZRUUtEQmRJWldGa2JHVjVWR1ZqYUc1dmJHOW5hV1Z6SUV4MFpERVdNQlFHQTFV"
        "RUN3d05ORE0xTkRZMU1EQXdNREF3TWpFaE1COEdBMVVFQXd3WU1UZ3dNRE5DTURBeE1EVXhNem"
        "d6TkRNeU16SXpOVE0yTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFa095TWlu"
        "UWRCTXkxR1NxNk43MnR3YjZ6Z0tDd2J5OWdIeWloZmdraHBucGxwcUNPNnNkNE9Fc0ljTWdNZG"
        "RTeUVwaVRRcm8wb3NRVW1OTDBBZ2dpeTZNeU1EQXdEQVlEVlIwVEFRSC9CQUl3QURBTEJnTlZI"
        "UThFQkFNQ0E4Z3dFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUhBd0l3REFZSUtvWkl6ajBFQXdJRk"
        "FBTklBREJGQWlCNXJMOEd2VjFNcEJ5eVFGVUhVQ1QrNzZibzQ5QzJEdXZLQkVqL3EzdVkzQUlo"
        "QU1ZSWVFNzhjaEFGNmtwTkZRNzRhZ0t0dFBReU1EQUdSMUlOeGt0VExlazkiLCJjZXJ0UHViS2"
        "V5IjoiOTBFQzhDOEE3NDFEMDRDQ0I1MTkyQUJBMzdCREFEQzFCRUIzODBBMEIwNkYyRjYwMUYy"
        "OEExN0UwOTIxQTY3QTY1QTZBMDhFRUFDNzc4Mzg0QjA4NzBDODBDNzVENEIyMTI5ODkzNDJCQT"
        "M0QTJDNDE0OThEMkY0MDIwODIyQ0IiLCJwcm9kdWN0aW9uUmVzdWx0IjoicGFzcyJ9fQ..FKaQ"
        "ydCfpz0Ya86MUWqAEB_hRcH4IwStZvPMgUj8XwaJCo3tquRpBQA6Udzy3hWXf6qB-XVVbJ5-u-"
        "KmkZzpMw"
    )

    jws_obj = jws.JWS()
    jws_obj.deserialize(payload)
    public_key = (
        "814634CCD80A05F0511CCF358415FBB8E55FBBA96D520DD0E7CE37C1AAD671884ECAAF"
        "D95879FCAD78974ABDAAB7583270B5BDF1EB3B9A7CE84F29F160E5F983"
    )

    monkeypatch.setenv("PUBLIC_KEY", public_key)

    # Given
    kwargs = {
        "device_id": "example-device-id",
        "device_cert": "example-device-cert",
        "_bucket_name": "example-bucket-name",
        "_key": "example-key",
        "_jws_obj": jws_obj,
    }

    # Then
    with assert_not_raises():
        # When
        runtimescript.ProductionRecord(**kwargs)


def test_signature_jws_obj_verify_is_called_regardless_of_instance_method():
    """This test exists so that if the signature verification is moved to the
    from_event method, the test will catch it. The signature verification
    should be called regardless of how the object is instantiated.
    """
    pytest.skip("Not implemented")


def test_lambda_handler_with_invalid_production_record_causes_create_thing_to_not_be_called():
    """Test that the lambda_handler does not call create_thing if the
    production record is invalid; The initializer will raise an exception and
    cause the function to exit.
    """
    pytest.skip("Not implemented")


@pytest.mark.usefixtures("aws_stub")
@pytest.mark.usefixtures("ignore_post_init")
def test_calling_lambda_handler_causes_no_exception(monkeypatch):
    """Test that the lambda_handler does not raise an exception when called
    with mock arguments.
    """
    # Given
    payload = (
        b"eyJhbGciOiJFUzI1NiIsInR5cCI6IkpPU0UiLCJpYXQiOjE3MTUzNDcwMTAsImtpZCI6Ik9FTV"
        b"9QUl9TaWduaW5nIiwiZ2lkIjoiMDMwMDAwMDBERUIwOURFQjA5REVCMDlERUIwOTAwMDAiLCJz"
        b"cW4iOiIxIiwicGlkIjoiNTMxNUI2QTNDNzMxRDFCQjYxMkU0MEI5MUZBN0QwQzciLCJkZXYiOn"
        b"siZGV2aWNlSUQiOiIxODAwM0IwMDEwNTEzODM0MzIzMjM1MzYiLCJkZXZpY2VDZXJ0IjoiTUlJ"
        b"Q1pqQ0NBZ3FnQXdJQkFnSUthd2tBQUdZK0hqOEFBekFNQmdncWhrak9QUVFEQWdVQU1JR2FNUX"
        b"N3Q1FZRFZRUUdFd0pIUWpFWE1CVUdBMVVFQ0F3T1EyRnRZbkpwWkdkbGMyaHBjbVV4RlRBVEJn"
        b"TlZCQWNNREZCbGRHVnlZbTl5YjNWbmFERWdNQjRHQTFVRUNnd1hTR1ZoWkd4bGVWUmxZMmh1Yj"
        b"J4dloybGxjeUJNZEdReEZqQVVCZ05WQkFzTURUUXpOVFEyTlRBd01EQXdNREl4SVRBZkJnTlZC"
        b"QU1NR0RFNE1EQXpRakF3TVRBMU1UTTRNelF6TWpNeU16VXpOakFnRncweU5EQTFNVEF4TXpFMk"
        b"5EZGFHQTh5TURVeE1Ea3lOakV6TVRZME4xb3dnWm94Q3pBSkJnTlZCQVlUQWtkQ01SY3dGUVlE"
        b"VlFRSURBNURZVzFpY21sa1oyVnphR2x5WlRFVk1CTUdBMVVFQnd3TVVHVjBaWEppYjNKdmRXZG"
        b"9NU0F3SGdZRFZRUUtEQmRJWldGa2JHVjVWR1ZqYUc1dmJHOW5hV1Z6SUV4MFpERVdNQlFHQTFV"
        b"RUN3d05ORE0xTkRZMU1EQXdNREF3TWpFaE1COEdBMVVFQXd3WU1UZ3dNRE5DTURBeE1EVXhNem"
        b"d6TkRNeU16SXpOVE0yTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFa095TWlu"
        b"UWRCTXkxR1NxNk43MnR3YjZ6Z0tDd2J5OWdIeWloZmdraHBucGxwcUNPNnNkNE9Fc0ljTWdNZG"
        b"RTeUVwaVRRcm8wb3NRVW1OTDBBZ2dpeTZNeU1EQXdEQVlEVlIwVEFRSC9CQUl3QURBTEJnTlZI"
        b"UThFQkFNQ0E4Z3dFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUhBd0l3REFZSUtvWkl6ajBFQXdJRk"
        b"FBTklBREJGQWlCNXJMOEd2VjFNcEJ5eVFGVUhVQ1QrNzZibzQ5QzJEdXZLQkVqL3EzdVkzQUlo"
        b"QU1ZSWVFNzhjaEFGNmtwTkZRNzRhZ0t0dFBReU1EQUdSMUlOeGt0VExlazkiLCJjZXJ0UHViS2"
        b"V5IjoiOTBFQzhDOEE3NDFEMDRDQ0I1MTkyQUJBMzdCREFEQzFCRUIzODBBMEIwNkYyRjYwMUYy"
        b"OEExN0UwOTIxQTY3QTY1QTZBMDhFRUFDNzc4Mzg0QjA4NzBDODBDNzVENEIyMTI5ODkzNDJCQT"
        b"M0QTJDNDE0OThEMkY0MDIwODIyQ0IiLCJwcm9kdWN0aW9uUmVzdWx0IjoicGFzcyJ9fQ..FKaQ"
        b"ydCfpz0Ya86MUWqAEB_hRcH4IwStZvPMgUj8XwaJCo3tquRpBQA6Udzy3hWXf6qB-XVVbJ5-u-"
        b"KmkZzpMw"
    )

    mock_event = MagicMock()
    _d = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "bulk-onboarding-bucket"},
                    "object": {"key": "1713531973.0.prd"},
                }
            }
        ]
    }

    mock_event.__getitem__.side_effect = _d.__getitem__
    mock_event.decode.side_effect = payload.decode
    monkeypatch.setenv("THING_GROUP_NAME", "iar-thing-group")

    # Then
    with assert_not_raises():
        # When
        runtimescript.lambda_handler(mock_event, MagicMock())


@pytest.mark.usefixtures("aws_stub")
@pytest.mark.usefixtures("ignore_post_init")
def test_instanciate_production_record_from_event_causes_production_record_object():
    """Test that process_production_record does not raise an exception when
    called with mock arguments, and that device_id/device_cert are correctly
    extracted from a ProductionRecord file.
    """
    # Given
    payload = (
        b"eyJhbGciOiJFUzI1NiIsInR5cCI6IkpPU0UiLCJpYXQiOjE3MTUzNDcwMTAsImtpZCI6Ik9FTV"
        b"9QUl9TaWduaW5nIiwiZ2lkIjoiMDMwMDAwMDBERUIwOURFQjA5REVCMDlERUIwOTAwMDAiLCJz"
        b"cW4iOiIxIiwicGlkIjoiNTMxNUI2QTNDNzMxRDFCQjYxMkU0MEI5MUZBN0QwQzciLCJkZXYiOn"
        b"siZGV2aWNlSUQiOiIxODAwM0IwMDEwNTEzODM0MzIzMjM1MzYiLCJkZXZpY2VDZXJ0IjoiTUlJ"
        b"Q1pqQ0NBZ3FnQXdJQkFnSUthd2tBQUdZK0hqOEFBekFNQmdncWhrak9QUVFEQWdVQU1JR2FNUX"
        b"N3Q1FZRFZRUUdFd0pIUWpFWE1CVUdBMVVFQ0F3T1EyRnRZbkpwWkdkbGMyaHBjbVV4RlRBVEJn"
        b"TlZCQWNNREZCbGRHVnlZbTl5YjNWbmFERWdNQjRHQTFVRUNnd1hTR1ZoWkd4bGVWUmxZMmh1Yj"
        b"J4dloybGxjeUJNZEdReEZqQVVCZ05WQkFzTURUUXpOVFEyTlRBd01EQXdNREl4SVRBZkJnTlZC"
        b"QU1NR0RFNE1EQXpRakF3TVRBMU1UTTRNelF6TWpNeU16VXpOakFnRncweU5EQTFNVEF4TXpFMk"
        b"5EZGFHQTh5TURVeE1Ea3lOakV6TVRZME4xb3dnWm94Q3pBSkJnTlZCQVlUQWtkQ01SY3dGUVlE"
        b"VlFRSURBNURZVzFpY21sa1oyVnphR2x5WlRFVk1CTUdBMVVFQnd3TVVHVjBaWEppYjNKdmRXZG"
        b"9NU0F3SGdZRFZRUUtEQmRJWldGa2JHVjVWR1ZqYUc1dmJHOW5hV1Z6SUV4MFpERVdNQlFHQTFV"
        b"RUN3d05ORE0xTkRZMU1EQXdNREF3TWpFaE1COEdBMVVFQXd3WU1UZ3dNRE5DTURBeE1EVXhNem"
        b"d6TkRNeU16SXpOVE0yTUZrd0V3WUhLb1pJemowQ0FRWUlLb1pJemowREFRY0RRZ0FFa095TWlu"
        b"UWRCTXkxR1NxNk43MnR3YjZ6Z0tDd2J5OWdIeWloZmdraHBucGxwcUNPNnNkNE9Fc0ljTWdNZG"
        b"RTeUVwaVRRcm8wb3NRVW1OTDBBZ2dpeTZNeU1EQXdEQVlEVlIwVEFRSC9CQUl3QURBTEJnTlZI"
        b"UThFQkFNQ0E4Z3dFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUhBd0l3REFZSUtvWkl6ajBFQXdJRk"
        b"FBTklBREJGQWlCNXJMOEd2VjFNcEJ5eVFGVUhVQ1QrNzZibzQ5QzJEdXZLQkVqL3EzdVkzQUlo"
        b"QU1ZSWVFNzhjaEFGNmtwTkZRNzRhZ0t0dFBReU1EQUdSMUlOeGt0VExlazkiLCJjZXJ0UHViS2"
        b"V5IjoiOTBFQzhDOEE3NDFEMDRDQ0I1MTkyQUJBMzdCREFEQzFCRUIzODBBMEIwNkYyRjYwMUYy"
        b"OEExN0UwOTIxQTY3QTY1QTZBMDhFRUFDNzc4Mzg0QjA4NzBDODBDNzVENEIyMTI5ODkzNDJCQT"
        b"M0QTJDNDE0OThEMkY0MDIwODIyQ0IiLCJwcm9kdWN0aW9uUmVzdWx0IjoicGFzcyJ9fQ..FKaQ"
        b"ydCfpz0Ya86MUWqAEB_hRcH4IwStZvPMgUj8XwaJCo3tquRpBQA6Udzy3hWXf6qB-XVVbJ5-u-"
        b"KmkZzpMw"
    )

    mock_event = MagicMock()
    _d = {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "bulk-onboarding-bucket"},
                    "object": {"key": "1713531973.0.prd"},
                }
            }
        ]
    }

    mock_event.__getitem__.side_effect = _d.__getitem__
    mock_event.decode.side_effect = payload.decode

    # When
    p_rec = runtimescript.ProductionRecord.from_event(mock_event)

    # Then
    assert isinstance(p_rec, runtimescript.ProductionRecord)
    assert p_rec.device_id == "18003B001051383432323536"
    assert p_rec.device_cert == (
        "-----BEGIN CERTIFICATE-----\n"
        "MIICZjCCAgqgAwIBAgIKawkAAGY+Hj8AAzAMBggqhkjOPQQDAgUAMIGaMQswCQYDVQQGEwJHQjE"
        "XMBUGA1UECAwOQ2FtYnJpZGdlc2hpcmUxFTATBgNVBAcMDFBldGVyYm9yb3VnaDEgMB4GA1UECg"
        "wXSGVhZGxleVRlY2hub2xvZ2llcyBMdGQxFjAUBgNVBAsMDTQzNTQ2NTAwMDAwMDIxITAfBgNVB"
        "AMMGDE4MDAzQjAwMTA1MTM4MzQzMjMyMzUzNjAgFw0yNDA1MTAxMzE2NDdaGA8yMDUxMDkyNjEz"
        "MTY0N1owgZoxCzAJBgNVBAYTAkdCMRcwFQYDVQQIDA5DYW1icmlkZ2VzaGlyZTEVMBMGA1UEBww"
        "MUGV0ZXJib3JvdWdoMSAwHgYDVQQKDBdIZWFkbGV5VGVjaG5vbG9naWVzIEx0ZDEWMBQGA1UECw"
        "wNNDM1NDY1MDAwMDAwMjEhMB8GA1UEAwwYMTgwMDNCMDAxMDUxMzgzNDMyMzIzNTM2MFkwEwYHK"
        "oZIzj0CAQYIKoZIzj0DAQcDQgAEkOyMinQdBMy1GSq6N72twb6zgKCwby9gHyihfgkhpnplpqCO"
        "6sd4OEsIcMgMddSyEpiTQro0osQUmNL0Aggiy6MyMDAwDAYDVR0TAQH/BAIwADALBgNVHQ8EBAM"
        "CA8gwEwYDVR0lBAwwCgYIKwYBBQUHAwIwDAYIKoZIzj0EAwIFAANIADBFAiB5rL8GvV1MpByyQF"
        "UHUCT+76bo49C2DuvKBEj/q3uY3AIhAMYIeE78chAF6kpNFQ74agKttPQyMDAGR1INxktTLek9"
        "\n-----END CERTIFICATE-----"
    )


if __name__ == "__main__":
    pytest.main(["-v", "-s", __file__])
