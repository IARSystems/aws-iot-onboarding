"""Perform runtime tasks on the production record files in an S3 bucket.

The function is triggered by an S3 bucket file upload event. The function
reads the production record files in the S3 bucket, extracts the x509 device
certificate PEM, creates a "Certificate" resource on the AWS IoT Service using
the extracted x509 certificate, creates a "Thing" resource on the AWS IoT
Service with `name = common_name`, and attaches the "Certificate" and "Thing"
resource.
"""

import binascii
import os
from dataclasses import dataclass

import boto3
from jwcrypto import jwk, jws
from cryptography import x509


@dataclass(frozen=True, kw_only=True, slots=True)
class ProductionRecord:
    """A representation of a production record file."""

    common_name: str
    device_cert: str
    _bucket_name: str
    _key: str
    _jws_obj: jws.JWS

    def __post_init__(self):
        """Validate the production record signature.

        This is done post-init because we want to guarantee that the signature
        is verified even if the caller does not instance the object using the
        `from_event` method.

        @raises jwscrypto.jws.InvalidJWSSignature if the signature is invalid
        """
        pub = binascii.unhexlify(os.environ["PUBLIC_KEY"])
        x, y = (jwk.base64url_encode(_) for _ in [pub[:32], pub[32:]])
        public_jwk = jwk.JWK(x=x, y=y, crv="P-256", kty="EC")

        # NOTE: This will raise an exception if the signature is invalid which
        # AWS claims to handle gracefully:
        # https://docs.aws.amazon.com/lambda/latest/dg/python-exceptions.html
        self._jws_obj.verify(public_jwk)

    @classmethod
    def from_event(cls, event):
        """Get the production record file from the S3 bucket, extract
        the x509 device certificate and the common name.
        """
        jws_obj = jws.JWS()
        jws_obj.deserialize(
            boto3.client("s3")
            .get_object(
                Bucket=(bucket_name := event["Records"][0]["s3"]["bucket"]["name"]),
                Key=(key := event["Records"][0]["s3"]["object"]["key"]),
            )
            .get("Body")
            .read()
            .decode("utf-8")
        )

        if (
            not isinstance(jws_obj.jose_header, dict)
            or (clear_text_json := jws_obj.jose_header.get("dev")) is None
        ):
            raise ValueError("Invalid JWS object")

        formatted_cert = os.linesep.join(
            [
                "-----BEGIN CERTIFICATE-----",
                clear_text_json["deviceCert"],
                "-----END CERTIFICATE-----",
            ]
        )
        cert_obj = x509.load_pem_x509_certificate(formatted_cert.encode("utf-8"))
        common_name_items = cert_obj.subject.get_attributes_for_oid(x509.NameOID.COMMON_NAME)
        common_name = common_name_items[0].value if len(common_name_items) else None

        return cls(
            common_name=common_name,
            device_cert=formatted_cert,
            _bucket_name=bucket_name,
            _key=key,
            _jws_obj=jws_obj,
        )

    def __del__(self):
        """Delete the production record file from the S3 bucket."""
        boto3.client("s3").delete_object(Bucket=self._bucket_name, Key=self._key)

    def onboard_device(self, thing_group_name: str):
        """Onboard the device to the AWS IoT Core service."""
        iot_client = boto3.client("iot")
        response = iot_client.create_thing(thingName=self.common_name)
        thing_arn = response["thingArn"]

        iot_client.add_thing_to_thing_group(
            thingGroupName=thing_group_name,
            thingGroupArn=iot_client.describe_thing_group(thingGroupName=thing_group_name)[
                "thingGroupArn"
            ],
            thingName=self.common_name,
            thingArn=thing_arn,
        )
        iot_client.attach_thing_principal(
            thingName=self.common_name,
            principal=iot_client.register_certificate_without_ca(
                certificatePem=self.device_cert,
                status="ACTIVE",
            )["certificateArn"],
        )


def lambda_handler(event, _context):
    """Process the production record in the S3 bucket.

    If the production record is valid (ie. the signature is verified by the
    public key in the config file), the device is onboarded. Otherwise, the
    verification fails and an exception bubbles up to AWS Lambda before the
    "Thing" and "Certificate" resources are created. If device onboarding is
    successful, the production record is deleted from the s3 bucket.
    """
    production_record = ProductionRecord.from_event(event)

    production_record.onboard_device(thing_group_name=os.environ["THING_GROUP_NAME"])
