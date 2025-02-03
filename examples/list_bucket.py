import os

import swiftclient

_authurl = os.environ["OS_AUTH_URL"]
_auth_version = os.environ["OS_IDENTITY_API_VERSION"]
_user = os.environ["OS_USERNAME"]
_key = os.environ["OS_PASSWORD"]
_os_options = {
    "user_domain_name": os.environ["OS_USER_DOMAIN_NAME"],
    "project_domain_name": os.environ["OS_USER_DOMAIN_NAME"],
    "project_name": os.environ["OS_PROJECT_NAME"],
}

conn = swiftclient.Connection(
    authurl=_authurl,
    user=_user,
    key=_key,
    os_options=_os_options,
    auth_version=_auth_version,
)

bucket_name = "2009846-test1"
for info in conn.get_container(bucket_name)[1]:
    print("{}\t{}\t{}".format(info["name"], info["bytes"], info["last_modified"]))

conn.close()
