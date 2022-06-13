SCRIPT_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S"
import subprocess
import os


def __get_script_path():
    current_dir = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current_dir, os.pardir, "scripts", "sp_api_connector.py")


def call(args):
    script_file = __get_script_path()
    args.insert(0, script_file)
    args.insert(0, "python3.6")
    try:
        out = subprocess.check_output(args, stderr=subprocess.STDOUT)
        return eval(out, {}, {})
    except subprocess.CalledProcessError as e:
        raise Exception(e.output)


def call_script_list_orders(credentials, date_from, date_to):
    args = [
        "LIST_ORDERS",
        credentials["refresh_token"],
        credentials["lwa_app_id"],
        credentials["lwa_client_secret"],
        credentials["aws_secret_key"],
        credentials["aws_access_key"],
        credentials["role_arn"],
        date_from.strftime(SCRIPT_DATETIME_FORMAT),
        date_to.strftime(SCRIPT_DATETIME_FORMAT),
    ]
    return call(args)


def call_script_get_order(credentials, order_refs):
    if isinstance(order_refs, list):
        order_refs = ",".join(order_refs)
    args = [
        "GET_ORDER",
        credentials["refresh_token"],
        credentials["lwa_app_id"],
        credentials["lwa_client_secret"],
        credentials["aws_secret_key"],
        credentials["aws_access_key"],
        credentials["role_arn"],
        order_refs,
    ]
    return call(args)
