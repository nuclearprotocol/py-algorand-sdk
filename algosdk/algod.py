from urllib.request import Request, urlopen
from urllib import parse
import urllib.error
import json
import base64
from . import error
from . import encoding
from . import constants


class AlgodClient:
    """
    Client class for kmd. Handles all algod requests.

    Args:
        algod_token (str): algod API token
        algod_address (str): algod address
        extended_header (dict, optional): extra header name/value for all requests

    Attributes:
        algod_token (str)
        algod_address (str)
        extended_header (dict)
    """
    def __init__(self, algod_token, algod_address, extended_header=None):
        self.algod_token = algod_token
        self.algod_address = algod_address
        self.extended_header = extended_header

    def algod_request(self, method, requrl, params=None, data=None, opt_header=None):
        """
        Execute a given request.

        Args:
            method (str): request method
            requrl (str): url for the request
            params (dict, optional): parameters for the request
            data (dict, optional): data in the body of the request
            opt_header (dict option): additional header for request

        Returns:
            dict: loaded from json response body
        """
        header = {}

        if self.extended_header:
            header.update(self.extended_header)

        if opt_header:
            header.update(opt_header)

        if requrl not in constants.no_auth:
            header.update({
                constants.algod_auth_header: self.algod_token
                })

        if requrl not in constants.unversioned_paths:
            requrl = constants.api_version_path_prefix + requrl
        if params:
            requrl = requrl + "?" + parse.urlencode(params)

        req = Request(self.algod_address+requrl, headers=header, method=method,
                      data=data)

        try:
            resp = urlopen(req)
        except urllib.error.HTTPError as e:
            e = e.read().decode("utf-8")
            try:
                raise error.AlgodHTTPError(json.loads(e)["message"])
            except:
                raise error.AlgodHTTPError(e)
        return json.loads(resp.read().decode("utf-8"))

    def status(self):
        """Return node status."""
        req = "/status"
        return self.algod_request("GET", req)

    def health(self):
        """Return null if the node is running."""
        req = "/health"
        return self.algod_request("GET", req)

    def status_after_block(self, block_num):
        """
        Return node status immediately after blockNum.

        Args:
            block_num: block number
        """
        req = "/status/wait-for-block-after/" + str(block_num)
        return self.algod_request("GET", req)

    def pending_transactions(self, max_txns=0):
        """
        Return pending transactions.

        Args:
            max_txns (int): maximum number of transactions to return;
                if max_txns is 0, return all pending transactions
        """
        query = {"max": max_txns}
        req = "/transactions/pending"
        return self.algod_request("GET", req, params=query)

    def versions(self):
        """Return algod versions."""
        req = "/versions"
        return self.algod_request("GET", req)

    def ledger_supply(self):
        """Return supply details for node's ledger."""
        req = "/ledger/supply"
        return self.algod_request("GET", req)

    def transactions_by_address(self, address, first=None, last=None,
                                limit=None, from_date=None, to_date=None):
        """
        Return transactions for an address. If indexer is not enabled, you can
        search by date and you do not have to specify first and last rounds.

        Args:
            address (str): account public key
            first (int, optional): no transactions before this block will be
                returned
            last (int, optional): no transactions after this block will be
                returned; defaults to last round
            limit (int, optional): maximum number of transactions to return;
                default is 100
            from_date (str, optional): no transactions before this date will be
                returned; format YYYY-MM-DD
            to_date (str, optional): no transactions after this date will be
                returned; format YYYY-MM-DD
        """
        query = dict()
        if first is not None:
            query["firstRound"] = first
        if last is not None:
            query["lastRound"] = last
        if limit is not None:
            query["max"] = limit
        if to_date is not None:
            query["toDate"] = to_date
        if from_date is not None:
            query["fromDate"] = from_date
        req = "/account/" + address + "/transactions"
        return self.algod_request("GET", req, params=query)

    def account_info(self, address):
        """
        Return account information.

        Args:
            address (str): account public key
        """
        req = "/account/" + address
        return self.algod_request("GET", req)

    def transaction_info(self, address, transaction_id):
        """
        Return transaction information.

        Args:
            address (str): account public key
            transaction_id (str): transaction ID
        """
        req = "/account/" + address + "/transaction/" + transaction_id
        return self.algod_request("GET", req)

    def pending_transaction_info(self, transaction_id):
        """
        Return transaction information for a pending transaction.

        Args:
            transaction_id (str): transaction ID
        """
        req = "/transactions/pending/" + transaction_id
        return self.algod_request("GET", req)

    def transaction_by_id(self, transaction_id):
        """
        Return transaction information; only works if indexer is enabled.

        Args:
            transaction_id (str): transaction ID
        """
        req = "/transaction/" + transaction_id
        return self.algod_request("GET", req)

    def suggested_fee(self):
        """Return suggested transaction fee."""
        req = "/transactions/fee"
        return self.algod_request("GET", req)

    def suggested_params(self):
        """Return suggested transaction parameters."""
        req = "/transactions/params"
        return self.algod_request("GET", req)

    def send_raw_transaction(self, txn, request_header=None):
        """
        Broadcast a signed transaction to the network.

        Args:
            txn (str): transaction to send, encoded in base64
            request_header (dict, optional): additional header for request

        Returns:
            str: transaction ID
        """
        txn = base64.b64decode(txn)
        req = "/transactions"
        return self.algod_request("POST", req, data=txn, opt_header=request_header)["txId"]

    def send_transaction(self, txn, request_header=None):
        """
        Broadcast a signed transaction object to the network.

        Args:
            txn (SignedTransaction or MultisigTransaction): transaction to send
            request_header (dict, optional): additional header for request

        Returns:
            str: transaction ID
        """
        return self.send_raw_transaction(encoding.msgpack_encode(txn), request_header)

    def block_info(self, round):
        """
        Return block information.

        Args:
            round (int): block number
        """
        req = "/block/" + str(round)
        return self.algod_request("GET", req)
