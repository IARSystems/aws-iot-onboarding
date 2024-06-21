"""This Script can be used to remove resources on the IoT Core service.
It deletes all things in a given group and any attached certificates.
"""

import argparse
import logging
import boto3

_log = logging.getLogger(__name__)


def get_things_in_group_by_region(group_name: str, region: str):
    """Yield Thing names contained in a Thing Group."""
    iot_client = boto3.client("iot", region)

    # Using empty string as a sentinal value (empty strings are not None).
    next_token = ""

    while next_token is not None:
        response = iot_client.list_things_in_thing_group(
            thingGroupName=group_name, nextToken=next_token, maxResults=100
        )

        yield from response["things"]

        next_token = response.get("nextToken")


def _parse_args():
    """Parse the command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("region_name", help="The region in which the group exists")
    parser.add_argument(
        "thing_group_name", help="Thing group name to delete (along with its contents)"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Logging verbosity")
    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.INFO)

    return args


def main():
    """Delete the named Thing Group, all Things within it, and all associated Certificates."""
    args = _parse_args()
    iot_client = boto3.client("iot", args.region_name)

    for thing in get_things_in_group_by_region(args.thing_group_name, args.region_name):
        associated_principals = iot_client.list_thing_principals(thingName=thing)["principals"]

        # Detach all principals and, if the principals are certificates, delete them
        # (A principal can be X.509 certificate, IAM user, group, role etc.)
        for associated_principal in associated_principals:
            iot_client.detach_thing_principal(thingName=thing, principal=associated_principal)
            parts = associated_principal.split(":cert/")

            if len(parts) > 1:
                _log.info("deleting certificate: %s", parts[1])
                iot_client.update_certificate(certificateId=parts[1], newStatus="INACTIVE")
                response = iot_client.list_attached_policies(target=associated_principal)
                for policy in response["policies"]:
                    iot_client.detach_principal_policy(
                        policyName=policy, principal=associated_principal)
                iot_client.delete_certificate(certificateId=parts[1])


        _log.info("deleting thing: %s", thing)
        iot_client.delete_thing(thingName=thing)


if __name__ == "__main__":
    main()
